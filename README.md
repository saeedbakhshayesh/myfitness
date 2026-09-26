# MyFitness — Workout Tracker
#### Video Demo: <URL HERE>
#### Description:

MyFitness is a modern, minimal web application designed to help users track
their daily workouts, monitor weekly progress, and stay consistent with their
fitness goals. Built with Flask, SQLite, Bootstrap 5, and Chart.js, the app
features a clean black-and-white interface inspired by modern fitness apps.

## Features

- **User Authentication** — Register, log in, log out with securely hashed passwords.
- **Workout Logging** — Add workouts with type, category, duration, calories, date, mood, and notes.
- **Dashboard** — Visual overview with stat cards, weekly progress bars, and a 7-day activity chart.
- **Workout Management** — View, edit, and delete any workout.
- **Weekly Goals** — Set target workout days and minutes per week, and track progress.
- **BMI Calculator** — Save height and weight, calculate BMI, and view the category.
- **CSV Export** — Download your entire workout history.

## Files

- `app.py` — Main Flask application with all routes.
- `helpers.py` — Utility functions (login_required, apology, BMI, week_start).
- `fitness.db` — SQLite database with three tables: users, workouts, goals.
- `templates/` — Jinja2 HTML templates.
- `static/css/styles.css` — Custom minimal design system.
- `static/js/main.js` — Sidebar toggle and small UI logic.

## Design Choices

I chose a monochrome palette (black/white) to reflect a "no-nonsense" athletic
aesthetic, similar to modern fitness brands. The sidebar navigation keeps the
focus on the content, and Chart.js provides an at-a-glance view of weekly
activity. All SQL queries use parameterized statements to prevent injection.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Initialize DB: `sqlite3 fitness.db < schema.sql` (or create tables manually)
3. Run: `flask run`
