import requests
from bs4 import BeautifulSoup

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

        # Print the extracted body text
        return { 
            "result":"success",
            "text": body_text[:15000] }
    else:    
        return {
            "reuslt":"error",
        }
