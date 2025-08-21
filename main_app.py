import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from tkcalendar import DateEntry
import calendar

# Import our backend components
import database_manager
import logic_manager

class AttendanceApp(tk.Tk):
    Time_In = "Time In"
    Time_Out = "Time Out"
    def __init__(self):
        super().__init__()

        self.title("Attendance Logger")
        window_width = 1000
        window_height = 700
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        center_x = int((screen_width / 2) - (window_width / 2))
        center_y = int((screen_height / 2) - (window_height / 2))
        
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Create a Notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Create tabs
        self.tab_attendance = ttk.Frame(self.notebook)
        self.tab_salary = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook)
        self.tab_edit = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_attendance, text="Attendance")
        self.notebook.add(self.tab_salary, text="Salary Report")
        self.notebook.add(self.tab_settings, text="Settings")
        self.notebook.add(self.tab_edit, text="Edit Logs")

        # Bind the window close event to our custom handler
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Initialize the database on startup
        database_manager.initialize_database()

        # Handle the automatic IN log on startup
        self.after(100, self.handle_startup_log)

        # Initialize the UI components for each tab
        self.setup_attendance_tab()
        self.setup_salary_tab()
        self.setup_settings_tab()
        self.setup_edit_logs_tab()
        
    def _create_time_list(self):
        """Generates a list of times in 15-minute increments."""
        times = []
        for hour in range(24):
            for minute in range(0, 60, 15):
                times.append(f"{hour:02d}:{minute:02d}")
        return times
    def handle_startup_log(self):
        """Called after GUI is ready to perform the automatic IN log."""
        message = logic_manager.handle_app_startup_in_log()
        self.update_attendance_status()
        self.update_history_tree()
        messagebox.showinfo("Auto Log", message)
        
    def on_close(self):
        """
        Custom handler for when the user closes the window.
        Logs the OUT time if an IN time exists for today.
        """
        today_record = logic_manager.get_today_attendance_status()
        if today_record and today_record['time_in'] and today_record['time_out'] is None:
            # Only log OUT if there's an IN time and no OUT time yet
            message = logic_manager.record_manual_out()
            messagebox.showinfo("Log Out", message)
        
        self.destroy() # Close the application

    def setup_attendance_tab(self):
        """Sets up the UI for the Attendance tab."""
        # --- UI for Attendance Status ---
        status_frame = ttk.Frame(self.tab_attendance)
        status_frame.pack(pady=10)

        ttk.Label(status_frame, text="Today's Attendance Status:", font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(status_frame, text="Fetching...", font=("Arial", 14), foreground="blue")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # --- UI for Log In/Out buttons ---
        button_frame = ttk.Frame(self.tab_attendance)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Log IN (Manual)", command=self.manual_in).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Log OUT (Manual)", command=self.manual_out).pack(side=tk.LEFT, padx=10)

        # --- UI for Attendance History ---
        history_frame = ttk.Frame(self.tab_attendance)
        history_frame.pack(expand=True, fill="both", padx=10, pady=10)

        ttk.Label(history_frame, text="Attendance History:", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Create a Treeview for history display
        columns = ("Date", self.Time_In, self.Time_Out)
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        self.history_tree.pack(side=tk.LEFT,expand=True, fill="both")

        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, anchor=tk.CENTER)

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.update_attendance_status()
        self.update_history_tree()

    def setup_salary_tab(self):
        """Sets up the UI for the Salary Report tab."""
        # Main frame for salary report
        report_frame = ttk.Frame(self.tab_salary, padding="10")
        report_frame.pack(fill="both", expand=True)
        
        # Controls for selecting report period
        period_control_frame = ttk.Frame(report_frame)
        period_control_frame.pack(pady=5)
        
        ttk.Label(period_control_frame, text="Select Report Month:").pack(side=tk.LEFT, padx=5)
        
        self.months = [datetime.date(2000, i, 1).strftime('%B') for i in range(1, 13)]
        self.month_combo = ttk.Combobox(period_control_frame, values=self.months, state="readonly", width=12)
        self.month_combo.set(datetime.date.today().strftime('%B'))
        self.month_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(period_control_frame, text="Year:").pack(side=tk.LEFT, padx=5)
        
        current_year = datetime.date.today().year
        self.years = list(range(current_year - 5, current_year + 2))
        self.year_combo = ttk.Combobox(period_control_frame, values=[str(year) for year in self.years], state="readonly", width=8)
        self.year_combo.set(current_year)
        self.year_combo.pack(side=tk.LEFT, padx=5)

        self.calculate_button = ttk.Button(period_control_frame, text="Calculate", command=self.calculate_and_show_salary)
        self.calculate_button.pack(side=tk.LEFT, padx=10)
        
        # The new "Today" button
        today_button_frame = ttk.Frame(report_frame)
        today_button_frame.pack(pady=5)
        self.today_button = ttk.Button(today_button_frame, text="Today", command=self.calculate_and_show_salary_till_today)
        self.today_button.pack()
        

        # --- Report Summary ---
        summary_frame = ttk.LabelFrame(report_frame, text="Salary Summary", padding="10")
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        text_scroll_frame = ttk.Frame(summary_frame)
        text_scroll_frame.pack(fill="both", expand=True)
        
        self.summary_text = tk.Text(text_scroll_frame, height=10, state='disabled', wrap='word')
        self.summary_text.pack(side=tk.LEFT,fill="both", expand=True)

        # Create a scrollbar and link it to the Text widget
        scrollbar_s = ttk.Scrollbar(text_scroll_frame, orient="vertical", command=self.summary_text.yview)
        scrollbar_s.pack(side=tk.RIGHT, fill=tk.Y)
        self.summary_text.config(yscrollcommand=scrollbar_s.set)
        
       # --- Report Details ---
        details_frame = ttk.LabelFrame(report_frame, text="Daily Breakdown", padding="10")
        details_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Date", "Status", self.Time_In, self.Time_Out, "Daily Pay", "Penalty Reason")

