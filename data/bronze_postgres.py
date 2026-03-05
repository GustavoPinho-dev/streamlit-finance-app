import os
from datetime import datetime
from typing import Any

import pandas as pd
import psycopg2
from psycopg2.extras import Json


class BronzePostgresRepository:
  """Persistência da camada Bronze no Postgres."""

  def __init__(self, database_url: str | None = None):
    self.database_url = database_url or os.getenv("DATABASE_URL")

  def is_enabled(self) -> bool:
    return bool(self.database_url)

  def _get_connection(self):
    if not self.database_url:
      raise ValueError("DATABASE_URL não configurada para camada Bronze.")
    return psycopg2.connect(self.database_url)

  def ensure_schema(self):
    """Cria schema/tabela bronze caso não existam."""
    with self._get_connection() as conn:
      with conn.cursor() as cur:
        cur.execute(
          """
          CREATE SCHEMA IF NOT EXISTS bronze;

          CREATE TABLE IF NOT EXISTS bronze.sheet_events (
            id BIGSERIAL PRIMARY KEY,
            source_sheet_id TEXT NOT NULL,
            source_tab_name TEXT NOT NULL,
            source_event_type TEXT NOT NULL,
            ingestion_ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            row_data JSONB NOT NULL,
            row_values JSONB,
            row_hash TEXT,
            inserted_by TEXT
          );

          CREATE INDEX IF NOT EXISTS idx_sheet_events_tab_name
            ON bronze.sheet_events (source_tab_name);

          CREATE INDEX IF NOT EXISTS idx_sheet_events_ingestion_ts
            ON bronze.sheet_events (ingestion_ts);
          """
        )
      conn.commit()

  def insert_sheet_event(
    self,
    source_sheet_id: str,
    source_tab_name: str,
    source_event_type: str,
    row_data: dict[str, Any],
    row_values: list[Any],
    inserted_by: str = "telegram-bot"
  ) -> bool:
    """Insere evento bruto vindo do Sheets/Bot na camada Bronze."""
    if not self.is_enabled():
      return False

    self.ensure_schema()

    row_hash = str(pd.util.hash_pandas_object(pd.Series(row_values), index=False).sum())

    with self._get_connection() as conn:
      with conn.cursor() as cur:
        cur.execute(
          """
          INSERT INTO bronze.sheet_events (
            source_sheet_id,
            source_tab_name,
            source_event_type,
            ingestion_ts,
            row_data,
            row_values,
            row_hash,
            inserted_by
          ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
          """,
          (
            source_sheet_id,
            source_tab_name,
            source_event_type,
            datetime.utcnow(),
            Json(row_data),
            Json(row_values),
            row_hash,
            inserted_by
          )
        )
      conn.commit()

    return True
