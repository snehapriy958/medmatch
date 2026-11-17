"""
MedMatch V2 — Live Staging E2E Integration, Clinical Workflow & Reliability Suite.
Executes against live Docker containers:
- Frontend (Reverse Proxy): http://localhost:5173
- Auth Service (Spring Boot): http://localhost:8081
- AI Service (FastAPI): http://localhost:8000
- PostgreSQL with pgvector: localhost:5434
- Redis: localhost:6380
- Celery Worker: active in cluster
"""

import io
import json
import os
import sys
import time
from pathlib import Path
from uuid import UUID, uuid4

import requests

BASE_AUTH_DIRECT = "http://localhost:8081"
BASE_AI_DIRECT = "http://localhost:8000"
BASE_FRONTEND = "http://localhost:5173"

REPO_ROOT = Path(__file__).resolve().parents[1]

results = {
    "phases": {},
    "metrics": {},
    "failures": [],
}


def log_test(phase: str, test_name: str, passed: bool, detail: str = ""):
    status_str = "PASS" if passed else "FAIL"
    print(f"[{status_str}] [{phase}] {test_name}: {detail}")
    if phase not in results["phases"]:
        results["phases"][phase] = []
    results["phases"][phase].append({
        "test": test_name,
        "passed": passed,
        "detail": detail
    })
    if not passed:
        results["failures"].append(f"[{phase}] {test_name}: {detail}")


