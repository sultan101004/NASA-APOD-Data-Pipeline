FROM apache/airflow:2.7.3

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copy DAGs and plugins
COPY --chown=airflow:root dags /opt/airflow/dags
COPY --chown=airflow:root plugins /opt/airflow/plugins

# Initialize DVC (will be configured at runtime)
RUN dvc init --no-scm || true

