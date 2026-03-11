## Raveya AI Backend

This project implements production-style AI modules for a sustainable products platform:

- **Module 1 (implemented)**: AI Auto-Category & Tag Generator
- **Module 2 (implemented)**: AI B2B Proposal Generator
- **Module 3 (designed)**: AI Impact Reporting Generator
- **Module 4 (designed)**: AI WhatsApp Support Bot

### Tech Stack

- **Backend**: FastAPI
- **DB**: SQLite via SQLAlchemy
- **AI Client**: OpenAI (via `OPENAI_API_KEY`) behind a small abstraction layer

### Architecture Overview

- `app/main.py`: FastAPI app, routes, and dependency wiring.
- `app/config.py`: Environment-based settings (API keys, DB URL, environment).
- `app/db.py`: SQLAlchemy engine, session factory, and base model.
- `app/models.py`: Database models (products, proposals, impact reports, conversations, AI logs).
- `app/schemas.py`: Pydantic models for request/response JSON schemas.
- `app/ai_client.py`: Thin wrapper around the LLM provider. All prompts and AI calls go through here.
- `app/services/`: Business logic per module, separate from HTTP and raw AI calls.
  - `catalog_service.py` – **Module 1** logic (fully implemented)
  - `proposal_service.py` – **Module 2** logic (fully implemented)
  - `impact_service.py` – **Module 3** architecture only
  - `whatsapp_service.py` – **Module 4** architecture only
- `app/logging_utils.py`: Prompt/response logging abstractions.

### AI Prompt Design (High-Level)

- **Module 1 – Catalog & Tags**
  - Input: product title, description, optional attributes.
  - System message constrains behavior: choose a **primary category** from a predefined list, then suggest a **sub-category**, **5–10 SEO tags**, and **sustainability filters** (plastic-free, compostable, vegan, recycled, etc.).
  - The assistant is instructed to **only** return valid JSON in a strict schema; extra text is rejected and re-parsed.

- **Module 2 – B2B Proposal Generator**
  - Input: company profile, target audience, total budget, sustainability priorities.
  - System prompt asks for:
    - Recommended sustainable product mix
    - Budget allocation within the limit
    - Estimated cost breakdown
    - Impact positioning summary
  - Again, the assistant is constrained to structured JSON; any deviation is treated as an error and retried or returned as validation failure.

### Clean Separation of Concerns

- **HTTP layer (FastAPI routes)**: validates input and output with Pydantic, converts exceptions to proper HTTP errors.
- **Services (`app/services/*`)**: hold **business logic** and orchestration of AI calls and DB persistence.
- **AI layer (`app/ai_client.py`)**: knows how to talk to OpenAI, build prompts, and parse JSON.
- **DB layer (`app/models.py`, `app/db.py`)**: purely persistence, unaware of AI or HTTP.

### Environment & API Keys

- Configure via `.env` (not committed):

```env
ENVIRONMENT=local
DATABASE_URL=sqlite:///./raveya.db
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
```

- `app/config.py` reads these values and exposes them as a settings object.

### Running the Project

```bash
cd raveya
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `/docs`.

### Implemented Endpoints (Key Examples)

- **Module 1 – Auto-category & tags**
  - `POST /ai/catalog/auto-tag`
  - Request: product info.
  - Response: JSON with `primary_category`, `sub_category`, `seo_tags`, `sustainability_filters`, plus DB record ID.

- **Module 2 – B2B proposal**
  - `POST /ai/proposals/generate`
  - Request: company + budget.
  - Response: JSON with `product_mix`, `budget_allocation`, `cost_breakdown`, `impact_positioning_summary`, plus DB record ID.

### Demo Video Suggestions

- Show hitting the two implemented endpoints from:
  - Swagger UI (`/docs`) **and/or**
  - A simple `demo.http` or Postman collection.
- Confirm:
  - Structured JSON responses.
  - DB records created (briefly show the SQLite DB with a viewer or log output).
  - Logs of prompts & AI responses stored in the `ai_logs` table.

