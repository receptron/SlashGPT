import asyncio
import os

import openai
import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector_async

load_dotenv()

sampleDataSet = ["富士山麓オウム鳴く", "一夜一夜に人見頃", "貸そうかなまぁ当てにするなひどすぎる借金"]

EMBEDDING_MODEL = "text-embedding-ada-002"

openai.api_key = os.getenv("OPENAI_API_KEY", None)


async def insert_data(conn):
    for query in sampleDataSet:
        query_embedding_response = openai.Embedding.create(
            model=EMBEDDING_MODEL,
            input=query,
        )
        query_embedding = query_embedding_response["data"][0]["embedding"]
        print(query_embedding)

        sql = "INSERT INTO vector_table (text, storage_id, embedding) VALUES (%s, %s, %s)"
        await conn.execute(sql, (query, "sample", query_embedding))


async def insert():
    conn = await psycopg.AsyncConnection.connect(dbname="test_vector", autocommit=True)
    await register_vector_async(conn)
    await insert_data(conn)


asyncio.run(insert())
