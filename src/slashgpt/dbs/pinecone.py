import openai
import pinecone
import tiktoken  # for counting tokens

from slashgpt.chat_config import ChatConfig
from slashgpt.utils.print import print_debug


class DBPinecone:
    @classmethod
    def factory(cls, table_name: str, config: ChatConfig):
        if table_name and config.PINECONE_API_KEY and config.PINECONE_ENVIRONMENT:
            assert table_name in pinecone.list_indexes(), f"No Pinecone table named {table_name}"
            return DBPinecone(table_name, config)

    def __init__(self, table_name: str, config: ChatConfig):
        self.config = config
        self.index = pinecone.Index(table_name)

    # Fetch artciles related to user messages
    def fetch_related_articles(self, messages, model_name: str, token_budget: int) -> str:
        """Return related articles with the question using the embedding vector search."""
        query = ""
        for message in messages:
            if message["role"] == "user":
                query = message["content"] + "\n" + query
        query_embedding_response = openai.Embedding.create(
            model=self.config.EMBEDDING_MODEL,
            input=query,
        )
        query_embedding = query_embedding_response["data"][0]["embedding"]

        results = self.index.query(query_embedding, top_k=12, include_metadata=True)

        articles = ""
        count = 0
        base_token = self.__messages_tokens(messages, model_name)
        if self.config.verbose:
            print_debug(f"messages token:{base_token}")
        for match in results["matches"]:
            article = match["metadata"]["text"]
            article_with_section = f'\n\nSection:\n"""\n{article}\n"""'
            if self.__num_tokens(articles + article_with_section + query, model_name) + base_token > token_budget:
                break
            else:
                count += 1
                articles += article_with_section
                if self.config.verbose:
                    print(len(article), self.__num_tokens(article, model_name))
        if self.config.verbose:
            print_debug(f"Articles:{count}, Tokens:{self.__num_tokens(articles + query, model_name)}")
        return articles

    # Returns the number of tokens in a string
    def __num_tokens(self, text: str, model_name: str) -> int:
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))

    # Returns the total number of tokens in messages
    def __messages_tokens(self, messages, model_name: str) -> int:
        return sum([self.__num_tokens(message["content"], model_name) for message in messages])
