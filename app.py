import os
import csv
import io
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, Response
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import (
    apology,
    login_required,
    calculate_bmi,
    bmi_category,
    week_start,
)

# ============================================
# APP CONFIGURATION
# ============================================

app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = lambda v: f"${v:,.2f}"

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure database
db = SQL("sqlite:///fitness.db")

# Valid categories
VALID_CATEGORIES = {"Cardio", "Strength", "Flexibility", "Other"}


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")

        if not username:
            return apology("must provide username", 400)
        if not password:
            return apology("must provide password", 400)
        if password != confirmation:
            return apology("passwords do not match", 400)

        # Check if username exists
        existing = db.execute("SELECT id FROM users WHERE username = ?", username)
        if existing:
            return apology("username already taken", 400)

        try:
            hash_val = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash_val)
        except Exception:
            return apology("registration failed", 400)

        # Log the user in automatically
        rows = db.execute("SELECT id FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]["id"]

        flash("Welcome to MyFitness! 💪")
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username:
            return apology("must provide username", 403)
        if not password:
            return apology("must provide password", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        flash("Welcome back! 🔥")
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    flash("Logged out. See you soon! 👋")
    return redirect("/login")


# ============================================
# DASHBOARD
# ============================================

@app.route("/")
@login_required
def index():
    """Show dashboard"""
    user_id = session["user_id"]

    # User info
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]
    goal_days = user["weekly_goal_days"] or 5
    goal_minutes = user["weekly_goal_minutes"] or 150

    # Week start (Monday)
    ws = week_start()

    # This week's stats
    week_stats = db.execute(
        """SELECT COUNT(*) AS c, COALESCE(SUM(duration), 0) AS mins, COALESCE(SUM(calories), 0) AS cals
           FROM workouts WHERE user_id = ? AND date >= ?""",
        user_id, ws.isoformat()
    )[0]

    week_count = week_stats["c"]
    week_minutes = week_stats["mins"]
    week_calories = week_stats["cals"]

    # Totals
    total_count = db.execute("SELECT COUNT(*) AS c FROM workouts WHERE user_id = ?", user_id)[0]["c"]

    # Percentages (capped at 100)
    days_percent = min(100, int((week_count / goal_days) * 100)) if goal_days else 0
    minutes_percent = min(100, int((week_minutes / goal_minutes) * 100)) if goal_minutes else 0

    # Recent workouts
    recent = db.execute(
        "SELECT * FROM workouts WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT 5",
        user_id
    )

    # Chart data — last 7 days
    today = datetime.date.today()
    labels = []
    minutes_data = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        labels.append(day.strftime("%a"))
        result = db.execute(
            "SELECT COALESCE(SUM(duration), 0) AS m FROM workouts WHERE user_id = ? AND date = ?",
            user_id, day.isoformat()
        )[0]["m"]
        minutes_data.append(result)

    return render_template(
        "index.html",
        username=user["username"],
        week_count=week_count,
        week_minutes=week_minutes,
        week_calories=week_calories,
        total_count=total_count,
        goal_days=goal_days,
        goal_minutes=goal_minutes,
        days_percent=days_percent,
        minutes_percent=minutes_percent,
        recent=recent,
        chart_labels=labels,
        chart_minutes=minutes_data,
    )


# ============================================
# WORKOUTS
# ============================================

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add a workout"""
    if request.method == "POST":
        type_ = request.form.get("type", "").strip()
        category = request.form.get("category", "").strip()
        duration = request.form.get("duration", "").strip()
        calories = request.form.get("calories", "").strip()
        date_ = request.form.get("date", "").strip()
        notes = request.form.get("notes", "").strip()
        mood = request.form.get("mood", "").strip()

        # Validation
        if not type_:
            return apology("must provide workout type", 400)
        if category not in VALID_CATEGORIES:
            return apology("invalid category", 400)
        if not duration.isdigit() or int(duration) <= 0:
            return apology("duration must be a positive number", 400)
        if not calories.isdigit() or int(calories) < 0:
            return apology("calories must be a non-negative number", 400)
        if not date_:
            return apology("must provide a date", 400)

        try:
            datetime.datetime.strptime(date_, "%Y-%m-%d")
        except ValueError:
            return apology("invalid date format", 400)

        db.execute(
            """INSERT INTO workouts (user_id, type, category, duration, calories, date, notes, mood)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            session["user_id"], type_, category, int(duration), int(calories),
            date_, notes or None, mood or None
        )

        flash("Workout added! 💪")
        return redirect("/")
    else:
        return render_template("add.html")


