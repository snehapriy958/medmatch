"""
Evaluation and Performance API Endpoints for MedMatch V2 Phase 15.

Provides read-only access to verified research evaluation artifacts,
safety benchmarks, and Phase 14 performance measurements.
Protected by role-based access control: SYSTEM_ADMIN, HOSPITAL_ADMIN, RESEARCH_COORDINATOR.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from app.api.deps import require_admin_or_researcher
from app.config.rate_limit import limiter
from app.config.settings import settings
from app.schemas.evaluation import (
    EvaluationAblationsResponse,
    EvaluationOverviewResponse,
    EvaluationPerformanceResponse,
    EvaluationSafetyResponse,
)
from app.services.evaluation_service import EvaluationService, get_evaluation_service

router = APIRouter(
    prefix=f"{settings.API_PREFIX}/evaluation",
    tags=["Evaluation"],
)


@router.get(
    "/overview",
    response_model=EvaluationOverviewResponse,
    summary="Evaluation Overview & Evidence Matrix",
    description=(
        "Retrieve the executive evaluation coverage matrix, key performance highlights, "
        "and strict evidence classification mappings across Phases 5 through 14."
    ),
)
@limiter.limit("60/minute")
def get_evaluation_overview(
    request: Request,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_researcher()),
    ],
    service: Annotated[
        EvaluationService,
        Depends(get_evaluation_service),
    ],
) -> EvaluationOverviewResponse:
    """
    Return executive evaluation overview and evidence matrix.
    """
    return service.get_overview()


@router.get(
    "/performance",
    response_model=EvaluationPerformanceResponse,
    summary="Phase 14 Performance Benchmark & Optimization Results",
    description=(
        "Retrieve empirical performance baseline measurements (Phase 14.1 frozen reference), "
        "same-run controlled N+1 criteria loading optimization results (Phase 14.2), "
        "direct PostgreSQL measurements, and vector retrieval scaling data."
    ),
)
@limiter.limit("60/minute")
def get_evaluation_performance(
    request: Request,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_researcher()),
    ],
    service: Annotated[
        EvaluationService,
        Depends(get_evaluation_service),
    ],
) -> EvaluationPerformanceResponse:
    """
    Return performance benchmarks and N+1 query optimization results.
    """
    return service.get_performance()


@router.get(
    "/safety",
    response_model=EvaluationSafetyResponse,
    summary="Phase 12 Safety Pipeline & Error Injection Benchmark",
    description=(
        "Retrieve Phase 12 adversarial error injection results (14 scenarios), "
        "clinical safety gate evaluations (A-S1 to A-S7), and Phase 9 human review "
        "routing and uncertainty triage data."
    ),
)
@limiter.limit("60/minute")
def get_evaluation_safety(
    request: Request,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_researcher()),
    ],
    service: Annotated[
        EvaluationService,
        Depends(get_evaluation_service),
    ],
) -> EvaluationSafetyResponse:
    """
    Return clinical safety pipeline, error injection, and human review routing data.
    """
    return service.get_safety()


@router.get(
    "/ablations",
    response_model=EvaluationAblationsResponse,
    summary="Phase 11 Experiments E0-E4 & Component Ablations A1-A5",
    description=(
        "Retrieve Phase 11 experimental comparisons (E0 baseline through E4 reranked RAG) "
        "and component ablations (A1 retrieval, A2 reranking, A3 patient profile, "
        "A4 RAG augmentation, A5 evidence grounding) on development test fixtures."
    ),
)
@limiter.limit("60/minute")
def get_evaluation_ablations(
    request: Request,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_researcher()),
    ],
    service: Annotated[
        EvaluationService,
        Depends(get_evaluation_service),
    ],
) -> EvaluationAblationsResponse:
    """
    Return Phase 11 experiments E0-E4 and component ablations A1-A5.
    """
    return service.get_ablations()
