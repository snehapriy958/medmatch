from prometheus_client import Counter, Histogram

# ==========================================================
# Matching Metrics
# ==========================================================

MATCH_REQUESTS = Counter(
    "medmatch_ai_match_requests_total",
    "Total eligibility matching requests"
)

MATCH_SUCCESS = Counter(
    "medmatch_ai_match_success_total",
    "Successful eligibility matches"
)

MATCH_FAILURE = Counter(
    "medmatch_ai_match_failure_total",
    "Failed eligibility matches"
)

MATCH_DURATION = Histogram(
    "medmatch_ai_match_duration_seconds",
    "Eligibility matching duration"
)

# ==========================================================
# Upload Metrics
# ==========================================================

UPLOAD_REQUESTS = Counter(
    "medmatch_ai_upload_requests_total",
    "Total upload requests"
)

UPLOAD_SUCCESS = Counter(
    "medmatch_ai_upload_success_total",
    "Successful uploads"
)

UPLOAD_FAILURE = Counter(
    "medmatch_ai_upload_failure_total",
    "Failed uploads"
)

# ==========================================================
# AI Metrics
# ==========================================================

EMBEDDING_REQUESTS = Counter(
    "medmatch_ai_embedding_requests_total",
    "Embedding generation requests"
)

LLM_REQUESTS = Counter(
    "medmatch_ai_llm_requests_total",
    "LLM requests"
)