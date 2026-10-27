"""payments.py - GST billing and receipts."""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import database
from helpers import login_required, role_required, money

payments_bp = Blueprint("payments", __name__)
GST = 0.18

def calculate_bill(amount):
    """amount + 18% GST; returns (amount, tax, total)."""
    amount = round(float(amount), 2)
    tax = round(amount * GST, 2)
    return amount, tax, round(amount + tax, 2)

@payments_bp.route("/milestones/<int:mid>/pay", methods=["GET", "POST"])
@role_required("client")
def pay_milestone(mid):
    m = database.fetch_one(
        "SELECT m.*, ct.contract_id, ct.project_id, p.title AS project_title "
        "FROM milestones m JOIN contracts ct ON ct.contract_id=m.contract_id "
        "JOIN projects p ON p.project_id=ct.project_id "
        "WHERE m.milestone_id=%s", (mid,))
    if m is None:
        flash("Milestone not found.", "danger")
        return redirect(url_for("reports.dashboard"))
    if m["status"] == "Paid":
        flash("This milestone is already settled.", "warning")
        return redirect(url_for("contracts.contract", cid=m["contract_id"]))
    if m["status"] != "Approved":
        flash("Approve the milestone before paying.", "warning")
        return redirect(url_for("contracts.contract", cid=m["contract_id"]))
    if request.method == "POST":
        mode = request.form.get("mode")
        if mode not in ("Cash", "UPI", "Card"):
            flash("Choose a valid payment mode.", "danger")
        else:
            amount, tax, total = calculate_bill(m["amount"])
            pid = database.transaction([
                ("INSERT INTO payments (milestone_id,amount,tax,total_paid,"
                 "mode,paid_on) VALUES (%s,%s,%s,%s,%s,%s)",
                 (mid, amount, tax, total, mode, date.today())),
                ("UPDATE milestones SET status='Paid' WHERE milestone_id=%s",
                 (mid,)),
            ])
            flash("Payment of %s recorded." % money(total), "success")
            return redirect(url_for("payments.receipt", payment_id=pid))
    amount, tax, total = calculate_bill(m["amount"])
    return render_template("payment.html", m=m, amount=amount, tax=tax,
                           total=total)

@payments_bp.route("/receipt/<int:payment_id>")
@login_required
def receipt(payment_id):
    r = database.fetch_one(
        "SELECT pay.*, m.title AS milestone_title, ct.contract_id, "
        "p.title AS project_title, u.name AS client_name, "
        "uu.name AS contractor_name FROM payments pay "
        "JOIN milestones m ON m.milestone_id = pay.milestone_id "
        "JOIN contracts ct ON ct.contract_id = m.contract_id "
        "JOIN projects p   ON p.project_id  = ct.project_id "
        "JOIN contractors co ON co.contractor_id = ct.contractor_id "
        "JOIN users u  ON u.user_id  = p.client_id "
        "JOIN users uu ON uu.user_id = co.user_id "
        "WHERE pay.payment_id=%s", (payment_id,))
    return render_template("receipt.html", r=r)