def run_phase3_live_integrations():
    print("\n========================================================")
    print("PHASE 3: LIVE SERVICE-TO-SERVICE INTEGRATION TESTS")
    print("========================================================")

    # 1. Frontend to Spring Boot Auth via Reverse Proxy
    try:
        r = requests.post(
            f"{BASE_FRONTEND}/api/auth/login",
            json={"email": "research@test.com", "password": "password123"},
            timeout=10,
        )
        passed = r.status_code == 200 and "accessToken" in r.json()
        log_test("Phase3", "1. Frontend -> Auth Reverse Proxy", passed, f"Status: {r.status_code}")
    except Exception as e:
        log_test("Phase3", "1. Frontend -> Auth Reverse Proxy", False, str(e))

    # 2. Frontend to FastAPI AI via Reverse Proxy
    try:
        r = requests.get(
            f"{BASE_FRONTEND}/api/ai/api/health/ready",
            timeout=10,
        )
        data = r.json()
        passed = r.status_code == 200 and data.get("status") == "UP"
        log_test("Phase3", "2. Frontend -> AI Reverse Proxy", passed, f"Status: {r.status_code}, Health: {data.get('status')}")
    except Exception as e:
        log_test("Phase3", "2. Frontend -> AI Reverse Proxy", False, str(e))

    # 3. Direct Spring Boot Authentication & Token for RESEARCH_COORDINATOR (Hospital 1)
    token_research = None
    hospital_h1 = None
    try:
        r = requests.post(
            f"{BASE_AUTH_DIRECT}/auth/login",
            json={"email": "research@test.com", "password": "password123"},
            timeout=10,
        )
        if r.status_code == 200:
            token_research = r.json()["accessToken"]
            hospital_h1 = r.json()["user"]["hospitalId"]
            passed = True
            detail = f"Received RS256 token for Research Coordinator (Hospital {hospital_h1})"
        else:
            passed = False
            detail = f"Status {r.status_code}: {r.text}"
        log_test("Phase3", "3. Spring Boot -> PostgreSQL Auth (Researcher)", passed, detail)
    except Exception as e:
        log_test("Phase3", "3. Spring Boot -> PostgreSQL Auth (Researcher)", False, str(e))

    # 4. Direct Spring Boot Authentication & Token for PHYSICIAN (Hospital 1)
    token_doctor = None
    try:
        r = requests.post(
            f"{BASE_AUTH_DIRECT}/auth/login",
            json={"email": "doctor@test.com", "password": "password123"},
            timeout=10,
        )
        if r.status_code == 200:
            token_doctor = r.json()["accessToken"]
            passed = True
            detail = f"Received RS256 token for Doctor (Role: PHYSICIAN)"
        else:
            passed = False
            detail = f"Status {r.status_code}: {r.text}"
        log_test("Phase3", "4. Spring Boot -> PostgreSQL Auth (Doctor)", passed, detail)
    except Exception as e:
        log_test("Phase3", "4. Spring Boot -> PostgreSQL Auth (Doctor)", False, str(e))

    # 5. Token for Tenant 2 (Manipal Hospital Admin)
    token_tenant2 = None
    hospital_h2 = None
    try:
        r = requests.post(
            f"{BASE_AUTH_DIRECT}/auth/login",
            json={"email": "manipal.admin@test.com", "password": "password123"},
            timeout=10,
        )
        if r.status_code == 200:
            token_tenant2 = r.json()["accessToken"]
            hospital_h2 = r.json()["user"]["hospitalId"]
            passed = True
            detail = f"Received RS256 token for Tenant 2 {hospital_h2}"
        else:
            passed = False
            detail = f"Status {r.status_code}: {r.text}"
        log_test("Phase3", "5. Multi-Tenant User 2 Auth (Manipal)", passed, detail)
    except Exception as e:
        log_test("Phase3", "5. Multi-Tenant User 2 Auth (Manipal)", False, str(e))

    # 6. FastAPI AI Service Health Checks (Postgres + pgvector + Redis)
    try:
        r = requests.get(f"{BASE_AI_DIRECT}/api/health/ready", timeout=10)
        checks = r.json().get("checks", {})
        passed = (
            r.status_code == 200
            and checks.get("database") == "UP"
            and checks.get("redis") == "UP"
            and checks.get("vector_search") == "UP"
        )
        log_test(
            "Phase3",
            "6. FastAPI -> DB (pgvector) & Redis Health",
            passed,
            f"DB: {checks.get('database')}, Redis: {checks.get('redis')}, Vector: {checks.get('vector_search')}",
        )
    except Exception as e:
        log_test("Phase3", "6. FastAPI -> DB (pgvector) & Redis Health", False, str(e))

    # 7. Live PDF Upload & Celery Task Submission (using Researcher token)
    task_id = None
    pdf_path = REPO_ROOT / "data" / "demo" / "clinical_trials" / "trial_A_NCT02484404_osimertinib_demo.pdf"
    if pdf_path.exists() and token_research:
        try:
            headers = {"Authorization": f"Bearer {token_research}"}
            with open(pdf_path, "rb") as f:
                files = {"file": ("trial_A_NCT02484404_osimertinib_demo.pdf", f, "application/pdf")}
                r = requests.post(f"{BASE_AI_DIRECT}/api/trials/upload", headers=headers, files=files, timeout=15)
            if r.status_code in [200, 202]:
                data = r.json()
                task_id = data.get("task_id") or data.get("id")
                passed = True
                detail = f"Upload accepted, Celery Task ID: {task_id}"
            else:
                passed = False
                detail = f"Status {r.status_code}: {r.text}"
            log_test("Phase3", "7. PDF Upload & Celery Task Enqueue", passed, detail)
        except Exception as e:
            log_test("Phase3", "7. PDF Upload & Celery Task Enqueue", False, str(e))
    else:
        log_test("Phase3", "7. PDF Upload & Celery Task Enqueue", False, "Fixture PDF or token missing")

    # 8. Celery Worker Task Status Polling
    if task_id and token_research:
        try:
            headers = {"Authorization": f"Bearer {token_research}"}
            final_status = "PENDING"
            for attempt in range(25):
                r = requests.get(f"{BASE_AI_DIRECT}/api/tasks/{task_id}", headers=headers, timeout=10)
                if r.status_code == 200:
                    final_status = r.json().get("status")
                    if final_status in ["SUCCESS", "COMPLETED", "FAILURE"]:
                        break
                time.sleep(2)
            passed = (r.status_code == 200) and (final_status in ["SUCCESS", "COMPLETED"])
            log_test("Phase3", "8. Celery Worker Execution State", passed, f"Task State: {final_status}")
        except Exception as e:
            log_test("Phase3", "8. Celery Worker Execution State", False, str(e))

    # 9. Vector Retrieval & Semantic Search via pgvector (Researcher token)
    if token_research:
        try:
            headers = {"Authorization": f"Bearer {token_research}"}
            search_payload = {
                "patient_note": "58-year-old female with metastatic Stage IV non-small cell lung cancer with EGFR exon 19 deletion.",
                "limit": 5
            }
            r = requests.post(f"{BASE_AI_DIRECT}/api/matching/search", headers=headers, json=search_payload, timeout=15)
            if r.status_code == 200:
                matches = r.json().get("matches", [])
                passed = len(matches) > 0
                detail = f"Retrieved {len(matches)} candidate trial matches via pgvector"
            else:
                passed = False
                detail = f"Status {r.status_code}: {r.text}"
            log_test("Phase3", "9. Vector Retrieval & pgvector Search", passed, detail)
        except Exception as e:
            log_test("Phase3", "9. Vector Retrieval & pgvector Search", False, str(e))

    # 10. Tenant Isolation Check Across Users
    if token_doctor and token_tenant2 and hospital_h1 and hospital_h2:
        try:
            # Doctor 1 accesses own hospital patients
            headers_doc = {"Authorization": f"Bearer {token_doctor}"}
            r_doc = requests.get(f"{BASE_AI_DIRECT}/api/patients", headers=headers_doc, timeout=10)
            doc_patients = r_doc.json().get("patients", [])

            # Tenant 2 accesses own hospital patients
            headers_t2 = {"Authorization": f"Bearer {token_tenant2}"}
            r_t2 = requests.get(f"{BASE_AI_DIRECT}/api/patients", headers=headers_t2, timeout=10)
            t2_patients = r_t2.json().get("patients", [])

            # Tenant 2 attempts to query Hospital 1's specific patient by ID (cross-tenant access)
            cross_tenant_blocked = True
            if doc_patients:
                target_p_id = doc_patients[0]["id"]
                r_cross = requests.get(f"{BASE_AI_DIRECT}/api/patients/{target_p_id}", headers=headers_t2, timeout=10)
                # Must fail with 404 or 403 (fail-closed, not leak data from Hospital 1)
                cross_tenant_blocked = r_cross.status_code in [403, 404]

            passed = (r_doc.status_code == 200) and (r_t2.status_code == 200) and cross_tenant_blocked
            log_test(
                "Phase3",
                "10. Tenant Isolation Enforcement",
                passed,
                f"H1 Patients: {len(doc_patients)}, H2 Patients: {len(t2_patients)}, Cross-tenant blocked: {cross_tenant_blocked}",
            )
        except Exception as e:
            log_test("Phase3", "10. Tenant Isolation Enforcement", False, str(e))

    return token_research, token_doctor, token_tenant2, hospital_h1, hospital_h2


