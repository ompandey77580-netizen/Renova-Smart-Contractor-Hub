"""reports.py - dashboards and admin reports."""
import csv, io
from datetime import date
from flask import Blueprint, render_template, request, session, Response, redirect, url_for
import database
from helpers import login_required, role_required

reports_bp = Blueprint("reports", __name__)

def _contract_rows(where_sql, params):
    """Contracts with milestone progress used by both dashboards."""
    rows = database.fetch_all(
        "SELECT ct.contract_id, ct.status, ct.start_date, ct.end_date, "
        "p.title AS project_title, p.deadline, "
        "uu.name AS contractor_name, u.name AS client_name "
        "FROM contracts ct "
        "JOIN projects p ON p.project_id = ct.project_id "
        "JOIN contractors co ON co.contractor_id = ct.contractor_id "
        "JOIN users uu ON uu.user_id = co.user_id "
        "JOIN users u ON u.user_id = p.client_id "
        "WHERE " + where_sql + " ORDER BY ct.contract_id DESC", params)
    miles = database.fetch_all("SELECT * FROM milestones")
    by_ct = {}
    for m in miles:
        by_ct.setdefault(m["contract_id"], []).append(m)
    today = str(date.today())
    for r in rows:
        ms = by_ct.get(r["contract_id"], [])
        unpaid = [m for m in ms if m["status"] != "Paid"]
        r["paid_stages"] = len(ms) - len(unpaid)
        r["total_stages"] = len(ms)
        nxt = min(unpaid, key=lambda m: str(m["due_date"])) if unpaid else None
        r["next_milestone"] = nxt["title"] if nxt else None
        r["next_due"] = nxt["due_date"] if nxt else None
        r["overdue"] = bool(r["status"] == "Active" and nxt
                            and str(nxt["due_date"]) < today)
    return rows

@reports_bp.route("/dashboard")
@login_required
def dashboard():
    role = session["role"]
    uid = session["user_id"]
    if role == "client":
        stats = database.fetch_one(
            "SELECT COUNT(*) AS projects, "
            "SUM(status='Open') AS open_projects, "
            "SUM(status='In Progress') AS active_projects, "
            "(SELECT COUNT(*) FROM bids b JOIN projects p ON "
            " p.project_id=b.project_id WHERE p.client_id=%s AND "
            " b.status='Pending') AS pending_bids "
            "FROM projects WHERE client_id=%s", (uid, uid))
        contracts = _contract_rows("p.client_id=%s", (uid,))
        return render_template("dashboard_client.html", s=stats,
                               contracts=contracts)
    if role == "contractor":
        stats = database.fetch_one(
            "SELECT COUNT(*) AS bids, SUM(status='Pending') AS pending_bids "
            "FROM bids b JOIN contractors c ON c.contractor_id=b.contractor_id "
            "WHERE c.user_id=%s", (uid,))
        earn = database.fetch_one(
            "SELECT COALESCE(SUM(pay.total_paid),0) AS earnings "
            "FROM payments pay JOIN milestones m ON "
            "m.milestone_id=pay.milestone_id "
            "JOIN contracts ct ON ct.contract_id=m.contract_id "
            "JOIN contractors c ON c.contractor_id=ct.contractor_id "
            "WHERE c.user_id=%s", (uid,))
        contracts = _contract_rows("co.user_id=%s", (uid,))
        active = sum(1 for c in contracts if c["status"] == "Active")
        return render_template("dashboard_contractor.html",
                               s=stats, earn=earn, contracts=contracts,
                               active_contracts=active)
    return redirect(url_for("admin.panel"))

@reports_bp.route("/admin/reports")
@role_required("admin")
def admin_reports():
    frm, to = request.args.get("from", ""), request.args.get("to", "")
    rows = database.fetch_all(
        "SELECT DATE(pay.paid_on) AS day, COUNT(*) AS payments, "
        "SUM(pay.amount) AS work_value, SUM(pay.tax) AS gst, "
        "SUM(pay.total_paid) AS total "
        "FROM payments pay WHERE (%s='' OR pay.paid_on >= %s) "
        "AND (%s='' OR pay.paid_on <= %s) GROUP BY DATE(pay.paid_on) "
        "ORDER BY day DESC", (frm, frm, to, to))
    return render_template("admin_reports.html", rows=rows, frm=frm, to=to)

@reports_bp.route("/admin/reports/export")
@role_required("admin")
def export_csv():
    rows = database.fetch_all(
        "SELECT pay.payment_id, pay.paid_on, pay.amount, pay.tax, "
        "pay.total_paid, pay.mode FROM payments pay "
        "ORDER BY pay.paid_on DESC")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["payment_id", "paid_on", "amount", "gst", "total", "mode"])
    for r in rows:
        w.writerow([r["payment_id"], r["paid_on"], r["amount"],
                    r["tax"], r["total_paid"], r["mode"]])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":
                             "attachment; filename=renova_payments.csv"})
