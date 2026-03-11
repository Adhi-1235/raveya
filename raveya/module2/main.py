from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.ai_client import AIClient
from app.config import get_settings
from app.db import Base, engine, get_db
from app.schemas import ProposalInput, ProposalOutput
from app.services.proposal_service import generate_b2b_proposal


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Module 2 – B2B Proposal Generator",
    version="1.0.0",
    description="Standalone UI and API for the AI B2B Proposal Generator.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_ai_client():
    settings = get_settings()
    if settings.AI_MODE == "mock":
        class _DummyClient:
            def generate_json(self, *args, **kwargs):
                raise RuntimeError("generate_json should not be called in mock AI_MODE")

        return _DummyClient()

    try:
        return AIClient()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@app.get("/", response_class=HTMLResponse, tags=["ui"])
def root_ui() -> str:
    """
    Simple browser UI for Module 2.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <title>Module 2 – B2B Proposal Generator</title>
        <style>
          body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem; background: #020617; color: #e5e7eb; }
          h1 { color: #f9a8d4; }
          label { display: block; margin-top: 1rem; font-weight: 600; }
          input[type="text"], input[type="number"], textarea {
            width: 100%; max-width: 720px; padding: 0.5rem 0.75rem; border-radius: 0.375rem;
            border: 1px solid #4b5563; background: #020617; color: #e5e7eb;
          }
          textarea { min-height: 100px; resize: vertical; }
          button {
            margin-top: 1.5rem; padding: 0.6rem 1.4rem; border-radius: 9999px; border: none;
            background: linear-gradient(135deg, #ec4899, #6366f1); color: white; font-weight: 600; cursor: pointer;
          }
          button:disabled { opacity: 0.5; cursor: not-allowed; }
          pre {
            margin-top: 2rem; padding: 1rem; background: #020617; border-radius: 0.5rem;
            border: 1px solid #1f2937; max-width: 900px; overflow-x: auto;
          }
          .status { margin-top: 1rem; font-size: 0.9rem; color: #93c5fd; }
        </style>
      </head>
      <body>
        <h1>Module 2 – AI B2B Proposal Generator</h1>
        <p>Generate a structured sustainable product proposal within a budget.</p>

        <form id="proposal-form">
          <label>Company name</label>
          <input type="text" id="company_name" required placeholder="GreenTech Corp" />

          <label>Contact email (optional)</label>
          <input type="text" id="contact_email" placeholder="procurement@example.com" />

          <label>Total budget (in your currency)</label>
          <input type="number" id="total_budget" min="1" step="0.01" required placeholder="5000" />

          <label>Target audience (optional)</label>
          <textarea id="target_audience" placeholder="Employees, event attendees, VIP customers..."></textarea>

          <label>Sustainability priorities (comma-separated, optional)</label>
          <input type="text" id="sustainability_priorities" placeholder="plastic-free, locally-sourced" />

          <label>Notes / constraints (optional)</label>
          <textarea id="notes" placeholder="Any extra context, e.g. remote teams, shipping rules, brands to avoid..."></textarea>

          <button type="submit" id="submit-btn">Generate proposal</button>
          <div class="status" id="status"></div>
        </form>

        <pre id="result"></pre>

        <script>
          const form = document.getElementById("proposal-form");
          const statusEl = document.getElementById("status");
          const resultEl = document.getElementById("result");
          const submitBtn = document.getElementById("submit-btn");

          form.addEventListener("submit", async (e) => {
            e.preventDefault();
            statusEl.textContent = "Calling AI, please wait...";
            submitBtn.disabled = true;
            resultEl.textContent = "";

            const rawPriorities = document.getElementById("sustainability_priorities").value;
            const priorities = rawPriorities
              .split(",")
              .map(s => s.trim())
              .filter(Boolean);

            const payload = {
              company_name: document.getElementById("company_name").value,
              contact_email: document.getElementById("contact_email").value || null,
              total_budget: Number(document.getElementById("total_budget").value),
              target_audience: document.getElementById("target_audience").value || null,
              sustainability_priorities: priorities.length ? priorities : null,
              notes: document.getElementById("notes").value || null
            };

            try {
              const resp = await fetch("/api/proposals/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
              });
              const json = await resp.json();
              if (!resp.ok) {
                statusEl.textContent = json.detail || "Request failed.";
              } else {
                statusEl.textContent = json.within_budget
                  ? "Success – proposal is within budget. Response shown below."
                  : "Generated proposal exceeds budget; see details below.";
                resultEl.textContent = JSON.stringify(json, null, 2);
              }
            } catch (err) {
              statusEl.textContent = "Network or server error.";
            } finally {
              submitBtn.disabled = false;
            }
          });
        </script>
      </body>
    </html>
    """


@app.post("/api/proposals/generate", response_model=ProposalOutput, tags=["api"])
def api_generate_proposal(
    payload: ProposalInput,
    db: Session = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
) -> ProposalOutput:
    try:
        return generate_b2b_proposal(db, ai_client, payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate proposal: {exc}",
        ) from exc

