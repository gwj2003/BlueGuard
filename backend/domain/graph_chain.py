import os
import re
from typing import Any, Optional

from langchain_community.graphs import Neo4jGraph
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from config import get_settings


def _normalize_cypher_query(query: Any) -> str:
    """Normalize LLM-generated Cypher text for safer execution."""
    if hasattr(query, "text"):
        query = getattr(query, "text")
    q = str(query or "").strip()
    q = re.sub(r"^```(?:cypher)?\s*", "", q, flags=re.IGNORECASE)
    q = re.sub(r"\s*```$", "", q)
    q = re.sub(r"^cypher\s+", "", q, flags=re.IGNORECASE)
    return q.strip()


def _strip_cypher_string_literals(cypher: str) -> str:
    s = re.sub(r"'(?:[^'\\]|\\.)*'", " ", cypher)
    s = re.sub(r'"(?:[^"\\]|\\.)*"', " ", s)
    s = re.sub(r"`(?:[^`\\]|\\.)*`", " ", s)
    return s


_WRITE_CYPHER = re.compile(
    r"(?<![.\w])("
    r"CREATE|MERGE|DELETE|DETACH|SET|REMOVE|FOREACH|LOAD\s+CSV|"
    r"GRANT|REVOKE|ALTER|"
    r"DROP\s+(CONSTRAINT|INDEX|DATABASE)|STOP\s+DATABASE"
    r")(?![\w])",
    re.IGNORECASE | re.DOTALL,
)

_CALL_CYPHER = re.compile(r"(?<![.\w])CALL(?![\w])", re.IGNORECASE)


MANUAL_STRUCTURED_SCHEMA = {
        "node_props": {
            "Species": [{"property": "name", "type": "STRING"}],
            "Taxonomy": [{"property": "name", "type": "STRING"}],
            "Origin": [{"property": "name", "type": "STRING"}],
            "Province": [{"property": "name", "type": "STRING"}],
            "City": [{"property": "name", "type": "STRING"}],
            "District": [{"property": "name", "type": "STRING"}],
            "Region": [{"property": "name", "type": "STRING"}],
            "Habitat": [{"property": "name", "type": "STRING"}],
            "Pathway": [{"property": "name", "type": "STRING"}],
            "Target": [{"property": "name", "type": "STRING"}],
            "Impact": [{"property": "name", "type": "STRING"}],
            "Control": [{"property": "name", "type": "STRING"}],
            "Event": [{"property": "name", "type": "STRING"}],
            "TimePeriod": [{"property": "name", "type": "STRING"}],
            "Morphology": [{"property": "name", "type": "STRING"}],
            "Habit": [{"property": "name", "type": "STRING"}]
        },
        "relationships": [
            {"start": "Species", "type": "HAS_ALIAS", "end": "Species"},
            {"start": "Species", "type": "BELONGS_TO", "end": "Taxonomy"},
            {"start": "Species", "type": "NATIVE_TO", "end": "Origin"},
            {"start": "Species", "type": "HAS_MORPHOLOGY", "end": "Morphology"},
            {"start": "Species", "type": "HAS_HABIT", "end": "Habit"},
            {"start": "Species", "type": "REPORTED_IN", "end": "Province"},
            {"start": "Species", "type": "REPORTED_IN", "end": "City"},
            {"start": "Species", "type": "REPORTED_IN", "end": "District"},
            {"start": "Species", "type": "HAS_EVENT", "end": "Event"},
            {"start": "District", "type": "LOCATED_IN", "end": "City"},
            {"start": "City", "type": "LOCATED_IN", "end": "Province"},
            {"start": "Origin", "type": "LOCATED_IN", "end": "Origin"},
            {"start": "Region", "type": "LOCATED_IN", "end": "Region"},
            {"start": "Species", "type": "THRIVES_IN", "end": "Habitat"},
            {"start": "Species", "type": "INTRODUCED_VIA", "end": "Pathway"},
            {"start": "Species", "type": "PREYS_ON", "end": "Target"},
            {"start": "Species", "type": "COMPETES_WITH", "end": "Target"},
            {"start": "Species", "type": "CAUSES", "end": "Impact"},
            {"start": "Species", "type": "AFFECTS", "end": "Target"},
            {"start": "Species", "type": "AFFECTS", "end": "Region"},
            {"start": "Event", "type": "AFFECTS", "end": "Target"},
            {"start": "Event", "type": "AFFECTS", "end": "Region"},
            {"start": "Species", "type": "MITIGATES", "end": "Control"}, 
            {"start": "Control", "type": "MITIGATES", "end": "Impact"},
            {"start": "Control", "type": "MITIGATES", "end": "Event"},
            {"start": "Event", "type": "DURING", "end": "TimePeriod"},
            {"start": "Event", "type": "CAUSES", "end": "Impact"},
            {"start": "Event", "type": "CAUSES", "end": "Event"},
            {"start": "Event", "type": "CONTAINS", "end": "Event"},
            {"start": "Region", "type": "CONTAINS", "end": "Region"},
            {"start": "Region", "type": "SPREAD_RISK_TO", "end": "Region"}
        ],
        "metadata": {}
    }


