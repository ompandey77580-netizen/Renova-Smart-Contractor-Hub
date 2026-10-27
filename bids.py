"""bids.py - placing, comparing and accepting bids."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import database
from helpers import login_required, role_required, parse_money

bids_bp = Blueprint("bids", __name__)

def _my_contractor_id():
    row = database.fetch_one(
        "SELECT contractor_id FROM contractors WHERE user_id=%s",
        (session["user_id"],))
    return row["contractor_id"] if row else None

@bids_bp.route("/projects/<int:pid>/bid", methods=["POST"])
@role_required("contractor")
def place_bid(pid):
    project = database.fetch_one(
        "SELECT * FROM projects WHERE project_id=%s AND status='Open'", (pid,))
    if project is None:
        flash("This project is not open for bidding.", "danger")
        return redirect(url_for("projects.list_projects"))
    cid = _my_contractor_id()
    existing = database.fetch_one(
        "SELECT * FROM bids WHERE project_id=%s AND contractor_id=%s",
        (pid, cid))
    try:
        amount = parse_money(request.form["amount"])
        days = int(request.form["duration_days"])
        proposal = request.form["proposal"].strip()
        if days <= 0:
            raise ValueError("Duration must be at least one day.")
        if len(proposal) < 20:
            raise ValueError("Describe your plan in at least 20 characters.")
        if existing and existing["status"] == "Pending":
            database.execute(
                "UPDATE bids SET amount=%s, duration_days=%s, proposal=%s "
                "WHERE bid_id=%s",
                (amount, days, proposal, existing["bid_id"]))
            flash("Your bid was updated.", "success")
        elif existing:
            flash("You already have a settled bid on this project.", "danger")
        else:
            database.execute(
                "INSERT INTO bids (project_id,contractor_id,amount,"
                "duration_days,proposal) VALUES (%s,%s,%s,%s,%s)",
                (pid, cid, amount, days, proposal))
            flash("Bid placed. The client has been notified.", "success")
    except (ValueError, KeyError) as e:
        flash(str(e), "danger")
    return redirect(url_for("projects.project_detail", pid=pid))

@bids_bp.route("/bids/<int:bid_id>/withdraw", methods=["POST"])
@role_required("contractor")
def withdraw_bid(bid_id):
    database.execute(
        "UPDATE bids SET status='Withdrawn' WHERE bid_id=%s AND status='Pending'",
        (bid_id,))
    flash("Bid withdrawn.", "info")
    return redirect(request.referrer or url_for("projects.list_projects"))

@bids_bp.route("/bids/<int:bid_id>/accept", methods=["POST"])
@role_required("client")
def accept_bid(bid_id):
    from contracts import create_contract_from_bid
    bid = database.fetch_one("SELECT * FROM bids WHERE bid_id=%s", (bid_id,))
    if bid is None or bid["status"] != "Pending":
        flash("This bid can no longer be accepted.", "danger")
        return redirect(request.referrer or url_for("reports.dashboard"))
    project = database.fetch_one(
        "SELECT * FROM projects WHERE project_id=%s AND status='Open' "
        "AND client_id=%s", (bid["project_id"], session["user_id"]))
    if project is None:
        flash("This project is not open for hiring.", "danger")
        return redirect(url_for("reports.dashboard"))
    create_contract_from_bid(bid, project)
    flash("Contractor hired. Contract created with milestone plan.", "success")
    return redirect(url_for("contracts.contract",
                            cid=_new_contract_id(bid["project_id"])))

def _new_contract_id(project_id):
    row = database.fetch_one(
        "SELECT contract_id FROM contracts WHERE project_id=%s", (project_id,))
    return row["contract_id"]
