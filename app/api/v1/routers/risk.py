"""Equipment risk scores and model registry routes (WP4)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.errors import ErrorCode, ProblemException, problem_responses
from app.core.rbac import Permission, Role, guard, require_permission
from app.db.session import get_db
from app.models.ml import ModelVersion, RiskScore
from app.models.user_profile import UserProfile
from app.schemas.ml import (
    EquipmentRiskResponse,
    ModelVersionResponse,
    RiskScoreResponse,
    StageChange,
)
from app.services import domain as domain_service
from app.services import model_ops, model_registry

router = APIRouter(tags=["risk"])
_risk_reader = require_permission(Permission.RISK_READ)
_model_admin = require_permission(Permission.MODEL_ADMIN)


# PUBLIC_INTERFACE
@router.get(
    "/equipment/{equipment_id}/risk",
    response_model=EquipmentRiskResponse,
    summary="Failure-risk scores for one equipment",
    description=(
        "Latest score and recent history. Scores from shadow-stage models are "
        "returned to Admins only (ADR-0006)."
    ),
    responses=problem_responses(401, 403, 404),
)
def get_equipment_risk(
    equipment_id: str = Path(..., description="Business equipment id."),
    limit: int = Query(50, ge=1, le=500),
    user: UserProfile = Depends(_risk_reader),
    db: Session = Depends(get_db),
) -> EquipmentRiskResponse:
    equipment = domain_service.get_equipment(db, equipment_id)
    stages = ["active"]
    if user.role == Role.ADMIN.value:
        stages.append("shadow")
    rows = db.execute(
        select(RiskScore, ModelVersion.version)
        .join(ModelVersion, ModelVersion.id == RiskScore.model_version_id)
        .where(
            RiskScore.equipment_id == equipment.id,
            RiskScore.stage.in_(stages),
        )
        .order_by(RiskScore.scored_at.desc())
        .limit(limit)
    ).all()
    history = []
    for score, version in rows:
        item = RiskScoreResponse.model_validate(score)
        item.model_version = version
        history.append(item)
    if not equipment.asset_class:
        status = "not_configured"
    else:
        status = "scored" if history else "no_scores"
    return EquipmentRiskResponse(
        equipment_id=equipment.equipment_id,
        asset_class=equipment.asset_class,
        status=status,
        latest=history[0] if history else None,
        history=history,
    )


# PUBLIC_INTERFACE
@router.get(
    "/models",
    response_model=list[ModelVersionResponse],
    summary="List registered model versions",
    dependencies=[guard(Permission.MODEL_ADMIN)],
    responses=problem_responses(401, 403),
)
def list_models(db: Session = Depends(get_db)) -> list[ModelVersionResponse]:
    rows = db.execute(
        select(ModelVersion).order_by(ModelVersion.created_at.desc())
    ).scalars()
    return [ModelVersionResponse.model_validate(r) for r in rows]


def _get_version(db: Session, model_id: str) -> ModelVersion:
    version = db.get(ModelVersion, model_id)
    if version is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.INVALID_REQUEST,
            detail=f"Model version '{model_id}' does not exist.",
        )
    return version


# PUBLIC_INTERFACE
@router.get(
    "/models/{model_id}/evaluation",
    summary="Shadow evaluation against confirmed failures (WP5)",
    description=(
        "Warning precision, failure recall and lead time for this version, "
        "compared with threshold alerts on the same equipment. Ground truth "
        "is work orders closed with failure_confirmed."
    ),
    dependencies=[guard(Permission.MODEL_ADMIN)],
    responses=problem_responses(401, 403, 404),
)
def evaluate_model(
    model_id: str = Path(...),
    days: int = Query(90, ge=1, le=730),
    horizon_days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
) -> dict:
    version = _get_version(db, model_id)
    return model_ops.evaluate_version(
        db, version, days=days, horizon_days=horizon_days
    )


# PUBLIC_INTERFACE
@router.get(
    "/models/{model_id}/drift",
    summary="Input and score drift against the training reference (WP5)",
    description=(
        "Population Stability Index per feature and for the score. "
        "Below 0.1 is stable, 0.1 to 0.25 moderate, and 0.25 or more "
        "significant."
    ),
    dependencies=[guard(Permission.MODEL_ADMIN)],
    responses=problem_responses(401, 403, 404),
)
def model_drift(
    model_id: str = Path(...),
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
) -> dict:
    return model_ops.drift_version(db, _get_version(db, model_id), days=days)


# PUBLIC_INTERFACE
@router.post(
    "/models/{model_id}/stage",
    response_model=ModelVersionResponse,
    summary="Change a model version's stage (shadow / active / retired)",
    description=(
        "Activating a version retires the currently active version for the "
        "same kind and asset class. The change and who made it are recorded."
    ),
    responses=problem_responses(401, 403, 404, 409),
)
def change_stage(
    payload: StageChange,
    model_id: str = Path(...),
    user: UserProfile = Depends(_model_admin),
    db: Session = Depends(get_db),
) -> ModelVersionResponse:
    version = db.get(ModelVersion, model_id)
    if version is None:
        raise ProblemException(
            status=404,
            code=ErrorCode.INVALID_REQUEST,
            detail=f"Model version '{model_id}' does not exist.",
        )
    if version.stage == "retired" and payload.stage != "retired":
        raise ProblemException(
            status=409,
            code=ErrorCode.INVALID_STATE,
            detail="Retired versions cannot be reinstated; register a new one.",
        )
    now = datetime.now(timezone.utc)
    actor = user.display_name or user.email or user.supabase_user_id
    if payload.stage == "active":
        # Verify the artifact loads before anyone is alerted from it.
        try:
            model_registry.load(version)
        except Exception as exc:  # noqa: BLE001
            raise ProblemException(
                status=409,
                code=ErrorCode.INVALID_STATE,
                detail=f"Artifact failed verification: {exc}",
            ) from exc
        db.execute(
            update(ModelVersion)
            .where(
                ModelVersion.kind == version.kind,
                ModelVersion.asset_class == version.asset_class,
                ModelVersion.stage == "active",
                ModelVersion.id != version.id,
            )
            .values(
                stage="retired", stage_changed_at=now, stage_changed_by=actor
            )
        )
    version.stage = payload.stage
    version.stage_changed_at = now
    version.stage_changed_by = actor
    db.commit()
    db.refresh(version)
    return ModelVersionResponse.model_validate(version)
