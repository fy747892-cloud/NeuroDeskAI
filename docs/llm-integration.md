# LLM Integration

The backend uses deterministic mock AI by default:

```bash
LLM_PROVIDER=mock
```

To enable a real OpenAI-compatible Chat Completions provider for conversation analysis and AI chat:

```bash
LLM_PROVIDER=openai
LLM_API_KEY=...
LLM_BASE_URL=https://api.openai.com/v1
LLM_ANALYSIS_MODEL=gpt-4o-mini
LLM_CHAT_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=30
```

Conversation analysis expects the model to return JSON with:

- `summary`
- `tasks.items`
- `appointments.items`

AI chat keeps retrieval tenant-scoped before any LLM call. If no context is found, the chat endpoint returns the local "not found" response without calling the LLM.
