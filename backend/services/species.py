from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domain.graph_chain import get_chain
from repositories.species_repository import list_locations_by_species, list_species_names


def list_species(db: Session) -> dict[str, list[str]]:
    return {"species": list_species_names(db)}


def resolve_species_for_graph_qa(raw: str, db: Session) -> tuple[str, bool]:
    value = (raw or "").strip()
    if not value:
        return "", False

    names = list_species_names(db)
    if value in names:
        return value, True

    lowered = {name.lower(): name for name in names}
    if value.lower() in lowered:
        return lowered[value.lower()], True

    return value, False


def get_species_info(species: str, db: Session) -> dict:
    canonical, known = resolve_species_for_graph_qa(species, db)
    display = canonical or species.strip()
    if known:
        cypher_target = canonical.replace("\\", "\\\\").replace("'", "\\'")
        graph_hint = (
            f"【图谱检索提示】本平台该物种标准名为“{canonical}”。"
            f"生成 Cypher 查询 Species 时，请对 s.name 使用模糊匹配"
            f"（例如 toLower(s.name) CONTAINS toLower('{cypher_target}')），不要假设图中名称与平台完全一致。\n"
        )
    else:
        graph_hint = (
            f"【图谱检索提示】用户输入为“{species.strip()}”；图中 Species.name 可能与平台 CSV 文件名不同，"
            "请用 CONTAINS、toLower 等做模糊匹配并尝试常见别名。\n"
        )

    question = (
        graph_hint
        + f"请介绍“{display}”的基本信息、危害与防治方法。若图谱查询无结果请在回答中说明。"
    )
    try:
        response = get_chain().invoke({"query": question})
        return {
            "info": response["result"],
            "cypher": response.get("generated_cypher", ""),
            "canonical_species": canonical if known else None,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"get_species_info: {exc}")
        raise HTTPException(status_code=503, detail="暂时无法获取知识图谱结果。") from exc


def list_species_locations(species: str, db: Session) -> dict[str, list[dict]]:
    try:
        return {"locations": list_locations_by_species(db, species, limit=1000)}
    except Exception as exc:
        print(f"Get locations error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
