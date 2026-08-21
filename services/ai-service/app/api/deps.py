from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session
from uuid import UUID
from app.config.roles import (
    HOSPITAL_ADMIN,
    PATIENT,
    PHYSICIAN,
    RESEARCH_COORDINATOR,
    SYSTEM_ADMIN,
    TRIAL_SPONSOR,
)
from app.config.security import verify_token
from app.config.types import JWTClaims
from app.db.session import get_db

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.criteria_embedding_repository import (
    CriteriaEmbeddingRepository,
)
from app.repositories.matching_repository import MatchingRepository
from app.repositories.patient_note_embedding_repository import (
    PatientNoteEmbeddingRepository,
)
from app.repositories.patient_note_repository import (
    PatientNoteRepository,
)
from app.repositories.patient_repository import PatientRepository
from app.repositories.trial_criteria_repository import (
    TrialCriteriaRepository,
)
from app.repositories.trial_repository import TrialRepository
from app.repositories.hospital_repository import HospitalRepository
from app.services.audit_service import AuditService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.matching_service import MatchingService
from app.services.patient_note_service import PatientNoteService
from app.services.patient_service import PatientService
from app.services.pdf_service import PDFService
from app.services.text_cleaner import TextCleaner
from app.services.trial_service import TrialService


security = HTTPBearer(auto_error=True)


# --------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(security),
    ],
) -> JWTClaims:
    """
    Authenticate JWT and return decoded claims.
    """

    token = credentials.credentials

    try:
        return verify_token(token)

    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def get_current_hospital_id(
    current_user: Annotated[
        JWTClaims,
        Depends(get_current_user),
    ],
) -> UUID:
    """
    Extract hospital ID from JWT.
    """

    hospital_id = current_user.get(
        "hospital_id"
    )

    if hospital_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hospital ID missing from token",
        )

    try:
        return UUID(str(hospital_id))

    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid hospital ID in token",
        ) from exc


# --------------------------------------------------------------------
# Role-based Authorization
# --------------------------------------------------------------------


def require_roles(
    *allowed_roles: str,
) -> Callable[..., JWTClaims]:
    """
    Allow only specified roles.
    """

    def dependency(
        current_user: Annotated[
            JWTClaims,
            Depends(get_current_user),
        ],
    ) -> JWTClaims:

        role = current_user.get("role")

        if role:
            role = (
                role.upper()
                .replace(
                    "ROLE_",
                    "",
                )
            )

        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return dependency


def require_admin() -> Callable[..., JWTClaims]:
    return require_roles(
        SYSTEM_ADMIN,
        HOSPITAL_ADMIN,
    )


def require_doctor() -> Callable[..., JWTClaims]:
    return require_roles(PHYSICIAN)


def require_researcher() -> Callable[..., JWTClaims]:
    return require_roles(RESEARCH_COORDINATOR)


def require_admin_or_doctor() -> Callable[..., JWTClaims]:
    return require_roles(
        SYSTEM_ADMIN,
        HOSPITAL_ADMIN,
        PHYSICIAN,
        RESEARCH_COORDINATOR,
    )


def require_admin_or_researcher() -> Callable[..., JWTClaims]:
    return require_roles(
        SYSTEM_ADMIN,
        HOSPITAL_ADMIN,
        PHYSICIAN,
        RESEARCH_COORDINATOR,
    )


def require_doctor_or_researcher() -> Callable[..., JWTClaims]:
    return require_roles(
        SYSTEM_ADMIN,
        HOSPITAL_ADMIN,
        PHYSICIAN,
        RESEARCH_COORDINATOR,
    )

# --------------------------------------------------------------------
# Repository Dependencies
# --------------------------------------------------------------------


def get_trial_repository(
    db: Annotated[Session, Depends(get_db)],
) -> TrialRepository:
    return TrialRepository(db)


def get_trial_criteria_repository(
    db: Annotated[Session, Depends(get_db)],
) -> TrialCriteriaRepository:
    return TrialCriteriaRepository(db)


def get_criteria_embedding_repository(
    db: Annotated[Session, Depends(get_db)],
) -> CriteriaEmbeddingRepository:
    return CriteriaEmbeddingRepository(db)


def get_matching_repository(
    db: Annotated[Session, Depends(get_db)],
) -> MatchingRepository:
    return MatchingRepository(db)


def get_patient_repository(
    db: Annotated[Session, Depends(get_db)],
) -> PatientRepository:
    return PatientRepository(db)


def get_patient_note_repository(
    db: Annotated[Session, Depends(get_db)],
) -> PatientNoteRepository:
    return PatientNoteRepository(db)


