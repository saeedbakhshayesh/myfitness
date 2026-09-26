import csv
import datetime
import functools
import urllib.parse

from flask import redirect, render_template, session

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """Decorate routes to require login."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI given weight in kg and height in cm."""
    if not weight_kg or not height_cm:
        return None
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def bmi_category(bmi):
    """Return BMI category string."""
    if bmi is None:
        return "Unknown"
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def week_start(date=None):
    """Return the Monday of the week for the given date (or today)."""
    if date is None:
        date = datetime.date.today()
    return date - datetime.timedelta(days=date.weekday())
