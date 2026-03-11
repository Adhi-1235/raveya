from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.ai_client import AIClient
from app.config import get_settings
from app.db import Base, engine, get_db
from app.schemas import CatalogInput, CatalogOutput
from app.services.catalog_service import auto_categorize_and_tag


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Module 1 – Auto Category & Tags",
    version="1.0.0",
    description="Standalone UI and API for the AI Auto-Category & Tag Generator.",
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
    Simple browser UI for Module 1.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <title>Module 1 – Auto Category & Tags</title>
        <style>
          body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem; background: #0b1120; color: #e5e7eb; }
          h1 { color: #a5b4fc; }
          label { display: block; margin-top: 1rem; font-weight: 600; }
          input[type="text"], textarea {
            width: 100%; max-width: 640px; padding: 0.5rem 0.75rem; border-radius: 0.375rem;
            border: 1px solid #4b5563; background: #020617; color: #e5e7eb;
          }
          textarea { min-height: 120px; resize: vertical; }
          button {
            margin-top: 1.5rem; padding: 0.6rem 1.4rem; border-radius: 9999px; border: none;
            background: linear-gradient(135deg, #4f46e5, #22c55e); color: white; font-weight: 600; cursor: pointer;
          }
          button:disabled { opacity: 0.5; cursor: not-allowed; }
          pre {
            margin-top: 2rem; padding: 1rem; background: #020617; border-radius: 0.5rem;
            border: 1px solid #1f2937; max-width: 760px; overflow-x: auto;
          }
          .status { margin-top: 1rem; font-size: 0.9rem; color: #93c5fd; }
          a { color: #93c5fd; }
        </style>
      </head>
      <body>
        <h1>Module 1 – AI Auto-Category & Tag Generator</h1>
        <p>Enter product details and let the model assign a primary category, sub-category, SEO tags, and sustainability filters.</p>

        <form id="product-form">
          <label>Product name</label>
          <input type="text" id="product_name" required placeholder="Reusable bamboo coffee cup" />

          <label>Description</label>
          <textarea id="description" required placeholder="Describe the product, materials, and use case..."></textarea>

          <label>Attributes (optional, JSON)</label>
          <textarea id="attributes" placeholder='{"capacity_ml": 350, "material": "bamboo"}'></textarea>

          <button type="submit" id="submit-btn">Generate categories & tags</button>
          <div class="status" id="status"></div>
        </form>

        <pre id="result"></pre>

        <script>
          const form = document.getElementById("product-form");
          const statusEl = document.getElementById("status");
          const resultEl = document.getElementById("result");
          const submitBtn = document.getElementById("submit-btn");

          form.addEventListener("submit", async (e) => {
            e.preventDefault();
            statusEl.textContent = "Calling AI, please wait...";
            submitBtn.disabled = true;
            resultEl.textContent = "";

            let attributes = null;
            const rawAttrs = document.getElementById("attributes").value.trim();
            if (rawAttrs) {
              try {
                attributes = JSON.parse(rawAttrs);
              } catch (err) {
                statusEl.textContent = "Attributes must be valid JSON.";
                submitBtn.disabled = false;
                return;
              }
            }

            const payload = {
              product_name: document.getElementById("product_name").value,
              description: document.getElementById("description").value,
              attributes: attributes
            };

            try {
              const resp = await fetch("/api/auto-tag", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
              });
              const json = await resp.json();
              if (!resp.ok) {
                statusEl.textContent = json.detail || "Request failed.";
              } else {
                statusEl.textContent = "Success. Response shown below.";
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


@app.post("/api/auto-tag", response_model=CatalogOutput, tags=["api"])
def api_auto_tag(
    payload: CatalogInput,
    db: Session = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
) -> CatalogOutput:
    try:
        return auto_categorize_and_tag(db, ai_client, payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-categorize product: {exc}",
        ) from exc