def get_patient_note_embedding_repository(
    db: Annotated[Session, Depends(get_db)],
) -> PatientNoteEmbeddingRepository:
    return PatientNoteEmbeddingRepository(db)


def get_audit_log_repository(
    db: Annotated[Session, Depends(get_db)],
) -> AuditLogRepository:
    return AuditLogRepository(db)


# --------------------------------------------------------------------
# Infrastructure Services
# --------------------------------------------------------------------


def get_pdf_service() -> PDFService:
    return PDFService()


def get_text_cleaner() -> TextCleaner:
    return TextCleaner()


def get_llm_service() -> LLMService:
    return LLMService()


def get_embedding_service(
    criteria_repository: Annotated[
        CriteriaEmbeddingRepository,
        Depends(get_criteria_embedding_repository),
    ],
    patient_note_repository: Annotated[
        PatientNoteEmbeddingRepository,
        Depends(get_patient_note_embedding_repository),
    ],
) -> EmbeddingService:

    return EmbeddingService(
        criteria_repository=criteria_repository,
        patient_note_repository=patient_note_repository,
    )


def get_audit_service(
    repository: Annotated[
        AuditLogRepository,
        Depends(get_audit_log_repository),
    ],
) -> AuditService:

    return AuditService(repository)

def get_hospital_repository(
    db: Annotated[Session, Depends(get_db)],
) -> HospitalRepository:
    return HospitalRepository(db)

def get_matching_service(
    repository: Annotated[
        MatchingRepository,
        Depends(get_matching_repository),
    ],
    hospital_repository: Annotated[
        HospitalRepository,
        Depends(get_hospital_repository),
    ],
    embedding_service: Annotated[
        EmbeddingService,
        Depends(get_embedding_service),
    ],
    llm_service: Annotated[
        LLMService,
        Depends(get_llm_service),
    ],
    audit_service: Annotated[
        AuditService,
        Depends(get_audit_service),
    ],
) -> MatchingService:

    return MatchingService(
        repository=repository,
        hospital_repository=hospital_repository,
        embedding_service=embedding_service,
        llm_service=llm_service,
        audit_service=audit_service,
    )


# --------------------------------------------------------------------
# Business Services
# --------------------------------------------------------------------


def get_trial_service(
    repository: Annotated[
        TrialRepository,
        Depends(get_trial_repository),
    ],
    criteria_repository: Annotated[
        TrialCriteriaRepository,
        Depends(get_trial_criteria_repository),
    ],
    pdf_service: Annotated[
        PDFService,
        Depends(get_pdf_service),
    ],
    text_cleaner: Annotated[
        TextCleaner,
        Depends(get_text_cleaner),
    ],
    llm_service: Annotated[
        LLMService,
        Depends(get_llm_service),
    ],
    embedding_service: Annotated[
        EmbeddingService,
        Depends(get_embedding_service),
    ],
    audit_service: Annotated[
        AuditService,
        Depends(get_audit_service),
    ],
) -> TrialService:

    return TrialService(
        repository=repository,
        criteria_repository=criteria_repository,
        pdf_service=pdf_service,
        text_cleaner=text_cleaner,
        llm_service=llm_service,
        embedding_service=embedding_service,
        audit_service=audit_service,
    )


def get_patient_service(
    repository: Annotated[
        PatientRepository,
        Depends(get_patient_repository),
    ],
    hospital_repository: Annotated[
        HospitalRepository,
        Depends(get_hospital_repository),
    ],
    audit_service: Annotated[
        AuditService,
        Depends(get_audit_service),
    ],
) -> PatientService:

    return PatientService(
        repository=repository,
        hospital_repository=hospital_repository,
        audit_service=audit_service,
    )


def get_patient_note_service(
    patient_repository: Annotated[
        PatientRepository,
        Depends(get_patient_repository),
    ],
    note_repository: Annotated[
        PatientNoteRepository,
        Depends(get_patient_note_repository),
    ],
    hospital_repository: Annotated[
        HospitalRepository,
        Depends(get_hospital_repository),
    ],
    embedding_service: Annotated[
        EmbeddingService,
        Depends(get_embedding_service),
    ],
    audit_service: Annotated[
        AuditService,
        Depends(get_audit_service),
    ],
) -> PatientNoteService:

    return PatientNoteService(
        patient_repository=patient_repository,
        note_repository=note_repository,
        hospital_repository=hospital_repository,
        embedding_service=embedding_service,
        audit_service=audit_service,
    )