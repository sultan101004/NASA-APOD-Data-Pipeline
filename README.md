# 🚀 MLOps Assignment 3: NASA APOD Data Pipeline

A complete ETL pipeline that extracts data from NASA's Astronomy Picture of the Day (APOD) API, transforms it, loads it into PostgreSQL and CSV, and versions it using DVC and Git.

## 📋 Overview

This project implements a robust, reproducible MLOps data ingestion pipeline using:
- **Apache Airflow** for workflow orchestration
- **Docker/Astronomer** for containerized deployment
- **PostgreSQL** for relational data storage
- **DVC** for data version control
- **Git** for code version control

## 🏗️ Architecture

The pipeline consists of 5 sequential steps:

1. **Extract (E)**: Fetches daily data from NASA APOD API
2. **Transform (T)**: Cleans and structures the JSON data into a Pandas DataFrame
3. **Load (L)**: Saves data to both PostgreSQL database and CSV file
4. **DVC Versioning**: Places CSV file under DVC version control
5. **Git Commit**: Commits DVC metadata file to Git repository

## 📁 Project Structure

```
MLOPs_A3/
├── dags/
│   ├── __init__.py
│   └── nasa_apod_pipeline.py      # Main Airflow DAG
├── plugins/
│   ├── __init__.py
│   └── apod_etl.py                # ETL utility functions
├── data/
│   └── .gitkeep                   # Placeholder for data directory
├── config/
│   └── init_postgres.sql          # PostgreSQL initialization script
├── Dockerfile                     # Custom Airflow image with DVC
├── docker-compose.yml             # Docker Compose configuration
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Git (for version control)
- At least 4GB RAM and 10GB disk space

### Setup Instructions

1. **Clone the repository** (if not already done):
   ```bash
   git clone <your-repo-url>
   cd MLOps_A3
   ```

2. **Initialize Git repository** (if not already initialized):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: NASA APOD pipeline setup"
   ```

3. **Initialize DVC** (optional, will be done automatically):
   ```bash
   dvc init
   ```

4. **Set Airflow user ID** (Linux/Mac):
   ```bash
   echo -e "AIRFLOW_UID=$(id -u)" > .env
   ```

   For Windows, create `.env` file manually:
   ```
   AIRFLOW_UID=50000
   ```

