from fastapi import FastAPI

from filters import select_candidates
from llm import build_mock_response
from models import AnalyzeResponse
from schemas import AthleteProfileInput

app = FastAPI(title="Table Tennis Gear Advisor API", version="0.1.0")


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(profile: AthleteProfileInput) -> AnalyzeResponse:
    _ = select_candidates(profile)
    return build_mock_response(profile)
