"""contracts.py - contract creation and the milestone workflow."""
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import database
from helpers import login_required, role_required, valid_date, parse_money

contracts_bp = Blueprint("contracts", __name__)

def _as_date(v):
    """MySQL returns date objects; SQLite stores ISO strings."""
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    return datetime.datetime.strptime(str(v)[:10], "%Y-%m-%d").date()

def create_contract_from_bid(bid, project):
    """Award the project: contract + a default 3-stage milestone plan."""
    start = _as_date(project["start_date"])
    end = start + datetime.timedelta(days=int(bid["duration_days"]))
    amount = float(bid["amount"])
    cuts = (0.40, 0.35, 0.25)                      # 40% / 35% / 25%
    titles = ("Site preparation and material purchase",
              "Main work execution",
              "Finishing, cleaning and handover")
    ops = [
        ("INSERT INTO contracts (project_id,contractor_id,final_amount,"
         "start_date,end_date) VALUES (%s,%s,%s,%s,%s)",
         (project["project_id"], bid["contractor_id"], amount, start, end)),
        ("UPDATE projects SET status='In Progress' WHERE project_id=%s",
         (project["project_id"],)),
        ("UPDATE bids SET status='Accepted' WHERE bid_id=%s", (bid["bid_id"],)),
        ("UPDATE bids SET status='Rejected' WHERE project_id=%s AND "
         "status='Pending' AND bid_id<>%s",
         (project["project_id"], bid["bid_id"])),
    ]
    contract_id = database.execute(ops[0][0], ops[0][1])
    for sql, params in ops[1:]:
        database.execute(sql, params)
    third = round(amount * cuts[2], 2)
    plan = [round(amount * cuts[0], 2), round(amount * cuts[1], 2)]
    plan.append(round(amount - plan[0] - plan[1], 2))   # exact total
    for i, (title, mamount) in enumerate(zip(titles, plan), 1):
        due = start + datetime.timedelta(days=int(int(bid["duration_days"]) * i / 3))
        database.execute(
            "INSERT INTO milestones (contract_id,title,description,due_date,"
            "amount) VALUES (%s,%s,%s,%s,%s)",
            (contract_id, title, "Stage %d of the accepted plan" % i,
             due, mamount))
    return contract_id

@contracts_bp.route("/contracts/<int:cid>")
@login_required
def contract(cid):
    c = database.fetch_one(
        "SELECT ct.*, p.title AS project_title, p.city, "
        "u.name AS client_name, uu.name AS contractor_name "
        "FROM contracts ct "
        "JOIN projects p  ON p.project_id = ct.project_id "
        "JOIN contractors co ON co.contractor_id = ct.contractor_id "
        "JOIN users u  ON u.user_id = p.client_id "
        "JOIN users uu ON uu.user_id = co.user_id "
        "WHERE ct.contract_id=%s", (cid,))
    if c is None:
        flash("Contract not found.", "danger")
        return redirect(url_for("reports.dashboard"))
    miles = database.fetch_all(
        "SELECT m.*, pay.payment_id FROM milestones m "
        "LEFT JOIN payments pay ON pay.milestone_id = m.milestone_id "
        "WHERE m.contract_id=%s ORDER BY m.milestone_id", (cid,))
    for m in miles:                       # date objects in both engines
        m["due_date"] = _as_date(m["due_date"])
    return render_template("contract.html", c=c, milestones=miles,
                           today=datetime.date.today())

@contracts_bp.route("/milestones/<int:mid>/complete", methods=["POST"])
@role_required("contractor")
def mark_complete(mid):
    note = request.form.get("work_note", "").strip()
    if len(note) < 10:
        flash("Add a short work note (10+ characters).", "danger")
        return redirect(request.referrer or url_for("reports.dashboard"))
    database.execute(
        "UPDATE milestones SET status='Completed', work_note=%s "
        "WHERE milestone_id=%s AND status='Pending'", (note, mid))
    flash("Milestone marked complete. Waiting for client approval.", "success")
    return redirect(request.referrer or url_for("reports.dashboard"))

@contracts_bp.route("/milestones/<int:mid>/approve", methods=["POST"])
@role_required("client")
def approve_milestone(mid):
    m = database.fetch_one("SELECT * FROM milestones WHERE milestone_id=%s",
                           (mid,))
    if m is None or m["status"] != "Completed":
        flash("Only completed milestones can be approved.", "danger")
        return redirect(request.referrer)
    if request.form.get("action") == "rework":
        database.execute(
            "UPDATE milestones SET status='Pending', rework_remark=%s "
            "WHERE milestone_id=%s",
            (request.form.get("remark", "Please rework."), mid))
        flash("Rework remark sent to the contractor.", "info")
    else:
        database.execute(
            "UPDATE milestones SET status='Approved' WHERE milestone_id=%s",
            (mid,))
        flash("Milestone approved. You can now pay this stage.", "success")
    return redirect(url_for("contracts.contract", cid=m["contract_id"]))
