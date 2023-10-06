import requests
import tiktoken
from bs4 import BeautifulSoup


def num_tokens(text: str) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-16k-0613")
    return len(encoding.encode(text))


def fetch(url: str):
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        contentType = response.headers["Content-Type"]
        if contentType[:9] == "text/html":
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all <p>, <div>, and <article> tags and extract their text content
            body_text = ""
            for tag in ["p", "div", "article"]:
                elements = soup.find_all(tag)
                for element in elements:
                    body_text += element.get_text() + "\n"
        else:
            print("non text/htlm")
            body_text = response.text

        num = num_tokens(body_text)
        if num > 4500:
            limit = int(len(body_text) * 4500 / num)
            body_text = body_text[:limit]

        return ({"result": "success", "text": body_text}, None)
    else:
        return (
            {
                "result": "error",
            },
            None,
        )