def assert_read_only_cypher(cypher: str) -> None:
    if not (cypher or "").strip():
        return
    body = _strip_cypher_string_literals(cypher)
    if _WRITE_CYPHER.search(body):
        raise ValueError("生成的 Cypher 含写操作或受限关键字，已拒绝执行")
    core = body.rstrip().rstrip(";").strip()
    if ";" in core:
        raise ValueError("拒绝执行包含多条语句的 Cypher")
    if get_settings().cypher_block_call and _CALL_CYPHER.search(body):
        raise ValueError("当前策略禁止 CALL 语句")


class ReadOnlyNeo4jGraph(Neo4jGraph):
    def query(self, query: str, params: Optional[dict] = None):
        normalized_query = _normalize_cypher_query(query)
        assert_read_only_cypher(normalized_query)
        try:
            return super().query(normalized_query, params or {})
        except Exception as exc:
            # Compatibility fallback for driver/library mismatch around Query objects.
            if "Query object is only supported for session.run" in str(exc):
                with self._driver.session(database=self._database) as session:  # type: ignore[attr-defined]
                    result = session.run(normalized_query, params or {})
                    return [record.data() for record in result]
            raise


_chain: Any = None
_neo4j_graph_instance: Optional[ReadOnlyNeo4jGraph] = None
_llm: Optional[ChatOpenAI] = None


SIMPLE_TEMPLATE_CYPHER = """
MATCH (s:Species)
WHERE toLower(s.name) CONTAINS toLower($needle)
OPTIONAL MATCH (s)-[r]->(n)
RETURN s.name AS species, type(r) AS rel_type, labels(n) AS nlabels, coalesce(n.name, '') AS related
LIMIT 40
"""


def get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        s = get_settings()
        key = s.openai_api_key or os.getenv("OPENAI_API_KEY", "")
        os.environ["OPENAI_API_KEY"] = key
        os.environ["OPENAI_API_BASE"] = s.openai_api_base or os.getenv("OPENAI_API_BASE", "")
        _llm = ChatOpenAI(model=s.llm_model, temperature=0, timeout=120)
    return _llm


def get_neo4j_graph() -> Optional[ReadOnlyNeo4jGraph]:
    get_chain()
    return _neo4j_graph_instance


def invalidate_chain():
    global _chain, _neo4j_graph_instance, _llm
    _chain = None
    _neo4j_graph_instance = None
    _llm = None


def _build_chain():
    global _chain, _neo4j_graph_instance
    s = get_settings()
    graph = None
    try:
        graph = ReadOnlyNeo4jGraph(
            url=s.neo4j_uri,
            username=s.neo4j_username,
            password=s.neo4j_password,
            database=s.neo4j_database,
            timeout=s.neo4j_query_timeout,
            refresh_schema=False,
        )
        if s.neo4j_refresh_schema:
            try:
                graph.refresh_schema()
            except Exception as e:
                print(f"Neo4j refresh_schema 失败，使用手工 schema: {e}")
                graph.structured_schema = MANUAL_STRUCTURED_SCHEMA
        else:
            graph.structured_schema = MANUAL_STRUCTURED_SCHEMA
    except Exception as e:
        print(f"警告：Neo4j 连接失败 ({e})，使用离线模式")
        graph = None

    llm = get_llm()

    CYPHER_GENERATION_TEMPLATE = """
        任务：将用户问题转换为 Neo4j Cypher 查询。
        Schema：{schema}
        说明与红线规则：
          1. 仅使用 Schema 中存在的关系和节点类型，禁止臆造关系名或标签。
          2. 节点名称模糊匹配优先使用 CONTAINS，但只在确实需要模糊检索时使用。
                    3. 关系类型写法必须符合 Neo4j 语法：多个关系类型只写成 `:CAUSES|AFFECTS`，不要写成 `:CAUSES|:AFFECTS`。
                         另外，尽量不要把“关系类型并列”与“变长路径 *0..1/*1..2”写在同一个模式里；如果需要多关系或多跳查询，优先拆成多个 MATCH / OPTIONAL MATCH。
                4. 【重要属性】：
           - REPORTED_IN 关系可能带有 `year` (年份) 和 `status` 属性。
           - MITIGATES 关系带有 `method` (如:化学/物理/生物) 和 `type` (主要/辅助) 属性。
           - CAUSES 关系带有 `type` (直接/间接) 属性。
              - SPREAD_RISK_TO 关系带有 `confidence` (高/中/低) 属性。
              - PREYS_ON / COMPETES_WITH 关系带有 `severity` (高/中/低) 属性。
                    5. 【查询策略】：
              - 查分布时优先用 Species-[:REPORTED_IN]->(Province/City/District)。
              - 查入侵史、事件、治理行动时优先用 Species-[:HAS_EVENT]->(Event)，再从 Event 继续查 DURING / AFTER / CAUSES / MITIGATES。
              - 查省市区层级时，可以补充使用 District-[:LOCATED_IN]->City、City-[:LOCATED_IN]->Province。
              - 查区域扩散时优先用 Region-[:SPREAD_RISK_TO]->Region 或 Region-[:CONTAINS]->Region。
              - 查防治手段时优先用 Species-[:MITIGATES]->(Control/Event/Impact)。
              - 查引入途径、生境、别名、分类、危害时分别使用 INTRODUCED_VIA、THRIVES_IN、HAS_ALIAS、BELONGS_TO、CAUSES/AFFECTS/PREYS_ON/COMPETES_WITH。
                    6. 如果问题涉及事件、时间或空间泛指词，优先按 Event / Region / TimePeriod 处理，不要强行映射到 Province。
                    7. 只输出纯粹的 Cypher 代码，不要任何 Markdown 格式或多余解释。
        用户问题：{question}
        Cypher："""

    CYPHER_PROMPT = PromptTemplate(
        input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
    )

    qa_prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""你是一个生物入侵领域的专家。基于以下数据库信息回答问题：\n{context}\n问题：{question}\n回答：""",
    )

    if graph:
        _neo4j_graph_instance = graph
        _chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            verbose=True,
            allow_dangerous_requests=True,
            validate_cypher=True,
            cypher_prompt=CYPHER_PROMPT,
            qa_prompt=qa_prompt,
        )
    else:
        _neo4j_graph_instance = None

        class SimpleChain:
            def __init__(self, llm_):
                self.llm = llm_

            def invoke(self, input_dict):
                question = input_dict.get("query", "")
                prompt = f"""你是一个水生入侵生物的专家。请回答以下问题：

