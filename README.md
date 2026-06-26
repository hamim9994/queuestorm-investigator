# QueueStorm Investigator

An AI-powered FastAPI service that analyzes customer complaint tickets together with their transaction history to surface root cause, risk, and recommended actions.

## Features

- **Ticket analysis** — POST a complaint plus a transaction history; receive root cause, sentiment, risk score, and recommended actions.
- **Pluggable analyzers** — falls back to a deterministic `BaseAnalyzer`; uses an LLM-backed analyzer when `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` is set.
- **Health endpoint** — `GET /health` for liveness probes.

## Project Structure

```
app/
├── main.py              # FastAPI entrypoint
├── config.py            # Settings (env-driven)
├── models/
│   ├── request.py       # AnalyzeTicketRequest
│   └── response.py      # AnalyzeTicketResponse
├── services/
│   ├── analyzer.py      # TicketAnalyzer dispatcher
│   ├── base_analyzer.py # Rule-based fallback
│   └── llm_analyzer.py  # OpenAI / Anthropic analyzers
└── utils/
tests/
├── test_30.py
└── test_api.py
Dockerfile
requirements.txt
```

## Requirements

- Python 3.11+
- Docker (optional, for containerized runs)
- An OpenAI or Anthropic API key (optional — service runs without one using the base analyzer)

## Configuration

Create a `.env` file in the project root:

```env
# LLM provider — leave blank to use the rule-based base analyzer
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

## Running Locally

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
# source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/docs for the interactive Swagger UI.

## Running with Docker

```bash
docker build -t queuestorm-investigator .
docker run -d --name queuestorm-investigator -p 8000:8000 queuestorm-investigator
```

Stop and remove:

```bash
docker stop queuestorm-investigator
docker rm queuestorm-investigator
```

## API

### `GET /health`

```json
{ "status": "ok" }
```

### `POST /analyze-ticket`

Request body:

```json
{
  "complaint": "My card was charged twice for order #12345",
  "transactions": [
    { "id": "tx_1", "amount": 49.99, "timestamp": "2026-06-20T10:15:00Z", "status": "completed" }
  ]
}
```

Response:

```json
{
  "root_cause": "...",
  "sentiment": "negative",
  "risk_score": 0.72,
  "recommended_actions": ["..."]
}
```

## Testing

```bash
pytest tests/
```

## License

MIT
