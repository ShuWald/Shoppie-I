from typing import Annotated

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(
    title="Shoppie-I API",
    version="0.1.0",
    description="FastAPI backend for the Shoppie-I hackathon project.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: Annotated[str, Field(min_length=1, description="User message for the assistant")]


class ChatResponse(BaseModel):
    reply: str
    source: str


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Shoppie-I API is running", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(
        reply=f"Backend received: {request.message}",
        source="stub",
    )