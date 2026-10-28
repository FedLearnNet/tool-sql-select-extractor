from __future__ import annotations

import re

from pyfedappwrap.engine.helper.url_helper import localhost_to_docker_host
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config import SqlSelectAppConfig

_BLOCKED_KEYWORDS = [
    # DML / DDL / privilege / execution
    "insert", "update", "delete", "drop", "alter", "create", "truncate",
    "merge", "grant", "revoke", "call", "execute", "exec", "prepare",
    "comment", "vacuum", "analyze", "refresh", "reindex",
    # common data export / file touching
    "copy", "load", "attach", "detach",
]

# SELECT ... INTO writes a new table in some SQL dialects -> block it
_BLOCKED_PATTERNS = [
    r"\binto\b",  # SELECT ... INTO ...
    r"\bfor\s+update\b",  # locks rows / can be abused
]


def _strip_sql_comments(sql: str) -> str:
    """
    Remove '-- ...' and '/* ... */' comments (simple, not perfect but sufficient here).
    """
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--.*?$", " ", sql, flags=re.MULTILINE)
    return sql


def ensure_select_only(sql: str) -> str:
    """
    Allow only SELECT (or WITH ... SELECT) statements.
    Block anything that looks like write/ddl/privileged execution, multi-statements, or SELECT INTO.

    Returns: sanitized SQL string
    Raises: ValueError on violation
    """
    if not isinstance(sql, str):
        raise ValueError("sql_select must be a string.")
    s = sql.strip()
    if not s:
        raise ValueError("sql_select is empty.")

    s = _strip_sql_comments(s).strip()
    if not s:
        raise ValueError("sql_select is empty after removing comments.")

    # Disallow multiple statements. Allow exactly one optional trailing semicolon.
    # Example allowed: "SELECT ...;" (one)
    # Example blocked: "SELECT ...; DROP TABLE x;"
    semi_count = s.count(";")
    if semi_count > 1:
        raise ValueError("Multiple SQL statements are not allowed.")
    if semi_count == 1 and not s.rstrip().endswith(";"):
        raise ValueError("Semicolon is only allowed as a trailing terminator.")
    s = s.rstrip().rstrip(";").strip()

    # Must start with SELECT or WITH
    head = s.lstrip().lower()
    if not (head.startswith("select") or head.startswith("with")):
        raise ValueError("Only SELECT statements are allowed (SELECT or WITH ... SELECT).")

    # Block keywords anywhere as whole words
    for kw in _BLOCKED_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", head, flags=re.IGNORECASE):
            raise ValueError(f"Disallowed SQL keyword detected: {kw}")

    # Block risky patterns
    for pat in _BLOCKED_PATTERNS:
        if re.search(pat, head, flags=re.IGNORECASE):
            raise ValueError(f"Disallowed SQL pattern detected: {pat}")

    # If starts with WITH, ensure there's a SELECT later (basic sanity)
    if head.startswith("with") and not re.search(r"\bselect\b", head, flags=re.IGNORECASE):
        raise ValueError("WITH query must contain a SELECT.")

    return s


def build_engine(cfg: SqlSelectAppConfig) -> Engine:
    dist = (cfg.sql_distribution or "").strip().lower()
    if dist not in {"postgres", "mysql", "sqlite"}:
        raise ValueError("sql_distribution must be one of: postgres, mysql, sqlite")

    if dist == "sqlite":
        # database: ':memory:' or file path
        db = cfg.database.strip()
        if not db:
            raise ValueError("database must be set for sqlite (path or ':memory:').")
        url = f"sqlite:///{db}" if db != ":memory:" else "sqlite:///:memory:"
        return create_engine(url, future=True)

    # For networked DBs
    host = cfg.host.strip()
    if not host:
        raise ValueError("host must be set.")
    host = localhost_to_docker_host(host)
    db = cfg.database.strip()
    if not db:
        raise ValueError("database must be set.")
    user = cfg.username.strip()
    if not user:
        raise ValueError("username must be set.")

    port = int(cfg.port)

    if dist == "postgres":
        # needs: psycopg2-binary (simple) or psycopg
        url = f"postgresql+psycopg2://{user}:{cfg.password}@{host}:{port}/{db}"
        return create_engine(url, pool_pre_ping=True, future=True)

    # mysql
    # needs: pymysql
    url = f"mysql+pymysql://{user}:{cfg.password}@{host}:{port}/{db}"
    return create_engine(url, pool_pre_ping=True, future=True)