5. **Build and start the services**:
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build the custom Airflow image with DVC and PostgreSQL drivers
   - Start PostgreSQL database
   - Start Airflow webserver (accessible at http://localhost:8080)
   - Start Airflow scheduler

6. **Access Airflow UI**:
   - Open your browser and go to: http://localhost:8080
   - Default credentials:
     - Username: `airflow`
     - Password: `airflow`

7. **Initialize PostgreSQL database**:
   ```bash
   docker-compose exec postgres psql -U airflow -d airflow -f /docker-entrypoint-initdb.d/init_postgres.sql
   ```
   
   Or manually:
   ```bash
   docker-compose exec postgres psql -U airflow -d airflow
   ```
   Then run:
   ```sql
   CREATE DATABASE apod_db;
   CREATE USER apod_user WITH PASSWORD 'apod_password';
   GRANT ALL PRIVILEGES ON DATABASE apod_db TO apod_user;
   ```

8. **Trigger the DAG**:
   - In Airflow UI, find the `nasa_apod_pipeline` DAG
   - Toggle it ON (if paused)
   - Click the "Play" button to trigger a run

## 🔧 Configuration

### Environment Variables

The pipeline uses the following environment variables (set in `docker-compose.yml`):

- `APOD_DB_NAME`: PostgreSQL database name (default: `apod_db`)
- `APOD_DB_USER`: PostgreSQL user (default: `apod_user`)
- `APOD_DB_PASSWORD`: PostgreSQL password (default: `apod_password`)
- `APOD_DB_HOST`: PostgreSQL host (default: `postgres`)
- `APOD_DB_PORT`: PostgreSQL port (default: `5432`)

### NASA API Key

The pipeline uses the demo API key (`DEMO_KEY`) by default. For production use, you can:
- Set up a free API key at https://api.nasa.gov/
- Modify `plugins/apod_etl.py` to use an environment variable for the API key

## 📊 Pipeline Details

### Step 1: Extract
- Connects to NASA APOD API endpoint
- Retrieves daily structured JSON data
- Handles errors and retries

### Step 2: Transform
- Extracts fields: `date`, `title`, `url`, `explanation`, `media_type`, `hdurl`, `copyright`, `service_version`
- Converts to Pandas DataFrame
- Adds extraction timestamp

### Step 3: Load
- **PostgreSQL**: Creates table if not exists, inserts/updates data with conflict resolution
- **CSV**: Saves to `data/apod_data.csv`, handles appending and deduplication

### Step 4: DVC Versioning
- Initializes DVC if needed
- Adds CSV file to DVC tracking
- Creates `.dvc` metadata file

### Step 5: Git Commit
- Stages DVC metadata file
- Commits with timestamped message
- Handles cases where Git is not configured

## 🧪 Testing

### Manual Testing

1. **Test API connection**:
   ```bash
   curl "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
   ```

2. **Test PostgreSQL connection**:
   ```bash
   docker-compose exec postgres psql -U apod_user -d apod_db -c "SELECT COUNT(*) FROM apod_data;"
   ```

3. **Check CSV file**:
   ```bash
   docker-compose exec airflow-webserver cat /opt/airflow/data/apod_data.csv
   ```

### Viewing Logs

```bash
# Airflow scheduler logs
docker-compose logs airflow-scheduler

# Airflow webserver logs
docker-compose logs airflow-webserver

# Specific task logs (via Airflow UI)
# Go to DAG → Task Instance → Logs
```

## 📝 Data Schema

The `apod_data` table in PostgreSQL has the following schema:

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| date | DATE | APOD date (unique) |
| title | TEXT | Image title |
| url | TEXT | Image URL |
| explanation | TEXT | Image explanation |
| media_type | VARCHAR(50) | Media type (image/video) |
| hdurl | TEXT | HD image URL |
| copyright | TEXT | Copyright information |
| service_version | VARCHAR(50) | API version |
| extracted_at | TIMESTAMP | Extraction timestamp |
| created_at | TIMESTAMP | Record creation time |

## 🐛 Troubleshooting

### Issue: DAG not appearing in Airflow UI
- **Solution**: Check if DAG file has syntax errors. View logs: `docker-compose logs airflow-scheduler`

### Issue: PostgreSQL connection failed
- **Solution**: Ensure PostgreSQL service is healthy: `docker-compose ps`
- Initialize database manually if needed (see Setup Instructions)

### Issue: DVC commands failing
- **Solution**: DVC is initialized automatically. Check if `/opt/airflow/.dvc` directory exists in container

### Issue: Git commit not working
- **Solution**: This is expected if Git repository is not initialized. Initialize with `git init` in project root

### Issue: Permission errors
- **Solution**: Ensure `.env` file has correct `AIRFLOW_UID` set (Linux/Mac: `id -u`, Windows: `50000`)

## 🔐 Security Notes

- Default passwords are for development only
- For production, use strong passwords and secrets management
- Consider using environment variables for sensitive data
- NASA API key should be stored securely (not hardcoded)

## 📚 Key Learnings

This project demonstrates:

1. **Orchestration Mastery**: Complex workflow dependencies using Apache Airflow
2. **Data Integrity**: Concurrent loading to multiple storage systems
3. **Data Lineage**: Version control with DVC and Git for reproducibility
4. **Containerized Deployment**: Docker-based deployment for consistency

## 🎯 Next Steps

- Set up remote DVC storage (S3, GCS, etc.)
- Add data quality checks
- Implement error notifications
- Add data transformation tests
- Set up CI/CD pipeline
- Deploy to Astronomer Cloud

## 📄 License

This project is for educational purposes as part of MLOps Assignment 3.

## 👤 Author

Sultan Shah, BS SE, FAST NUCES, Islamabad.

---

**Deadline**: November 16, 2025

