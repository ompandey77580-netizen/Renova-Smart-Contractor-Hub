-- schema_sqlite.sql - SQLite mirror of schema.sql (identical columns,
-- constraints and statuses) so the project can run with zero configuration.
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT(80)  NOT NULL,
    email         TEXT(120) NOT NULL UNIQUE,
    password_hash TEXT(64)  NOT NULL,
    salt          TEXT(32)  NOT NULL,
    role          TEXT(12)  NOT NULL
                  CHECK (role IN ('client','contractor','admin')),
    phone         TEXT(15)  NOT NULL,
    address       TEXT(150),
    city          TEXT(60),
    created_at    TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS contractors (
    contractor_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INT NOT NULL UNIQUE,
    specialization   TEXT(120) NOT NULL,
    skills           TEXT(200),
    experience_years NUMERIC(4,1) NOT NULL DEFAULT 0,
    hourly_rate      NUMERIC(10,2) NOT NULL CHECK (hourly_rate > 0),
    city             TEXT(60) NOT NULL,
    available        TEXT(3) DEFAULT 'Yes' CHECK (available IN ('Yes','No')),
    rating_avg       NUMERIC(3,2) DEFAULT 0.00,
    verified         INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS projects (
    project_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id   INT NOT NULL,
    title       TEXT(150) NOT NULL,
    description TEXT NOT NULL,
    category    TEXT(12) NOT NULL
                CHECK (category IN ('Painting','Masonry','Carpentry','Electrical',
                                    'Plumbing','Interior','Other')),
    budget_min  NUMERIC(10,2) NOT NULL CHECK (budget_min > 0),
    budget_max  NUMERIC(10,2) NOT NULL,
    city        TEXT(60) NOT NULL,
    start_date  TEXT NOT NULL,
    deadline    TEXT NOT NULL,
    status      TEXT(12) DEFAULT 'Open'
                CHECK (status IN ('Open','In Progress','Completed','Cancelled')),
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    CHECK (budget_max >= budget_min),
    CHECK (deadline >= start_date),
    FOREIGN KEY (client_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bids (
    bid_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INT NOT NULL,
    contractor_id  INT NOT NULL,
    amount         NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    duration_days  INT NOT NULL CHECK (duration_days > 0),
    proposal       TEXT NOT NULL,
    status         TEXT(10) DEFAULT 'Pending'
                   CHECK (status IN ('Pending','Accepted','Rejected','Withdrawn')),
    bid_date       TEXT DEFAULT (datetime('now','localtime')),
    UNIQUE (project_id, contractor_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (contractor_id) REFERENCES contractors(contractor_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS contracts (
    contract_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INT NOT NULL UNIQUE,
    contractor_id  INT NOT NULL,
    final_amount   NUMERIC(10,2) NOT NULL CHECK (final_amount > 0),
    start_date     TEXT NOT NULL,
    end_date       TEXT NOT NULL,
    status         TEXT(10) DEFAULT 'Active'
                   CHECK (status IN ('Active','Completed','Cancelled')),
    created_at     TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (contractor_id) REFERENCES contractors(contractor_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS milestones (
    milestone_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id   INT NOT NULL,
    title         TEXT(120) NOT NULL,
    description   TEXT,
    due_date      TEXT NOT NULL,
    amount        NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    status        TEXT(10) DEFAULT 'Pending'
                  CHECK (status IN ('Pending','Completed','Approved','Paid')),
    work_note     TEXT,
    rework_remark TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    milestone_id INT NOT NULL UNIQUE,
    amount       NUMERIC(10,2) NOT NULL,
    tax          NUMERIC(10,2) NOT NULL,
    total_paid   NUMERIC(10,2) NOT NULL,
    mode         TEXT(6) NOT NULL CHECK (mode IN ('Cash','UPI','Card')),
    paid_on      TEXT NOT NULL,
    FOREIGN KEY (milestone_id) REFERENCES milestones(milestone_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INT NOT NULL UNIQUE,
    reviewer_id INT NOT NULL,
    rating      INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
    note_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INT NOT NULL,
    message    TEXT(200) NOT NULL,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_projects_status_city ON projects(status, city);
CREATE INDEX IF NOT EXISTS idx_bids_project_status  ON bids(project_id, status);
CREATE INDEX IF NOT EXISTS idx_payments_paid_on     ON payments(paid_on);
