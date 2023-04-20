# SlashGPT

SlashGPT is a front-end of GPT3/4, which allows the user to chat with various bots with special purposes.
Each bot comes with a set of prompts, which optimizes the conversation for a specific purpose. 

The user may switch to any bot by typing "/{botname}". For example, "/patent" initializes the bot with
a specific set of prompts, which hleps the user to file patent.

## Initialization

1. Install the required packages: `pip install -r requirements.txt`
2. Create .env file, and spacify your OpenAI key as follows:
    OPENAI_API_KEY=...
3. You may optionally specify the Model. The default is "gpt-3.5-turbo".
    OPENAI_API_MODEL=...
4. You may optionally specify the temperature. The default is 0.7.
    OPENAI_TEMPERATURE=...

## Execution

1. Type `./SlashGPT.py`
2. When you see "You:", type a message to the chat bot OR type a slash command starting with "/".

## Output

1. Each conversation will be store as a json file under the "output/{context}" folder, 
where the context is "GTP" for general chat, and the slash key for a specialized chat.
2. Please notice that the "output" folder is ignored by git. 

## Prompt Extension

1. Create a new JSON file in "promots" folder with following properties:
 title (string): Title for the user to see (required)
 source (string): Source of the prompt (optional: URL, email, github id, or twitter id)
 promot (array of strings): The system prompt which defines the bot (required)
2. Name of that file becomes the slash command. (the slash command "foo.json" is "/foo")
3. If you want to share it, please make a pull request.
