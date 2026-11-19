# EvalForge – LLM Evaluation, Benchmarking & Observability Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-black.svg?logo=next.js)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-blue.svg?logo=typescript)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg?logo=python)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg?logo=postgresql)](https://www.postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-5.4+-37814A.svg?logo=celery)](https://docs.celeryq.dev)
[![Tests](https://img.shields.io/badge/Tests-10%20Passed-success.svg)]()

> A developer-first full-stack LLM evaluation and observability workspace engineered to benchmark accuracy, context grounding, latency, and execution economics.

---

## 1. Product Vision & Core Capabilities

EvalForge solves the five critical challenges faced by GenAI & RAG teams:
1. **Answer Correctness**: Measure ground truth alignment using exact match, token-level F1 lexical scoring, and LLM-as-a-judge semantic evaluations.
2. **Faithfulness & Grounding**: Verify if generated statements are supported by retrieved context chunks using claim-level extraction.
3. **Multi-Model Benchmarking**: Compare candidate models (OpenAI GPT-4o, Anthropic Claude 3.5, Google Gemini, and deterministic Mock engines) side-by-side with radar charts and win rates.
4. **Economic & Latency Observability**: Track exact input/output tokens and versioned USD pricing tables per 1 Million tokens.
5. **Execution Tracing & Failure RCA**: Hierarchical span waterfalls isolating retrieval, model generation, tool execution, and evaluation latencies.

---

## 2. Technology Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Recharts, Lucide Icons.
- **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, ReportLab.
- **Background Workers**: Celery + Redis (with async fallback runner for zero-dependency local runs).
- **Database**: PostgreSQL 16 with pgvector (and SQLite zero-config fallback for testing).
- **Testing**: Pytest, Pytest-Asyncio, HTTPX TestClient.
- **Containerization**: Docker, Docker Compose.

---

## 3. Getting Started (Local Development)

### Prerequisites
- Python 3.12+
- Node.js 18+ & npm 9+

### 1. Backend Setup & Seeding
```bash
cd backend
# Install dependencies
pip install -r requirements.txt

# Run database seed (creates demo user, projects, datasets, experiments, and traces)
python seed_data.py

# Start FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: `http://127.0.0.1:8000/api/v1/docs`

### 2. Frontend Setup
```bash
cd frontend
# Install dependencies
npm install

# Start Next.js development server
npm run dev
```
Open `http://localhost:3000` in your browser.

**Default Demo Credentials:**
- Email: `demo@evalforge.dev`
- Password: `evalforge123`

---

## 4. One-Click Runner Scripts

- **Windows (PowerShell)**:
  ```powershell
  .\scripts\run_local.ps1
  ```
- **macOS / Linux (Bash)**:
  ```bash
  chmod +x scripts/run_local.sh
  ./scripts/run_local.sh
  ```

---

## 5. Automated Test Suite Execution

Run the complete test suite:
```bash
cd backend
python -m pytest -v
```

### Verified Test Suite Results:
```text
tests/test_auth.py::test_health_endpoint PASSED                          [ 10%]
tests/test_auth.py::test_login_demo_user PASSED                          [ 20%]
tests/test_auth.py::test_login_invalid_password PASSED                   [ 30%]
tests/test_evaluators.py::test_answer_correctness_exact_match PASSED     [ 40%]
tests/test_evaluators.py::test_answer_correctness_f1 PASSED              [ 50%]
tests/test_evaluators.py::test_faithfulness_evaluator PASSED             [ 60%]
tests/test_evaluators.py::test_hallucination_evaluator PASSED            [ 70%]
tests/test_integration.py::test_full_evaluation_workflow PASSED          [ 80%]
tests/test_pricing.py::test_cost_estimation_gpt4o PASSED                 [ 90%]
tests/test_pricing.py::test_cost_estimation_mock_model PASSED            [100%]

============================= 10 passed in 10.57s =============================
```

---

## 6. Docker Compose Deployment

```bash
docker compose up -d --build
```
This spins up:
- `evalforge_db`: PostgreSQL 16 + pgvector (`localhost:5432`)
- `evalforge_redis`: Redis 7 (`localhost:6379`)
- `evalforge_backend`: FastAPI (`http://localhost:8000`)
- `evalforge_worker`: Celery worker
- `evalforge_frontend`: Next.js production build (`http://localhost:3000`)

---

## 7. Platform Structure

```
evalforge/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # Versioned REST endpoints (auth, projects, datasets, etc.)
│   │   ├── core/           # Config, database engine, security (JWT/bcrypt), pricing tables
│   │   ├── models/         # SQLAlchemy 2.0 relational models
│   │   ├── schemas/        # Pydantic v2 validation models
│   │   ├── providers/      # Multi-provider adapter (OpenAI, Anthropic, Gemini, Mock)
│   │   ├── evaluators/     # Evaluator engine (Correctness, Faithfulness, Precision, Recall, etc.)
│   │   ├── experiments/    # Pipeline runner & cancellation management
│   │   ├── workers/        # Celery task definitions & asynchronous dispatchers
│   │   ├── tracing/        # Execution tracer & secrets redaction engine
│   │   ├── reports/        # Executive ReportLab PDF and CSV generator
│   │   └── main.py         # FastAPI application entrypoint
│   ├── tests/              # Pytest unit & integration test suite
│   ├── seed_data.py        # Demo dataset & experiment seeder
│   └── requirements.txt    # Pinned Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router (10 dedicated pages)
│   │   ├── components/     # Sidebar, Header, KPI Cards
│   │   ├── lib/            # API client & formatting utilities
│   │   └── types/          # TypeScript interface definitions
│   ├── package.json
│   └── tailwind.config.js
├── docker/                 # Production Dockerfiles (backend & frontend)
├── docs/                   # Architecture & AWS deployment documentation
├── scripts/                # Startup runner scripts (bash & powershell)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 8. Known Limitations & Future Improvements

1. **pgvector Embeddings Extension**: Currently semantic comparison supports lexical F1 and LLM judges. Vector embeddings search can be expanded with pgvector indexing in a dedicated retrieval playground.
2. **Real-time WebSockets**: Job updates currently use resilient client polling; upgrading to WebSockets or SSE for experiment streaming is a natural next step.
3. **Fine-tuning Export**: Ability to export failed test cases directly as a JSONL fine-tuning dataset for smaller distilled models.
