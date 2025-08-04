import database_manager
import datetime

# --- Helper Functions for Dates and Times ---

def get_current_date_str():
    """Returns today's date in YYYY-MM-DD string format."""
    return datetime.date.today().strftime('%Y-%m-%d')

def get_current_time_str():
    """Returns the current time in HH:MM:SS string format."""
    return datetime.datetime.now().strftime('%H:%M:%S')

def get_start_end_dates_for_period(today_date_obj=None):
    """
    Calculates the start and end dates (YYYY-MM-DD strings) for the current
    attendance period based on configured month_start_day and month_end_day.
    Uses the 28th to 27th rollover logic.
    """
    if today_date_obj is None:
        today_date_obj = datetime.date.today()

    # Get settings from database, convert to int, use defaults if None
    month_start_day_raw = database_manager.get_setting('month_start_day')
    month_end_day_raw = database_manager.get_setting('month_end_day')
    month_start_day = int(month_start_day_raw) if month_start_day_raw is not None else 28
    month_end_day = int(month_end_day_raw) if month_end_day_raw is not None else 27

    # Determine the correct period based on the current day
    if today_date_obj.day >= month_start_day:
        # If today is on or after the start day, period is current month's start to next month's end
        start_date_obj = today_date_obj.replace(day=month_start_day)
        # To get next month's end day, go to start of next month, add 1 month, subtract 1 day
        # Or, simpler: go to next month, then set to end_day
        # Let's calculate next month's date and then replace day
        next_month = today_date_obj.replace(day=1) + datetime.timedelta(days=32) # Go to next month
        end_date_obj = next_month.replace(day=month_end_day)
    else:
        # If today is before the start day, period is previous month's start to current month's end
        end_date_obj = today_date_obj.replace(day=month_end_day)
        # To get previous month's start day, go to start of current month, subtract 1 day, then set to start_day
        previous_month = today_date_obj.replace(day=1) - datetime.timedelta(days=1) # Go to previous month
        start_date_obj = previous_month.replace(day=month_start_day)

    return start_date_obj.strftime('%Y-%m-%d'), end_date_obj.strftime('%Y-%m-%d')

def get_total_hours_worked(time_in_str, time_out_str):
    """
    Calculates the total hours worked given 'In' and 'Out' time strings.
    Handles overnight shifts (time_out_str < time_in_str).
    Returns hours as a float.
    """
    if not time_in_str or not time_out_str:
        return 0.0

    FMT = '%H:%M:%S'
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
    FMT = '%H:%M:%S'
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


def calculate_monthly_salary():
    """
    Calculates the total monthly salary for the current attendance period
    based on all defined rules.
    """
    start_date_str, end_date_str = get_start_end_dates_for_period()

    # Fetch settings
    fixed_monthly_salary_str = database_manager.get_setting('fixed_monthly_salary')
    hourly_rate_str = database_manager.get_setting('hourly_rate')

    fixed_monthly_salary = float(fixed_monthly_salary_str) if fixed_monthly_salary_str is not None else 0.0
    hourly_rate = float(hourly_rate_str) if hourly_rate_str is not None else 0.0

    if fixed_monthly_salary == 0 or hourly_rate == 0:
        return {
            "total_salary": 0.0,
            "details": [],
            "summary": "Please set Fixed Monthly Salary and Hourly Rate in settings."
        }

    fixed_salary_per_day = fixed_monthly_salary / 30.0

    # Fetch all logs and holidays for the period
    all_logs = {log['date']: log for log in database_manager.get_attendance_logs_in_range(start_date_str, end_date_str)}
    all_holidays = {h['holiday_date']: h['description'] for h in database_manager.get_holidays_in_range(start_date_str, end_date_str)}

    total_calculated_salary = 0.0
    daily_breakdown = []
    
    late_count = 0
    late_deduction_total = 0.0
    actual_working_saturdays = 0
    saturday_holiday = 0
    
    current_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        log_entry = all_logs.get(date_str)
        day_status = "Working Day"
        daily_contribution = 0.0
        late_reason = ""
        is_late_instance = False
        
        # Rule 1 & 3: Sundays and Public Holidays are paid days off
        if is_weekend(current_date):
            if current_date.weekday() == 6: # Sunday
                day_status = "Paid Day Off (Sunday)"
                daily_contribution = fixed_salary_per_day
            elif current_date.weekday() == 5: # Saturday - check Rule 2 later
                if log_entry and log_entry['time_in']:
                    daily_contribution, is_late_instance, late_reason = \
                    get_daily_pay_and_penalties(log_entry, fixed_salary_per_day, hourly_rate)
                    day_status = "Working Saturday"
                    actual_working_saturdays += 1 # Count this as a worked Saturday
                    if is_late_instance:
                        late_count += 1
                else:
                    day_status = "Unlogged Saturday (Pending Rule 2)"
                    daily_contribution = 0.0 # Will be adjusted if it's one of the 2 paid Saturdays    
        
        if is_public_holiday(date_str) and day_status != "Paid Day Off (Sunday)": # Ensure holiday takes precedence unless it's a Sunday
            day_status = f"Paid Day Off (Public Holiday: {all_holidays[date_str]})"
            if current_date.weekday() == 5: # Saturday
                saturday_holiday = 1 # Count this as a holiday Saturday
                day_status = "Holiday Saturday"
        
            daily_contribution = fixed_salary_per_day

        if day_status == "Working Day": # Only apply specific attendance rules for actual working days
            daily_contribution, is_late_instance, late_reason = \
                get_daily_pay_and_penalties(log_entry, fixed_salary_per_day, hourly_rate)
            
            if is_late_instance:
                late_count += 1
            
            # If no IN time, and not a special paid day off (weekend/holiday), it's a missed day
            if not log_entry or not log_entry['time_in']:
                day_status = "Absent"
            elif "Half Day" in late_reason:
                day_status = "Half Day"
            elif "Late" in late_reason:
                day_status = "Working Day (Late)"
            else:
                day_status = "Working Day (On Time)"
            
        
        total_calculated_salary += daily_contribution

        daily_breakdown.append({
            "date": date_str,
            "status": day_status,
            "in": log_entry['time_in'] if log_entry else 'N/A',
            "out": log_entry['time_out'] if log_entry else 'N/A',
            "daily_pay_contribution": round(daily_contribution, 2),
            "penalty_reason": late_reason
        })
        current_date += datetime.timedelta(days=1)

    # --- Apply Post-Iteration Rules ---

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
    one_paid_day_off_applied = False
    for i, day_info in enumerate(daily_breakdown):
        # A candidate is an "Absent" day that is NOT a weekend and NOT a public holiday
        
        if day_info['status'] == "Absent" and not is_weekend(datetime.datetime.strptime(day_info['date'], '%Y-%m-%d').date()) \
           and not is_public_holiday(day_info['date']) and not one_paid_day_off_applied:
            
            # Re-add the daily pay that was initially set to 0.0 for this absent day
            total_calculated_salary += fixed_salary_per_day
            daily_breakdown[i]['status'] = "Paid Day Off (Auto Granted)"
            daily_breakdown[i]['penalty_reason'] = "" # Clear previous absent reason
            daily_breakdown[i]['daily_pay_contribution'] = round(fixed_salary_per_day, 2)
            one_paid_day_off_applied = True
            break # Only grant one such day
        
    saturday_deduction = 0.0
    saturday_reason = ""
    if actual_working_saturdays < 2 and saturday_holiday == 0 and one_paid_day_off_applied:
        missed_saturdays_for_deduction = 2 - actual_working_saturdays
        saturday_deduction = missed_saturdays_for_deduction * fixed_salary_per_day
        total_calculated_salary -= saturday_deduction
        saturday_reason = f"Deducted for {missed_saturdays_for_deduction} unlogged Saturday(s) (Expected 2 worked)"
    else:
        one_paid_day_off_applied = True
        total_calculated_salary += fixed_salary_per_day
    

    summary = f"Salary calculated for period: {start_date_str} to {end_date_str}\n"
    summary += f"Total Late Instances: {late_count} ({late_deductions_count} day(s) cut, PKR {late_deduction_total:.2f})\n"
    summary += f"Saturdays Worked (not holidays): {actual_working_saturdays} {saturday_reason}\n"
    if one_paid_day_off_applied:
        summary += "One auto-granted paid day off applied.\n"

    return {
        "total_salary": round(total_calculated_salary, 2),
        "details": daily_breakdown,
        "summary": summary,
        "period_start": start_date_str,
        "period_end": end_date_str
    }


