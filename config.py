from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyfedappwrap.learning.run_runfig import AppConfig, AppInputConfig, AppOutputConfig


@dataclass
class SqlSelectAppConfig(AppConfig):
    sql_distribution: str = "postgres"  # postgres|mysql|sqlite
    host: str = "host.docker.internal"
    port: int = 5432
    database: str = "demo"  # for sqlite: file path or ':memory:'
    username: str = "demo"
    password: str = "demo"
    sql_select: str = "SELECT * FROM patients LIMIT 10"


@dataclass
class SqlSelectAppInputConfig(AppInputConfig):
    # no inputs required
    pass


@dataclass
class SqlSelectAppOutputConfig(AppOutputConfig):
    dataset: Path | None = None
