#!/usr/bin/env bash
set -e

# Change to the directory where the docker-compose.yml is located
cd "$(dirname "$0")/.."

echo "Starting OffBoardMe Backend Development Environment..."

# 1. Check if .env exists
if [ ! -f .env ]; then
  echo "Error: .env file not found."
  echo "Please copy .env.example to .env and fill in the required passwords (DB_PASSWORD, NEO4J_PASSWORD) and secrets (KAFKA_CLUSTER_ID, JWT_SECRET)."
  echo "Command: cp .env.example .env"
  exit 1
fi

# 2. Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker daemon is not running."
  echo "Please start Docker Desktop or the docker service and try again."
  exit 1
fi

# 3. Start containers in the background
echo "Starting Docker containers..."
docker compose up --build -d

# 4. Wait for healthchecks to pass
echo "Waiting for services to become healthy..."
TIMEOUT=120
START_TIME=$(date +%s)

while true; do
  # Get the status of all containers
  STATUS=$(docker compose ps --format json | grep -o '"Health":"[^"]*"' | cut -d'"' -f4)
  
  # Check if any container is starting or unhealthy
  if ! echo "$STATUS" | grep -q "starting\|unhealthy"; then
    # Ensure there's at least one healthy container and no missing health statuses for services that should have them
    if echo "$STATUS" | grep -q "healthy"; then
      break
    fi
  fi
  
  CURRENT_TIME=$(date +%s)
  ELAPSED_TIME=$((CURRENT_TIME - START_TIME))
  
  if [ $ELAPSED_TIME -ge $TIMEOUT ]; then
    echo "Timeout: Services did not become healthy within $TIMEOUT seconds."
    docker compose logs
    exit 1
  fi
  
  sleep 5
done

# 5. Print summary
echo ""
echo "All services are up and healthy!"
echo ""
echo "FastAPI Backend:       http://localhost:8888"
echo "Kafka UI:              http://localhost:8080"
echo "Neo4j Browser:         http://localhost:7474"
echo "PostgreSQL:            localhost:5432"
echo "API Documentation:     http://localhost:8888/docs"
echo ""
echo "Use 'docker compose logs -f backend' to view the API logs."
