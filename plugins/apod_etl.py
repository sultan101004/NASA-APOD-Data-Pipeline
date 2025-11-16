"""
APOD ETL Utility Functions
Contains functions for Extract, Transform, and Load operations
"""

import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# NASA APOD API endpoint
APOD_API_URL = "https://api.nasa.gov/planetary/apod"
API_KEY = "DEMO_KEY"


def extract_apod_data(date=None):
    """
    Extract data from NASA APOD API
    
    Args:
        date (str, optional): Date in YYYY-MM-DD format. If None, gets today's APOD.
    
    Returns:
        dict: Raw JSON response from API
    """
    try:
        params = {"api_key": API_KEY}
        if date:
            params["date"] = date
        
        logger.info(f"Fetching APOD data from {APOD_API_URL}")
        response = requests.get(APOD_API_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Successfully fetched APOD data for date: {data.get('date', 'today')}")
        return data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching APOD data: {str(e)}")
        raise


def transform_apod_data(raw_data):
    """
    Transform raw APOD JSON data into a clean DataFrame
    
    Args:
        raw_data (dict): Raw JSON response from API
    
    Returns:
        pd.DataFrame: Transformed data with selected fields
    """
    try:
        # Select fields of interest
        selected_fields = {
            'date': raw_data.get('date'),
            'title': raw_data.get('title'),
            'url': raw_data.get('url'),
            'explanation': raw_data.get('explanation'),
            'media_type': raw_data.get('media_type'),
            'hdurl': raw_data.get('hdurl', ''),
            'copyright': raw_data.get('copyright', ''),
            'service_version': raw_data.get('service_version', '')
        }
        
        # Create DataFrame
        df = pd.DataFrame([selected_fields])
        
        # Add timestamp for tracking
        df['extracted_at'] = datetime.now().isoformat()
        
        logger.info(f"Transformed APOD data: {len(df)} row(s)")
        return df
    
    except Exception as e:
        logger.error(f"Error transforming APOD data: {str(e)}")
        raise


def load_to_postgres(df, table_name='apod_data'):
    """
    Load DataFrame to PostgreSQL database
    
    Args:
        df (pd.DataFrame): DataFrame to load
        table_name (str): Name of the table to insert into
    
    Returns:
        bool: True if successful
    """
    try:
        # Get database connection parameters from environment
        db_config = {
            'host': os.getenv('APOD_DB_HOST', 'postgres'),
            'port': os.getenv('APOD_DB_PORT', '5432'),
            'database': os.getenv('APOD_DB_NAME', 'apod_db'),
            'user': os.getenv('APOD_DB_USER', 'apod_user'),
            'password': os.getenv('APOD_DB_PASSWORD', 'apod_password')
        }
        
        logger.info(f"Connecting to PostgreSQL database: {db_config['database']}")
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            title TEXT,
            url TEXT,
            explanation TEXT,
            media_type VARCHAR(50),
            hdurl TEXT,
            copyright TEXT,
            service_version VARCHAR(50),
            extracted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date)
        );
        """
        cursor.execute(create_table_query)
        conn.commit()
        
        # Insert data (using ON CONFLICT to handle duplicates)
        insert_query = f"""
        INSERT INTO {table_name} 
        (date, title, url, explanation, media_type, hdurl, copyright, service_version, extracted_at)
        VALUES %s
        ON CONFLICT (date) DO UPDATE SET
            title = EXCLUDED.title,
            url = EXCLUDED.url,
            explanation = EXCLUDED.explanation,
            media_type = EXCLUDED.media_type,
            hdurl = EXCLUDED.hdurl,
            copyright = EXCLUDED.copyright,
            service_version = EXCLUDED.service_version,
            extracted_at = EXCLUDED.extracted_at;
        """
        
        # Convert DataFrame to list of tuples
        values = [tuple(row) for row in df.values]
        execute_values(cursor, insert_query, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Successfully loaded {len(df)} row(s) to PostgreSQL table: {table_name}")
        return True
    
    except Exception as e:
        logger.error(f"Error loading data to PostgreSQL: {str(e)}")
        raise


def load_to_csv(df, filepath='data/apod_data.csv'):
    """
    Load DataFrame to CSV file
    
    Args:
        df (pd.DataFrame): DataFrame to save
        filepath (str): Path to CSV file
    
    Returns:
        str: Path to the saved CSV file
    """
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Check if file exists to append or create new
        if os.path.exists(filepath):
            # Append mode - read existing and append new data
            existing_df = pd.read_csv(filepath)
            # Remove duplicates based on date
            combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=['date'], keep='last')
            combined_df.to_csv(filepath, index=False)
            logger.info(f"Appended data to existing CSV: {filepath}")
        else:
            # Create new file
            df.to_csv(filepath, index=False)
            logger.info(f"Created new CSV file: {filepath}")
        
        return filepath
    
    except Exception as e:
        logger.error(f"Error loading data to CSV: {str(e)}")
        raise

