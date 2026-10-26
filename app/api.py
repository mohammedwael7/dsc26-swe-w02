"""HTTP boundary for the parcel service."""

from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

from fastapi import FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.domain import EventType, InvalidTransition, Parcel, ParcelState, apply_event

PROBLEM = "application/problem+json"


class ParcelInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    merchant_ref: str = Field(min_length=1, max_length=64)
    cod_amount_piastres: int = Field(ge=0, le=5_000_000, strict=True)
    address_text: str = Field(min_length=1, max_length=500)


class EventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: EventType


def _parcel_json(parcel: Parcel) -> dict[str, object]:
    data = asdict(parcel)
    data["state"] = parcel.state.value
    return data


def _problem(status: int, title: str, detail: str | None = None, *, errors=None) -> JSONResponse:
    body: dict[str, object] = {
        "type": "about:blank",
        "title": title,
        "status": status,
    }
    if detail:
        body["detail"] = detail
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(body, status_code=status, media_type=PROBLEM)


def _documented_problem(description: str) -> dict[str, object]:
    return {"description": description, "content": {PROBLEM: {"schema": {"type": "object"}}}}


def create_app() -> FastAPI:
    app = FastAPI(title="Tawseel Parcel API", version="1.0.0")
    # All mutable data is scoped to this app instance.
    parcels: dict[str, Parcel] = {}
    creation_order: dict[str, int] = {}
    merchant_refs: set[str] = set()
    cursors: dict[str, tuple[str | None, int]] = {}
    next_sequence = 0

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errors = [
            {"loc": list(error["loc"]), "msg": error["msg"]}
            for error in exc.errors()
        ]
        return _problem(422, "Validation Error", "The request contains invalid fields.", errors=errors)

    @app.post(
        "/v1/parcels", operation_id="createParcel", status_code=201,
        responses={409: _documented_problem("Duplicate merchant reference."), 422: _documented_problem("Invalid request body.")},
    )
    async def create_parcel(payload: ParcelInput, response: Response):
        nonlocal next_sequence
        if payload.merchant_ref in merchant_refs:
            return _problem(409, "Conflict", "merchant_ref already exists.")
        parcel_id = f"pcl_{uuid4().hex}"
        parcel = Parcel(id=parcel_id, **payload.model_dump())
        parcels[parcel_id] = parcel
        merchant_refs.add(parcel.merchant_ref)
        creation_order[parcel_id] = next_sequence
        next_sequence += 1
        response.headers["Location"] = f"/v1/parcels/{parcel_id}"
        return _parcel_json(parcel)

    @app.get(
        "/v1/parcels/{parcel_id}", operation_id="getParcel",
        responses={404: _documented_problem("Parcel not found.")},
    )
    async def get_parcel(parcel_id: str):
        parcel = parcels.get(parcel_id)
        if parcel is None:
            return _problem(404, "Not Found", "Parcel not found.")
        return _parcel_json(parcel)

    @app.get(
        "/v1/parcels", operation_id="listParcels",
        responses={400: _documented_problem("Cursor is invalid."), 422: _documented_problem("Invalid state or limit.")},
    )
    async def list_parcels(
        state: ParcelState | None = None,
        limit: int = Query(default=20, ge=1, le=100),
        cursor: str | None = None,
    ):
        after = -1
        if cursor is not None:
            issued = cursors.get(cursor)
            if issued is None or issued[0] != (state.value if state else None):
                return _problem(400, "Bad Request", "Cursor is invalid for this query.")
            after = issued[1]
        matching = sorted(
            (parcel for parcel in parcels.values()
             if creation_order[parcel.id] > after and (state is None or parcel.state is state)),
            key=lambda parcel: creation_order[parcel.id],
        )
        page = matching[:limit]
        next_cursor = None
        if len(matching) > limit and page:
            next_cursor = uuid4().hex
            cursors[next_cursor] = (state.value if state else None, creation_order[page[-1].id])
        return {"items": [_parcel_json(parcel) for parcel in page], "next_cursor": next_cursor}

    @app.post(
        "/v1/parcels/{parcel_id}/events", operation_id="recordParcelEvent",
        responses={404: _documented_problem("Parcel not found."), 409: _documented_problem("Invalid lifecycle transition."), 422: _documented_problem("Unknown or missing event type.")},
    )
    async def record_event(parcel_id: str, payload: EventInput):
        parcel = parcels.get(parcel_id)
        if parcel is None:
            return _problem(404, "Not Found", "Parcel not found.")
        try:
            updated = apply_event(parcel, payload.type)
        except InvalidTransition as exc:
            return _problem(409, "Conflict", str(exc))
        parcels[parcel_id] = updated
        return _parcel_json(updated)

    return app


app = create_app()
