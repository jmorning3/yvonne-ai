# Yvonne AI

Model-agnostic FastAPI orchestration backend with OpenAI, Gemini, and mock providers,
validation, retry/backoff, failover, circuit breaking, stable response mapping, Docker, and CI.

## Start locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
pytest -q
uvicorn backend.app.main:app --reload
```

The default mock provider requires no API key. Never commit a populated `.env` file.

- `GET /api/health`
- `POST /api/chat` with `{"userId":"john","message":"Hello Yvonne"}`
