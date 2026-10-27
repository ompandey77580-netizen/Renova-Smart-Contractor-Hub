-- schema.sql - creates the database of renova_db (MySQL 8.0).
-- Eight core business tables + notifications (FR19).
CREATE DATABASE IF NOT EXISTS renova_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE renova_db;

CREATE TABLE users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(80)  NOT NULL,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash CHAR(64)     NOT NULL,
    salt          CHAR(32)     NOT NULL,
    role          ENUM('client','contractor','admin') NOT NULL,
    phone         VARCHAR(15)  NOT NULL,
    address       VARCHAR(150),
    city          VARCHAR(60),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE contractors (
    contractor_id    INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL UNIQUE,
    specialization   VARCHAR(120) NOT NULL,
    skills           VARCHAR(200),
    experience_years DECIMAL(4,1) NOT NULL DEFAULT 0,
    hourly_rate      DECIMAL(10,2) NOT NULL CHECK (hourly_rate > 0),
    city             VARCHAR(60)  NOT NULL,
    available        ENUM('Yes','No') DEFAULT 'Yes',
    rating_avg       DECIMAL(3,2) DEFAULT 0.00,
    verified         TINYINT(1)   DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE projects (
    project_id  INT AUTO_INCREMENT PRIMARY KEY,
    client_id   INT NOT NULL,
    title       VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    category    ENUM('Painting','Masonry','Carpentry','Electrical',
                     'Plumbing','Interior','Other') NOT NULL,
    budget_min  DECIMAL(10,2) NOT NULL CHECK (budget_min > 0),
    budget_max  DECIMAL(10,2) NOT NULL,
    city        VARCHAR(60) NOT NULL,
    start_date  DATE NOT NULL,
    deadline    DATE NOT NULL,
    status      ENUM('Open','In Progress','Completed','Cancelled')
                DEFAULT 'Open',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    CHECK (budget_max >= budget_min),
    CHECK (deadline >= start_date),
    FOREIGN KEY (client_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE bids (
    bid_id         INT AUTO_INCREMENT PRIMARY KEY,
    project_id     INT NOT NULL,
    contractor_id  INT NOT NULL,
    amount         DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    duration_days  INT NOT NULL CHECK (duration_days > 0),
    proposal       TEXT NOT NULL,
    status         ENUM('Pending','Accepted','Rejected','Withdrawn')
                   DEFAULT 'Pending',
    bid_date       DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_bid (project_id, contractor_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
        ON DELETE CASCADE,
    FOREIGN KEY (contractor_id) REFERENCES contractors(contractor_id)
        ON DELETE CASCADE
);

CREATE TABLE contracts (
    contract_id    INT AUTO_INCREMENT PRIMARY KEY,
    project_id     INT NOT NULL UNIQUE,
    contractor_id  INT NOT NULL,
    final_amount   DECIMAL(10,2) NOT NULL CHECK (final_amount > 0),
    start_date     DATE NOT NULL,
    end_date       DATE NOT NULL,
    status         ENUM('Active','Completed','Cancelled')
                   DEFAULT 'Active',
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
        ON DELETE CASCADE,
    FOREIGN KEY (contractor_id) REFERENCES contractors(contractor_id)
        ON DELETE CASCADE
);

CREATE TABLE milestones (
    milestone_id  INT AUTO_INCREMENT PRIMARY KEY,
    contract_id   INT NOT NULL,
    title         VARCHAR(120) NOT NULL,
    description   TEXT,
    due_date      DATE NOT NULL,
    amount        DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    status        ENUM('Pending','Completed','Approved','Paid')
                  DEFAULT 'Pending',
    work_note     TEXT,
    rework_remark TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
        ON DELETE CASCADE
);

CREATE TABLE payments (
    payment_id   INT AUTO_INCREMENT PRIMARY KEY,
    milestone_id INT NOT NULL UNIQUE,
    amount       DECIMAL(10,2) NOT NULL,
    tax          DECIMAL(10,2) NOT NULL,
    total_paid   DECIMAL(10,2) NOT NULL,
    mode         ENUM('Cash','UPI','Card') NOT NULL,
    paid_on      DATE NOT NULL,
    FOREIGN KEY (milestone_id) REFERENCES milestones(milestone_id)
        ON DELETE CASCADE
);

CREATE TABLE reviews (
    review_id   INT AUTO_INCREMENT PRIMARY KEY,
    contract_id INT NOT NULL UNIQUE,
    reviewer_id INT NOT NULL,
    rating      INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
        ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE notifications (
    note_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    message     VARCHAR(200) NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_projects_status_city ON projects(status, city);
CREATE INDEX idx_bids_project_status  ON bids(project_id, status);
CREATE INDEX idx_payments_paid_on     ON payments(paid_on);
