# SlashGPT

SlashGPT is a playground for develeopers to make quick prototypes of LLM apps (apps with Natural Language UI).

Here are the design goals:

1. Extremely easy to create a new LLM app. You just need to add a new manifest file (in Json).
2. Instantly switch between apps. Just type "/{appname}"
3. Extensible enough so that it is possible to implement most of LLM apps without writing any code. 

## Initialization

1. Install the required packages: 

    `pip install -r requirements.txt`

2. Create .env file, and spacify your OpenAI key as follows:

    `OPENAI_API_KEY=...`

3. You may optionally specify Pinecone key and environment.

    `PINECONE_API_KEY=...`
    `PINECONE_ENVIRONMENT=...`
    `GOOGLE_PALM_KEY=...`
    `WOLFRAM_API_KEY=...`

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
    *data* (array of string, optional): {random} will put one of them randamly into the prompt
    *embeddings* (object, optional):
      *name* (string, required): index name
    *resource* (string, optional): location of the resource file. Use {resource} to paste it into the prompt
    *functions* (string, optional): location of the function definitions. 
    *module* (string, optional): location of the pytoh script to be loaded for function calls
    *actions* (object, optional): Template-based function processor (see details below)

Name of that file becomes the slash command. (the slash command of "foo.json" is "/foo")

## Actions

It defines template-based implementations (including mocks) for functions (alternative to writing python code using the "module" property).

It supports three different ways. 

1. Formatted string.

Use this method to develop the front-end of a system before the backend become ready. Here is an example (home2).

```
  "actions": {
    "fill_bath": { "message":"Success. I started filling the bath tab." },
    "set_temperature": { "message":"Success. I set the teperature to {temperature} for {location}" },
    "start_sprinkler": { "message":"Success. I started the sprinkler for {location}" },
    "take_picture": { "message":"Success. I took a picture of {location}" },
    "play_music": { "message":"Success. I started playing {music} in {location}" },
    "control_light": { "message":"Success. The light switch of {location} is now {switch}." }
  }
```

2. REST calls

Use this method to call REST API (equivalent to ChatGPT's plugin system). Here is an example (currency).

```
  "actions": {
    "convert": {
      "url": "https://today-currency-converter.oiconma.repl.co/currency-converter?from={from}&to={to}&amount={amount}"
    }
  }
```

3. data URL

This mechod allows a developer to generate a text data (typically in JSON, but not limited to), and turn it into a data URL. 

Here is an example for "make_event" function (cal).

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