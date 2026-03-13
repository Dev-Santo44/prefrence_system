"""
Database helper for AI-Driven Personal Preference Identifier
Manages MySQL connection using mysql-connector-python.
"""

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "preference_db"),
    "port": int(os.getenv("DB_PORT", 3306)),
}


def get_connection():
    """Create and return a new MySQL database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise RuntimeError(f"Database connection failed: {e}")


def execute_query(query: str, params: tuple = (), fetch: bool = False):
    """
    Execute a SQL query.
    - If fetch=True, returns all rows.
    - If fetch=False, commits and returns lastrowid.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return cursor.lastrowid
    except Error as e:
        conn.rollback()
        raise RuntimeError(f"Query execution failed: {e}")
    finally:
        cursor.close()
        conn.close()
