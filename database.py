"""database.py - the only module that talks to the database.

Primary engine : MySQL 8.0 (as documented in the Black Book).
Demo fallback  : SQLite (zero-configuration) - used automatically when the
mysql-connector driver or a running MySQL server is not available, so the
project can be demonstrated anywhere (DB_MODE=sqlite forces it).
"""
import os, re, shutil, datetime

MODE = os.environ.get("DB_MODE", "auto").strip().lower()   # mysql | sqlite | auto
DB_NAME = os.environ.get("DB_NAME", "renova_db")
SQLITE_FILE = os.environ.get("SQLITE_FILE",
                             os.path.join("instance", "renova.db"))
_MYSQL_POOL = None
_sqlite_mod = None


# --------------------------------------------------------------------------- 
# engine selection
# ---------------------------------------------------------------------------
def _active_mode():
    """Decide mysql vs sqlite once ('auto' probes MySQL, falls back)."""
    global _MYSQL_POOL, _sqlite_mod
    if MODE in ("mysql", "sqlite"):
        return MODE
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASS", ""),
            connection_timeout=2)
        conn.close()
        return "mysql"
    except Exception:
        return "sqlite"


def _sql_for_sqlite(sql):
    """Translate the few MySQL-only constructs used by the project."""
    s = sql.replace("%s", "?")
    s = re.sub(r"\bDATE\(", "date(", s)
    # CONCAT(a, b, c)  ->  (a || b || c)   [top-level commas only]
    m = re.search(r"\bCONCAT\(([^()]*)\)", s)
    while m:
        args = [a.strip() for a in m.group(1).split(",")]
        s = s[:m.start()] + "(" + " || ".join(args) + ")" + s[m.end():]
        m = re.search(r"\bCONCAT\(([^()]*)\)", s)
    return s


# ---------------------------------------------------------------------------
# MySQL path (original documented implementation)
# ---------------------------------------------------------------------------
def _mysql_conn(with_db=True):
    import mysql.connector
    kw = dict(host=os.environ.get("DB_HOST", "localhost"),
              user=os.environ.get("DB_USER", "root"),
              password=os.environ.get("DB_PASS", ""),
              autocommit=False)
    if with_db:
        kw["database"] = DB_NAME
    return mysql.connector.connect(**kw)


def _ensure_mysql_db():
    """Create the schema database if it does not exist yet."""
    conn = _mysql_conn(with_db=False)
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS %s "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci" % DB_NAME)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# public API (identical signatures for both engines)
# ---------------------------------------------------------------------------
def get_connection():
    """Return a connection; autocommit is OFF so routes control commits."""
    global _MYSQL_POOL
    if _active_mode() == "mysql":
        if _MYSQL_POOL is None:
            from mysql.connector import pooling
            _ensure_mysql_db()
            _MYSQL_POOL = pooling.MySQLConnectionPool(
                pool_name="renova", pool_size=5, pool_reset_session=True,
                host=os.environ.get("DB_HOST", "localhost"),
                user=os.environ.get("DB_USER", "root"),
                password=os.environ.get("DB_PASS", ""),
                database=DB_NAME, autocommit=False)
        return _MYSQL_POOL.get_connection()
    # sqlite path ------------------------------------------------------------
    global _sqlite_mod
    if _sqlite_mod is None:
        import sqlite3
        _sqlite_mod = sqlite3
    os.makedirs(os.path.dirname(SQLITE_FILE) or ".", exist_ok=True)
    conn = _sqlite_mod.connect(SQLITE_FILE, timeout=10)
    conn.row_factory = _sqlite_mod.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return _SQLiteConn(conn)


class _SQLiteCursor:
    def __init__(self, cur):
        self._cur = cur
    def execute(self, sql, params=()):
        self._cur.execute(_sql_for_sqlite(sql), tuple(params))
        return self
    def fetchone(self):  return self._cur.fetchone()
    def fetchall(self):  return self._cur.fetchall()
    lastrowid = property(lambda self: self._cur.lastrowid)
    rowcount  = property(lambda self: self._cur.rowcount)


class _SQLiteConn:
    """Thin wrapper so routes can use conn.cursor()/commit()/close()."""
    def __init__(self, conn):
        self._conn = conn
    def cursor(self, *a, **k):
        return _SQLiteCursor(self._conn.cursor())
    def commit(self):   self._conn.commit()
    def rollback(self): self._conn.rollback()
    def close(self):    self._conn.close()


def execute(sql, params=()):
    """Run one INSERT / UPDATE / DELETE and commit. Returns lastrowid."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)          # parameterised - no SQL injection
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def fetch_all(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return [dict(r) if not isinstance(r, dict) else r for r in cur.fetchall()]
    finally:
        conn.close()

def fetch_one(sql, params=()):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None

def transaction(operations):
    """operations = list of (sql, params) executed atomically.
    Returns the lastrowid of the final statement."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        last = 0
        for sql, params in operations:
            cur.execute(sql, params)
            last = cur.lastrowid
        conn.commit()
        return last
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Create the schema (first run only) and load demo data if empty."""
    first_run = False
    conn = get_connection()
    cur = conn.cursor()
    if _active_mode() == "mysql":
        cur.execute("SHOW TABLES LIKE 'users'")
        first_run = cur.fetchone() is None
    else:
        cur.execute("SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='users'")
        first_run = cur.fetchone() is None
    conn.close()
    if first_run:
        schema = "schema.sql" if _active_mode() == "mysql" else "schema_sqlite.sql"
        conn = get_connection()
        cur = conn.cursor()
        for stmt in open(schema).read().split(";"):
            if stmt.strip():
                cur.execute(stmt)
        conn.commit()
        conn.close()
    # seed demo accounts on a fresh database
    users = fetch_one("SELECT COUNT(*) AS n FROM users")
    if users and users["n"] == 0:
        try:
            import seed
            seed.run()
            print("[renova] demo data loaded - login admin@renova.in / Admin@123")
        except Exception as e:                       # never block startup
            print("[renova] demo seed skipped:", e)

def backup_db(folder="backup"):
    os.makedirs(folder, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if _active_mode() == "mysql":
        name = "renova_" + stamp + ".sql"
        path = os.path.join(folder, name)
        cmd = ["mysqldump", "-u", os.environ.get("DB_USER", "root"), DB_NAME]
        if os.environ.get("DB_PASS"):
            cmd = ["mysqldump", "-u", os.environ.get("DB_USER", "root"),
                   "-p" + os.environ.get("DB_PASS", ""), DB_NAME]
        with open(path, "w") as f:
            import subprocess
            subprocess.run(cmd, stdout=f, check=True)
    else:
        name = "renova_" + stamp + ".db"
        path = os.path.join(folder, name)
        shutil.copy2(SQLITE_FILE, path)
    return path
