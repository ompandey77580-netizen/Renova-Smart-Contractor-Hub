"""helpers.py - validation, formatting and access-control decorators."""
import re
from datetime import datetime
from functools import wraps
from flask import session, redirect, url_for, flash

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]{2,}$")
PHONE_RE = re.compile(r"^[6-9]\d{9}$")

class ValidationError(ValueError):
    pass

def valid_email(s):    return bool(EMAIL_RE.match(s or ""))
def valid_phone(s):    return bool(PHONE_RE.match(s or ""))

def valid_date(s):
    try:
        datetime.strptime(s or "", "%Y-%m-%d")
        return True
    except ValueError:
        return False

def parse_money(s):
    v = float(s)
    if v <= 0:
        raise ValidationError("Amount must be positive.")
    return round(v, 2)

def money(v):
    return "Rs. {:,.2f}".format(v or 0)

def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        return fn(*a, **k)
    return wrapper

def role_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **k):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))
            if session.get("role") not in roles:
                flash("You are not allowed to open that page.", "danger")
                return redirect(url_for("reports.dashboard"))
            return fn(*a, **k)
        return wrapper
    return deco
