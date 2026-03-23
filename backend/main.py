from pydantic import ValidationError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from enrich import enrich_setup
from llm import build_local_response, validate_analysis_payload
from models import AnalyzeResponse, ErrorResponse
from schemas import AthleteProfileInput

app = FastAPI(title="Table Tennis Gear Advisor API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail and "detail" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": "http_error", "detail": str(exc.detail)})


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={502: {"model": ErrorResponse}},
)
def analyze(profile: AthleteProfileInput) -> AnalyzeResponse:
    enriched_setup = enrich_setup(profile)
    try:
        response = build_local_response(profile, enriched_setup)
        return validate_analysis_payload(response.model_dump())
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "invalid_analysis_response",
                "detail": str(exc),
            },
        ) from exc
