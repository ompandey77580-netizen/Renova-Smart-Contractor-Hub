"""seed.py - loads a realistic demo dataset on first run so the platform
can be showcased immediately (matches the scenario in the Black Book).

Demo logins created:
    admin@renova.in     / Admin@123     (administrator)
    client@renova.in    / Client@123    (client - Meera Deshmukh)
    ramesh@renova.in    / Contract@123  (contractor - Ramesh Shaikh, verified)
    mistry@renova.in    / Contract@123  (contractor - Jayesh Mistry, unverified)
"""
import datetime, secrets
import database
from auth import hash_password
from payments import calculate_bill

def _user(name, email, pwd, role, phone, city):
    salt = secrets.token_hex(16)          # salt must be hex for bytes.fromhex()
    return database.execute(
        "INSERT INTO users (name,email,password_hash,salt,role,phone,city) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (name, email, hash_password(pwd, salt), salt, role, phone, city))

def _days(n):
    return (datetime.date.today() + datetime.timedelta(days=n)).isoformat()

def run():
    # ------------------------------------------------------------------ users
    admin = _user("Admin (Renova)", "admin@renova.in", "Admin@123",
                  "admin", "9822000000", "Virar")
    client = _user("Meera Deshmukh", "client@renova.in", "Client@123",
                   "client", "9822011223", "Virar West")
    ramesh = _user("Ramesh Shaikh", "ramesh@renova.in", "Contract@123",
                   "contractor", "9822044556", "Virar West")
    mistry = _user("Jayesh Mistry", "mistry@renova.in", "Contract@123",
                   "contractor", "9822055566", "Nalasopara")

    r_id = database.execute(
        "INSERT INTO contractors (user_id,specialization,skills,"
        "experience_years,hourly_rate,city,available,verified) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (ramesh, "Painting", "Interior, Exterior, Texture, Waterproofing",
         11, 350, "Virar West", "Yes", 1))
    m_id = database.execute(
        "INSERT INTO contractors (user_id,specialization,skills,"
        "experience_years,hourly_rate,city,available,verified) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (mistry, "Masonry", "Plaster, Tiling, Repairs, Waterproofing",
         8, 400, "Nalasopara", "Yes", 0))

    # -------------------------------------------------------------- projects
    p1 = database.execute(
        "INSERT INTO projects (client_id,title,description,category,"
        "budget_min,budget_max,city,start_date,deadline) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (client, "Kitchen renovation of 1BHK flat",
         "Complete makeover of a 9x8 kitchen: modular cabinets, quartz "
         "platform, wall tiles up to ceiling and new plumbing points for "
         "the sink and purifier.",
         "Interior", 45000, 70000, "Virar West", _days(5), _days(60)))
    p2 = database.execute(
        "INSERT INTO projects (client_id,title,description,category,"
        "budget_min,budget_max,city,start_date,deadline) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (client, "Exterior painting of building staircase",
         "Weather-coat painting of the staircase and lobby walls of a "
         "ground-plus-three building. Scaffolding will be arranged by us.",
         "Painting", 20000, 30000, "Vasai West", _days(10), _days(45)))
    p3 = database.execute(
        "INSERT INTO projects (client_id,title,description,category,"
        "budget_min,budget_max,city,start_date,deadline) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (client, "Bathroom plumbing and tiling repair",
         "Replace rusted drain pipes, re-tiling of the bathroom floor "
         "and fixing of one new shower point.",
         "Plumbing", 15000, 25000, "Virar West", _days(-20), _days(20)))

    # ------------------------------------------------------------------ bids
    database.execute(
        "INSERT INTO bids (project_id,contractor_id,amount,duration_days,"
        "proposal,status) VALUES (%s,%s,%s,%s,%s,%s)",
        (p1, r_id, 52000, 18,
         "Two painters and one carpenter. Branded acrylic cabinets, "
         "Quartz platform with 10-year warranty. Stage-wise payment.", "Pending"))
    database.execute(
        "INSERT INTO bids (project_id,contractor_id,amount,duration_days,"
        "proposal,status) VALUES (%s,%s,%s,%s,%s,%s)",
        (p1, m_id, 56500, 15,
         "Team of four. Includes plumbing redo and full tiling with "
         "anti-skid floor tiles. Material bills shared daily.", "Pending"))
    database.execute(
        "INSERT INTO bids (project_id,contractor_id,amount,duration_days,"
        "proposal,status) VALUES (%s,%s,%s,%s,%s,%s)",
        (p3, r_id, 24000, 12,
         "Includes pipe replacement, anti-fungal coating before tiling "
         "and designer anti-skid tiles. 12 working days.", "Accepted"))

    # ------------------------------------- contract 1: running (project p3)
    c1 = database.execute(
        "INSERT INTO contracts (project_id,contractor_id,final_amount,"
        "start_date,end_date,status) VALUES (%s,%s,%s,%s,%s,%s)",
        (p3, r_id, 24000, _days(-18), _days(-6), "Active"))
    database.execute("UPDATE projects SET status='In Progress' "
                     "WHERE project_id=%s", (p3,))
    m1 = database.execute(
        "INSERT INTO milestones (contract_id,title,description,due_date,"
        "amount,status,work_note) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (c1, "Site preparation and material purchase",
         "Stage 1 of the accepted plan", _days(-12), 9600, "Paid",
         "Old fittings removed; pipes and tiles purchased and on site."))
    m2 = database.execute(
        "INSERT INTO milestones (contract_id,title,description,due_date,"
        "amount,status,work_note) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (c1, "Main work execution",
         "Stage 2 of the accepted plan", _days(-2), 8400, "Approved",
         "Drain lines replaced; floor re-tilled and grouted."))
    m3 = database.execute(
        "INSERT INTO milestones (contract_id,title,description,due_date,"
        "amount,status,work_note) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (c1, "Finishing, cleaning and handover",
         "Stage 3 of the accepted plan", _days(6), 6000, "Pending", None))
    amount, tax, total = calculate_bill(9600)
    database.execute(
        "INSERT INTO payments (milestone_id,amount,tax,total_paid,mode,"
        "paid_on) VALUES (%s,%s,%s,%s,%s,%s)",
        (m1, amount, tax, total, "UPI", _days(-11)))

    # --------------------------------- contract 2: completed + reviewed (p4)
    p4 = database.execute(
        "INSERT INTO projects (client_id,title,description,category,"
        "budget_min,budget_max,city,start_date,deadline,status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (client, "Bedroom interior painting",
         "Emulsion painting of one bedroom with putty finish.",
         "Painting", 10000, 15000, "Virar West",
         _days(-60), _days(-35), "Completed"))
    c2 = database.execute(
        "INSERT INTO contracts (project_id,contractor_id,final_amount,"
        "start_date,end_date,status) VALUES (%s,%s,%s,%s,%s,%s)",
        (p4, r_id, 12000, _days(-55), _days(-40), "Completed"))
    m4 = database.execute(
        "INSERT INTO milestones (contract_id,title,description,due_date,"
        "amount,status,work_note) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (c2, "Full work - single stage",
         "Single-stage contract", _days(-42), 12000, "Paid",
         "Putty, primer and two coats of emulsion completed."))
    amount, tax, total = calculate_bill(12000)
    database.execute(
        "INSERT INTO payments (milestone_id,amount,tax,total_paid,mode,"
        "paid_on) VALUES (%s,%s,%s,%s,%s,%s)",
        (m4, amount, tax, total, "Card", _days(-41)))
    database.execute(
        "INSERT INTO reviews (contract_id,reviewer_id,rating,comment) "
        "VALUES (%s,%s,%s,%s)",
        (c2, client, 5,
         "Clean finish, finished two days early and cleared all dust."))
    database.execute(
        "UPDATE contractors SET rating_avg=(SELECT ROUND(AVG(rating),2) "
        "FROM reviews) WHERE contractor_id=%s", (r_id,))

    # --------------------------------------------------------- notifications
    for msg in ("New bid on your project 'Kitchen renovation of 1BHK flat'.",
                "Ramesh Shaikh accepted for 'Bathroom plumbing and tiling "
                "repair'. Contract created."):
        database.execute(
            "INSERT INTO notifications (user_id,message) VALUES (%s,%s)",
            (client, msg))

    print("[renova] seeded: 4 users, 4 projects, 3 bids, 2 contracts, "
          "4 milestones, 2 payments, 1 review")

if __name__ == "__main__":
    run()
