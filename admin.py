"""admin.py - user management and contractor verification."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
import database
from helpers import role_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin")
@role_required("admin")
def panel():
    users = database.fetch_all(
        "SELECT u.*, c.contractor_id, c.rating_avg, c.verified, "
        "c.specialization FROM users u "
        "LEFT JOIN contractors c ON c.user_id = u.user_id "
        "ORDER BY u.created_at DESC")
    counts = {
        "users":       database.fetch_one(
            "SELECT COUNT(*) AS n FROM users")["n"],
        "contractors": database.fetch_one(
            "SELECT COUNT(*) AS n FROM contractors")["n"],
        "projects":    database.fetch_one(
            "SELECT COUNT(*) AS n FROM projects")["n"],
        "revenue":     float(database.fetch_one(
            "SELECT COALESCE(SUM(total_paid),0) AS n FROM payments")["n"] or 0),
    }
    return render_template("admin.html", users=users, counts=counts)

@admin_bp.route("/admin/verify/<int:contractor_id>", methods=["POST"])
@role_required("admin")
def verify(contractor_id):
    new = 0 if request.form.get("current") == "1" else 1
    database.execute(
        "UPDATE contractors SET verified=%s WHERE contractor_id=%s",
        (new, contractor_id))
    flash("Contractor verification updated.", "success")
    return redirect(url_for("admin.panel"))

@admin_bp.route("/admin/deactivate/<int:user_id>", methods=["POST"])
@role_required("admin")
def deactivate(user_id):
    # soft block: rename e-mail so the account cannot log in again
    database.execute(
        "UPDATE users SET email=CONCAT('blocked_', user_id, '_', email) "
        "WHERE user_id=%s", (user_id,))
    flash("Account blocked.", "info")
    return redirect(url_for("admin.panel"))

@admin_bp.route("/admin/backup")
@role_required("admin")
def backup():
    from database import backup_db
    path = backup_db()
    flash("Backup written to %s" % path, "success")
    return redirect(url_for("admin.panel"))
