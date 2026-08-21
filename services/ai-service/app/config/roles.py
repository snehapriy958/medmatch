"""
Application role constants.

These roles must remain consistent with the Spring Boot Auth Service
and the frontend authorization model.
"""

SYSTEM_ADMIN = "SYSTEM_ADMIN"
HOSPITAL_ADMIN = "HOSPITAL_ADMIN"
RESEARCH_COORDINATOR = "RESEARCH_COORDINATOR"
PHYSICIAN = "PHYSICIAN"
TRIAL_SPONSOR = "TRIAL_SPONSOR"
PATIENT = "PATIENT"


ALL_ROLES = {
    SYSTEM_ADMIN,
    HOSPITAL_ADMIN,
    RESEARCH_COORDINATOR,
    PHYSICIAN,
    TRIAL_SPONSOR,
    PATIENT,
}