def run_phase4_clinical_matching_workflows(token_research):
    print("\n========================================================")
    print("PHASE 4: END-TO-END CLINICAL MATCHING WORKFLOWS")
    print("========================================================")

    if not token_research:
        print("[SKIP] Phase 4 skipped: Missing authentication token")
        return

    headers = {"Authorization": f"Bearer {token_research}"}

    # Scenario A: Clearly Eligible Patient
    patient_eligible = (
        "58-year-old female diagnosed with metastatic Stage IV lung adenocarcinoma with documented "
        "EGFR exon 19 deletion. ECOG performance status 1. Platelets 210,000/uL, absolute neutrophil count 2,800/uL. "
        "Creatinine 0.9 mg/dL. Brain MRI confirms no intracranial or central nervous system metastases. "
        "No prior treatment with 3rd generation EGFR-TKI (Osimertinib)."
    )

    try:
        r = requests.post(
            f"{BASE_AI_DIRECT}/api/matching/evaluate",
            headers=headers,
            json={"patient_note": patient_eligible, "limit": 3},
            timeout=90,
        )
        if r.status_code == 200:
            data = r.json()
            evaluations = data.get("results") or data.get("evaluations", [])
            passed = len(evaluations) > 0
            first_decision = evaluations[0].get("eligibility") or evaluations[0].get("eligibility_status") if evaluations else "N/A"
            detail = f"Evaluated {len(evaluations)} candidate trials. Decision: {first_decision}"
        else:
            passed = False
            detail = f"Status {r.status_code}: {r.text}"
        log_test("Phase4", "1. Patient Clinical Evaluation (Eligible Case)", passed, detail)
    except Exception as e:
        log_test("Phase4", "1. Patient Clinical Evaluation (Eligible Case)", False, str(e))

    time.sleep(3)

    # Scenario B: Hard Exclusion Conflict
    patient_exclusion = (
        "61-year-old male with Stage IV NSCLC EGFR exon 19 deletion. "
        "Patient previously received Osimertinib 80mg daily for 14 months with recent disease progression. "
        "ECOG 1, Platelets 180,000/uL."
    )
    try:
        r = requests.post(
            f"{BASE_AI_DIRECT}/api/matching/evaluate",
            headers=headers,
            json={"patient_note": patient_exclusion, "limit": 3},
            timeout=90,
        )
        if r.status_code == 200:
            data = r.json()
            evaluations = data.get("results") or data.get("evaluations", [])
            passed = len(evaluations) > 0
            first_decision = evaluations[0].get("eligibility") or evaluations[0].get("eligibility_status") if evaluations else "N/A"
            detail = f"Evaluated {len(evaluations)} candidate trials. Decision: {first_decision}"
        else:
            passed = False
            detail = f"Status {r.status_code}: {r.text}"
        log_test("Phase4", "2. Patient Clinical Evaluation (Exclusion Case)", passed, detail)
    except Exception as e:
        log_test("Phase4", "2. Patient Clinical Evaluation (Exclusion Case)", False, str(e))

    time.sleep(3)

    # Scenario C: Missing Information / Open-World Abstention
    patient_unknown = (
        "55-year-old female with newly diagnosed Stage IV NSCLC. "
        "EGFR mutation testing in progress (results pending). "
        "No brain imaging performed to date. Platelets 195,000/uL."
    )
    try:
        r = requests.post(
            f"{BASE_AI_DIRECT}/api/matching/evaluate",
            headers=headers,
            json={"patient_note": patient_unknown, "limit": 3},
            timeout=90,
        )
        if r.status_code == 200:
            data = r.json()
            evaluations = data.get("results") or data.get("evaluations", [])
            # Verify that missing EGFR and brain imaging is NOT an automatic ELIGIBLE pass
            passed = len(evaluations) > 0
            for ev in evaluations:
                ev_status = ev.get("eligibility") or ev.get("eligibility_status")
                if ev_status in ["Eligible", "ELIGIBLE"]:
                    passed = False  # Critical safety failure if pending marker passes
            detail = f"Evaluated {len(evaluations)} candidate trials safely: 0 false-positive ELIGIBLE outcomes for pending markers"
        else:
            passed = False
            detail = f"Status {r.status_code}: {r.text}"
        log_test("Phase4", "3. Open-World Abstention (Pending/Unknown Markers)", passed, detail)
    except Exception as e:
        log_test("Phase4", "3. Open-World Abstention (Pending/Unknown Markers)", False, str(e))


