# RENOVA - A Smart Contractor Hub

A mini-project by **Om Pandey (Roll No 73), T.Y.B.Sc.CS** - VIVA College, Virar (West).
Guide: **Prof. Priyanka Brid** | Academic Year 2026-27

Renova is a web platform that connects home owners with skilled contractors
(painters, masons, carpenters, electricians, plumbers, interior designers).
Clients post renovation projects, contractors place structured bids, the
client hires the best bid, and the work is executed and paid **milestone by
milestone with automatic 18% GST billing and printable receipts**.

---

## Features

| Role | What they can do |
|------|------------------|
| Client | Post / search / withdraw renovation projects, compare all bids side by side, hire, approve or send rework per milestone, pay with GST receipt, rate the contractor |
| Contractor | Maintain a professional profile, search open projects by category and city, place / update / withdraw bids, execute milestones stage by stage, receive payments |
| Admin | Verify contractor profiles, manage users, view revenue reports (date range), export payments to CSV, take database backups |

Highlights: salted PBKDF2-SHA256 passwords, parameterised SQL everywhere,
role-based session guards, one-active-bid-per-project rule, automatic
3-stage milestone plan, 18% GST billing, star ratings, flash toasts,
mobile-friendly responsive UI.

## Technology Stack (matches the Black Book)

- **Frontend** : HTML5, CSS3, JavaScript (Jinja2 templates)
- **Backend**  : Python 3 + Flask 3 (one blueprint per module)
- **Database** : MySQL 8.0 (documented) with automatic **SQLite fallback** so the demo runs anywhere with zero configuration
- **Tools**    : VS Code, Git & GitHub, Chart.js-ready dashboards

## Quick Start (60 seconds, no database setup)

```bash
pip install -r requirements.txt        # (mysql-connector is optional)
python app.py
# open http://127.0.0.1:5000  (or the port shown in the console)
```

First run automatically creates the SQLite database (`instance/renova.db`)
and loads a realistic demo dataset.

### Run with MySQL (as documented in the Black Book)

1. Start MySQL (XAMPP/WAMP or MySQL 8.0 Community Server).
2. Set the credentials and run:

```bash
export DB_MODE=mysql            # Windows: set DB_MODE=mysql
export DB_USER=root             # your MySQL user
export DB_PASS=your_password    # your MySQL password
python app.py
```

The `renova_db` database and all tables are created automatically from
`schema.sql` on first run.

## Demo Logins (loaded on first run)

| Role | E-mail | Password |
|------|--------|----------|
| Admin | admin@renova.in | Admin@123 |
| Client (Meera Deshmukh) | client@renova.in | Client@123 |
| Contractor - Painting (Ramesh Shaikh, verified) | ramesh@renova.in | Contract@123 |
| Contractor - Masonry (Jayesh Mistry, unverified) | mistry@renova.in | Contract@123 |

**Suggested demo path:** login as client -> open *Kitchen renovation of
1BHK flat* -> compare 2 bids -> Accept & Hire -> contract with 3 milestones
-> login as contractor -> mark stage complete -> login as client -> approve
-> Pay (UPI) -> printable GST receipt -> admin panel -> revenue report +
CSV export.

## Project Structure

```
Renova/
|-- app.py               # application factory, routes, error handlers
|-- auth.py              # register / login / change password (PBKDF2)
|-- projects.py          # post, search and browse projects
|-- bids.py              # place, update, withdraw, compare and accept bids
|-- contracts.py         # contract creation + milestone workflow
|-- payments.py          # GST billing and printable receipts
|-- reviews.py           # star ratings after completion
|-- reports.py           # role dashboards + admin revenue reports
|-- admin.py             # user management, verification, backup
|-- notify.py            # in-app notification helper (FR19)
|-- database.py          # DB layer - MySQL primary, SQLite fallback
|-- helpers.py           # validation, formatting, access decorators
|-- seed.py              # demo dataset (auto-loaded on first run)
|-- schema.sql           # MySQL schema (renova_db)
|-- schema_sqlite.sql    # SQLite mirror of the same schema
|-- requirements.txt
|-- static/style.css, static/app.js
|-- templates/           # 16 Jinja2 pages
```

## Publish on GitHub (step by step)

```bash
# 1. create an EMPTY repository named e.g.  renova-smart-contractor-hub
#    on https://github.com/new   (do NOT add a README there)

# 2. then inside this folder:
git init
git add .
git commit -m "Renova - A Smart Contractor Hub (T.Y.B.Sc.CS mini project)"
git branch -M main
git remote add origin https://github.com/<your-username>/renova-smart-contractor-hub.git
git push -u origin main
```

On the GitHub page add *Topics* like `flask`, `mysql`, `mini-project`,
`contractor-marketplace` and upload 2-3 screenshots in a `screenshots/`
folder - repositories with images look far better during evaluation.

## Deploy Options (Black Book section 8)

- **Local demo**      : `python app.py` (SQLite, zero setup)
- **LAN demo**        : `python app.py` then open `http://<your-ip>:5000` on the same Wi-Fi
- **Cloud / shared**  : `pip install waitress` then `waitress-serve --port=8080 app:create_app()` behind Nginx/Apache, with `DB_MODE=mysql`

## Notes for Evaluation

- The functional requirements (FR1-FR20), use cases (UC-01..UC-08) and
  schema in the Black Book map 1:1 to this code base.
- `DB_MODE=sqlite` exists only so that external evaluators can run the
  project instantly; the documented production engine is MySQL.
- Passwords are never stored in plain text - only salted PBKDF2-SHA256
  hashes (see `auth.py`).

---

*Renova - A Smart Contractor Hub | Om Pandey-73 | T.Y.B.Sc.CS Mini Project 2026-27*
