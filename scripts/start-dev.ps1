$ErrorActionPreference = "Stop"

# Change to the directory where the docker-compose.yml is located
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -Path "$scriptPath\.."

Write-Host "Starting OffBoardMe Backend Development Environment..." -ForegroundColor Cyan

# 1. Check if .env exists
if (!(Test-Path ".env")) {
    Write-Host "Error: .env file not found." -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and fill in the required passwords (DB_PASSWORD, NEO4J_PASSWORD) and secrets (KAFKA_CLUSTER_ID, JWT_SECRET)." -ForegroundColor Yellow
    Write-Host "Command: Copy-Item .env.example .env" -ForegroundColor Yellow
    exit 1
}

# Source .env file to load variables
if (Test-Path ".env") {
    Get-Content .env | Where-Object { $_ -match "^[^#]" -and $_ -match "=" } | ForEach-Object {
        $name, $value = $_ -split '=', 2
        Set-Item -Path "env:$name" -Value $value.Trim()
    }
}

$API_PORT = if ($env:API_PORT) { $env:API_PORT } else { "8888" }
$KAFKA_UI_PORT = if ($env:KAFKA_UI_PORT) { $env:KAFKA_UI_PORT } else { "8080" }
$NEO4J_BROWSER_PORT = if ($env:NEO4J_BROWSER_PORT) { $env:NEO4J_BROWSER_PORT } else { "7474" }
$DB_PORT = if ($env:DB_PORT) { $env:DB_PORT } else { "5432" }


# 2. Check if Docker daemon is running
try {
    $null = docker info 2>&1
} catch {
    Write-Host "Error: Docker daemon is not running." -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# 3. Start containers in the background
Write-Host "Starting Docker containers..." -ForegroundColor Cyan
docker compose up --build -d

# 4. Wait for healthchecks to pass
Write-Host "Waiting for services to become healthy..." -ForegroundColor Cyan
$timeout = 120
$startTime = Get-Date

while ($true) {
    # Get the status of all containers
    $statusJson = docker compose ps --format json
    
    # Check if any container is starting or unhealthy
    $isStarting = $statusJson -match '"Health":"starting"'
    $isUnhealthy = $statusJson -match '"Health":"unhealthy"'
    $isHealthy = $statusJson -match '"Health":"healthy"'
    
    if (-not $isStarting -and -not $isUnhealthy -and $isHealthy) {
        break
    }
    
    $elapsedTime = (Get-Date) - $startTime
    
    if ($elapsedTime.TotalSeconds -ge $timeout) {
        Write-Host "Timeout: Services did not become healthy within $timeout seconds." -ForegroundColor Red
        docker compose logs
        exit 1
    }
    
    Start-Sleep -Seconds 5
}

# 5. Print summary
Write-Host ""
Write-Host "All services are up and healthy!" -ForegroundColor Green
Write-Host "FastAPI Backend:       http://localhost:$API_PORT"
Write-Host "Kafka UI:              http://localhost:$KAFKA_UI_PORT"
Write-Host "Neo4j Browser:         http://localhost:$NEO4J_BROWSER_PORT"
Write-Host "PostgreSQL:            localhost:$DB_PORT"
Write-Host "API Documentation:     http://localhost:$API_PORT/docs"
Write-Host ""
Write-Host "Use 'docker compose logs -f backend' to view the API logs." -ForegroundColor DarkGray
