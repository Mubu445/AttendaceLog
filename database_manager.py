import sqlite3
import os
import sys
import shutil

# Define the name of our database file
APP_NAME = "AttendanceLogger"

def get_db_path():
    """Returns the persistent path for the database, copying from bundled copy if needed."""
    # Where the DB should live (persistent location)
    local_appdata = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
    db_dir = os.path.join(local_appdata, APP_NAME)
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "attendance.db")

    # If DB doesn't exist yet, copy from the bundled source
    if not os.path.exists(db_path):
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller exe
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))  # folder where bundled files live
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        bundled_db = os.path.join(base_dir, "attendance.db")
        shutil.copyfile(bundled_db, db_path)

    return db_path
def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    DB_NAME = get_db_path()
    conn = sqlite3.connect(DB_NAME)
    # Set row_factory to sqlite3.Row to allow accessing columns by name
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """
    Initializes the database by creating tables and inserting default settings
    if they don't already exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Create 'settings' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY NOT NULL,
            value TEXT
        )
    ''')

    # 2. Create 'attendance_logs' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE, -- YYYY-MM-DD
            time_in TEXT NOT NULL,    -- HH:MM:SS
            time_out TEXT             -- HH:MM:SS (can be NULL)
        )
    ''')

    # 3. Create 'holidays' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            holiday_date TEXT NOT NULL UNIQUE, -- YYYY-MM-DD
            description TEXT
        )
    ''')

    # Insert default settings if they don't exist
    # Using INSERT OR IGNORE will prevent errors if the keys already exist
    INSERT_OR_IGNORE_SETTING_SQL = "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)"
    cursor.execute(INSERT_OR_IGNORE_SETTING_SQL, ('fixed_monthly_salary', '0'))
    cursor.execute(INSERT_OR_IGNORE_SETTING_SQL, ('hourly_rate', '0'))
    cursor.execute(INSERT_OR_IGNORE_SETTING_SQL, ('month_start_day', '29'))
    cursor.execute(INSERT_OR_IGNORE_SETTING_SQL, ('month_end_day', '28'))

    conn.commit()
    conn.close()

# --- Functions for Settings Management ---

def get_setting(key):
    """Retrieves a setting's value from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result['value'] if result else " "

def update_setting(key, value):
    """Inserts or updates a setting's value in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # INSERT OR REPLACE will insert if key doesn't exist, otherwise update
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

# --- Functions for Attendance Logs ---

def insert_attendance_log(date_str, time_in_str):
    """Inserts a new attendance log for a given date and time_in."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO attendance_logs (date, time_in) VALUES (?, ?)",
                       (date_str, time_in_str))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # This means a record for this date already exists (due to UNIQUE constraint)
        return False
    finally:
        conn.close()

def get_attendance_log_by_date(date_str):
    """Retrieves an attendance log for a specific date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance_logs WHERE date = ?", (date_str,))
    record = cursor.fetchone()
    conn.close()
    return record # Returns a sqlite3.Row object or None

def update_attendance_log_out_time(date_str, time_out_str):
    """Updates the time_out for an existing attendance log."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE attendance_logs SET time_out = ? WHERE date = ?",
                   (time_out_str, date_str))
    conn.commit()
    conn.close()

def update_attendance_log_times(date_str, time_in_str, time_out_str):
    """Updates both time_in and time_out for an existing attendance log."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE attendance_logs SET time_in = ?, time_out = ? WHERE date = ?",
                   (time_in_str, time_out_str, date_str))
    conn.commit()
    conn.close()

def get_attendance_logs_in_range(start_date_str, end_date_str):
    """Retrieves all attendance logs within a specified date range (inclusive)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance_logs WHERE date BETWEEN ? AND ? ORDER BY date ASC",
                   (start_date_str, end_date_str))
    records = cursor.fetchall()
    conn.close()
    return records # Returns a list of sqlite3.Row objects

# --- Functions for Holidays ---

def insert_holiday(holiday_date_str, description=""):
    """Inserts a new holiday record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO holidays (holiday_date, description) VALUES (?, ?)",
                       (holiday_date_str, description))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Holiday for this date already exists
        return False
    finally:
        conn.close()

def get_holidays_in_range(start_date_str, end_date_str):
    """Retrieves all holidays within a specified date range (inclusive)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM holidays WHERE holiday_date BETWEEN ? AND ? ORDER BY holiday_date ASC",
                   (start_date_str, end_date_str))
    records = cursor.fetchall()
    conn.close()
    return records # Returns a list of sqlite3.Row objects

def delete_holiday(holiday_date_str):
    """Deletes a holiday record for a specific date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM holidays WHERE holiday_date = ?", (holiday_date_str,))
    conn.commit()
    conn.close()


def update_attendance_log(date, time_in, time_out):
    """Updates an existing attendance log entry for a specific date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE attendance_logs SET time_in=?, time_out=? WHERE date=?",
                   (time_in, time_out, date))
    conn.commit()
    conn.close()

def delete_attendance_log(date):
    """Deletes an attendance log entry for a specific date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance_logs WHERE date=?", (date,))
    conn.commit()
    conn.close()

# You should already have this function, but just in case:
def get_all_attendance_logs():
    """Fetches all attendance logs from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, time_in, time_out FROM attendance_logs ORDER BY date DESC")
    logs = cursor.fetchall()
    conn.close()
    
    logs_list = []
    for log in logs:
        logs_list.append({
            'date': log[0],
            'time_in': log[1],
            'time_out': log[2],
        })
    return logs_list



def get_attendance_logs_in_range_for_editTab(start_date, end_date):
    """Fetches attendance logs within a specified date range."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT date, time_in, time_out FROM attendance_logs WHERE date BETWEEN ? AND ? ORDER BY date DESC",
                   (start_date, end_date))
    logs = cursor.fetchall()
    conn.close()
    
    logs_list = []
    for log in logs:
        logs_list.append({
            'date': log[0],
            'time_in': log[1],
            'time_out': log[2],
        })
    return logs_list

def add_attendance_log(date, time_in, time_out):
    """Adds a new attendance log entry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO attendance_logs (date, time_in, time_out) VALUES (?, ?, ?)",
                   (date, time_in, time_out))
    conn.commit()
    conn.close()
