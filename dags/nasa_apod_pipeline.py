"""
NASA APOD Data Pipeline DAG
This DAG implements a complete ETL pipeline with 5 steps:
1. Extract data from NASA APOD API
2. Transform the data
3. Load to PostgreSQL and CSV
4. Version control with DVC
5. Commit DVC metadata to Git
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from plugins.apod_etl import extract_apod_data, transform_apod_data, load_to_postgres, load_to_csv
import os
import logging

logger = logging.getLogger(__name__)

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'nasa_apod_pipeline',
    default_args=default_args,
    description='NASA APOD ETL Pipeline with DVC and Git versioning',
    schedule_interval=timedelta(days=1),  # Run daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['nasa', 'apod', 'etl', 'dvc', 'postgres'],
)


def step1_extract(**context):
    """Step 1: Extract data from NASA APOD API"""
    logger.info("Step 1: Extracting data from NASA APOD API")
    raw_data = extract_apod_data()
    
    # Store in XCom for next task
    context['ti'].xcom_push(key='raw_apod_data', value=raw_data)
    logger.info(f"Extracted data for date: {raw_data.get('date')}")
    return raw_data


def step2_transform(**context):
    """Step 2: Transform the raw data"""
    logger.info("Step 2: Transforming APOD data")
    
    # Get data from previous task
    raw_data = context['ti'].xcom_pull(key='raw_apod_data', task_ids='step1_extract')
    
    if not raw_data:
        raise ValueError("No data received from extraction step")
    
    df = transform_apod_data(raw_data)
    
    # Store in XCom for next task
    context['ti'].xcom_push(key='transformed_df', value=df.to_dict('records'))
    logger.info(f"Transformed {len(df)} row(s)")
    return df.to_dict('records')


def step3_load(**context):
    """Step 3: Load data to PostgreSQL and CSV"""
    logger.info("Step 3: Loading data to PostgreSQL and CSV")
    
    # Get transformed data from previous task
    df_records = context['ti'].xcom_pull(key='transformed_df', task_ids='step2_transform')
    
    if not df_records:
        raise ValueError("No transformed data received")
    
    import pandas as pd
    df = pd.DataFrame(df_records)
    
    # Load to PostgreSQL
    load_to_postgres(df, table_name='apod_data')
    
    # Load to CSV
    csv_path = load_to_csv(df, filepath='data/apod_data.csv')
    
    # Store CSV path in XCom for DVC step
    context['ti'].xcom_push(key='csv_path', value=csv_path)
    logger.info(f"Loaded data to PostgreSQL and CSV: {csv_path}")
    return csv_path


def step4_dvc_version_prep(**context):
    """Prepare CSV path for DVC versioning"""
    csv_path = context['ti'].xcom_pull(key='csv_path', task_ids='step3_load')
    if not csv_path:
        raise ValueError("No CSV path received from load step")
    # Store absolute path for BashOperator
    abs_csv_path = os.path.abspath(csv_path) if not os.path.isabs(csv_path) else csv_path
    context['ti'].xcom_push(key='abs_csv_path', value=abs_csv_path)
    return abs_csv_path


# Define tasks
task_extract = PythonOperator(
    task_id='step1_extract',
    python_callable=step1_extract,
    dag=dag,
)

task_transform = PythonOperator(
    task_id='step2_transform',
    python_callable=step2_transform,
    dag=dag,
)

task_load = PythonOperator(
    task_id='step3_load',
    python_callable=step3_load,
    dag=dag,
)

task_dvc_version_prep = PythonOperator(
    task_id='step4_dvc_version_prep',
    python_callable=step4_dvc_version_prep,
    dag=dag,
)

task_dvc_version = BashOperator(
    task_id='step4_dvc_version',
    bash_command="""
    cd /opt/airflow
    CSV_PATH="{{ ti.xcom_pull(key='abs_csv_path', task_ids='step4_dvc_version_prep') }}"
    echo "CSV Path: $CSV_PATH"
    
    # Initialize DVC if not already initialized
    if [ ! -d .dvc ]; then
        dvc init --no-scm || true
    fi
    
    # Add file to DVC
    dvc add "$CSV_PATH" || exit 1
    
    # Verify DVC metadata file was created
    DVC_METADATA="${CSV_PATH}.dvc"
    if [ ! -f "$DVC_METADATA" ]; then
        echo "Error: DVC metadata file not created: $DVC_METADATA"
        exit 1
    fi
    
    echo "DVC versioning complete. Metadata: $DVC_METADATA"
    echo "$DVC_METADATA" > /tmp/dvc_metadata_path.txt
    """,
    dag=dag,
)

task_git_commit = BashOperator(
    task_id='step5_git_commit',
    bash_command="""
    cd /opt/airflow
    
    # Check if Git repository is initialized
    if [ ! -d .git ]; then
        echo "Warning: Git repository not initialized. Skipping Git commit."
        echo "To enable Git commits, initialize a Git repository in the project root."
        exit 0
    fi
    
    # Get DVC metadata path
    DVC_METADATA=$(cat /tmp/dvc_metadata_path.txt 2>/dev/null || echo "")
    if [ -z "$DVC_METADATA" ]; then
        # Try to find it from the CSV path
        CSV_PATH="{{ ti.xcom_pull(key='abs_csv_path', task_ids='step4_dvc_version_prep') }}"
        DVC_METADATA="${CSV_PATH}.dvc"
    fi
    
    if [ ! -f "$DVC_METADATA" ]; then
        echo "Warning: DVC metadata file not found: $DVC_METADATA"
        exit 0
    fi
    
    # Configure Git (if not already configured)
    git config user.name "Airflow" || true
    git config user.email "airflow@example.com" || true
    
    # Stage the DVC metadata file
    git add "$DVC_METADATA" || {
        echo "Warning: Git add failed. This is expected if Git is not properly configured."
        exit 0
    }
    
    # Commit the changes
    COMMIT_MSG="Add DVC metadata for APOD data - $(date '+%Y-%m-%d %H:%M:%S')"
    git commit -m "$COMMIT_MSG" || {
        echo "Info: No changes to commit or Git not configured. This is acceptable."
        exit 0
    }
    
    echo "Successfully committed DVC metadata to Git: $DVC_METADATA"
    """,
    dag=dag,
)

# Define task dependencies
task_extract >> task_transform >> task_load >> task_dvc_version_prep >> task_dvc_version >> task_git_commit

