import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> None:
        """Gracefully skip loading .env when python-dotenv is missing."""
        return None

# Load environment variables from .env (if present)
load_dotenv()

try:
    from anthropic import Anthropic
except ImportError as exc:
    raise ImportError(
        'anthropic package is required. Install with `pip install anthropic fastapi uvicorn python-dotenv`.'
    ) from exc


class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User message sent to Claude.")
    system: Optional[str] = Field(
        default="You are a helpful assistant for the Penn × Anthropic Emp Matching initiative."
    )
    model: str = Field(default="claude-3-5-sonnet-20241022")
    max_tokens: int = Field(default=256, ge=1, le=2048)


class PromptResponse(BaseModel):
    reply: str


class ProfileQuestion(BaseModel):
    question: str = Field(..., min_length=5, description="Question about the stored user dataset.")
    model: str = Field(default="claude-haiku-4-5-20251001")
    max_tokens: int = Field(default=256, ge=64, le=1024)


app = FastAPI(title="Penn × Anthropic FastAPI backend")

# PROFILE_DATA_PATH can also come from .env:
# e.g. PROFILE_DATA_PATH=personal.json
PROFILE_DATA_PATH = Path(os.getenv("PROFILE_DATA_PATH", "personal.json"))
_PROFILE_CACHE: Optional[Dict[str, Any]] = None


def get_client() -> Anthropic:
    api_key = ""  
    api_key = os.getenv("ANTHROPIC_API_KEY")  # <- now populated by load_dotenv()
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY environment variable not set",
        )
    return Anthropic(api_key=api_key)


def get_profile_dataset() -> Dict[str, Any]:
    global _PROFILE_CACHE  # noqa: PLW0603 - cache to avoid repeated disk I/O
    if _PROFILE_CACHE is None:
        if not PROFILE_DATA_PATH.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Profile data file not found at {PROFILE_DATA_PATH.resolve()}",
            )
        try:
            with PROFILE_DATA_PATH.open(encoding="utf-8") as profile_file:
                _PROFILE_CACHE = json.load(profile_file)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=500, detail="Profile JSON file is invalid") from exc
    return _PROFILE_CACHE


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


@app.post("/api/claude", response_model=PromptResponse)
async def call_claude(payload: PromptRequest) -> PromptResponse:
    client = get_client()

    try:
        response = client.messages.create(
            model=payload.model,
            max_tokens=payload.max_tokens,
            system=payload.system,
            messages=[{"role": "user", "content": payload.prompt}],
        )
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=502, detail=f"Anthropic API call failed: {exc}") from exc

    reply_text = "".join(block.text for block in response.content if hasattr(block, "text"))
    return PromptResponse(reply=reply_text or "[Claude did not return any text]")


@app.post("/api/profile-question", response_model=PromptResponse)
async def ask_about_profile(payload: ProfileQuestion) -> PromptResponse:
    dataset = get_profile_dataset()
    dataset_text = json.dumps(dataset, indent=2)
    composed_prompt = (
        "Use the following JSON dataset describing Penn × Anthropic users to answer the question.\n"
        "Be specific and reference available fields, acknowledging when data is absent.\n\n"
        f"PROFILE DATASET:\n{dataset_text}\n\n"
        f"QUESTION: {payload.question}\n"
        "Respond with concise paragraphs."
    )

    client = get_client()
    try:
        response = client.messages.create(
            model=payload.model,
            max_tokens=payload.max_tokens,
            system="You analyze first-party user profile datasets for Penn × Anthropic.",
            messages=[{"role": "user", "content": composed_prompt}],
        )
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=502, detail=f"Anthropic API call failed: {exc}") from exc

    reply_text = "".join(block.text for block in response.content if hasattr(block, "text"))
    return PromptResponse(reply=reply_text or "[Claude did not return any text]")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server_fastapi:app",  # change module name if this file is named differently
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )
