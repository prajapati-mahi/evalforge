# EvalForge Technical Architecture Document

## 1. System Overview

EvalForge is a developer-first LLM Evaluation, Benchmarking & Observability workspace engineered to answer five core questions for AI engineers:
1. **Is my LLM application producing correct answers?** (Answer Correctness via Exact, Lexical F1, Semantic, & LLM Judge)
2. **Are its responses grounded in the supplied context?** (Faithfulness claim-level extraction & verification)
3. **Which LLM model or prompt performs better?** (Multi-model comparative benchmarks, radar scoring, win rates)
4. **How much time and money does each execution consume?** (Granular token and versioned pricing cost tracking)
5. **Why did a particular AI execution fail?** (Full execution traces with hierarchical spans: retrieval, model generation, tool execution, evaluation)

---

## 2. Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Frontend (Next.js 14 App Router)             │
│  Overview • Projects • Datasets • Experiments • Comparison  │
│  Metrics Playground • Traces Waterfall • Prompts • Settings  │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / REST / JSON
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend (API v1)                  │
│   Auth • Projects • Datasets • Experiments • Traces • Reports│
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────┐┌──────────────▼───────────────┐
│     SQLAlchemy ORM Layer    ││  Celery / Async Task Worker  │
│  PostgreSQL / pgvector /    ││  Redis Queue + Fallback      │
│  SQLite zero-config fallback││  Background Execution Engine │
└─────────────────────────────┘└──────────────┬───────────────┘
                                              │
               ┌──────────────────────────────┴───────────────┐
               │         Evaluation Engine & Multi-Provider   │
               │  OpenAI • Anthropic • Gemini • Mock Engine   │
               │  Correctness • Faithfulness • Precision      │
               │  Recall • Relevance • Hallucination Freedom  │
               └──────────────────────────────────────────────┘
```

---

## 3. Database Schema

The relational schema implements clean data isolation:
- `users`: Core developer identity, hashed credentials, and roles.
- `projects`: Project boundaries isolating datasets, experiments, prompts, and traces.
- `project_members`: Role-based access control (owner, editor, viewer).
- `datasets`: Versioned benchmark collections supporting JSONL and CSV imports.
- `dataset_cases`: Test cases storing `input_text`, `expected_output`, `context`, and `metadata_json`.
- `prompts` & `prompt_versions`: Immutable versioned prompts with detected `{{variables}}`.
- `model_providers` & `model_pricing`: Encrypted key storage and versioned pricing ($/1M tokens).
- `experiments`: High-level test runs with configurations, status tracking, and progress counters.
- `experiment_runs`: Model-specific execution records with pre-aggregated summary metrics.
- `test_case_runs`: Case-level execution records capturing input, output, tokens, latency, and cost.
- `evaluation_results`: Granular metric scores, reasoning, supported claims, unsupported claims, and human-in-the-loop review overrides.
- `traces` & `trace_spans`: Hierarchical execution trees linking spans (`retrieval`, `model_generation`, `tool_execution`, `evaluation`).
- `background_jobs`: Async status tracker for Celery and worker tasks.

---

## 4. Evaluation Engine Metrics

1. **Answer Correctness**:
   - Normalized exact matching
   - Token-level F1 overlap
   - LLM-as-a-judge semantic scoring against expected output
2. **Faithfulness**:
   - Decomposes generated output into individual factual assertions
   - Checks each assertion against provided context chunks
   - Output: `score = supported_assertions / total_assertions`
3. **Context Precision**:
   - Assesses signal-to-noise ratio in retrieved documents
4. **Context Recall**:
   - Evaluates whether context contains all ground truth facts
5. **Response Relevance**:
   - Evaluates directness and penalizes evasiveness or rambling
6. **Hallucination Detection**:
   - Audits assertions for fabrications or unsupported claims
