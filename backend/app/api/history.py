"""Read and manage generated caption history."""

import sqlite3

from fastapi import APIRouter, HTTPException, Query, Request

from app.models.history import HistoryListResponse, HistoryRecord
from app.services.history_service import HistoryRepository

router = APIRouter(prefix="/history", tags=["Caption History"])


def _repository(request: Request) -> HistoryRepository:
    return request.app.state.history_repository


def _database_error() -> HTTPException:
    return HTTPException(status_code=503, detail="Caption history is temporarily unavailable.")


@router.get(
    "/",
    response_model=HistoryListResponse,
    summary="List caption generation history",
    description="Returns completed combined generations newest first. Limit is 1–100; offset is zero-based.",
)
def list_history(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> HistoryListResponse:
    try:
        rows, total = _repository(request).list(limit=limit, offset=offset)
        return HistoryListResponse(records=[HistoryRecord.model_validate(row) for row in rows], limit=limit, offset=offset, total=total)
    except sqlite3.Error as exc:
        raise _database_error() from exc


@router.get(
    "/{record_id}",
    response_model=HistoryRecord,
    summary="Get one history record",
)
def get_history_record(record_id: int, request: Request) -> HistoryRecord:
    try:
        row = _repository(request).get(record_id)
    except sqlite3.Error as exc:
        raise _database_error() from exc
    if row is None:
        raise HTTPException(status_code=404, detail="History record not found.")
    return HistoryRecord.model_validate(row)


@router.delete(
    "/{record_id}",
    status_code=204,
    summary="Delete one history record",
)
def delete_history_record(record_id: int, request: Request) -> None:
    try:
        deleted = _repository(request).delete(record_id)
    except sqlite3.Error as exc:
        raise _database_error() from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="History record not found.")
