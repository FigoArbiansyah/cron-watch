# CronWatch (Odoo 17)

![Odoo Version](https://img.shields.io/badge/Odoo-17.0-blue.svg)
![License](https://img.shields.io/badge/License-LGPL--3-green.svg)

**CronWatch** is a powerful utility module for Odoo 17 designed to provide deep visibility into the execution history of your Scheduled Actions (`ir.cron`). It helps administrators monitor performance, identify silent failures, and debug complex backend processes with ease.

---

## 🚀 Key Features

### 1. Granular Execution Tracking
Enable or disable tracking on a per-job basis. Only track the actions that matter to you to keep your database lean.

### 2. Performance Monitoring
*   **Start & End Time**: Precise recording of when a job started and finished.
*   **Duration Calculation**: Automatically calculates the execution time.
*   **Average Duration**: View the average runtime of a job over time to identify performance degradation.

### 3. Error Analysis & Debugging
*   **Full Traceback Capture**: If a job fails, the module captures the complete Python traceback.
*   **Failure Notifications**: Visual badges and banners highlight failed runs.
*   **Error Summary**: Quick overview of the error message without opening technical logs.

### 4. Smart Dashboards
*   **Smart Buttons**: Integrated "Executions", "Successes", and "Failures" counters directly on the Scheduled Action form.
*   **Status Badges**: Real-time status indicators (Running, Success, Failed) in list and form views.

### 5. Automated Log Management
*   **Retention Policy**: Configure how many days of logs to keep for each job.
*   **Garbage Collection**: Automatically purges old logs to prevent database bloat.
*   **Manual Purge**: One-click button to clear history for specific jobs.

---

## 🛠 Installation

1.  Copy the `scheduled_actions_tracker` folder to your Odoo custom addons directory.
2.  Restart your Odoo server.
3.  Activate **Developer Mode**.
4.  Go to **Apps** -> **Update Apps List**.
5.  Search for "Scheduled Actions Tracker" and click **Install**.

---

## 📖 Usage Guide

### Enabling Tracking
1.  Navigate to **Settings** -> **Technical** -> **Automation** -> **Scheduled Actions**.
    *(Or use the dedicated menu: **Technical** -> **Scheduled Actions Tracker** -> **Scheduled Actions**)*
2.  Open a Scheduled Action you wish to monitor.
3.  Go to the **Execution Tracking** tab.
4.  Toggle **Enable Execution Tracking** to ON.
5.  Set a **Log Retention (days)** period (e.g., 30 days).

### Viewing Logs
*   **From the Action Form**: Click the **Executions** smart button at the top right.
*   **Main Log View**: Navigate to **Technical** -> **Scheduled Actions Tracker** -> **Execution Logs**.
*   **In-Place Summary**: The "Execution Tracking" tab shows the last execution date, status, and average duration.

### Debugging Failures
1.  In the **Execution Logs** list, filter by **Failed**.
2.  Open a failed log entry.
3.  Check the **Traceback Details** tab to see exactly where the code crashed.

---

## 🏗 Technical Architecture

### Models
*   `ir.cron` (Inherited): Adds tracking configuration and statistical computed fields.
*   `cron.log` (New): Stores the history of every execution, including metadata and error details.

### Security
*   The module is restricted to the **Administration / Settings** group by default.
*   A dedicated menu structure is provided under the **Technical** category.

### UI/UX
*   Uses native Odoo 17 components (Selection Badges, Dynamic Banners, Smart Buttons).
*   Custom CSS for the Traceback viewer to provide a "Code Editor" feel.

---

## 📝 License
This module is licensed under the **LGPL-3** license.

---

*Developed with ❤️ for Odoo Administrators.*
