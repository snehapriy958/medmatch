# MedMatch Security Baseline

**Document ID:** SEC-BASE-001  
**Phase:** Phase 0 Baseline  
**Scope:** Authentication Security, Cryptography, Data Privacy, Input Validation, and Threat Audit

---

## 1. Security Architecture Summary

The MedMatch platform demonstrates strong defensive security foundations across token cryptography, multi-tenant isolation, file upload boundaries, and PHI (Protected Health Information) audit log protection.

```text
Authentication: IMPLEMENTED (RS256 Asymmetric JWT)
Role-Based Access Control: IMPLEMENTED (Spring Security + FastAPI Guards)
Multi-Tenancy Isolation: IMPLEMENTED (Application-level query scoping)
File Upload Validation: IMPLEMENTED (Magic byte + Size + Extension checks)
Injection Protection: IMPLEMENTED (Parameterized SQL queries throughout)
PHI Minimization in Logs: IMPLEMENTED (Patient notes withheld from audit text)
PostgreSQL Row-Level Security: MISSING
CSRF Protection: DISABLED (Stateless JWT architecture)
```

---

## 2. Threat & Vulnerability Audit Findings

### 2.1. Hardcoded Secrets & Key Management
- **Audit Findings:**
  - **No hardcoded secrets in source code.** API keys and database credentials are read exclusively through environment variables (`GOOGLE_API_KEY`, `DATABASE_PASSWORD`, `DATABASE_URL`).
  - **RSA Keys:** The asymmetric key pair (`private.pem`, `public.pem`) in `services/auth-service/src/main/resources/keys/` and `services/ai-service/keys/` is properly excluded in `.gitignore` and **not committed** to git history (verified via `git ls-files "*key*" "*pem*"`).
  - **Environment Files:** Root `.env` and `services/ai-service/.env` contain local development credentials and are excluded in `.gitignore`.
  - **Recommendation:** Rotate any development API keys prior to production deployment; enforce Kubernetes Secret injection via Vault or cloud secret managers.

### 2.2. File Upload Security
- **Location:** `app/services/pdf_service.py:save_pdf` and `_validate_pdf`.
- **Protections Implemented:**
  1. **Extension Whitelisting:** Rejects any filename not ending in `.pdf`.
  2. **Magic Byte Signature Verification:** Inspects the first chunk of uploaded bytes to verify the standard `%PDF-` file header signature (`b"%PDF-"`), rejecting renamed executables or malicious payloads.
  3. **File Size Capping:** Strictly enforces maximum upload size (`settings.MAX_UPLOAD_SIZE_MB`, default 20MB) during streaming chunks, rejecting oversized payloads with HTTP 413.
  4. **Randomized UUID Filenames:** Uploaded files are written as `{uuid4()}.pdf`, preventing path traversal attacks (e.g., `../../etc/passwd`) and directory collision.
  5. **Parser Validation & Cleanup:** Validates document structure using `pymupdf.open()` and immediately deletes invalid or failed uploads from disk.

### 2.3. SQL Injection Analysis
- **Location:** `app/repositories/matching_repository.py` and `app/repositories/match_repository.py`.
- **Audit Findings:**
  - Raw SQL queries utilize SQLAlchemy's `text()` construct with **strictly parameterized bind variables**:
    ```python
    query = text("... WHERE t.hospital_id = :hospital_id ... te.embedding <=> CAST(:embedding AS vector) ...")
    self.db.execute(query, {"embedding": embedding, "hospital_id": hospital_id, "trial_limit": limit})
    ```
  - No string interpolation (`f"SELECT ... {user_input}"`) or unescaped concatenation was discovered in either Python or Java repositories.
  - Query parameters are sanitized by the database driver (`psycopg2-binary` and PostgreSQL JDBC).

### 2.4. Cross-Origin Resource Sharing (CORS) & Host Filtering
- **AI Service (`app/main.py`):**
  - Uses `TrustedHostMiddleware` to restrict allowed hosts to `settings.TRUSTED_HOSTS` (`localhost`, `127.0.0.1`, `testserver`, `ai-service`). Production validator rejects `*` wildcards.
  - Uses `CORSMiddleware` with explicit origin whitelisting:
    ```python
    allow_origins=["http://localhost", "http://localhost:80", "http://localhost:5173", "http://localhost:5174"]
    ```
- **Auth Service (`SecurityConfig.java`):**
  - Defines `.cors(cors -> {})` and disables CSRF (`.csrf(csrf -> csrf.disable())`) which is standard for stateless Bearer token APIs.
- **Reverse Proxy (`nginx.conf`):**
  - Normalizes external requests to internal port `5173`, mitigating cross-origin browser issues in Docker environments.

### 2.5. PHI Minimization & Sensitive Data in Logs
- **Location:** `app/services/matching_service.py:_log_matching_audit`
- **Audit Findings:**
  - The patient clinical note is **explicitly withheld** from the audit log details to prevent storing sensitive narrative clinical data in plain text:
    ```python
    # The patient note itself is intentionally not written to the
    # audit details to avoid storing unnecessary clinical content.
    details=(
        f"Eligibility={result.eligibility}; "
        f"Confidence={result.confidence}; "
        f"MatchedInclusion={len(result.matched_inclusion)}; "
        ...
    )
    ```
  - Prompt construction logs trial counts and criteria counts, but suppresses the full prompt text to avoid logging PHI.

### 2.6. Input Validation & Error Handling
- **API Payloads:**
  - FastAPI routes enforce strict Pydantic schemas with constraints:
    - `patient_note`: `min_length=20`, `max_length=10000`.
    - `limit`: `ge=1`, `le=100`.
    - `extra="forbid"` on `MatchingRequest` prevents unexpected payload tampering.
  - Spring Boot controllers use Jakarta Bean Validation (`@Valid`, `@NotNull`, `@Email`, `@Size`).
  - Frontend forms use Zod schemas matching backend constraints.
- **Error Handlers:**
  - `app/exceptions/handlers.py` maps internal exceptions to structured HTTP error responses, preventing raw database tracebacks or internal paths from leaking to clients in production.

---

## 3. Security Prioritization & Identified Vulnerabilities

| Vulnerability / Risk | Severity | Affected Area | Impact | Remediation Plan |
| :--- | :--- | :--- | :--- | :--- |
| **No Database RLS** | **Medium** | PostgreSQL schema | If application code omits `hospital_id`, cross-tenant data could leak. | Enable PostgreSQL Row Level Security (RLS) with session-scoped tenant variables. |
| **Unmounted Tasks Route** | **Low** | `app/api/routes/tasks.py` | Unmounted route contains dead code with no authentication decorator. | Remove or mount route with proper JWT authentication guards. |
| **Role Name Discrepancy** | **Low** | Java enums vs DB seed | Seeded roles (`ADMIN`, `DOCTOR`) diverge from enum names (`SYSTEM_ADMIN`, `PHYSICIAN`). | Consolidate migration scripts to standard role names across both microservices. |
| **Plaintext Key Files on Disk** | **Low** | Local filesystem (`keys/`) | Key files rely solely on file permissions. | Inject keys exclusively via environment variables or secret volumes in deployment. |
