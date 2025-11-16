# 🚀 Quick Setup Guide

## Prerequisites
- Docker Desktop (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- Git (optional, for version control)
- At least 4GB RAM and 10GB free disk space

## Step-by-Step Setup

### 1. Create Environment File

**Windows (PowerShell):**
```powershell
echo "AIRFLOW_UID=50000" > .env
```

**Linux/Mac:**
```bash
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

### 2. Initialize Git Repository (Optional but Recommended)

```bash
git init
git add .
git commit -m "Initial commit: NASA APOD pipeline"
```

### 3. Build and Start Services

```bash
docker-compose up --build -d
```

This will:
- Build the custom Airflow image with DVC and PostgreSQL drivers
- Start PostgreSQL database (with automatic APOD database initialization)
- Start Airflow webserver
- Start Airflow scheduler

### 4. Wait for Services to be Ready

Wait about 30-60 seconds for all services to initialize. Check status:

```bash
docker-compose ps
```

All services should show "Up" status.

### 5. Access Airflow UI

- Open browser: http://localhost:8080
- Login:
  - Username: `airflow`
  - Password: `airflow`

### 6. Enable and Trigger the DAG

1. In Airflow UI, find `nasa_apod_pipeline` DAG
2. Toggle it ON (switch on the left)
3. Click the "Play" button (▶️) to trigger a manual run

### 7. Monitor Execution

- Click on the DAG name to see the graph view
- Click on individual tasks to see logs
- Green = success, Red = failed, Yellow = running

## Verification

### Check PostgreSQL Data

```bash
docker-compose exec postgres psql -U apod_user -d apod_db -c "SELECT * FROM apod_data ORDER BY date DESC LIMIT 5;"
```

### Check CSV File

```bash
docker-compose exec airflow-webserver cat /opt/airflow/data/apod_data.csv
```

### Check DVC Files

```bash
docker-compose exec airflow-webserver ls -la /opt/airflow/data/*.dvc
```

## Troubleshooting

### Services won't start
- Check Docker is running: `docker ps`
- Check ports 8080 and 5432 are not in use
- View logs: `docker-compose logs`

### DAG not appearing
- Check DAG file syntax: `docker-compose logs airflow-scheduler | grep -i error`
- Ensure DAG file is in `dags/` directory

### Database connection errors
- Wait for PostgreSQL to fully initialize (can take 30-60 seconds)
- Check PostgreSQL is healthy: `docker-compose ps postgres`

### DVC/Git errors
- These are expected if Git is not initialized
- The pipeline will still complete successfully
- To enable Git: initialize repo in project root before starting containers

## Stopping Services

```bash
docker-compose down
```

To also remove volumes (deletes all data):

```bash
docker-compose down -v
```

## Next Steps

- Review the main [README.md](README.md) for detailed documentation
- Customize the pipeline for your needs
- Set up remote DVC storage (S3, GCS, etc.)
- Deploy to Astronomer Cloud

