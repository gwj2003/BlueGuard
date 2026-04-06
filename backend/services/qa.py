from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from graph_chain import invoke_qa
from qa_cache import qa_cache
from repositories.species_repository import list_species_names


def ask_question(question: str, db: Session) -> dict:
    value = (question or "").strip()
    if not value:
        raise HTTPException(status_code=400, detail="问题不能为空")

    cached = qa_cache.get(value)
    if cached:
        return cached

    try:
        response = invoke_qa(value, list_species_names(db))
        payload = {
            "answer": response.get("result", "无法获取回答"),
            "cypher": response.get("generated_cypher", ""),
            "from_template": bool(response.get("from_template", False)),
        }
        qa_cache.set(value, payload)
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"QA Error: {exc}")
        raise HTTPException(status_code=503, detail=f"暂时无法回答: {type(exc).__name__}") from exc


def get_suggestions(species: str) -> dict[str, list[str]]:
    return {
        "suggestions": [
            f"介绍一下 {species}",
            f"{species} 的危害是什么？",
            f"如何防治 {species}？",
            f"{species} 属于什么分类？",
            f"{species} 的原产地在哪？",
        ]
    }
