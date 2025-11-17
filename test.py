import pandas as pd
import psycopg2
from psycopg2 import OperationalError

# pd.set_option('mode.chained_assignment', None)
from sqlalchemy import create_engine

def create_connection(db_name, db_user, db_password, db_host, db_port):
    """
    create a connection to a PostgreSQL database using SQLAlchemy
    """
    try:
        engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    return engine

db_name = "postgrescvedumper"
db_user = "postgrescvedumper"
db_password = "a42a18537d74c3b7e584c769152c3d"
db_host = "127.0.0.1"
db_port = "5432"
conn = create_connection(db_name, db_user, db_password, db_host, db_port)

query = """
SELECT cv.cve_id, f.filename, f.num_lines_added, f.num_lines_deleted, f.code_before, f.code_after, cc.cwe_id 
FROM file_change f, commits c, fixes fx, cve cv, cwe_classification cc
WHERE f.hash = c.hash 
AND c.hash = fx.hash 
AND fx.cve_id = cv.cve_id 
AND cv.cve_id = cc.cve_id 
AND f.programming_language = 'Python'
AND cc.cwe_id = 'CWE-89'
"""

python_sql_injection_fixes = pd.read_sql_query(query, conn)
python_sql_injection_fixes.head(5)
