"""
api/main.py
AfriLearn — Local FastAPI server.
Combines RAG context retrieval + Ollama local model inference.
Called by the AfriLearn PWA frontend at http://localhost:8000.

Start server:
  uvicorn api.main:app --host 0.0.0.0 --port 8000

Endpoints:
  GET  /health           — Service health check
  POST /generate         — Generate a quiz question or tutor response
  POST /tutor            — Multi-turn AI Tutor Chat
"""

import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.models import GenerateRequest, GenerateResponse, HealthResponse
from evaluation.format_validator import validate_output_format
from training.alpaca_prompt import format_inference_prompt

try:
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger.warning("LangChain not available — RAG disabled. Responses will not be curriculum-grounded.")

OLLAMA_BASE_URL   = "http://localhost:11434"
OLLAMA_MODEL_NAME = "afrilearn-tutor"
RAG_KB_DIR        = "afrilearn_knowledge_base"
EMBEDDING_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"
RAG_TOP_K         = 3

# Module-level state — initialised in lifespan
vectorstore   = None
rag_available = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load RAG vectorstore on startup. Release on shutdown."""
    global vectorstore, rag_available

    if RAG_AVAILABLE and Path(RAG_KB_DIR).exists():
        logger.info(f"Loading RAG knowledge base from {RAG_KB_DIR}...")
        try:
            embedding_model = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            vectorstore   = Chroma(persist_directory=RAG_KB_DIR, embedding_function=embedding_model)
            rag_available = True
            logger.success("RAG knowledge base loaded.")
        except Exception as e:
            logger.warning(f"RAG load failed: {e}. Continuing without RAG.")
    else:
        logger.warning(
            f"RAG knowledge base not found at {RAG_KB_DIR}. "
            "Run: python rag/build_knowledge_base.py"
        )

    yield

    logger.info("Shutting down AfriLearn API.")


app = FastAPI(
    title="AfriLearn AI API",
    description="Offline AI tutor for primary school children in Ghana and Nigeria.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # PWA running on same device — allow all localhost origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def retrieve_curriculum_context(query: str, country: str, subject: str) -> str:
    """Retrieve top-k curriculum chunks from ChromaDB."""
    if not rag_available or vectorstore is None:
        return ""
    try:
        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": RAG_TOP_K,
                "filter": {"country": country.lower()} if country else None,
            }
        )
        docs = retriever.get_relevant_documents(f"{country} {subject} {query}")
        if not docs:
            return ""
        return "\n\n".join(
            f"[Curriculum Reference — {doc.metadata.get('filename', 'Unknown')}]\n{doc.page_content}"
            for doc in docs
        )
    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
        return ""


def build_instruction(req: GenerateRequest) -> str:
    """Build the instruction string from a GenerateRequest."""
    if req.country == "Nigeria":
        return (
            f"COUNTRY: {req.country} | SUBJECT: {req.subject} | "
            f"GRADE: Primary {req.grade} | TERM: {req.term} | WEEK: {req.week} | "
            f"DIFFICULTY: {req.difficulty} | "
            f"TASK: Generate one multiple-choice question aligned to NERDC curriculum scope."
        )
    else:  # Ghana
        strand_part = f"STRAND: {req.strand} | " if req.strand else ""
        return (
            f"COUNTRY: {req.country} | SUBJECT: {req.subject} | "
            f"GRADE: Basic {req.grade} | {strand_part}"
            f"DIFFICULTY: {req.difficulty} | "
            f"TASK: Generate one multiple-choice question aligned to NaCCA curriculum scope."
        )


def build_input_context(req: GenerateRequest) -> str:
    return (
        f"student_age: {req.student_age} | "
        f"session_streak: {req.session_streak}_correct | "
        f"last_topic_score: {req.last_topic_score:.0f}% | "
        f"prior_topic: {req.prior_topic or 'none'} | "
        f"device_locale: {req.country}"
    )


def build_tutor_instruction(req: GenerateRequest) -> str:
    """Build the system instruction for multi-turn AI Tutor Chat."""
    country_curriculum = "NERDC Nigeria primary curriculum" if req.country == "Nigeria" else "NaCCA Ghana Standards-Based Curriculum"
    return (
        f"SYSTEM_ROLE: You are the AfriLearn AI Tutor. You run entirely offline on the student's device. "
        f"You follow the {country_curriculum}. "
        f"You adapt explanation depth to the student's age ({req.student_age}). "
        f"You never give the answer directly on first failure — scaffold first. "
        f"COUNTRY: {req.country} | SUBJECT: {req.subject} | GRADE: {'Primary' if req.country == 'Nigeria' else 'Basic'} {req.grade} | "
        f"INTERACTION_TYPE: tutor_chat_multi_turn"
    )


def format_turn_history(turns: list[dict]) -> str:
    if not turns:
        return ""
    history_str = "TURN_HISTORY: [\n"
    for turn in turns:
        history_str += f'  {{"role": "{turn["role"]}", "content": "{turn["content"]}"}},\n'
    history_str += "]"
    return history_str


def extract_curriculum_ref(output: str) -> str | None:
    match = re.search(r"CURRICULUM_REF:\s*(\S+)", output)
    return match.group(1) if match else None


async def call_ollama(prompt: str) -> str:
    """Call local Ollama model. Returns generated text."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model":  OLLAMA_MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p":       0.9,
                    "num_ctx":     2048,
                },
            },
        )
        response.raise_for_status()
        return response.json()["response"]


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check that Ollama is running and the model is loaded."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            models = [m["name"] for m in r.json().get("models", [])]
            model_loaded = any(OLLAMA_MODEL_NAME in m for m in models)
    except Exception:
        model_loaded = False

    return HealthResponse(
        status="ok" if model_loaded else "degraded",
        model=OLLAMA_MODEL_NAME,
        rag=rag_available,
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate_question(req: GenerateRequest):
    """
    Generate a curriculum-aligned quiz question.
    Retrieves RAG context if available, then calls Ollama.
    """
    instruction    = build_instruction(req)
    input_context  = build_input_context(req)
    rag_context    = retrieve_curriculum_context(req.subject, req.country, req.subject)

    # Prepend RAG context to instruction if available
    if rag_context:
        instruction = (
            f"CURRICULUM_CONTEXT (use this to ensure alignment):\n{rag_context}\n\n"
            + instruction
        )

    prompt = format_inference_prompt(instruction, input_context)

    try:
        model_output = await call_ollama(prompt)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
                "Ensure Ollama is running: ollama serve"
            ),
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")

    format_errors = validate_output_format(model_output)

    return GenerateResponse(
        response=model_output,
        model=OLLAMA_MODEL_NAME,
        country=req.country,
        subject=req.subject,
        grade=req.grade,
        difficulty=req.difficulty,
        curriculum_ref=extract_curriculum_ref(model_output),
        format_valid=len(format_errors) == 0,
        format_errors=format_errors,
    )


