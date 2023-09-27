# Manifest File Is All You Need

**Author:** Satoshi Nakajima

I started writing LLM applications on top of GPT3.5 in April 2023, inspired by my son's open source project, [BabyAGI](https://github.com/yoheinakajima/babyagi). A that moment, I was aware that there is a library called [LangChain](https://github.com/langchain-ai/langchain), which was quite popular among developers, but I chose to write directly on top of OpenAI's API -- because the API is quite straightfoward. It actuallly allows me to create a simple chat application with a few lines of code.

Since I wantd to create multiple LLM application, I started it as an open source projet, [SlashGPT](https://github.com/snakajima/SlashGPT), as my playground (this name came from "slash commands", which allows me to switch among AI agents from the terminal).

The design goal of this project was very clear from the biginning. 

1. It allows developers to create various LLM applications very quickly.
2. It allows developers to define the behavior of each LLM agent declaratively (without writing code).
3. It enables complex applications, which involves embedded database and code execution.

I am a big fan of "Declarative Programming", because it will significantly simplify the application development process, allowing web-based application creation (by non-develpers) or even full automations. You can think is a part of no-code movement. 

If we want to build a scalable LLM application business targeting tens of thounsands of enterprise customers, it does not make sense to write custom code for each customer. The "Declarative Programming" is the only way to scale such a business.

## Manifest File

In order to create an AI agent (a chat bot, with a specific prompt and behaviors), we need to create a manifest file.

Here is a simple example, which defines a "Brand Manager" agent.

```
title: Brand Manager
prompt:
  - You are an experienced marketing person with thirty years of experience.
  - You help companies to come up with attractive vision & mission statements, and even company names.
```

The *title* defines the title of the agent (for the user).
The *prompt* defines the system prompt to LLM.

When the user select this agent, SlashGPT creates a new chat session with this manifest file and wait for use's input. When the user enters a question, it sends that question to GPT 3.5 (which is the default LLM) along with a system prompt specified in the manifest file, and present the response to the user. 

Here is a little bit complext example, defines the "Code Interpreter" agent on top of Code Llama2.

```
title: Code Interpreter with code_llamma
model: code_llama
temperature: 0
form: Write some Python code to {question} (surround it with ```).
notebook: true
prompt:
- You are a data scientist who runs Python code to analyze data.
- When you write code, make it sure that you expicitly import all necessary libraries,
  such as mumpy and matplotlib
```

- The *model* defines the LLM.
- The *temperature* defines the temperature for LLM (between 0 and 1.0)
- The *form* defines the template to modify user's question.
- The *notebook* defines if we want to record the interaction in Jupyter Notebook or not.