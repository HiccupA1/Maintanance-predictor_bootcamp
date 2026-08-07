"""Equipment, parameter, reading, and alert API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Path, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.core.errors import ErrorCode, ProblemException
from app.db.session import get_db
from app.models.alert import Alert
from app.models.equipment import Equipment, Parameter, Reading
from app.schemas.domain import (
    AlertResponse,
    EquipmentCreate,
    EquipmentListResponse,
    EquipmentResponse,
    EquipmentUpdate,
    ParameterCreate,
    ParameterResponse,
    ParameterUpdate,
    ReadingCreate,
    ReadingResponse,
    ReadingUpdate,
)
from app.services import domain as service

router = APIRouter(tags=["equipment"])


# PUBLIC_INTERFACE
@router.get("/equipment", response_model=EquipmentListResponse)
def list_equipment(db: Session = Depends(get_db)) -> EquipmentListResponse:
    """List all equipment ordered by human-readable equipment id."""
    rows = db.execute(select(Equipment).order_by(Equipment.equipment_id)).scalars().all()
    return EquipmentListResponse(
        items=[EquipmentResponse.model_validate(row) for row in rows],
        total=len(rows),
    )


# PUBLIC_INTERFACE
@router.post("/equipment", response_model=EquipmentResponse, status_code=201)
def create_equipment(
    payload: EquipmentCreate, db: Session = Depends(get_db)
) -> EquipmentResponse:
    """Create equipment."""
    if db.execute(
        select(Equipment).where(Equipment.equipment_id == payload.equipment_id)
    ).scalar_one_or_none():
        raise ProblemException(
            status=409,
            code=ErrorCode.INVALID_REQUEST,
            detail="equipment_id already exists.",
        )
    row = Equipment(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return EquipmentResponse.model_validate(row)


# PUBLIC_INTERFACE
@router.get("/equipment/{equipment_id}", response_model=EquipmentResponse)
def get_equipment(
    equipment_id: str = Path(...), db: Session = Depends(get_db)
) -> EquipmentResponse:
    """Fetch one equipment record."""
    return EquipmentResponse.model_validate(service.get_equipment(db, equipment_id))


# PUBLIC_INTERFACE
@router.put("/equipment/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    payload: EquipmentUpdate,
    equipment_id: str = Path(...),
    db: Session = Depends(get_db),
) -> EquipmentResponse:
    """Replace equipment metadata."""
    row = service.get_equipment(db, equipment_id)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return EquipmentResponse.model_validate(row)


# PUBLIC_INTERFACE
@router.delete(
    "/equipment/{equipment_id}",
    response_model=None,
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["Admin"]))],
)
def delete_equipment(
    equipment_id: str = Path(..., description="Human-readable equipment identifier."),
    db: Session = Depends(get_db),
) -> Response:
    """Delete equipment; database cascades child records."""
    row = service.get_equipment(db, equipment_id)
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# PUBLIC_INTERFACE
@router.get(
    "/equipment/{equipment_id}/parameters",
    response_model=list[ParameterResponse],
)
def list_parameters(
    equipment_id: str, db: Session = Depends(get_db)
) -> list[ParameterResponse]:
    """List parameters configured for equipment."""
    equipment = service.get_equipment(db, equipment_id)
    rows = list(
        db.execute(
            select(Parameter)
            .where(Parameter.equipment_id == equipment.id)
            .order_by(Parameter.name)
        ).scalars()
    )
    return [ParameterResponse.model_validate(row) for row in rows]


# PUBLIC_INTERFACE
@router.post(
    "/equipment/{equipment_id}/parameters",
    response_model=ParameterResponse,
    status_code=201,
)
def create_parameter(
    payload: ParameterCreate, equipment_id: str, db: Session = Depends(get_db)
) -> ParameterResponse:
    """Create a threshold parameter."""
    equipment = service.get_equipment(db, equipment_id)
    row = Parameter(equipment_id=equipment.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return ParameterResponse.model_validate(row)


# PUBLIC_INTERFACE
@router.put("/parameters/{parameter_id}", response_model=ParameterResponse)
def update_parameter(
    payload: ParameterUpdate, parameter_id: str, db: Session = Depends(get_db)
) -> ParameterResponse:
    """Replace parameter configuration."""
    row = service.get_parameter(db, parameter_id)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return ParameterResponse.model_validate(row)


# PUBLIC_INTERFACE
@router.post("/readings", response_model=ReadingResponse, status_code=201)
def create_reading(
    payload: ReadingCreate,
    x_user_name: str | None = Header(default=None, alias="X-User-Name"),
    db: Session = Depends(get_db),
) -> ReadingResponse:
    """Store a reading and evaluate threshold alerts."""
    row = service.create_reading(db, payload, x_user_name or "dev")
    return ReadingResponse.model_validate(row)


# PUBLIC_INTERFACE
@router.get(
    "/equipment/{equipment_id}/parameters/{parameter_id}/readings",
    response_model=list[ReadingResponse],
)
def list_readings(
    equipment_id: str, parameter_id: str, db: Session = Depends(get_db)
) -> list[ReadingResponse]:
    """Return parameter readings in reverse chronological order."""
    equipment = service.get_equipment(db, equipment_id)
    service.get_parameter(db, parameter_id)
    rows = list(
        db.execute(
            select(Reading)
            .where(
                Reading.equipment_id == equipment.id,
                Reading.parameter_id == parameter_id,
            )
            .order_by(Reading.timestamp.desc())
        ).scalars()
    )
    return [ReadingResponse.model_validate(row) for row in rows]


# PUBLIC_INTERFACE
@router.put("/readings/{reading_id}", response_model=ReadingResponse)
def update_reading(
    payload: ReadingUpdate,
    reading_id: str,
    x_user_name: str | None = Header(default=None, alias="X-User-Name"),
    db: Session = Depends(get_db),
) -> ReadingResponse:
    """Edit a recent reading."""
    row = service.update_reading(db, reading_id, payload, x_user_name or "dev")
    return ReadingResponse.model_validate(row)


# PUBLIC_INTERFACE
@router.delete(
    "/readings/{reading_id}",
    response_model=None,
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["Operator"]))],
)
def delete_reading(
    reading_id: str = Path(..., description="Reading UUID."),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a reading."""
    row = db.get(Reading, reading_id)
    if row is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.INVALID_REQUEST,
            detail=f"Reading '{reading_id}' does not exist.",
        )
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# PUBLIC_INTERFACE
@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(db: Session = Depends(get_db)) -> list[AlertResponse]:
    """List alerts newest first."""
    rows = list(
        db.execute(select(Alert).order_by(Alert.created_at.desc())).scalars()
    )
    return [AlertResponse.model_validate(row) for row in rows]


# PUBLIC_INTERFACE
@router.delete(
    "/alerts/{alert_id}",
    response_model=None,
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["PlantManager"]))],
)
def delete_alert(
    alert_id: str = Path(..., description="Alert UUID."),
    db: Session = Depends(get_db),
) -> Response:
    """Delete an alert."""
    row = db.get(Alert, alert_id)
    if row is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.ALERT_NOT_FOUND,
            detail=f"Alert '{alert_id}' does not exist.",
        )
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# PUBLIC_INTERFACE
@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: str, db: Session = Depends(get_db)) -> AlertResponse:
    """Fetch an alert by id."""
    row = db.get(Alert, alert_id)
    if row is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.ALERT_NOT_FOUND,
            detail=f"Alert '{alert_id}' does not exist.",
        )
    return AlertResponse.model_validate(row)
