
from fastapi import FastAPI, HTTPException
from app.services.chat import ask_question
from pydantic import BaseModel, Field, field_validator
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Shivalik AI API",
    description="RAG-powered university information assistant",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty or whitespace")

        return value

class Source(BaseModel):
    citation_id: int
    title: str
    url: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    retrieved_chunks: int
    conversation_id: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Shivalik AI",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        result = ask_question(
            question=request.question,
            conversation_id=request.conversation_id,
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process the question.",
        )
