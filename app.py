from __future__ import annotations

import logging

import pandas as pd
from pyfedappwrap.types.databaseadopter.base_importer import BaseExtractorAdopterAPP
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from config import SqlSelectAppConfig, SqlSelectAppInputConfig, SqlSelectAppOutputConfig
from sql import ensure_select_only, build_engine


class SqlSelectExtractorAPP(
    BaseExtractorAdopterAPP[SqlSelectAppConfig, SqlSelectAppInputConfig, SqlSelectAppOutputConfig]
):
    """
    SQL Select Extractor (Database Adopter)
    - Connects to a configured SQL database
    - Executes a single SELECT statement (read-only)
    - Exports the result as CSV
    """

    def run_adopter(self) -> SqlSelectAppOutputConfig:
        query = ensure_select_only(str(self.config.sql_select))

        engine = build_engine(self.config)

        try:
            df = pd.read_sql_query(sql=text(query), con=engine)
        except SQLAlchemyError as e:
            self.logger.error(e)
            raise RuntimeError(f"SQL execution failed: {e}") from e
        finally:
            try:
                engine.dispose()
            except Exception as ec:
                logging.error(ec)
                raise RuntimeError(f"SQL dispose failed: {ec}") from ec

        self.logger.info(f"Executed query: {query}")
        out_path = self.save_df(df, "sql_select_result")

        self.logger.info("Found rows: %d, columns: %d", df.shape[0], df.shape[1])
        self.logger.info(f"Saved result: {out_path}")
        self.send_metric("rows", float(df.shape[0]), 0.0)
        self.send_metric("cols", float(df.shape[1]), 0.0)

        return SqlSelectAppOutputConfig(dataset=out_path)
