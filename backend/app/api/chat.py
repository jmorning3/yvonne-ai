from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.app.core.orchestrator import Orchestrator
from backend.app.models.requests import ChatRequest
from backend.app.models.responses import ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> JSONResponse:
    orchestrator: Orchestrator = request.app.state.orchestrator
    mapped = await orchestrator.process(payload)
    return JSONResponse(mapped.body.model_dump(mode="json", by_alias=True), mapped.status_code)