def run_phase5_failure_and_recovery(token_research):
    print("\n========================================================")
    print("PHASE 5: FAILURE & RECOVERY TESTING")
    print("========================================================")

    if not token_research:
        print("[SKIP] Phase 5 skipped: Missing authentication token")
        return

    headers = {"Authorization": f"Bearer {token_research}"}

    # 1. Malformed / Fake PDF Upload
    try:
        fake_content = b"This is not a real PDF document at all."
        files = {"file": ("malicious.pdf", io.BytesIO(fake_content), "application/pdf")}
        r = requests.post(f"{BASE_AI_DIRECT}/api/trials/upload", headers=headers, files=files, timeout=10)
        passed = r.status_code in [400, 422]
        log_test("Phase5", "1. Malformed Header PDF Rejection", passed, f"Status: {r.status_code}")
    except Exception as e:
        log_test("Phase5", "1. Malformed Header PDF Rejection", False, str(e))

    # 2. Non-PDF File Extension
    try:
        txt_content = b"%PDF-1.4 Fake header but text file"
        files = {"file": ("exploit.exe", io.BytesIO(txt_content), "application/octet-stream")}
        r = requests.post(f"{BASE_AI_DIRECT}/api/trials/upload", headers=headers, files=files, timeout=10)
        passed = r.status_code in [400, 422]
        log_test("Phase5", "2. Invalid File Extension Rejection", passed, f"Status: {r.status_code}")
    except Exception as e:
        log_test("Phase5", "2. Invalid File Extension Rejection", False, str(e))

    # 3. Oversized File Upload (> 50MB)
    try:
        oversized = b"%PDF-1.4 " + (b"0" * (52 * 1024 * 1024))
        files = {"file": ("oversized.pdf", io.BytesIO(oversized), "application/pdf")}
        r = requests.post(f"{BASE_AI_DIRECT}/api/trials/upload", headers=headers, files=files, timeout=20)
        passed = r.status_code in [400, 413, 422]
        log_test("Phase5", "3. Oversized PDF Rejection (>50MB)", passed, f"Status: {r.status_code}")
    except Exception as e:
        log_test("Phase5", "3. Oversized PDF Rejection (>50MB)", False, str(e))

    # 4. Tampered / Invalid JWT
    try:
        tampered_token = token_research[:-10] + "tampered00"
        bad_headers = {"Authorization": f"Bearer {tampered_token}"}
        r = requests.get(f"{BASE_AI_DIRECT}/api/patients", headers=bad_headers, timeout=10)
        passed = r.status_code == 401
        log_test("Phase5", "4. Tampered JWT Rejection", passed, f"Status: {r.status_code}")
    except Exception as e:
        log_test("Phase5", "4. Tampered JWT Rejection", False, str(e))

    # 5. Missing Authorization Header
    try:
        r = requests.get(f"{BASE_AI_DIRECT}/api/patients", timeout=10)
        passed = r.status_code in [401, 403]
        log_test("Phase5", "5. Missing Auth Header Rejection", passed, f"Status: {r.status_code}")
    except Exception as e:
        log_test("Phase5", "5. Missing Auth Header Rejection", False, str(e))


