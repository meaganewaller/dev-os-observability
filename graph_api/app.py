"""
Minimal read-only Cypher bridge for Grafana (JSON API) or curl.

Set MG_HOST / MG_PORT. Only queries starting with MATCH or CALL are accepted.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from gqlalchemy import Memgraph
from pydantic import BaseModel, Field

ALLOWED = re.compile(r"^\s*(MATCH|CALL|SHOW|RETURN|WITH)\b", re.I)
FORBIDDEN = re.compile(r"\b(CREATE|MERGE|DELETE|SET|REMOVE|DROP)\b", re.I)

app = FastAPI(title="Dev OS Graph API", version="0.1.0")


def _db() -> Memgraph:
    return Memgraph(
        host=os.environ.get("MG_HOST", "127.0.0.1"),
        port=int(os.environ.get("MG_PORT", "7687")),
    )


class CypherBody(BaseModel):
    query: str = Field(..., min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/cypher")
def run_cypher(body: CypherBody) -> List[Dict[str, Any]]:
    q = body.query.strip()
    if FORBIDDEN.search(q):
        raise HTTPException(status_code=400, detail="Write or DDL queries are not allowed")
    if not ALLOWED.match(q):
        raise HTTPException(status_code=400, detail="Query must start with MATCH, CALL, SHOW, or RETURN")
    db = _db()
    rows: List[Dict[str, Any]] = []
    for row in db.execute_and_fetch(q, body.parameters):
        rows.append(dict(row))
    return rows
