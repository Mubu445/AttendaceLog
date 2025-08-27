import calendar
import database_manager
import datetime
import sqlite3
# --- Helper Functions for Dates and Times ---

def get_current_date_str():
    """Returns today's date in YYYY-MM-DD string format."""
    return datetime.date.today().strftime('%Y-%m-%d')

def get_current_time_str():
    """Returns the current time in HH:MM:SS string format."""
    return datetime.datetime.now().strftime('%H:%M')

def get_start_end_dates_for_period(date_to_use=None):
    """
    Calculates the start and end dates (YYYY-MM-DD strings) for the current
    attendance period based on configured month_start_day and month_end_day.
    Uses the 28th to 27th rollover logic.
    """
    # Get settings from database, convert to int, use defaults if None
    month_start_day_raw = database_manager.get_setting('month_start_day')
    month_end_day_raw = database_manager.get_setting('month_end_day')
    month_start_day = int(month_start_day_raw) if month_start_day_raw is not None else 28
    month_end_day = int(month_end_day_raw) if month_end_day_raw is not None else 27
    
    if date_to_use is None:
        base_date = datetime.date.today()
        end_date = base_date - datetime.timedelta(days=1)
    else:
        base_date = date_to_use
        end_date = base_date.replace(day=month_end_day)

    prev_month = base_date.replace(day=1) - datetime.timedelta(days=1)
    start_date = prev_month.replace(day=month_start_day)


    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def get_total_hours_worked(time_in_str, time_out_str):
    """
    Calculates the total hours worked given 'In' and 'Out' time strings.
    Handles overnight shifts (time_out_str < time_in_str).
    Returns hours as a float.
    """
    if not time_in_str or not time_out_str:
        return 0.0

    FMT = '%H:%M'
    t_in = datetime.datetime.strptime(time_in_str, FMT).time()
    t_out = datetime.datetime.strptime(time_out_str, FMT).time()

    dummy_date = datetime.date(1, 1, 1) # A dummy date for datetime object creation
    dt_in = datetime.datetime.combine(dummy_date, t_in)
    dt_out = datetime.datetime.combine(dummy_date, t_out)

    if dt_out < dt_in:
        # Handles overnight shifts (e.g., In 22:00:00, Out 06:00:00 next day)
        dt_out += datetime.timedelta(days=1)

    duration = dt_out - dt_in
    return duration.total_seconds() / 3600.0 # Convert seconds to hours

# --- Attendance Logging Logic ---

def handle_app_startup_in_log():
    """
    Handles the automatic 'In' logging logic when the app starts.
    - If no 'In' for today, records it.
    - If 'In' already recorded and 'Out' was set, clears 'Out' to extend session.
    """
    today_str = get_current_date_str()
    current_time_str = get_current_time_str()
    
    today_record = database_manager.get_attendance_log_by_date(today_str)

    if not today_record:
        # No record for today, insert new 'In'
        database_manager.insert_attendance_log(today_str, current_time_str)
        return "Logged IN automatically for today."
    elif today_record['time_out'] is not None:
        # Record exists, and 'Out' was set. Clear 'Out' as user is back 'In'.
        database_manager.update_attendance_log_out_time(today_str, None) # Set time_out to NULL
        return "You are back IN. Previous OUT time cleared."
    else:
        # Record exists, and 'Out' is NULL (already logged in)
        return "You are already logged IN for today. Welcome back!"

def record_manual_in():
    """Records a manual 'In' time for today. Overwrites existing 'In' if present."""
    today_str = get_current_date_str()
    current_time_str = get_current_time_str()

    today_record = database_manager.get_attendance_log_by_date(today_str)
    if today_record:
        # If record exists, update time_in and clear time_out (as per requirement)
        database_manager.update_attendance_log_times(today_str, current_time_str, None)
        return "Manual IN recorded. Previous OUT time cleared if set."
    else:
        # No record, insert new
        database_manager.insert_attendance_log(today_str, current_time_str)
        return "Manual IN recorded for today."

def record_manual_out():
    """Records a manual 'Out' time for today."""
    today_str = get_current_date_str()
    current_time_str = get_current_time_str()

    today_record = database_manager.get_attendance_log_by_date(today_str)
    if today_record and today_record['time_in']: # Ensure there's an 'In' to log 'Out' from
        database_manager.update_attendance_log_out_time(today_str, current_time_str)
        return "Manual OUT recorded for today."
    else:
        return "Cannot log OUT: No IN time recorded for today."

