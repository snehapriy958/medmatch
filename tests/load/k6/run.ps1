param(
    [string]$Script = "auth.js"
)

# ====================================
# Service URLs
# ====================================

$env:AUTH_URL = "http://localhost:8081"
$env:BASE_URL = "http://localhost:8000"

# ====================================
# Benchmark Users
# ====================================

$env:ADMIN_USERNAME = "admin"
$env:ADMIN_PASSWORD = "Admin@123"

$env:DOCTOR_USERNAME = "doctor1"
$env:DOCTOR_PASSWORD = "Doctor@123"

$env:RESEARCHER_USERNAME = "researcher1"
$env:RESEARCHER_PASSWORD = "Researcher@123"

# ====================================
# Run Benchmark
# ====================================

New-Item -ItemType Directory -Force -Path ".\results" | Out-Null

k6 run `
    --summary-export ".\results\$($Script.Replace('.js','')).json" `
    ".\scripts\$Script"