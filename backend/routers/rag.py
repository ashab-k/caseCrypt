"""Authenticated public-corpus research. No writes or case-document retrieval."""
from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from middleware.auth import get_current_user
from models.research import CorpusStatus, ResearchRequest, ResearchResponse, SearchResponse
from services.corpus_service import CorpusUnavailable, corpus_status
from services.rag_service import query, retrieve

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get('/corpus/status', response_model=CorpusStatus)
async def status():
    return await run_in_threadpool(corpus_status)


@router.post('/search', response_model=SearchResponse)
async def search(body: ResearchRequest):
    try:
        return await run_in_threadpool(retrieve, body.question, body.act, body.top_k)
    except CorpusUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post('/query', response_model=ResearchResponse)
async def ask(body: ResearchRequest):
    try:
        return await run_in_threadpool(query, body.question, body.act, body.top_k)
    except CorpusUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