问题：{question}

基于你的知识库，请提供一个详细的回答。"""
                result = self.llm.invoke(prompt)
                return {
                    "result": result.content if hasattr(result, "content") else str(result),
                    "generated_cypher": "",
                }

        _chain = SimpleChain(llm)

    return _chain


def get_chain(force_refresh: bool = False):
    global _chain
    if force_refresh:
        invalidate_chain()
    if _chain is None:
        _build_chain()
    return _chain


def _extract_species_needle(question: str, gbif_names: list) -> Optional[str]:
    q = (question or '').strip()
    if len(q) > 200:
        return None
    if not re.search(r"(介绍|危害|防治|分类|原产地|是什么|什么是|哪种|如何|怎样|请问|查询|说说|讲讲)", q):
        return None

    names_sorted = sorted((name for name in gbif_names if name), key=len, reverse=True)
    for name in names_sorted:
        if name in q:
            return name

    fallback_patterns = [
        r"(?:介绍一下|介绍下|介绍|什么是|请介绍|简述|说说|讲讲|了解一下)\s*[:：]?\s*([^\s，。！？?、:：]{2,20})",
        r"(?:关于|针对|对于)\s*([^\s，。！？?、:：]{2,20})\s*(?:介绍|是什么|如何|危害|防治)",
    ]
    for pattern in fallback_patterns:
        match = re.search(pattern, q)
        if match:
            candidate = match.group(1).strip()
            if candidate:
                return candidate
    return None


def try_simple_template_qa(question: str, gbif_names: list) -> Optional[dict]:
    """命中简单模板时：1 次参数化 Cypher + 1 次 LLM 总结，跳过 Cypher 生成 LLM。"""
    needle = _extract_species_needle(question, gbif_names)
    if not needle:
        return None

    graph = get_neo4j_graph()
    if graph is None:
        return None

    try:
        rows = graph.query(SIMPLE_TEMPLATE_CYPHER.strip(), params={"needle": needle})
    except Exception as exc:
        print(f"simple template Cypher 失败: {exc}")
        return None

    if not rows:
        return None

    llm = get_llm()
    context = str(rows)[:8000]
    prompt = (
        "你是水生入侵生物专家。根据下列图谱查询结果回答用户问题；若信息不足请说明。\n"
        f"图谱数据：\n{context}\n\n用户问题：{question}\n回答："
    )
    result = llm.invoke(prompt)
    text = result.content if hasattr(result, "content") else str(result)
    return {
        "result": text,
        "generated_cypher": SIMPLE_TEMPLATE_CYPHER.strip(),
        "from_template": True,
    }

def invoke_qa(question: str, gbif_names: list) -> dict:
    template_result = try_simple_template_qa(question, gbif_names)
    if template_result:
        return template_result
    chain = get_chain()
    return chain.invoke({"query": question})
