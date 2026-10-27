"""projects.py - posting, editing and searching renovation projects."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import database
from helpers import login_required, role_required, valid_date, parse_money

projects_bp = Blueprint("projects", __name__)
CATEGORIES = ("Painting", "Masonry", "Carpentry",
              "Electrical", "Plumbing", "Interior", "Other")

@projects_bp.route("/projects")
@login_required
def list_projects():
    q, cat, city = (request.args.get(k, "").strip()
                    for k in ("q", "category", "city"))
    sql = ("SELECT p.*, u.name AS client_name "
           "FROM projects p JOIN users u ON u.user_id = p.client_id "
           "WHERE p.status='Open'")
    params = []
    if q:
        sql += " AND (p.title LIKE %s OR p.description LIKE %s)"
        params += ["%" + q + "%", "%" + q + "%"]
    if cat:
        sql += " AND p.category=%s";  params.append(cat)
    if city:
        sql += " AND p.city LIKE %s"; params.append("%" + city + "%")
    sql += " ORDER BY p.created_at DESC"
    rows = database.fetch_all(sql, tuple(params))
    return render_template("projects.html", projects=rows,
                           categories=CATEGORIES)

@projects_bp.route("/projects/new", methods=["GET", "POST"])
@role_required("client")
def post_project():
    if request.method == "POST":
        f = request.form
        try:
            bmin, bmax = parse_money(f["budget_min"]), parse_money(f["budget_max"])
            if bmax < bmin:
                raise ValueError("Budget maximum must be >= minimum.")
            if f["category"] not in CATEGORIES:
                raise ValueError("Choose a valid category.")
            if not valid_date(f["start_date"]) or not valid_date(f["deadline"]):
                raise ValueError("Enter valid dates (YYYY-MM-DD).")
            if f["deadline"] < f["start_date"]:
                raise ValueError("Deadline must be after the start date.")
            pid = database.execute(
                "INSERT INTO projects (client_id,title,description,category,"
                "budget_min,budget_max,city,start_date,deadline) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (session["user_id"], f["title"].strip(), f["description"].strip(),
                 f["category"], bmin, bmax, f["city"].strip(),
                 f["start_date"], f["deadline"]))
            flash("Project #%d published." % pid, "success")
            return redirect(url_for("projects.my_projects"))
        except (ValueError, KeyError) as e:
            flash(str(e) if str(e) else "Invalid input.", "danger")
    return render_template("project_form.html", categories=CATEGORIES)

@projects_bp.route("/projects/<int:pid>")
@login_required
def project_detail(pid):
    project = database.fetch_one(
        "SELECT p.*, u.name AS client_name FROM projects p "
        "JOIN users u ON u.user_id=p.client_id WHERE p.project_id=%s", (pid,))
    if project is None:
        flash("Project not found.", "danger")
        return redirect(url_for("projects.list_projects"))
    bids = database.fetch_all(
        "SELECT b.*, c.contractor_id, c.rating_avg, c.experience_years, "
        "u.name AS contractor_name FROM bids b "
        "JOIN contractors c ON c.contractor_id=b.contractor_id "
        "JOIN users u ON u.user_id=c.user_id "
        "WHERE b.project_id=%s AND b.status IN ('Pending','Accepted') "
        "ORDER BY b.amount", (pid,))
    my_bid = None
    if session.get("role") == "contractor":
        my_bid = database.fetch_one(
            "SELECT b.* FROM bids b JOIN contractors c "
            "ON c.contractor_id=b.contractor_id "
            "WHERE b.project_id=%s AND c.user_id=%s", (pid, session["user_id"]))
    return render_template("project_detail.html", p=project, bids=bids,
                           my_bid=my_bid)

@projects_bp.route("/my-projects")
@role_required("client")
def my_projects():
    rows = database.fetch_all(
        "SELECT p.*, (SELECT COUNT(*) FROM bids b WHERE "
        "b.project_id=p.project_id AND b.status<>'Withdrawn') AS bid_count "
        "FROM projects p WHERE client_id=%s ORDER BY created_at DESC",
        (session["user_id"],))
    return render_template("my_projects.html", projects=rows)
