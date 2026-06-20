### Ensure .venv has all dependencies

```bash
rm -rf .venv
uv venv
uv sync

.venv/bin/python -c "import dotenv, pydantic, langchain_chroma, langchain_core, langgraph; print('ok')"
```

### Use local .venv interpreter

- Create or Edit .vscode/settings.json
- Put the code below in:

```json
{
  "python.defaultInterpreterPath": "/Users/immanuel/Documents/Learning/unlimited-code/agentic_ai_class/6-week_six/rag_agent/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.analysis.extraPaths": [
    "/Users/immanuel/Documents/Learning/unlimited-code/agentic_ai_class/6-week_six/rag_agent/src"
  ],
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.indexing": true
}
```

### Clear Pylance cache

- Cmd + Shift + P
- Python: Clear Cache and Reload Window