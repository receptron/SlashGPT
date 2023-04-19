# SlashGPT

SlashGPT is a front-end of GPT3/4, which allows the user to chat with various bots with special purposes.
Each bot comes with a set of prompts, which optimizes the conversation for a specific purpose. 

The user may switch to any bot by typing "/{botname}". For example, "/patent" initializes the bot with
a specific set of prompts, which hleps the user to file patent.

## Initialization

1. Create .env file, and spacify your OpenAI key as follows:
    OPENAI_API_KEY=...
2. Install the required packages: `pip install -r requirements.txt`