def update_attendance_entry(date_str, new_time_in_str, new_time_out_str):
    """Allows editing of existing attendance records."""
    # Basic validation: check if times are valid formats (HH:MM:SS)
    # More robust validation will be needed in GUI or here
    if not new_time_in_str:
        return "Error: IN time cannot be empty.", False

    # Check for valid time format. This is a simple regex check, could be more robust.
    import re
    time_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}$')
    if not time_pattern.match(new_time_in_str):
        return "Error: Invalid IN time format. Use HH:MM:SS.", False
    if new_time_out_str and not time_pattern.match(new_time_out_str):
        return "Error: Invalid OUT time format. Use HH:MM:SS.", False

    try:
        database_manager.update_attendance_log_times(date_str, new_time_in_str, new_time_out_str if new_time_out_str else None)
        return "Attendance entry updated successfully.", True
    except Exception as e:
        return f"Error updating attendance: {e}", False


def get_today_attendance_status():
    """Retrieves and returns the current day's attendance status."""
    today_str = get_current_date_str()
    record = database_manager.get_attendance_log_by_date(today_str)
    return record # Returns sqlite3.Row or None

def get_recent_attendance_history(days=30):
    """Fetches attendance logs for the last 'days' for display in history."""
    today_date_obj = datetime.date.today()
    start_date_obj = today_date_obj - datetime.timedelta(days=days)
    
    start_date_str = start_date_obj.strftime('%Y-%m-%d')
    end_date_str = today_date_obj.strftime('%Y-%m-%d')
    
    return database_manager.get_attendance_logs_in_range(start_date_str, end_date_str)

# --- Salary Calculation Logic (NEW FUNCTIONS) ---

def is_weekend(date_obj):
    """Checks if a date is a Saturday (5) or Sunday (6). Monday is 0."""
    return date_obj.weekday() in [5, 6]

def is_public_holiday(date_str):
    """Checks if a date is a user-defined public holiday."""
    # We need to fetch all holidays and check if date_str is in them.
    # For efficiency, a set of holidays in range could be passed, or fetched once.
    # For now, we'll fetch just for this date.
    holidays = database_manager.get_holidays_in_range(date_str, date_str)
    return len(holidays) > 0

def get_daily_pay_and_penalties(log_entry, fixed_salary_per_day, hourly_rate):
    """
    Calculates the daily pay contribution and penalties for a single day,
    applying rules 5 (Half Day) and 6 (Hourly Cut).
    Returns (daily_salary_contribution, is_late_for_cumulative_count, reason_for_penalty_msg).
    """
    daily_pay = fixed_salary_per_day
    is_late_for_cumulative_count = False
    penalty_reason = ""

    if not log_entry or not log_entry['time_in']:
        # No 'In' log for a working day
        return 0.0, False, "Absent (No IN Time)"

    time_in_str = log_entry['time_in']
    
    # Convert time_in_str to datetime.time object for easier comparison
    FMT = '%H:%M'
    try:
        in_time = datetime.datetime.strptime(time_in_str, FMT).time()
    except ValueError:
        return 0.0, False, "Invalid IN Time Format" # Should be prevented by validation

    # Rule 5: Log In After 12 PM is Half Day
    if in_time >= datetime.time(12, 0, 0):
        daily_pay = fixed_salary_per_day / 2
        return daily_pay, False, "Half Day (Logged IN after 12:00 PM)" # Overrides other rules

    # Rule 6: Log In After 10 AM Hourly Cut
    elif in_time >= datetime.time(11, 0, 0): # Logged in 11:00 to 11:59 (2 hours cut)
        hours_to_cut = 2
        daily_pay -= (hourly_rate * hours_to_cut)
        is_late_for_cumulative_count = True # Still counts as a 'late' instance for Rule 4
        penalty_reason = f"Late (IN after 11 AM) - {hours_to_cut} hours cut"
    elif in_time >= datetime.time(10, 0, 0): # Logged in 10:00 to 10:59 (1 hour cut)
        hours_to_cut = 1
        daily_pay -= (hourly_rate * hours_to_cut)
        is_late_for_cumulative_count = True # Still counts as a 'late' instance for Rule 4
        penalty_reason = f"Late (IN after 10 AM) - {hours_to_cut} hour cut"

    # Rule 4 (Part 1): Late Arrival (after 9:15 AM) - only for cumulative count
    elif in_time > datetime.time(9, 15, 0):
        is_late_for_cumulative_count = True
        penalty_reason = "Late (IN after 09:15 AM)"
    else:
        penalty_reason = "On Time"

    # Ensure daily_pay doesn't go negative
    if daily_pay < 0:
        daily_pay = 0.0

    return daily_pay, is_late_for_cumulative_count, penalty_reason


