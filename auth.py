"""auth.py - registration, login and password management."""
import hashlib, hmac, secrets, re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import database
from helpers import valid_email, valid_phone

auth_bp = Blueprint("auth", __name__)

def hash_password(password, salt_hex):
    """Salted PBKDF2-HMAC-SHA256, 100000 iterations -> 64 hex chars."""
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), 100000).hex()

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip().lower()
        phone   = request.form.get("phone", "").strip()
        city    = request.form.get("city", "").strip()
        role    = request.form.get("role", "")
        pwd     = request.form.get("password", "")
        pwd2    = request.form.get("password2", "")
        spec    = request.form.get("specialization", "").strip()

        if not name or not valid_email(email) or not valid_phone(phone):
            flash("Please check the name, e-mail and phone fields.", "danger")
        elif role not in ("client", "contractor"):
            flash("Choose a valid role.", "danger")
        elif len(pwd) < 8 or pwd != pwd2:
            flash("Password must be 8+ characters and match twice.", "danger")
        elif database.fetch_one("SELECT 1 FROM users WHERE email=%s", (email,)):
            flash("An account with this e-mail already exists.", "danger")
        else:
            salt = secrets.token_hex(16)
            uid = database.execute(
                "INSERT INTO users (name,email,password_hash,salt,role,phone,city) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (name, email, hash_password(pwd, salt), salt, role, phone, city))
            if role == "contractor":
                database.execute(
                    "INSERT INTO contractors (user_id, specialization, city) "
                    "VALUES (%s,%s,%s)", (uid, spec or "General", city))
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pwd   = request.form.get("password", "")
        user  = database.fetch_one("SELECT * FROM users WHERE email=%s", (email,))
        if user and hmac.compare_digest(
                hash_password(pwd, user["salt"]), user["password_hash"]):
            session.clear()
            session["user_id"] = user["user_id"]
            session["role"]    = user["role"]
            session["name"]    = user["name"]
            return redirect(url_for("reports.dashboard"))
        flash("Invalid e-mail or password.", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        user = database.fetch_one(
            "SELECT * FROM users WHERE user_id=%s", (session["user_id"],))
        old = request.form.get("old", "")
        new = request.form.get("new", "")
        if not hmac.compare_digest(hash_password(old, user["salt"]),
                                   user["password_hash"]):
            flash("Current password is wrong.", "danger")
        elif len(new) < 8:
            flash("New password must be 8+ characters.", "danger")
        else:
            salt = secrets.token_hex(16)
            database.execute(
                "UPDATE users SET password_hash=%s, salt=%s WHERE user_id=%s",
                (hash_password(new, salt), salt, user["user_id"]))
            flash("Password changed.", "success")
    return render_template("change_password.html")
