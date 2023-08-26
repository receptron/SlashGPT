#!/usr/bin/env python3
import ast  # for converting embeddings saved as strings back to arrays
import os

import openai  # for calling the OpenAI API
import pandas as pd  # for storing text and embeddings data
import pinecone
import tiktoken  # for counting tokens
from dotenv import load_dotenv

# Configuration
load_dotenv()  # Load default environment variables (.env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"
openai.api_key = OPENAI_API_KEY
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
assert PINECONE_API_KEY, "PINECONE_API_KEY environment variable is missing from .env"
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
assert PINECONE_ENVIRONMENT, "PINECONE_ENVIRONMENT environment variable is missing from .env"

# models
EMBEDDING_MODEL = "text-embedding-ada-002"
GPT_MODEL = "gpt-3.5-turbo"

# Initialize Pinecone
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

# Create Pinecone index
table_name = "olympic-2022"
dimension = 1536
metric = "cosine"
pod_type = "p1"
if table_name not in pinecone.list_indexes():
    print("Creating pinecone index")
    pinecone.create_index(table_name, dimension=dimension, metric=metric, pod_type=pod_type)

# Connect to the index
index = pinecone.Index(table_name)


def load_vectors():
    print("loadig CSV file")
    embeddings_path = "./output/winter_olympics_2022.csv"

    df = pd.read_csv(embeddings_path)

    # convert embeddings from CSV str type back to list type
    print("converting it to list type")
    df["embedding"] = df["embedding"].apply(ast.literal_eval)
    # print(df)

    print("writing vectors")
    vectors = [(f"id_{i}", row["embedding"], {"text": row["text"]}) for i, row in df.iterrows()]
    # print(vectors)
    for vector in vectors:
        index.upsert([vector])


# search function
def strings_ranked_by_relatedness(query: str, top_n: int = 100) -> object:
    """Returns a list of strings and relatednesses, sorted from most related to least."""
    query_embedding_response = openai.Embedding.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    query_embedding = query_embedding_response["data"][0]["embedding"]

    results = index.query(query_embedding, top_k=top_n, include_metadata=True)
    return results


# examples
# results = strings_ranked_by_relatedness("curling gold medal", top_n=5)
# for match in results["matches"]:
#    print(match["score"])


def num_tokens(text: str, model: str = GPT_MODEL) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def query_message(query: str, model: str, token_budget: int) -> str:
    """Return a message for GPT, with relevant source texts pulled from a dataframe."""
    results = strings_ranked_by_relatedness(query)
    introduction = 'Use the below articles on the 2022 Winter Olympics to answer the subsequent question. If the answer cannot be found in the articles, write "I could not find an answer."'
    question = f"\n\nQuestion: {query}"
    message = introduction
    for match in results["matches"]:
        string = match["metadata"]["text"]
        next_article = f'\n\nWikipedia article section:\n"""\n{string}\n"""'
        if num_tokens(message + next_article + question, model=model) > token_budget:
            break
        else:
            message += next_article
    return message + question


def ask(
    query: str,
    model: str = GPT_MODEL,
    token_budget: int = 4096 - 500,
    print_message: bool = False,
) -> str:
    """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
    message = query_message(query, model=model, token_budget=token_budget)
    if print_message:
        print(message)
    messages = [
        {
            "role": "system",
            "content": "You answer questions about the 2022 Winter Olympics.",
        },
        {"role": "user", "content": message},
    ]
    response = openai.ChatCompletion.create(model=model, messages=messages, temperature=0)
    response_message = response["choices"][0]["message"]["content"]
    return response_message


query = "Please list the names of Japanese athletes won the gold medal at the 2022 Winter Olympics along with event names they won the medal."
res = ask(query)
print(f"Q: {query}\nA: {res}")

query = "Which athletes won the gold medal in curling at the 2022 Winter Olympics?"
res = ask(query)
print(f"Q: {query}\nA: {res}")
