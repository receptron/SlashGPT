import ast  # for converting embeddings saved as strings back to arrays
import os

import chromadb
import numpy as np
import openai  # for calling the OpenAI API
import pandas as pd  # for storing text and embeddings data
from dotenv import load_dotenv

# from scipy import spatial  # for calculating vector similarities for search


load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY", None)
EMBEDDING_MODEL = "text-embedding-ada-002"

# download pre-chunked text and pre-computed embeddings
# this file is ~200 MB, so may take a minute depending on your connection speed
embeddings_path = "https://cdn.openai.com/API/examples/data/winter_olympics_2022.csv"
# embeddings_path = "./testdata/winter_olympics_2022.csv"

print("loading... (takes a while)")
df = pd.read_csv(embeddings_path)

# convert embeddings from CSV str type back to list type
df["embedding"] = df["embedding"].apply(ast.literal_eval)


db_path = os.path.normpath(os.path.expanduser("~/.slashgpt/chroma-db"))

client = chromadb.PersistentClient(path=db_path)

collection = client.get_or_create_collection("olympics-2022")

for i, row in df.iterrows():
    query_embedding_response = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=row["text"],
    )

    collection.upsert(
        ids=[str(i)],
        embeddings=row["embedding"],
        metadatas=[
            {"id": i},
        ],
        documents=[row["text"]],
    )

q = "Sharipzyanov"
query_embedding_response = openai.embeddings.create(
    model=EMBEDDING_MODEL,
    input=q,
)

res = collection.query(
    query_embeddings=[np.array(query_embedding_response.data[0].embedding).tolist()],
    n_results=1,
)

print(list(map(lambda x: "".join(x), list(*res["documents"]))))