@app.post("/tutor", response_model=GenerateResponse)
async def tutor_chat(req: GenerateRequest):
    """
    Multi-turn AI Tutor Chat.
    Maintains pedagogical scaffolding across conversation turns.
    """
    if not req.student_message:
        raise HTTPException(status_code=400, detail="student_message is required for tutor_chat mode")

    instruction   = build_tutor_instruction(req)
    turn_history  = format_turn_history(req.turn_history or [])
    input_context = (
        f"{turn_history}\n"
        f"CURRENT_TURN: {{\"role\": \"student\", \"content\": \"{req.student_message}\"}}\n"
        f"STUDENT_CONTEXT: {{\"age\": {req.student_age}, \"grade\": \"{'Primary' if req.country == 'Nigeria' else 'Basic'} {req.grade}\", "
        f"\"last_quiz_score\": {req.last_topic_score:.0f}, \"session_attempts\": {req.session_streak}}}"
    )

    prompt = format_inference_prompt(instruction, input_context)

    try:
        model_output = await call_ollama(prompt)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. Ensure Ollama is running: ollama serve",
        )

    format_errors = validate_output_format(model_output)

    return GenerateResponse(
        response=model_output,
        model=OLLAMA_MODEL_NAME,
        country=req.country,
        subject=req.subject,
        grade=req.grade,
        difficulty=req.difficulty,
        curriculum_ref=extract_curriculum_ref(model_output),
        format_valid=len(format_errors) == 0,
        format_errors=format_errors,
    )
