# Startup News Agent

This project is a small Python news agent built with `uv`, LangChain, and a YAML-based agent configuration. The goal is to accept a user news query, use a news tool to fetch relevant startup news and articles, and return structured JSON output.

## What The Project Is

This repo is intended to be a minimal agent-based Python application with:

- a Python codebase
- `uv` for dependency management
- a YAML config file for model and prompt settings
- a news lookup tool callable by an LLM agent

## What The Agent Does

The agent takes a news query such as startup news in a country, uses a `get_news()` tool to fetch relevant articles, and returns a structured JSON array of results.

Each result is expected to include:

- `title`
- `description`
- `country`
- `date`
- `link`

The agent can also include extra useful fields when relevant, such as `source` or `author`.

## APIs Used

This project uses:

- News API via the `newsapi-python` client library
- an LLM provider API through LangChain

If configured for OpenAI, it uses the OpenAI API.
If configured for Anthropic, it uses the Anthropic API.

## Model Used

The model is intended to be configured in YAML rather than hardcoded in Python.

Examples:

- `gpt-4.1-mini` for OpenAI
- `claude-sonnet-4-20250514` for Anthropic

The active model should be defined in your agent config file, for example `config/news_agent.yml`.

## How To Run It

From the repo root:

```bash
./.venv/bin/python src/main.py
```

If `uv` is available in your shell, you can also use:

```bash
uv run python src/main.py
```

If your script is updated to accept a query argument, a typical usage would look like:

```bash
./.venv/bin/python src/main.py "startup news in Nigeria"
```

## Required Environment Variables

Create a `.env` file in the project root and add the variables required by your chosen provider.

For News API:

```env
NEWS_API_KEY=your_news_api_key
```

For OpenAI:

```env
OPENAI_API_KEY=your_openai_api_key
```

For Anthropic:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
```

Only set the model provider key you actually plan to use.