# Create a frame to hold the treeview and the scrollbar side-by-side
        tree_scroll_frame = ttk.Frame(details_frame)
        tree_scroll_frame.pack(fill="both", expand=True)

        self.details_tree = ttk.Treeview(tree_scroll_frame, columns=columns, show="headings")
        self.details_tree.pack(side=tk.LEFT, fill="both", expand=True)

# Configure treeview columns
        for col in columns:
            self.details_tree.heading(col, text=col)
            self.details_tree.column(col, anchor=tk.CENTER, width=100)

        self.details_tree.column("Status", width=150)
        self.details_tree.column("Penalty Reason", width=200)


        scrollbar_s = ttk.Scrollbar(tree_scroll_frame, orient="vertical", command=self.details_tree.yview)
        scrollbar_s.pack(side=tk.RIGHT, fill=tk.Y)
        self.details_tree.configure(yscrollcommand=scrollbar_s.set)

        
    def calculate_and_show_salary_till_today(self):
        """
        Calculates the salary for the current month up to today and displays the report.
        This is a convenience method for quick calculations without needing to select month/year.
        """
        # Clear previous report
        self.summary_text.config(state='normal')
        self.summary_text.delete('1.0', tk.END)
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)
            
        report = logic_manager.calculate_monthly_salary()
         # Populate summary text
        summary_text = f"Total Salary Until Today: PKR {report['total_salary_until_today']:.2f}\n"
        summary_text += f"Gross Salary (without deductions): PKR {report['gross_salary']:.2f}\n\n"
        
        if "Please set" in report['summary']:
            messagebox.showwarning("Settings Missing", "Please ensure Fixed Monthly Salary and Hourly Rate are set in the Settings tab.")

        summary_text += report['summary']
        
        self.summary_text.insert(tk.END, summary_text)
        self.summary_text.config(state='disabled')

        # Populate daily breakdown Treeview
        for day in report['details']:
            self.details_tree.insert("", tk.END, values=(
                day['date'],
                day['status'],
                day['in'],
                day['out'],
                day['daily_pay_contribution'],
                day['penalty_reason']
            ))
        
    def calculate_and_show_salary(self):
        """
        Calculates the monthly salary and displays the report on the Salary tab.
        """
        # Clear previous report
        self.summary_text.config(state='normal')
        self.summary_text.delete('1.0', tk.END)
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)

        # Get selected month and year from comboboxes
        try:
            selected_month_name = self.month_combo.get()
            selected_year = int(self.year_combo.get())
            selected_month = self.months.index(selected_month_name) + 1
            print(f"Calculating salary for {selected_month_name} {selected_year}")
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Please select a valid month and year.")
            return

        # Call the logic manager with the selected period
        report = logic_manager.calculate_monthly_salary(report_month=selected_month, report_year=selected_year)
        
        # Populate summary text
        summary_text = f"Total Calculated Salary: PKR {report['total_salary']:.2f}\n"
        summary_text += f"Gross Salary (without deductions): PKR {report['gross_salary']:.2f}\n\n"
        
        if "Please set" in report['summary']:
            messagebox.showwarning("Settings Missing", "Please ensure Fixed Monthly Salary and Hourly Rate are set in the Settings tab.")

        summary_text += report['summary']
        
        self.summary_text.insert(tk.END, summary_text)
        self.summary_text.config(state='disabled')

        # Populate daily breakdown Treeview
        for day in report['details']:
            self.details_tree.insert("", tk.END, values=(
                day['date'],
                day['status'],
                day['in'],
                day['out'],
                day['daily_pay_contribution'],
                day['penalty_reason']
            ))

    def setup_settings_tab(self):
        """Sets up the UI for the Settings tab."""
        # Main frame for settings
        settings_frame = ttk.Frame(self.tab_settings, padding="10")
        settings_frame.pack(fill="both", expand=True)

        # --- Settings for Salary and Month Period ---
        config_frame = ttk.LabelFrame(settings_frame, text="General Settings", padding="10")
        config_frame.pack(fill="x", padx=10, pady=10)

        self.salary_label = ttk.Label(config_frame, text="Fixed Monthly Salary:", width=20)
        self.salary_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.salary_entry = ttk.Entry(config_frame)
        self.salary_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.rate_label = ttk.Label(config_frame, text="Hourly Rate:", width=20)
        self.rate_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.rate_entry = ttk.Entry(config_frame)
        self.rate_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.month_start_label = ttk.Label(config_frame, text="Month Start Day:", width=20)
        self.month_start_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.month_start_entry = ttk.Entry(config_frame)
        self.month_start_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.month_end_label = ttk.Label(config_frame, text="Month End Day:", width=20)
        self.month_end_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.month_end_entry = ttk.Entry(config_frame)
        self.month_end_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Button(config_frame, text="Update Settings", command=self.update_settings).grid(row=4, column=0, columnspan=2, pady=10)

        # --- Holidays Management ---
        holidays_frame = ttk.LabelFrame(settings_frame, text="Public Holidays", padding="10")
        holidays_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame for holiday input fields and buttons
        holiday_input_frame = ttk.Frame(holidays_frame)
        holiday_input_frame.pack(fill="x", pady=5)
        
        ttk.Label(holiday_input_frame, text="Date (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)
        
        self.holiday_date_entry = DateEntry(
        holiday_input_frame,
        width=15,
        background='darkblue',
        foreground='white',
        borderwidth=2,
        date_pattern='yyyy-mm-dd'
        )
        
        self.holiday_date_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(holiday_input_frame, text="Description:").pack(side=tk.LEFT, padx=5)
        self.holiday_desc_entry = ttk.Entry(holiday_input_frame)
        self.holiday_desc_entry.pack(side=tk.LEFT, padx=5, expand=True, fill="x")

        ttk.Button(holiday_input_frame, text="Add Holiday", command=self.add_holiday).pack(side=tk.LEFT, padx=5)

        # Treeview to display holidays
        columns = ("Date", "Description")
        self.holiday_tree = ttk.Treeview(holidays_frame, columns=columns, show="headings")
        self.holiday_tree.pack(expand=True, fill="both")

        for col in columns:
            self.holiday_tree.heading(col, text=col)
            self.holiday_tree.column(col, anchor=tk.CENTER)

        # Add a scrollbar
        scrollbar_h = ttk.Scrollbar(holidays_frame, orient="vertical", command=self.holiday_tree.yview)
        self.holiday_tree.configure(yscrollcommand=scrollbar_h.set)
        scrollbar_h.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Delete button for holidays
        delete_holiday_button = ttk.Button(holidays_frame, text="Delete Selected Holiday", command=self.delete_holiday)
        delete_holiday_button.pack(pady=5)
        
        self.load_settings()
        self.load_holidays()

    def setup_edit_logs_tab(self):
        """Sets up the UI for the Edit Logs tab."""
        edit_logs_frame = ttk.Frame(self.tab_edit, padding="10")
        edit_logs_frame.pack(fill="both", expand=True)
        
        # --- NEW: Date Range Filter Controls ---
        filter_frame = ttk.Frame(edit_logs_frame)
        filter_frame.pack(fill="x", pady=5)
        
        ttk.Label(filter_frame, text="Start Date:").pack(side=tk.LEFT, padx=5)
        self.log_start_date_var = DateEntry(filter_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.log_start_date_var.pack(side=tk.LEFT, padx=5)
        
        
        ttk.Label(filter_frame, text="End Date:").pack(side=tk.LEFT, padx=5)
        self.log_end_date_var = DateEntry(filter_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.log_end_date_var.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = ttk.Button(filter_frame, text="Refresh Logs", command=self.populate_logs_treeview)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Controls for editing logs
        controls_frame = ttk.Frame(edit_logs_frame)
        controls_frame.pack(fill="x", pady=5)
        
        ttk.Label(controls_frame, text="Date:").pack(side=tk.LEFT, padx=5)
        self.edit_date_var = DateEntry(controls_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.edit_date_var.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(controls_frame, text="Time In:").pack(side=tk.LEFT, padx=5)
        self.edit_time_in_var = tk.StringVar()
        self.edit_time_in_combo = ttk.Combobox(controls_frame, textvariable=self.edit_time_in_var, width=8, state="readonly")
        self.edit_time_in_combo['values'] = self._create_time_list()
        self.edit_time_in_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(controls_frame, text="Time Out:").pack(side=tk.LEFT, padx=5)
        self.edit_time_out_var = tk.StringVar()
        self.edit_time_out_combo = ttk.Combobox(controls_frame, textvariable=self.edit_time_out_var, width=8, state="readonly")
        self.edit_time_out_combo['values'] = self._create_time_list()
        self.edit_time_out_combo.pack(side=tk.LEFT, padx=5)
        
        self.edit_button = ttk.Button(controls_frame, text="Update Log", command=self.update_log_entry)
        self.edit_button.pack(side=tk.LEFT, padx=5)
        
        self.add_button = ttk.Button(controls_frame, text="Add New Log", command=self.add_log_entry_ui)
        self.add_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(controls_frame, text="Delete Selected", command=self.delete_log_entry)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # Treeview to display logs
        columns = ("Date", self.Time_In, self.Time_Out)
        self.logs_treeview = ttk.Treeview(edit_logs_frame, columns=columns, show="headings", selectmode="extended")
        self.logs_treeview.pack(fill="both", expand=True, pady=10)
        
        for col in columns:
            self.logs_treeview.heading(col, text=col)
            self.logs_treeview.column(col, anchor=tk.CENTER, width=150)

        # Bind a click event to the Treeview to load selected log into entry fields
        self.logs_treeview.bind("<<TreeviewSelect>>", self.on_log_select)
        
        # Set default values for the date range
        today = datetime.date.today()
        # Set to the start of the current month
        self.log_start_date_var.set_date(today.replace(day=1))
        # Set to the current date
        self.log_end_date_var.set_date(today)
        # Populate the treeview on startup
        self.populate_logs_treeview()

    def add_log_entry_ui(self):
        """Adds a new log entry based on the values in the entry fields."""
        date = self.edit_date_var.get()
        time_in = self.edit_time_in_var.get()
        time_out = self.edit_time_out_var.get()
        
        if not all([date, time_in, time_out]):
            messagebox.showwarning("Incomplete Data", "All fields (Date, Time In, Time Out) must be filled to add a new log.")
            return
            
        result = logic_manager.add_log_entry(date, time_in, time_out)
        messagebox.showinfo("Add Status", result)
        
        # Refresh the UI and clear the fields
        self.populate_logs_treeview()
        self.edit_date_var.delete(0, tk.END)
        self.edit_time_in_var.set("")
        self.edit_time_out_var.set("")
        
    def populate_logs_treeview(self):
        """Fetches and populates the logs Treeview based on the specified date range."""
        for item in self.logs_treeview.get_children():
            self.logs_treeview.delete(item)
            
        start_date_str = self.log_start_date_var.get()
        end_date_str = self.log_end_date_var.get()

        # Simple date validation
        try:
            datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
            datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            messagebox.showwarning("Invalid Date Format", "Please use YYYY-MM-DD format for dates.")
            return

        logs = database_manager.get_attendance_logs_in_range_for_editTab(start_date_str, end_date_str)
        for log in logs:
            self.logs_treeview.insert("", tk.END, values=(log['date'], log['time_in'], log['time_out']))
        
        
    def delete_log_entry(self):
        """Deletes the selected log entries."""
        selected_items = self.logs_treeview.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select at least one log to delete.")
            return

        confirmation_message = f"Are you sure you want to delete {len(selected_items)} selected log(s)?"
        if messagebox.askyesno("Confirm Deletion", confirmation_message):
            dates_to_delete = []
            for item in selected_items:
                date = self.logs_treeview.item(item, 'values')[0]
                dates_to_delete.append(date)

            for date in dates_to_delete:
                logic_manager.delete_log_entry(date)
            
            messagebox.showinfo("Delete Status", f"{len(selected_items)} log(s) deleted successfully.")
            
            # Refresh the Treeview and the Salary Report
            self.populate_logs_treeview()
            self.calculate_and_show_salary()


    def on_log_select(self, event):
        """Loads the selected log's data into the entry fields."""
        selected_item = self.logs_treeview.focus()
        if selected_item:
            values = self.logs_treeview.item(selected_item, 'values')
            self.edit_date_var.set_date(values[0])
            self.edit_time_in_var.set(values[1])
            self.edit_time_out_var.set(values[2])
        else:
            self.edit_date_var.delete(0, tk.END)
            self.edit_time_in_var.set("")
            self.edit_time_out_var.set("")


    def update_log_entry(self):
        """Updates the selected log entry with new values."""
        date = self.edit_date_var.get()
        time_in = self.edit_time_in_var.get()
        time_out = self.edit_time_out_var.get()
        
        if not all([date, time_in, time_out]):
            messagebox.showwarning("Incomplete Data", "Date, Time In, and Time Out must all be filled.")
            return

        result = logic_manager.update_log_entry(date, time_in, time_out)
        messagebox.showinfo("Update Status", result)
        self.populate_logs_treeview()
        self.calculate_and_show_salary() # Recalculate salary to reflect changes


    def update_attendance_status(self):
        """Updates the status label on the Attendance tab."""
        record = logic_manager.get_today_attendance_status()
        if record:
            if record['time_out']:
                self.status_label.config(text=f"Logged OUT at {record['time_out']}", foreground="red")
            else:
                self.status_label.config(text=f"Logged IN at {record['time_in']}", foreground="green")
        else:
            self.status_label.config(text="Not Logged IN today", foreground="black")

    def update_history_tree(self):
        """Fetches recent history and populates the Treeview."""
        # Clear existing entries
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # Get records from the logic manager and insert into the Treeview
        history = logic_manager.get_recent_attendance_history(days=30)
        for record in history:
            self.history_tree.insert("", tk.END, values=(record['date'], record['time_in'], record['time_out'] if record['time_out'] else 'N/A'))

    def manual_in(self):
        """Handles manual IN button click."""
        message = logic_manager.record_manual_in()
        messagebox.showinfo("Manual Log In", message)
        self.update_attendance_status()
        self.update_history_tree()

    def manual_out(self):
        """Handles manual OUT button click."""
        message = logic_manager.record_manual_out()
        messagebox.showinfo("Manual Log Out", message)
        self.update_attendance_status()
        self.update_history_tree()
        
    def load_settings(self):
        """Loads settings from the database and populates the entry fields."""
        self.salary_entry.delete(0, tk.END)
        self.salary_entry.insert(0, database_manager.get_setting('fixed_monthly_salary'))
        self.rate_entry.delete(0, tk.END)
        self.rate_entry.insert(0, database_manager.get_setting('hourly_rate'))
        self.month_start_entry.delete(0, tk.END)
        self.month_start_entry.insert(0, database_manager.get_setting('month_start_day'))
        self.month_end_entry.delete(0, tk.END)
        self.month_end_entry.insert(0, database_manager.get_setting('month_end_day'))

    def update_settings(self):
        """Saves the settings from the entry fields to the database."""
        try:
            # Basic validation
            fixed_salary = float(self.salary_entry.get())
            hourly_rate = float(self.rate_entry.get())
            month_start = int(self.month_start_entry.get())
            month_end = int(self.month_end_entry.get())
            if not (1 <= month_start <= 31 and 1 <= month_end <= 31):
                 messagebox.showerror("Error", "Month start/end day must be between 1 and 31.")
                 return
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for settings.")
            return

        database_manager.update_setting('fixed_monthly_salary', str(fixed_salary))
        database_manager.update_setting('hourly_rate', str(hourly_rate))
        database_manager.update_setting('month_start_day', str(month_start))
        database_manager.update_setting('month_end_day', str(month_end))
        messagebox.showinfo("Success", "Settings updated successfully!")

    def load_holidays(self):
        """Loads holidays from the database and populates the Treeview."""
        # Clear existing entries
        for item in self.holiday_tree.get_children():
            self.holiday_tree.delete(item)

        # Get all holidays for the next year (to cover any period)
        today = datetime.date.today()
        first_day = today.replace(day=1)
        last_day = datetime.date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        holidays = database_manager.get_holidays_in_range(first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d'))
        
        for h in holidays:
            self.holiday_tree.insert("", tk.END, values=(h['holiday_date'], h['description']))
            
    def add_holiday(self):
        """Adds a new holiday to the database."""
        holiday_date = self.holiday_date_entry.get_date().strftime('%Y-%m-%d')
        description = self.holiday_desc_entry.get()
        
        if not holiday_date:
            messagebox.showerror("Error", "Please enter a date for the holiday.")
            return
        
        # Basic date validation
        try:
            datetime.datetime.strptime(holiday_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD.")
            return

        success = database_manager.insert_holiday(holiday_date, description)
        if success:
            messagebox.showinfo("Success", "Holiday added successfully!")
            self.holiday_date_entry.delete(0, tk.END)
            self.holiday_desc_entry.delete(0, tk.END)
            self.load_holidays() # Refresh the treeview
        else:
            messagebox.showerror("Error", "Holiday for this date already exists.")
            
    def delete_holiday(self):
        """Deletes the selected holiday from the database."""
        selected_items = self.holiday_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a holiday to delete.")
            return

        selected_item = selected_items[0]  # ✅ Extract the first item ID (str)
        selected_date = self.holiday_tree.item(selected_item)['values'][0]

        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the holiday on {selected_date}?"):
            database_manager.delete_holiday(selected_date)
            messagebox.showinfo("Success", "Holiday deleted successfully.")
            self.load_holidays()  # Refresh the treeview


if __name__ == "__main__":
    app = AttendanceApp()
    app.mainloop()