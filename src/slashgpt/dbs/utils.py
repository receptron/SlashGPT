from slashgpt.chat_config import ChatConfig
from slashgpt.dbs.db_pgvector import DBPgVector
from slashgpt.dbs.db_pinecone import DBPinecone
from slashgpt.dbs.vector_engine_openai import VectorEngineOpenAI
from slashgpt.manifest import Manifest
from slashgpt.utils.print import print_warning


vector_dbs = {
    "pinecone": DBPinecone,
    "pgvector": DBPgVector,
}

vector_engines = {
    "openai": VectorEngineOpenAI
}

def get_vector_db(manifest: Manifest, config: ChatConfig):
    embeddings = manifest.get("embeddings")
    if embeddings:
        table_name = embeddings.get("name")

        try:
            dbs = vector_dbs[embeddings["db_type"]]
            engine = vector_engines[embeddings["engine_type"]]
            if dbs and engine:
                return dbs.factory(table_name, embeddings, engine, config.verbose)
        except Exception as e:
            print_warning(f"Pinecone Error: {e}")
