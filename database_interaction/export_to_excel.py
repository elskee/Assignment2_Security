#!/usr/bin/env python3
"""
Script to export SQL query results to Excel.
Reads SQL from dataclean.sql and database credentials from .env
"""

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get database connection parameters from environment
    db_config = {
        'host': os.getenv('POSTGRES_HOST', '127.0.0.1'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DBNAME', 'postgrescvedumper'),
        'user': os.getenv('POSTGRES_USER', 'postgrescvedumper'),
        'password': os.getenv('POSTGRES_PASSWORD')
    }
    
    # Read SQL query from file
    with open('dataclean.sql', 'r') as f:
        sql_query = f.read()
    
    print("Connecting to database...")
    print(f"Host: {db_config['host']}:{db_config['port']}")
    print(f"Database: {db_config['database']}")
    print(f"User: {db_config['user']}")
    
    # Connect to PostgreSQL database
    try:
        conn = psycopg2.connect(**db_config)
        print("Successfully connected to database!")
        
        # Execute query and load results into pandas DataFrame
        print("\nExecuting query...")
        df = pd.read_sql_query(sql_query, conn)
        
        print(f"Query returned {len(df)} rows")
        print("\nPreview of results:")
        print(df.head())
        
        # Export to Excel
        output_filename = 'dataclean_results.xlsx'
        print(f"\nExporting to {output_filename}...")
        df.to_excel(output_filename, index=False, engine='openpyxl')
        
        print(f"Successfully exported to {output_filename}")
        
        # Close connection
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