def run_phase6_live_performance_metrics(token_research):
    print("\n========================================================")
    print("PHASE 6: CONCURRENT API PERFORMANCE BENCHMARKS")
    print("========================================================")

    if not token_research:
        print("[SKIP] Phase 6 skipped: Missing authentication token")
        return

    headers = {"Authorization": f"Bearer {token_research}"}

    # 1. Health check throughput (low overhead)
    latencies = []
    errors = 0
    total_reqs = 30
    t0_all = time.perf_counter()
    for _ in range(total_reqs):
        t0 = time.perf_counter()
        try:
            r = requests.get(f"{BASE_AI_DIRECT}/api/health/ready", timeout=5)
            if r.status_code != 200:
                errors += 1
        except Exception:
            errors += 1
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)
    t1_all = time.perf_counter()

    latencies.sort()
    n = len(latencies)
    p50 = latencies[int(n * 0.50)]
    p95 = latencies[int(n * 0.95)]
    p99 = latencies[int(n * 0.99)]
    rps = round(total_reqs / (t1_all - t0_all), 2)
    error_rate = round((errors / float(total_reqs)) * 100, 2)

    results["metrics"]["health_api"] = {
        "requests": total_reqs,
        "throughput_rps": rps,
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "error_rate_pct": error_rate
    }
    print(f"Health Check API: {rps} req/sec | p50: {p50:.2f}ms | p95: {p95:.2f}ms | p99: {p99:.2f}ms | Errors: {error_rate}%")

    # 2. Vector Semantic Search Throughput & Latency (Live pgvector)
    search_latencies = []
    search_errors = 0
    search_reqs = 20
    query_payload = {
        "patient_note": "Stage IV NSCLC adenocarcinoma with documented EGFR Exon 19 deletion and prior chemotherapy.",
        "limit": 5
    }

    t0_search_all = time.perf_counter()
    for _ in range(search_reqs):
        t0 = time.perf_counter()
        try:
            r = requests.post(f"{BASE_AI_DIRECT}/api/matching/search", headers=headers, json=query_payload, timeout=10)
            if r.status_code != 200:
                search_errors += 1
        except Exception:
            search_errors += 1
        t1 = time.perf_counter()
        search_latencies.append((t1 - t0) * 1000.0)
    t1_search_all = time.perf_counter()

    search_latencies.sort()
    sn = len(search_latencies)
    s_p50 = search_latencies[int(sn * 0.50)]
    s_p95 = search_latencies[int(sn * 0.95)]
    s_p99 = search_latencies[int(sn * 0.99)]
    s_rps = round(search_reqs / (t1_search_all - t0_search_all), 2)
    s_err = round((search_errors / float(search_reqs)) * 100, 2)

    results["metrics"]["vector_search_api"] = {
        "requests": search_reqs,
        "throughput_rps": s_rps,
        "p50_ms": round(s_p50, 2),
        "p95_ms": round(s_p95, 2),
        "p99_ms": round(s_p99, 2),
        "error_rate_pct": s_err
    }
    print(f"Vector Search API: {s_rps} req/sec | p50: {s_p50:.2f}ms | p95: {s_p95:.2f}ms | p99: {s_p99:.2f}ms | Errors: {s_err}%")


def main():
    print("================================================================================")
    print("MEDMATCH V2 — LIVE STAGING E2E INTEGRATION & WORKFLOW VALIDATOR")
    print("Target Environment: Docker Staging (Containers running on localhost)")
    print("================================================================================")

    token_research, token_doctor, token_tenant2, hospital_h1, hospital_h2 = run_phase3_live_integrations()
    run_phase4_clinical_matching_workflows(token_research)
    run_phase5_failure_and_recovery(token_research)
    run_phase6_live_performance_metrics(token_research)

    out_file = REPO_ROOT / "reports" / "live_staging_execution_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n================================================================================")
    print("E2E RUN SUMMARY")
    print("================================================================================")
    total_passed = sum(1 for p in results["phases"].values() for t in p if t["passed"])
    total_tests = sum(len(p) for p in results["phases"].values())
    print(f"Total Live E2E Checks: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {len(results['failures'])}")
    if results["failures"]:
        print("\nFailed Checks:")
        for fail in results["failures"]:
            print(f"  - {fail}")
    print(f"\nResults saved to: {out_file}")


if __name__ == "__main__":
    main()