# --- Testing Block (only runs when logic_manager.py is executed directly) ---
if __name__ == "__main__":
    import os
    # Ensure database is initialized for testing logic
    if os.path.exists(database_manager.DB_NAME):
        os.remove(database_manager.DB_NAME)
        print(f"Removed existing {database_manager.DB_NAME} for a fresh start.")
    database_manager.initialize_database()

    print("--- Testing Salary Calculation Logic ---")

    # Set up test settings
    database_manager.update_setting('fixed_monthly_salary', '60000') # PKR 60,000 / 30 = 2000 per day
    database_manager.update_setting('hourly_rate', '250') # PKR 250 per hour
    database_manager.update_setting('month_start_day', '28')
    database_manager.update_setting('month_end_day', '27')

    # Example: Start a new period for calculations (e.g., current date is Aug 4, 2025)
    # The period would be from 2025-07-28 to 2025-08-27
    test_period_start = datetime.date(2025, 7, 28)
    test_period_end = datetime.date(2025, 8, 27)

    #Insert working days (Mon-Fri) with 6 late entries
    late_dates = ['2025-07-28', '2025-07-30', '2025-08-01', '2025-08-05', '2025-08-07', '2025-08-08']
    normal_time = '09:00:00'
    late_time = '10:30:00'
    out_time = '17:00:00'

    curr = test_period_start
    while curr <= test_period_end:
        if curr.weekday() < 5:  # Mon–Fri
            in_time = late_time if curr.strftime('%Y-%m-%d') in late_dates else normal_time
            date_str = curr.strftime('%Y-%m-%d')
            database_manager.insert_attendance_log(date_str, in_time)
            database_manager.update_attendance_log_out_time(date_str, out_time)
        curr += datetime.timedelta(days=1)

    # Work only 1 Saturday: e.g., August 3, 2025 is a Saturday
    database_manager.insert_attendance_log('2025-08-02', '09:00:00')  # Saturday worked
    database_manager.update_attendance_log_out_time('2025-08-02', '13:00:00')

    # Insert a public holiday (to make sure holiday logic doesn't interfere)
    database_manager.insert_holiday('2025-08-14', 'Independence Day')

    # Run salary calculation
    salary_report = calculate_monthly_salary()

    # Output
    print("\n--- Salary Report ---")
    print(salary_report['summary'])
    print(f"Total Calculated Salary: PKR {salary_report['total_salary']:.2f}\n")

    print("--- Daily Breakdown ---")
    for day in salary_report['details']:
        print(f"{day['date']} | Status: {day['status']:<30} | In: {day['in']:<8} | Out: {day['out']:<8} | Pay: {day['daily_pay_contribution']:.2f} | Penalty: {day['penalty_reason']}")