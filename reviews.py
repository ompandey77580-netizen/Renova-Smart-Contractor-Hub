"""reviews.py - ratings after completion."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import database
from helpers import login_required, role_required

reviews_bp = Blueprint("reviews", __name__)

@reviews_bp.route("/contracts/<int:cid>/review", methods=["POST"])
@role_required("client")
def add_review(cid):
    try:
        rating = int(request.form.get("rating", "0"))
    except ValueError:
        rating = 0
    if not 1 <= rating <= 5:
        flash("Rating must be between 1 and 5 stars.", "danger")
        return redirect(request.referrer)
    ct = database.fetch_one(
        "SELECT * FROM contracts WHERE contract_id=%s", (cid,))
    if ct is None or ct["status"] != "Completed":
        flash("You can review a contractor only after completion.", "warning")
        return redirect(request.referrer)
    database.execute(
        "INSERT INTO reviews (contract_id, reviewer_id, rating, comment) "
        "VALUES (%s,%s,%s,%s)",
        (cid, session["user_id"], rating,
         request.form.get("comment", "").strip()))
    database.execute(
        "UPDATE contractors SET rating_avg = "
        "(SELECT ROUND(AVG(r.rating),2) FROM reviews r "
        " JOIN contracts c2 ON c2.contract_id = r.contract_id "
        " WHERE c2.contractor_id = %s) WHERE contractor_id = %s",
        (ct["contractor_id"], ct["contractor_id"]))
    flash("Thank you for your review!", "success")
    return redirect(url_for("contracts.contract", cid=cid))
