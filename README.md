# SlashGPT

SlashGPT is a playground for develeopers to make quick prototypes of LLM agents (or apps with Natural Language UI).

Here are the design goals:

1. Extremely easy to create a new LLM agent. You just need to add a new manifest file (in Json).
2. Instantly switch amang agents, by just typing "/{agent_name}"
3. Extensible enough so that it is possible to implement most of LLM agents without writing any code.
4. It is possible to integrate ChatGPT plugins as agents without writing any code.
5. It enables broker agent (or dispatcher), which routes user's messgae to an appropraite agent.
6. It is able to run generated Python code like Code Interpreter (see "code" agent).

> [!NOTE]  
> If you want to try it out immediately, please try the Google Google Colaboratory version.  

<a href="https://colab.research.google.com/github/snakajima/SlashGPT/blob/main/notebooks/SlashGPT_on_GoogleColab.ipynb">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab">
</a>

## QuickStart

```
pip install slashgpt
```

```
export OPENAI_API_KEY=XXX
```

XXX is you open api key.

```
slashGPT
```

Then run SlashGPT

## Initialization for develeoper

1. Install the required packages: 

    `pip install -r requirements.txt`

2. Create .env file, and specify your OpenAI key as follows:

    `OPENAI_API_KEY=...`

3. You need to specify other variables to use following features (optional).

    - PINECONE_API_KEY, PINECONE_ENVIRONMENT: required to use embedding vector db.
    - GOOGLE_PALM_KEY: required to switch to "palm" model with /llm command.
    - REPLICATE_API_TOKEN: required to switch to "llama2" model with /llm command.
    - CODEBOX_API_KEY: set this to "local" to use CodeBox's LocalBox instead of IPython
    - SLASH_GPT_ENV_WOLFRAM_API_KEY: required to use "walfram" agent.
    - SLASH_GPT_ENV_OPENWEATHER_API_KEY: required to use "weather" agent.
    - SLASH_GPT_ENV_NOTEABLE_API_KEY: required to use "noteable" agent.
    - SLASH_GPT_ENV_WEBPILOT_UID: required to use "webpilot" agent (any unique UUID is fine)
    - ALCHEMY_API_KEY: required to use "web3" agent.

## Execution

1. Type `./SlashGPT.py`

2. When you see "You({agent_name}):", type a message to the agent OR type a slash command starting with "/".

3. It activate "dispatcher" agent first, which is able to dispatch queries to appropriate agents.

4. Type "/help" to see the list of system commands and available agents.

## Execution on Docker

1. Build docker image `docker build -t slashgpt .`

2. Run SlashGPT on Docker `docker run -it slashgpt  ./SlashGPT.py`

## Outputs

1. Each conversation will be store as a json file under the "output/{context}" folder, 
where the context is "GTP" for general chat, and the app id for a specialized chat.

2. Please notice that the "output" folder is ignored by git. 

3. Code Interpreter agents will generate Jupyter notebook in "output/notebooks" folder.

## Code Interpreter Agents

Some of agents are built to mimic the behaviors of ChatGPT code intepreter (or Noteable plugin)
with various LLMs.

- code: GPT3.5
- code_palm2: PaLM2 (GOOGLE_PALM_KEY key is required)
- code_llama: LlaMA (REPLICATE_API_TOKEN is required)

code (GPT3.5) works just like Code Interpreter. It is able to respond to the output of nenerated code appropriately.

code_palm2 (PaLM2) and code_llma (LlaMA) are not able to respond to the output of generated code (they often enter into an infinit loop). Therefore, we stop the conversation after the output, and the user needs to explicitly ask it to analize the result.

For the runtime, it uses IPython by default, but it uses CodeBox if you specify CODEBOX_API_KEY key. IPython displays images as popups, but does not write them into the notebook. CodeBox is able to write them into the notebook.

Sample queries.

- Draw sine curve
- List first 50 prime numbers
- graph common moving average
- Draw histogram
- Graph 4 year stock price of apple and tesla using yfinance

## Manifest files

Create a new manifest file, {agent_name}.json in "manifests" folder with following properties:

- *title* (string, **required**): Title for the user to see
- *about* (string, optional): About the manifest (URL, email, github id, or twitter id)
- *prompt* (array of strings, **required**): The system prompts which define the agent (required)
- *form* (string): format string to extend user's query (e.g. "Write python code to {question}").
- *result_form* (string): format string to extend function call result.
- *skip_function_result* (boolean): skip the chat completion right after the function call.
- *notebook* (boolean): create a new notebook at the beginning of each session (for code_palm2)
- *bot* (string, optional): Agent name
- *you* (string, optional): User name. The default is You({agent_name}).
- *sample* (string, optional): Sample question (type "/sample" to send it)
- *intro* (array of strings, optional): Introduction statements (will be randomly selected)
- *model* (string, optional): LLM model (such as "gpt-4-613", the default is "gpt-3-turbo")
- *temperature* (number, optional): Temperature (the default is 0.7)
- *list* (array of string, optional): {random} will put one of them randamly into the prompt
- *embeddings* (object, optional):
  - *name* (string, optional): index name of the embedding vector database
