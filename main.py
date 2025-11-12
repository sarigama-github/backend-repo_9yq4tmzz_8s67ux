import os
from typing import List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db, create_document, get_documents
from schemas import IdeaAnalysis, DeckAnalysis, ContactMessage

app = FastAPI(title="StartupMate API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "StartupMate Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# ---------- Gemini AI Integration (Stubbed) ----------
# NOTE: Replace stub responses with calls to Google Gemini API if available.

def gemini_analyze_idea(idea: str) -> Dict[str, Any]:
    # Stubbed analysis to keep the demo functional without external keys.
    base_tags = ["market", "problem-solution", "MVP", "risks", "growth"]
    return {
        "summary": f"Concise overview of the idea: {idea[:120]}...",
        "market": "Estimated TAM/SAM/SOM with initial hypothesis and segments.",
        "target_audience": "Early adopters in SMB/enterprise depending on positioning.",
        "competitors": ["Incumbent A", "Startup B", "Open-source C"],
        "risks": [
            "Go-to-market complexity",
            "Data availability and model drift",
            "Regulatory or privacy constraints"
        ],
        "next_steps": [
            "Define problem statement and success metric",
            "Outline 2-week MVP with clear scope",
            "Talk to 10 target users and validate willingness to pay"
        ],
        "score_overall": 72,
        "tags": base_tags
    }

async def gemini_analyze_deck(file: UploadFile) -> Dict[str, Any]:
    # Stubbed scoring logic
    name = file.filename or "deck"
    # We won't actually read the entire file; preview first bytes
    content = await file.read(2048)
    preview = content.decode(errors="ignore") if isinstance(content, (bytes, bytearray)) else ""
    categories = {
        "Problem": 70,
        "Solution": 75,
        "Market": 68,
        "Business Model": 62,
        "Traction": 55,
        "Team": 80,
        "Go-To-Market": 60
    }
    overall = int(sum(categories.values()) / len(categories))
    return {
        "filename": name,
        "mime_type": file.content_type,
        "size_bytes": len(content),
        "overall_score": overall,
        "category_scores": categories,
        "suggestions": [
            "Clarify the quantified problem impact",
            "Add early validation/traction signals",
            "Tighten GTM milestones with specific channels"
        ],
        "extracted_text_preview": preview
    }

# ---------- API Models ----------
class IdeaRequest(BaseModel):
    idea: str

# ---------- Routes ----------
@app.post("/api/validate-idea")
async def validate_idea(payload: IdeaRequest):
    if not payload.idea or len(payload.idea.strip()) < 10:
        raise HTTPException(status_code=400, detail="Please provide a more detailed idea (at least 10 characters).")
    analysis = gemini_analyze_idea(payload.idea.strip())
    doc = IdeaAnalysis(idea=payload.idea.strip(), **analysis)
    inserted_id = create_document("ideaanalysis", doc)
    return {"id": inserted_id, "analysis": doc.model_dump()}

@app.post("/api/score-deck")
async def score_deck(file: UploadFile = File(...)):
    allowed = {"application/pdf", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload PDF, PPTX, or DOCX.")
    result = await gemini_analyze_deck(file)
    doc = DeckAnalysis(**result)
    inserted_id = create_document("deckanalysis", doc)
    return {"id": inserted_id, "scorecard": doc.model_dump()}

@app.get("/api/reports")
async def list_reports(limit: int = 50):
    idea_docs = get_documents("ideaanalysis", limit=limit)
    deck_docs = get_documents("deckanalysis", limit=limit)
    # Convert ObjectId to string safely
    def normalize(doc):
        d = {k: (str(v) if k == "_id" else v) for k, v in doc.items()}
        return d
    return {
        "ideas": [normalize(x) for x in idea_docs],
        "decks": [normalize(x) for x in deck_docs],
    }

@app.post("/api/contact")
async def contact(msg: ContactMessage):
    _id = create_document("contactmessage", msg)
    return {"status": "received", "id": _id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