def calculate_monthly_salary(report_month=None, report_year=None):
    """
    Calculates the total monthly salary for the current attendance period
    based on all defined rules.
    """
    today = 0
    if report_month is None or report_year is None:
        start_date_str, end_date_str = get_start_end_dates_for_period()
        today = 1
    else:
        report_date = datetime.date(report_year, report_month, 1)
        start_date_str, end_date_str = get_start_end_dates_for_period(report_date)
    # Fetch settings
    fixed_monthly_salary_str = database_manager.get_setting('fixed_monthly_salary')
    hourly_rate_str = database_manager.get_setting('hourly_rate')

    try:
        fixed_monthly_salary = float(fixed_monthly_salary_str)
        hourly_rate = float(hourly_rate_str)
    except (ValueError, TypeError):
        fixed_monthly_salary = 0.0
        hourly_rate = 0.0

    if fixed_monthly_salary == 0 or hourly_rate == 0:
        return {
            "total_salary": 0.0,
            "details": [],
            "summary": "Please set Fixed Monthly Salary and Hourly Rate in settings."
        }

    total_calculated_salary = fixed_monthly_salary
    fixed_salary_per_day = fixed_monthly_salary / 30.0

    # Fetch all logs and holidays for the period
    all_logs = {log['date']: log for log in database_manager.get_attendance_logs_in_range(start_date_str, end_date_str)}
    all_holidays = {h['holiday_date']: h['description'] for h in database_manager.get_holidays_in_range(start_date_str, end_date_str)}

    
    daily_breakdown = []
    
    late_count = 0
    absent_days_count = 0
    
    late_deduction_total = 0.0
    actual_working_saturdays = 0
    saturday_holiday = 0
    gross_salary = 0
    current_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    total_salary_until_today = 0.0
    if end_date - current_date >= datetime.timedelta(days=30):
        today = 0
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        log_entry = all_logs.get(date_str)
        day_status = "Working Day"
        daily_contribution = 0.0
        late_reason = ""
        is_late_instance = False
        gross_salary += fixed_salary_per_day 
        is_holiday = is_public_holiday(date_str)
        is_sunday = is_weekend(current_date) and current_date.weekday() == 6
        is_saturday = is_weekend(current_date) and current_date.weekday() == 5
        
        
        if is_holiday:
            day_status = f"Paid Day Off (Public Holiday: {all_holidays[date_str]})"
            daily_contribution = fixed_salary_per_day
            if current_date.weekday() == 5: # Saturday
                saturday_holiday = 1 # Count this as a holiday Saturday
                day_status = "Holiday Saturday"
        elif is_sunday:
            day_status = "Paid Day Off (Sunday)"
            daily_contribution = fixed_salary_per_day
        elif is_saturday:
            daily_contribution = fixed_salary_per_day
            if log_entry and log_entry['time_in']:
                daily_contribution, is_late_instance, late_reason = \
                get_daily_pay_and_penalties(log_entry, fixed_salary_per_day, hourly_rate)
                day_status = "Working Saturday"
                actual_working_saturdays += 1 # Count this as a worked Saturday
                if is_late_instance:
                    late_count += 1
            else:
                day_status = "Unlogged Saturday (Pending Rule 2)"
        elif log_entry and log_entry['time_in'] and log_entry['time_out']:
            daily_contribution, is_late_instance, late_reason = \
                get_daily_pay_and_penalties(log_entry, fixed_salary_per_day, hourly_rate)
            
            if is_late_instance:
                late_count += 1
            
            if "Half Day" in late_reason:
                day_status = "Half Day"
            elif "Late" in late_reason:
                day_status = "Working Day (Late)"
            else:
                day_status = "Working Day (On Time)"
        else:
            day_status = "Absent"
            if not is_weekend(current_date) and not is_holiday:
                absent_days_count += 1
                daily_contribution = 0.0 # Deduction will be applied later
        
        daily_breakdown.append({
            "date": date_str,
            "status": day_status,
            "in": log_entry['time_in'] if log_entry else 'N/A',
            "out": log_entry['time_out'] if log_entry else 'N/A',
            "daily_pay_contribution": round(daily_contribution, 2),
            "penalty_reason": late_reason
        })
        if today == 1:
            total_salary_until_today += daily_contribution
        current_date += datetime.timedelta(days=1)
    
    one_paid_day_off_applied = False
    # --- Apply Post-Iteration Rules ---
    if absent_days_count > 0:
        absent_days_count -= 1
        one_paid_day_off_applied = True
        # Also need to find the first absent day in the breakdown and update it
        for i, day_info in enumerate(daily_breakdown):
            if day_info['status'] == "Absent":
                daily_breakdown[i]['status'] = "Paid Day Off (Auto Granted)"
                daily_breakdown[i]['daily_pay_contribution'] = round(fixed_salary_per_day, 2)
                break
        absent_deduction_amount = absent_days_count * fixed_salary_per_day
        total_calculated_salary -= absent_deduction_amount
    
    # Rule 4: Cumulative Late Penalty
    late_deductions_count = late_count // 3
    late_deduction_amount = late_deductions_count * fixed_salary_per_day
    total_calculated_salary -= late_deduction_amount
    late_deduction_total = late_deduction_amount

    # Rule 2: Two Saturdays are paid off, Two Saturdays are worked.
    # We count *worked* Saturdays. If less than 2, apply deduction.
    # Note: If a Saturday was a public holiday, it's already accounted for as paid.
    # We only care about Saturdays that were NOT holidays, where user was expected to log in.


    # Count actual working saturdays (not holidays) that had IN/OUT

    # Rule 1: One additional paid day off per month, handled by app (if user missed a day)
    # Iterate through breakdown to find a candidate for the 'one paid day off'
    # This rule is applied *after* other deductions, if there's a missed working day.
    saturday_deduction = 0.0
    saturday_reason = ""
    paid_day_off_used_for_saturday = False
    
    if actual_working_saturdays < 2 and saturday_holiday == 0:
        if not one_paid_day_off_applied:
            paid_day_off_used_for_saturday = True
        missed_saturdays_for_deduction = 2 - actual_working_saturdays - (1 if paid_day_off_used_for_saturday else 0)
        saturday_deduction = missed_saturdays_for_deduction * fixed_salary_per_day
        total_calculated_salary -= saturday_deduction
        saturday_reason = f"Deducted for {missed_saturdays_for_deduction} unlogged Saturday(s) (Expected 2 worked)"
    
    if paid_day_off_used_for_saturday:
        one_paid_day_off_applied = True
        
    summary = f"Salary calculated for period: {start_date_str} to {end_date_str}\n"
    summary += f"Total Late Instances: {late_count} ({late_deductions_count} day(s) cut, PKR {late_deduction_total:.2f})\n"
    summary += f"Saturdays Worked (not holidays): {actual_working_saturdays} {saturday_reason}\n"
    if one_paid_day_off_applied:
        summary += "One auto-granted paid day off applied.\n"
    days_in_month = calendar.monthrange(current_date.year, current_date.month)[1]
    if days_in_month == 31 and today == 0:
        gross_salary -= fixed_salary_per_day 
        
    return {
        "total_salary": round(total_calculated_salary, 2),
        "gross_salary": round(gross_salary, 2),
        "total_salary_until_today": round(total_salary_until_today, 2),
        "details": daily_breakdown,
        "summary": summary,
        "period_start": start_date_str,
        "period_end": end_date_str
    }

def update_log_entry(date, time_in, time_out):
    """Updates an attendance log entry in the database."""
    if not date:
        return "Error: Date is required."
    database_manager.update_attendance_log(date, time_in, time_out)
    return "Log entry updated successfully."

def delete_log_entry(date):
    """Deletes an attendance log entry from the database."""
    if not date:
        return "Error: Date is required."
    database_manager.delete_attendance_log(date)
    return "Log entry deleted successfully."

def add_log_entry(date, time_in, time_out):
    """Adds a new attendance log entry to the database."""
    if not all([date, time_in, time_out]):
        return "Error: All fields are required."
    
    # We can add more robust date/time validation here if needed
    try:
        database_manager.add_attendance_log(date, time_in, time_out)
        return f"Log entry for {date} added successfully."
    except sqlite3.IntegrityError:
        return f"Error: A log for {date} already exists."
    except Exception as e:
        return f"An error occurred: {e}"
    