"""Equipment, parameter, reading, and alert API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Path
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ErrorCode, ProblemException, problem_responses
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
) -> Equipment:
    """Create equipment after validating criticality in the inclusive 1-5 range."""
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
    # Ensure the returned payload matches the declared response_model exactly.
    return EquipmentResponse.model_validate(row)


# PUBLIC_INTERFACE
@router.get("/equipment/{equipment_id}", response_model=EquipmentResponse)
def get_equipment(
    equipment_id: str = Path(...), db: Session = Depends(get_db)
) -> Equipment:
    """Fetch one equipment record."""
    return service.get_equipment(db, equipment_id)


# PUBLIC_INTERFACE
@router.put("/equipment/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    payload: EquipmentUpdate,
    equipment_id: str = Path(...),
    db: Session = Depends(get_db),
) -> Equipment:
    """Replace equipment metadata."""
    row = service.get_equipment(db, equipment_id)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


# PUBLIC_INTERFACE
@router.get(
    "/equipment/{equipment_id}/parameters",
    response_model=list[ParameterResponse],
)
def list_parameters(
    equipment_id: str, db: Session = Depends(get_db)
) -> list[Parameter]:
    """List parameters configured for equipment."""
    equipment = service.get_equipment(db, equipment_id)
    return list(
        db.execute(
            select(Parameter)
            .where(Parameter.equipment_id == equipment.id)
            .order_by(Parameter.name)
        ).scalars()
    )


# PUBLIC_INTERFACE
@router.post(
    "/equipment/{equipment_id}/parameters",
    response_model=ParameterResponse,
    status_code=201,
)
def create_parameter(
    payload: ParameterCreate, equipment_id: str, db: Session = Depends(get_db)
) -> Parameter:
    """Create a threshold parameter for equipment."""
    equipment = service.get_equipment(db, equipment_id)
    row = Parameter(equipment_id=equipment.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# PUBLIC_INTERFACE
@router.put("/parameters/{parameter_id}", response_model=ParameterResponse)
def update_parameter(
    payload: ParameterUpdate, parameter_id: str, db: Session = Depends(get_db)
) -> Parameter:
    """Replace a parameter threshold configuration."""
    row = service.get_parameter(db, parameter_id)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


# PUBLIC_INTERFACE
@router.post("/readings", response_model=ReadingResponse, status_code=201)
def create_reading(
    payload: ReadingCreate,
    x_user_name: str | None = Header(default=None, alias="X-User-Name"),
    db: Session = Depends(get_db),
) -> Reading:
    """Store a reading and evaluate threshold alerts."""
    return service.create_reading(db, payload, x_user_name or "dev")


# PUBLIC_INTERFACE
@router.get(
    "/equipment/{equipment_id}/parameters/{parameter_id}/readings",
    response_model=list[ReadingResponse],
)
def list_readings(
    equipment_id: str, parameter_id: str, db: Session = Depends(get_db)
) -> list[Reading]:
    """Return parameter readings in reverse chronological order."""
    equipment = service.get_equipment(db, equipment_id)
    service.get_parameter(db, parameter_id)
    return list(
        db.execute(
            select(Reading)
            .where(
                Reading.equipment_id == equipment.id,
                Reading.parameter_id == parameter_id,
            )
            .order_by(Reading.timestamp.desc())
        ).scalars()
    )


# PUBLIC_INTERFACE
@router.put("/readings/{reading_id}", response_model=ReadingResponse)
def update_reading(
    payload: ReadingUpdate,
    reading_id: str,
    x_user_name: str | None = Header(default=None, alias="X-User-Name"),
    db: Session = Depends(get_db),
) -> Reading:
    """Edit a recent reading and record the modification audit fields."""
    return service.update_reading(db, reading_id, payload, x_user_name or "dev")


# PUBLIC_INTERFACE
@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(db: Session = Depends(get_db)) -> list[Alert]:
    """List alerts newest first."""
    return list(
        db.execute(
            select(Alert)
            .options(selectinload(Alert.equipment), selectinload(Alert.parameter))
            .order_by(Alert.created_at.desc())
        )
        .scalars()
    )


# PUBLIC_INTERFACE
@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: str, db: Session = Depends(get_db)) -> Alert:
    """Fetch an alert by id."""
    row = db.get(Alert, alert_id)
    if row is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.ALERT_NOT_FOUND,
            detail=f"Alert '{alert_id}' does not exist.",
        )
    return row
