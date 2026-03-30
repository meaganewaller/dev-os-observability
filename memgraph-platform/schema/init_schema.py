#!/usr/bin/env python3
"""Apply Memgraph indexes and unique constraints via CALL schema.assert (idempotent)."""

from __future__ import annotations

import os
import sys

from gqlalchemy import Memgraph

from indexes import indices_to_cypher_literal, uniques_to_cypher_literal


def main() -> int:
    host = os.environ.get("MG_HOST", "127.0.0.1")
    port = int(os.environ.get("MG_PORT", "7687"))

    im = indices_to_cypher_literal()
    um = uniques_to_cypher_literal()
    query = f"""
CALL schema.assert({im}, {um}, {{}}, false)
YIELD action, label, key, keys, unique
RETURN action, label, key, keys, unique;
"""
    db = Memgraph(host=host, port=port)
    for row in db.execute_and_fetch(query):
        print(row)
    print("schema.assert completed OK", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
