import asyncio
import os

import numpy as np
import openai
import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector_async

load_dotenv()

sampleDataSet = ["富士山麓オウム鳴く", "一夜一夜に人見頃", "貸そうかなまぁ当てにするなひどすぎる借金"]

EMBEDDING_MODEL = "text-embedding-ada-002"

openai.api_key = os.getenv("OPENAI_API_KEY", None)


async def semantic_search(conn, query):
    query_embedding_response = openai.Embedding.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    query_embedding = np.array(query_embedding_response["data"][0]["embedding"])

    async with conn.cursor() as cur:
        sql = "SELECT id, text FROM vector_table where storage_id = %s ORDER BY embedding <=> %s LIMIT 5"
        await cur.execute(
            sql,
            (
                "sample",
                query_embedding,
            ),
        )
        return await cur.fetchall()


async def search():
    conn = await psycopg.AsyncConnection.connect(dbname="test_vector", autocommit=True)
    await register_vector_async(conn)
    query = "富士山"
    result = await semantic_search(conn, query)

    print(result)


asyncio.run(search())
