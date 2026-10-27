"""app.py - application factory, routing and access control."""
import os
from flask import Flask, session, redirect, url_for, render_template, flash
from functools import wraps
import database
from helpers import role_required
from auth import auth_bp
from projects import projects_bp
from bids import bids_bp
from contracts import contracts_bp
from payments import payments_bp
from reviews import reviews_bp
from reports import reports_bp
from admin import admin_bp

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("RENOVA_SECRET", "renova-key-73")
    try:
        database.init_db()          # idempotent: creates schema + demo data
    except Exception as exc:        # never block startup on DB hiccups
        print("[renova] database init warning:", exc)

    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(bids_bp)
    app.register_blueprint(contracts_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("reports.dashboard"))
        return redirect(url_for("auth.login"))

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("error.html", code=404, msg="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", code=500, msg="Internal error"), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