@app.route("/workouts")
@login_required
def workouts():
    """List all workouts"""
    rows = db.execute(
        "SELECT * FROM workouts WHERE user_id = ? ORDER BY date DESC, id DESC",
        session["user_id"]
    )
    return render_template("workouts.html", workouts=rows)


@app.route("/edit/<int:workout_id>", methods=["GET", "POST"])
@login_required
def edit(workout_id):
    """Edit a workout"""
    user_id = session["user_id"]

    workout = db.execute(
        "SELECT * FROM workouts WHERE id = ? AND user_id = ?",
        workout_id, user_id
    )
    if not workout:
        return apology("workout not found", 404)

    if request.method == "POST":
        type_ = request.form.get("type", "").strip()
        category = request.form.get("category", "").strip()
        duration = request.form.get("duration", "").strip()
        calories = request.form.get("calories", "").strip()
        date_ = request.form.get("date", "").strip()
        notes = request.form.get("notes", "").strip()
        mood = request.form.get("mood", "").strip()

        if not type_:
            return apology("must provide workout type", 400)
        if category not in VALID_CATEGORIES:
            return apology("invalid category", 400)
        if not duration.isdigit() or int(duration) <= 0:
            return apology("duration must be a positive number", 400)
        if not calories.isdigit() or int(calories) < 0:
            return apology("calories must be a non-negative number", 400)
        if not date_:
            return apology("must provide a date", 400)

        db.execute(
            """UPDATE workouts SET type = ?, category = ?, duration = ?, calories = ?,
               date = ?, notes = ?, mood = ? WHERE id = ? AND user_id = ?""",
            type_, category, int(duration), int(calories), date_,
            notes or None, mood or None, workout_id, user_id
        )

        flash("Workout updated! ✅")
        return redirect("/workouts")
    else:
        return render_template("edit.html", workout=workout[0])


@app.route("/delete/<int:workout_id>", methods=["POST"])
@login_required
def delete(workout_id):
    """Delete a workout"""
    db.execute(
        "DELETE FROM workouts WHERE id = ? AND user_id = ?",
        workout_id, session["user_id"]
    )
    flash("Workout deleted.")
    return redirect("/workouts")


# ============================================
# GOALS
# ============================================

@app.route("/goals", methods=["GET", "POST"])
@login_required
def goals():
    """Set weekly goals"""
    user_id = session["user_id"]

    if request.method == "POST":
        goal_days = request.form.get("goal_days", "").strip()
        goal_minutes = request.form.get("goal_minutes", "").strip()

        if not goal_days.isdigit() or not (1 <= int(goal_days) <= 7):
            return apology("days must be between 1 and 7", 400)
        if not goal_minutes.isdigit() or not (10 <= int(goal_minutes) <= 3000):
            return apology("minutes must be between 10 and 3000", 400)

        db.execute(
            "UPDATE users SET weekly_goal_days = ?, weekly_goal_minutes = ? WHERE id = ?",
            int(goal_days), int(goal_minutes), user_id
        )
        flash("Goals updated! 🎯")
        return redirect("/goals")
    else:
        user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]
        return render_template("goals.html", user=user)


# ============================================
# BMI
# ============================================

@app.route("/bmi", methods=["GET", "POST"])
@login_required
def bmi():
    """Calculate BMI"""
    user_id = session["user_id"]

    if request.method == "POST":
        height = request.form.get("height", "").strip()
        weight = request.form.get("weight", "").strip()

        try:
            h = float(height)
            w = float(weight)
        except ValueError:
            return apology("invalid measurements", 400)

        if not (50 <= h <= 250):
            return apology("height must be between 50 and 250 cm", 400)
        if not (20 <= w <= 400):
            return apology("weight must be between 20 and 400 kg", 400)

        db.execute("UPDATE users SET height_cm = ?, weight_kg = ? WHERE id = ?", h, w, user_id)
        flash("Measurements saved!")
        return redirect("/bmi")

    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]
    bmi_val = calculate_bmi(user["weight_kg"], user["height_cm"])
    category = bmi_category(bmi_val)
    return render_template("bmi.html", user=user, bmi=bmi_val, category=category)


# ============================================
# EXPORT CSV
# ============================================

@app.route("/export")
@login_required
def export_csv():
    """Export workouts as CSV"""
    rows = db.execute(
        "SELECT date, type, category, duration, calories, mood, notes FROM workouts WHERE user_id = ? ORDER BY date DESC",
        session["user_id"]
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Category", "Duration (min)", "Calories", "Mood", "Notes"])
    for r in rows:
        writer.writerow([
            r["date"], r["type"], r["category"], r["duration"],
            r["calories"], r["mood"] or "", r["notes"] or ""
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=myfitness_workouts.csv"}
    )


# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    app.run(debug=True)
