---
module: agent
owns: [services]
last_reviewed: be87c877b610
---
# agent
The LLM reasoning layer: builds deterministic evidence context from the DB, applies guardrail prompts, and calls an OpenAI-compatible chat model to answer questions or draft memos.

## Structure
- `client.py` — `LLMClient` protocol and `OpenAIClient`, a thin provider-agnostic wrapper over the `openai` SDK (`base_url`/`api_key`/`model` from settings, temperature 0); `get_llm_client()` factory.
- `prompts.py` — `SYSTEM_PROMPT` (evidence-only, cite-IDs, refuse-unsupported guardrails), the ask-mode JSON response format, `MEMO_TEMPLATE`, and `ask_user_message()`/`memo_user_message()` builders.
- `retrieval.py` — `build_context()`: deterministically loads a project's evidence + metrics (optionally filtered to `allowed_evidence_ids`) via `app.services` and renders it into a flat text context plus the list of evidence IDs offered to the model.
- `agent.py` — orchestration: `answer_question()` (retrieval → prompt → LLM call → parse/validate JSON into `AskResponse`, filtering evidence IDs to only those actually offered) and `generate_memo()` (retrieval → prompt → LLM call → markdown content + evidence IDs used).

## Public interface
`answer_question()`, `generate_memo()` (from `agent.py`), `LLMClient`/`get_llm_client()` (from `client.py`) — consumed by `app.services.agent` and `app.api.routes.agent`.

## Depends on
`app.services` (queries/projects, for retrieval), `app.schemas.agent` (`AskResponse`), `app.core.config` (LLM settings), and the `openai` SDK.
