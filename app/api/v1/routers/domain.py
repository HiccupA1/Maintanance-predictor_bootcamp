"""Equipment, parameter, reading, and alert API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ErrorCode, ProblemException
from app.core.rbac import Permission, guard, require_permission
from app.db.session import get_db
from app.models.alert import Alert
from app.models.equipment import Equipment, Parameter, Reading
from app.models.user_profile import UserProfile
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

# Handlers that record who acted need the authenticated profile, so they take
# the guard as a parameter rather than a route-level dependency.
_reading_writer = require_permission(Permission.READING_WRITE)


def _actor_name(user: UserProfile) -> str:
    """Name recorded on readings; taken from the verified profile, never a
    client-supplied header."""
    return user.display_name or user.email or user.supabase_user_id


# PUBLIC_INTERFACE
@router.get(
    "/equipment",
    response_model=EquipmentListResponse,
    dependencies=[guard(Permission.EQUIPMENT_READ)],
)
def list_equipment(db: Session = Depends(get_db)) -> EquipmentListResponse:
    """List all equipment ordered by human-readable equipment id."""
    rows = (
        db.execute(select(Equipment).order_by(Equipment.equipment_id))
        .scalars()
        .all()
    )
    return EquipmentListResponse(
        items=[EquipmentResponse.model_validate(row) for row in rows],
        total=len(rows),
    )


# PUBLIC_INTERFACE
@router.post(
    "/equipment",
    response_model=EquipmentResponse,
    status_code=201,
    dependencies=[guard(Permission.EQUIPMENT_WRITE)],
)
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
@router.get(
    "/equipment/{equipment_id}",
    response_model=EquipmentResponse,
    dependencies=[guard(Permission.EQUIPMENT_READ)],
)
def get_equipment(
    equipment_id: str = Path(...), db: Session = Depends(get_db)
) -> EquipmentResponse:
    """Fetch one equipment record."""
    return EquipmentResponse.model_validate(
        service.get_equipment(db, equipment_id)
    )


# PUBLIC_INTERFACE
@router.put(
    "/equipment/{equipment_id}",
    response_model=EquipmentResponse,
    dependencies=[guard(Permission.EQUIPMENT_WRITE)],
)
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
    dependencies=[guard(Permission.EQUIPMENT_DELETE)],
)
def delete_equipment(
    equipment_id: str = Path(
        ..., description="Human-readable equipment identifier."
    ),
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
    dependencies=[guard(Permission.PARAMETER_READ)],
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
    dependencies=[guard(Permission.PARAMETER_WRITE)],
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
@router.put(
    "/parameters/{parameter_id}",
    response_model=ParameterResponse,
    dependencies=[guard(Permission.PARAMETER_WRITE)],
)
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
    user: UserProfile = Depends(_reading_writer),
    db: Session = Depends(get_db),
) -> ReadingResponse:
    """Store a reading and evaluate threshold alerts."""
    row = service.create_reading(db, payload, _actor_name(user))
    return ReadingResponse.model_validate(row)


# PUBLIC_INTERFACE
@router.get(
    "/equipment/{equipment_id}/parameters/{parameter_id}/readings",
    response_model=list[ReadingResponse],
    dependencies=[guard(Permission.READING_READ)],
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
    user: UserProfile = Depends(_reading_writer),
    db: Session = Depends(get_db),
) -> ReadingResponse:
    """Edit a recent reading."""
    row = service.update_reading(db, reading_id, payload, _actor_name(user))
    return ReadingResponse.model_validate(row)


# PUBLIC_INTERFACE
@router.delete(
    "/readings/{reading_id}",
    response_model=None,
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[guard(Permission.READING_WRITE)],
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
@router.get(
    "/alerts",
    response_model=list[AlertResponse],
    dependencies=[guard(Permission.ALERT_READ)],
)
def list_alerts(db: Session = Depends(get_db)) -> list[AlertResponse]:
    """List alerts newest first."""
    rows = list(
        db.execute(
            select(Alert, Equipment.name, Parameter.name)
            .outerjoin(Equipment, Alert.equipment_id == Equipment.id)
            .outerjoin(Parameter, Alert.parameter_id == Parameter.id)
            .order_by(Alert.created_at.desc())
        ).all()
    )
    responses = []
    for alert, equipment_name, parameter_name in rows:
        response = AlertResponse.model_validate(alert)
        response.equipment_name = equipment_name
        response.parameter_name = parameter_name
        responses.append(response)
    return responses


# PUBLIC_INTERFACE
@router.delete(
    "/alerts/{alert_id}",
    response_model=None,
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[guard(Permission.ALERT_DELETE)],
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
@router.get(
    "/alerts/{alert_id}",
    response_model=AlertResponse,
    dependencies=[guard(Permission.ALERT_READ)],
)
def get_alert(alert_id: str, db: Session = Depends(get_db)) -> AlertResponse:
    """Fetch an alert by id."""
    row = db.execute(
        select(Alert, Equipment.name, Parameter.name)
        .outerjoin(Equipment, Alert.equipment_id == Equipment.id)
        .outerjoin(Parameter, Alert.parameter_id == Parameter.id)
        .where(Alert.id == alert_id)
    ).first()
    if row is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.ALERT_NOT_FOUND,
            detail=f"Alert '{alert_id}' does not exist.",
        )
    alert, equipment_name, parameter_name = row
    response = AlertResponse.model_validate(alert)
    response.equipment_name = equipment_name
    response.parameter_name = parameter_name
    return response