- *resource* (string, optional): location of the resource file. Use {resource} to paste it into the prompt
- *functions* (string, optional): location of the function definitions 
- *module* (string, optional): location of the Python script to be loaded for function calls
- *actions* (object, optional): Template-based function processor (see details below)

Name of that file becomes the slash command. (the slash command of "foo.json" is "/foo")

## Actions

It defines template-based function implementations (including mockups), alternative to writing Python code using the "module" property.

It supports four different methods. 

### 1. Formatted string.

Use this method to develop the front-end of a system before the backend become ready. 

- *message* (format string, required): chat messgae to be added 
- *manifest* (format string, optional): manifest file name to be loaded for chained action

Here is an example (home2).

```
  "actions": {
    "fill_bath": { "type": "message_template", "message":"Success. I started filling the bath tab." },
    "set_temperature": { "type": "message_template", "message":"Success. I set the teperature to {temperature} for {location}" },
    "start_sprinkler": { "type": "message_template", "message":"Success. I started the sprinkler for {location}" },
    "take_picture": { "type": "message_template", "message":"Success. I took a picture of {location}" },
    "play_music": { "type": "message_template", "message":"Success. I started playing {music} in {location}" },
    "control_light": { "type": "message_template", "message":"Success. The light switch of {location} is now {switch}." }
  }
```

### 2. REST calls

Use this method to call REST APIs (equivalent to ChatGPT's plugin system).

- *url* (string, required): Python-style format string, which references to function arguments.
- *method* (string, optional): Specify "POST" if we need to use HTTP-POST. The body will contain a JSON representation of function parameters.

Here is an example (currency).

```
  "actions": {
    "convert": {
      "type": "rest",
      "url": "https://today-currency-converter.oiconma.repl.co/currency-converter?from={from}&to={to}&amount={amount}"
    }
  }
```

### 3. GraphQL calls

Use this method to call GraphQL APIs.

- *url* (string, required): GraphQL server url.

Here is an example (spacex).

```
  "actions": {
    "convert": {
      "type": "graphQL",
      "url": "https://spacex-production.up.railway.app/graphql"
    }
  }
```

### 4. data URL

This mechod allows a developer to generate a text data (typically in JSON, but not limited to), and turn it into a data URL.

- *template* (string, required): The location of the template file.
- *mime_type* (string, required): The mime type of the data.
- *message* (string, required): Python-style format string, which references to the data-URL as {url}.

Here is an example for "make_event" function (cal).

```
  "actions": {
    "make_event": {
      "type": "data_url",
      "template": "./resources/calendar.ics",
      "mime_type": "text/calendar",
      "message": "The event was scheduled. Here is the invitation link: '{url}'"
    }
  }
```

The contents of calendar.ics file.
```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//My Calendar//NONSGML v1.0//EN
BEGIN:VEVENT
DTSTART:{DTSTART}
DTEND:{DTEND}
SUMMARY:{SUMMARY}
DESCRIPTION:{DESCRIPTION}
LOCATION:{LOCATION}
END:VEVENT
END:VCALENDAR
```

The definition of "make_event" function.
```
{
  "name": "make_event",
  "description": "Create a calendar event in iCalendar format",
  "parameters": {
    "type": "object",
    "properties": {
      "SUMMARY": {
        "type": "string",
        "description": "a short, one-line description of the event"
      },
      "DESCRIPTION": {
        "type": "string",
        "description": "a more complete description of the calendar",
        "maxLength": 400
      },
      "DTSTART": {
        "type": "string",
        "format": "date-time",
        "description": "the date and time in UTC that the event begins such as 19980119T020000Z"
      },
      "DTEND": {
        "type": "string",
        "format": "date-time",
        "description": "the date and time in UTC that the event ends such as 19980119T030000Z"
      },
      "LOCATION": {
        "type": "string",
        "description": "the intended venue with address for the event."
      }
    },
    "required": ["SUMMARY", "DTSTART", "DTEND", "DESCRIPTION", "LOCATION"]
  }
}
```

## Standard Test Squence

This is the standard test squence.

```
# Test REST API
Input: /sample currency
Expected Output: 1 USD is equivalent to 146.31 JPY.
Input: /switch main

# Test REST API with appkey header (WEBPILOT_UID in .env is required)
Input: /sample webpilot
Expected Output: Title: France riorts ...\nSummary: The fourth night ...
Input: /switch main

# Test GraphQL
You: /sample spacex
Expected Output: The CEO of SpaceX is Elon Musk.
Input: /switch main

# Test DataURL
You: /sample cal
Expected Output: I have scheduled a meeting with Tim Cook on July 4th at 8:00 PM UTC for 30 minutes. The meeting will be held at Tim Cook's office. I have sent the invitation to Tim Cook at tim@apple.com.
Iput: /switch main

# Test Code Interpreter
You: /code
You: /sample_stock
Expected Output: <Marketcap history of Apple and Tesla>
```


# Unittest

## Run test

```
make test
```

# Code formatter and linter

## Lint

```
make lint
```

## Format

```
make format
```
