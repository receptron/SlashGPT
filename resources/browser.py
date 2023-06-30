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
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all <p>, <div>, and <article> tags and extract their text content
        body_text = ''
        for tag in ['p', 'div', 'article']:
            elements = soup.find_all(tag)
            for element in elements:
                body_text += element.get_text() + '\n'

        num = num_tokens(body_text)
        if num > 5000:
            limit = int(len(body_text) * 5000 / num)
            body_text = body_text[:limit]

        return { 
            "result":"success",
            "text": body_text }
    else:    
        return {
            "reuslt":"error",
        }
