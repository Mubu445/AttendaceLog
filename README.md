# 🕒 Attendance & Payroll System

A smart, user-friendly **desktop application** built with **Python and Tkinter** for managing daily attendance, salary reports, and holiday tracking. Designed for personal or small-team use, it automatically logs working hours and calculates salary based on customizable settings.

---

## ✨ Key Features

- ✅ **Automatic Time Logging**
  - Logs **Time In** when you open the app and **Time Out** when you close it.
  - Ensures accurate daily attendance with no manual effort.

- 📝 **Manual Log Management**
  - Edit or add logs from any date using the calendar and dropdown menus.
  - Fix errors or missed entries effortlessly via the **Edit Logs** tab.

- 🧮 **Dynamic Salary Reports**
  - Calculate salary for any period or until today.
  - Shows gross, penalties (lateness/absence), and net salary breakdown.

- ⚙️ **Customizable Settings**
  - Set your **monthly salary**, **hourly rate**, and **month boundaries**.
  - Configure work hours and other preferences.

- 📅 **Holiday Management**
  - Add/delete public holidays to exclude them from salary calculations.
  - Prevents false deductions on non-working days.

---

## 🚀 Getting Started

### ✅ Prerequisites

- Python **3.13.0** or higher
- `tkcalendar` library (used for calendar widgets)

### 📦 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Mubu445/AttendaceLog.git
   cd AttendaceLog
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Running the App

To launch the application:

```bash
python main_app.py
```

The GUI will open and automatically log your **Time In** for the day if not already logged.

---

## 🔁 Make App Start Automatically (for Auto Time In)

For **Time In to be logged automatically**, the application must start automatically when your system boots.

### 🪟 How to Set Up on Windows (for Auto Time In)

1.  **Create a simple batch file:**

      * Open a text editor (like Notepad).
      * Paste the following two lines into the file, making sure to replace the path with the actual location of your `main_app.py` file:
        ```bat
        @echo off
        python "C:\Users\YourPath\AttendaceLog\main_app.py"
        ```
      * Save this file as **`run_attendance.bat`** in a convenient place (e.g., in your project folder).

2.  **Place a shortcut in the Startup folder:**

      * Press `Win + R`, type `shell:startup`, and hit **Enter**. This opens the **Startup** folder.
      * Right-click the `run_attendance.bat` file you just created and select **Create shortcut**.
      * Drag and drop this new shortcut into the **Startup** folder.

3.  Restart your system. The app will now run on startup, automatically logging your **Time In**.
---

## 📝 Usage Guide

### 🕐 1. Automatic Logging

* **Time In:** Logged automatically on app launch.
* **Time Out:** Logged automatically when the app is closed.
* **Re-opening the App:** Clears the earlier Time Out for the same day and logs a new one on exit.

### ✍️ 2. Manual Log Management

Located in the **Edit Logs** tab:

* **Add New Log:** Select a date, time in/out, then click **Add New Log**.
* **Update Log:** Select from the table → edit → click **Update Log**.
* **Delete Log:** Select one or more logs → click **Delete Selected**.

### 💰 3. Salary Report

* Choose a **month & year** and click **Calculate** to view:

  * Total working days
  * Deductions (lateness, absence)
  * Net earnings
* Use **"Today"** to calculate salary from the month start to the current day.

### ⚙️ 4. Settings Tab

* Set your:

  * **Monthly Salary**
  * **Hourly Rate**
  * **Working Hours Per Day**
  * **Month Start & End Day**
* These settings control how salary and deductions are calculated.

### 🎉 5. Holiday Tab

* Mark public holidays to:

  * Exclude them from working days.
  * Prevent unfair deductions.

---

## ⚠️ Rules for Lateness & Absence

> **Current Behaviour:**
> Lateness, early leave, and absence are evaluated using predefined rules matching the my job:

* Late if **Time In is after 09:15 AM**
* One Hour cut based in hourly rate if Time in is after 10:00 AM
* Half Day if Time In After 12 pm
* One Day Salary cut if three Late 
* Absence if **no log is recorded**
* Penalties based on:

  * Hourly rate
  * Missed hours
  * Configured daily work hours


---

## 📁 Project Structure

```
attendance-app/
├── main_app.py            # Main Tkinter GUI application
├── logic_manager.py       # Business logic for calculations, salary, etc.
├── database_manager.py    # SQLite data layer
├── requirements.txt       # Required Python packages
├── README.md              # Project documentation
└── attendance.db          # SQLite database file (generated)
```
---

## 📜 License

This project is licensed under the MIT License. Feel free to use and extend it.

---

## 👨‍💻 Author

Made with ❤️ by **[Mubu445](https://github.com/Mubu445)**
Contributions, issues, and suggestions are welcome!

```
