# SlashGPT

SlashGPT is a playground for devleopers to make quick prototypes of apps with Natural Language UI.

Here are the design goals:
1. Easy to add a new app. You just need to add a new manifest file (in Json).
2. Super easy to switch between apps. Just type "/{appname}"
3. Extensible

## Initialization

1. Install the required packages: 

    `pip install -r requirements.txt`

2. Create .env file, and spacify your OpenAI key as follows:

    `OPENAI_API_KEY=...`

3. You may optionally specify Pinecone key and environment.

    `PINECONE_API_KEY=...`
    `PINECONE_ENVIRONMENT=...`
    `GOOGLE_PALM_KEY=...`

## Execution

1. Type `./SlashGPT.py`

2. When you see "You:", type a message to the chat bot OR type a slash command starting with "/".

## Outputs

1. Each conversation will be store as a json file under the "output/{context}" folder, 
where the context is "GTP" for general chat, and the app id for a specialized chat.

2. Please notice that the "output" folder is ignored by git. 

## Manifest files

Create a new manifest file in "prompts" folder with following properties:

    *title* (string, required): Title for the user to see
    *source* (string, optional): Source of the prompt (URL, email, github id, or twitter id)
    *promt* (array of strings, required): The system prompts which define the bot (required)
    *bot* (string, optional): Bot name
    *sample* (string, optional): Sample question (type "/sample" to send it)
    *intro* (array of strings, optional): Introduction statements (will be randomly selected)
    *model* (string, optional): LLM model (gpt-4)
    *temperature* (string, optional): Temperature
    *articles* (string, optional): name of embedding database
    *resource* (string, optional): location of the resource file. Use {resource} to paste it into the prompt
    *functions* (string, optional): location of the function definitions. 
    *module* (string, optional): location of the pytoh script to be loaded for function calls
    *data* (array of string, optional): {random} will put one of them into the prompt
    *actions* (json, optional): Template-based function processor

Name of that file becomes the slash command. (the slash command of "foo.json" is "/foo")

## Actions

It defines template-based actions for functions. I will generatae a text file using the template file and function parameters, create a "data:" URL, then generate a system message with that url. 

Here is an example for "make_event" function.

```
  "actions": {
    "make_event": {
      "template": "./resources/calendar.ics",
      "mime_type": "text/calendar",
      "chained_msg": "The event was scheduled. Here is the invitation link: '{url}'"
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