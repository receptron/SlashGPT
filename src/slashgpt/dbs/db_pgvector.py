import os

import numpy as np
import psycopg2
from pgvector.psycopg2 import register_vector
from psycopg2.extensions import AsIs

from slashgpt.dbs.base import VectorDBBase
from slashgpt.dbs.vector_engine import VectorEngine
from slashgpt.utils.print import print_error


class DBPgVector(VectorDBBase):
    @classmethod
    def factory(cls, table_name: str, vector_engine: VectorEngine, verbose: bool):
        postgresql_config = os.getenv("POSTGRESQL_CONFIG", None)
        if postgresql_config:
            return DBPgVector(table_name, vector_engine, verbose)
        else:
            print_error("POSTGRESQL_CONFIG environment variable is missing from .env")

    def __init__(self, table_name: str, vector_engine: VectorEngine, verbose: bool):
        super().__init__(table_name, vector_engine, verbose)
        postgresql_config = os.getenv("POSTGRESQL_CONFIG", None)
        self.conn = psycopg2.connect(postgresql_config)
        self.table_name = table_name
        register_vector(self.conn)

    def fetch_data(self, query_embedding):
        cur = self.conn.cursor()
        sql = "SELECT id, text FROM %s ORDER BY embedding <=> %s LIMIT 5"
        cur.execute(
            sql,
            (
                AsIs(self.table_name),
                np.array(query_embedding),
            ),
        )

        response = cur.fetchall()
        results = []
        for data in response:
            results.append(data[1])
        return results
