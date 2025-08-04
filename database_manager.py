import sqlite3
import os
import datetime # Import for date/time formatting

# Define the name of our database file
DB_NAME = 'attendance.db'

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
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
    cursor.execute(INSERT_OR_IGNORE_SETTING_SQL, ('month_start_day', '28'))
    cursor.execute(INSERT_OR_IGNORE_SETTING_SQL, ('month_end_day', '27'))

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
    return result['value'] if result else None

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


# --- Testing Block (only runs when database_manager.py is executed directly) ---
if __name__ == "__main__":
    # Clean up previous db for fresh start for testing
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Removed existing {DB_NAME} for a fresh start.")

    initialize_database()
    print("Database initialized successfully!")

    print("\n--- Testing Settings ---")
    update_setting('fixed_monthly_salary', '75000')
    update_setting('hourly_rate', '350')
    print(f"Fixed Monthly Salary: {get_setting('fixed_monthly_salary')}")
    print(f"Hourly Rate: {get_setting('hourly_rate')}")
    print(f"Month Start Day: {get_setting('month_start_day')}")
    print(f"Month End Day: {get_setting('month_end_day')}")

    print("\n--- Testing Attendance Logs ---")
    today = datetime.date.today().strftime('%Y-%m-%d')
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    print(f"Inserting log for {today}: {insert_attendance_log(today, '09:00:00')}")
    print(f"Inserting log for {yesterday}: {insert_attendance_log(yesterday, '09:10:00')}")
    print(f"Trying to insert {today} again (should be False): {insert_attendance_log(today, '09:00:00')}")

    print(f"Today's log before out: {get_attendance_log_by_date(today)}")
    update_attendance_log_out_time(today, '17:30:00')
    print(f"Today's log after out: {get_attendance_log_by_date(today)}")

    print("Updating yesterday's log to be 09:05:00 - 17:00:00")
    update_attendance_log_times(yesterday, '09:05:00', '17:00:00')
    print(f"Yesterday's log after update: {get_attendance_log_by_date(yesterday)}")

    print("\nAttendance logs in range (yesterday to tomorrow):")
    for log in get_attendance_logs_in_range(yesterday, tomorrow):
        print(f"  Date: {log['date']}, In: {log['time_in']}, Out: {log['time_out']}")

    print("\n--- Testing Holidays ---")
    holiday1 = (datetime.date.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    holiday2 = (datetime.date.today() + datetime.timedelta(days=14)).strftime('%Y-%m-%d')

    print(f"Inserting holiday {holiday1}: {insert_holiday(holiday1, 'National Holiday')}")
    print(f"Inserting holiday {holiday2}: {insert_holiday(holiday2, 'Local Event')}")
    print(f"Trying to insert {holiday1} again (should be False): {insert_holiday(holiday1, 'Another Name')}")

    print("\nHolidays in range (today to end of month):")
    end_of_month = (datetime.date.today().replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    for holiday in get_holidays_in_range(today, end_of_month.strftime('%Y-%m-%d')):
        print(f"  Date: {holiday['holiday_date']}, Description: {holiday['description']}")

    print(f"\nDeleting holiday {holiday1}:")
    delete_holiday(holiday1)
    print("Holidays after deletion:")
    for holiday in get_holidays_in_range(today, end_of_month.strftime('%Y-%m-%d')):
        print(f"  Date: {holiday['holiday_date']}, Description: {holiday['description']}")
