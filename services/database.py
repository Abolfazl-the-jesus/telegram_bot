import sqlite3
from pathlib import Path

DB_PATH = Path('data') / 'superbot.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE,
            username TEXT,
            is_premium INTEGER DEFAULT 0,
            user_best_quality TEXT DEFAULT NULL,
            cookie_enc_path TEXT DEFAULT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proxy TEXT UNIQUE,
            added_at INTEGER DEFAULT (strftime('%s','now')),
            last_checked INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0,
            quarantined INTEGER DEFAULT 0
        )
    ''')
        # users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        gender TEXT,
        province TEXT,
        city TEXT,
        profile_pic TEXT,
        status TEXT DEFAULT 'idle',    -- idle, searching, chatting
        partner_id INTEGER,
        credits INTEGER DEFAULT 0,
        created_at INTEGER DEFAULT (strftime('%s','now'))
    )
    """)
    
    # invites table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invites (
        code TEXT PRIMARY KEY,
        inviter_id INTEGER,
        created_at INTEGER DEFAULT (strftime('%s','now'))
    )
    """)
        # used_invites: record which user used which code (to prevent reuse)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS used_invites (
        user_id INTEGER PRIMARY KEY,
        code TEXT,
        used_at INTEGER DEFAULT (strftime('%s','now'))
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_id INTEGER,
        reported_id INTEGER,
        reason TEXT,
        created_at INTEGER DEFAULT (strftime('%s','now'))
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        blocked_id INTEGER,
        created_at INTEGER DEFAULT (strftime('%s','now'))
    )
    """)
    conn.commit()
    conn.close()

def get_user_best_quality(tg_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT user_best_quality FROM users WHERE tg_id=?', (tg_id,))
    res = cur.fetchone()
    conn.close()
    return res[0] if res else None

def set_user_best_quality(tg_id: int, format_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO users (tg_id, user_best_quality) VALUES (?, ?) ON CONFLICT(tg_id) DO UPDATE SET user_best_quality=excluded.user_best_quality', (tg_id, format_id))
    conn.commit()
    conn.close()

def set_user_cookie_path(tg_id: int, enc_path: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO users (tg_id, cookie_enc_path) VALUES (?, ?) ON CONFLICT(tg_id) DO UPDATE SET cookie_enc_path=excluded.cookie_enc_path', (tg_id, enc_path))
    conn.commit()
    conn.close()

def get_user_cookie_path(tg_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT cookie_enc_path FROM users WHERE tg_id=?', (tg_id,))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else None

def add_proxy_to_db(proxy: str):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute('INSERT OR IGNORE INTO proxies(proxy, is_active, quarantined) VALUES(?, 0, 0)', (proxy,))
        conn.commit()
        return True
    finally:
        conn.close()

def remove_proxy_from_db(proxy: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM proxies WHERE proxy=?', (proxy,))
    conn.commit()
    conn.close()

def quarantine_proxy_in_db(proxy: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO proxies(proxy, is_active, quarantined) VALUES(?, 0, 1)', (proxy,))
    cur.execute('UPDATE proxies SET quarantined=1 WHERE proxy=?', (proxy,))
    conn.commit()
    conn.close()

def list_proxies_from_db(limit: int = 100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, proxy, added_at, last_checked, is_active, fail_count, quarantined FROM proxies ORDER BY id DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_active_proxies_from_db(limit: int = 50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT proxy FROM proxies WHERE is_active=1 AND quarantined=0 ORDER BY fail_count ASC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def mark_proxy_failed_in_db(proxy: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE proxies SET fail_count = fail_count + 1, last_checked = strftime("%s","now") WHERE proxy=?', (proxy,))
    cur.execute('SELECT fail_count FROM proxies WHERE proxy=?', (proxy,))
    r = cur.fetchone()
    if r and r[0] >= 3:
        cur.execute('UPDATE proxies SET is_active=0 WHERE proxy=?', (proxy,))
    conn.commit()
    conn.close()

def mark_proxy_ok_in_db(proxy: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE proxies SET fail_count = 0, is_active=1, last_checked = strftime("%s","now"), quarantined=0 WHERE proxy=?', (proxy,))
    conn.commit()
    conn.close()


# ---------------- user lifecycle ----------------

def create_user_if_not_exists(user_id: int, username: str = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, username, credits) VALUES (?, ?, ?)",
                (user_id, username or "", 10))  # default 10 credits on first create
    conn.commit()
    conn.close()

def set_username(user_id: int, username: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET username = ? WHERE user_id = ?", (username or "", user_id))
    conn.commit()
    conn.close()

# profile setters
def set_gender(user_id: int, gender: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET gender = ? WHERE user_id = ?", (gender, user_id))
    conn.commit()
    conn.close()

def set_province(user_id: int, province: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET province = ? WHERE user_id = ?", (province, user_id))
    conn.commit()
    conn.close()

def set_city(user_id: int, city: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET city = ? WHERE user_id = ?", (city, user_id))
    conn.commit()
    conn.close()

def set_profile_pic(user_id: int, file_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET profile_pic = ? WHERE user_id = ?", (file_id, user_id))
    conn.commit()
    conn.close()

def is_profile_complete(user_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT gender, province, city, profile_pic FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row and all(row))

# ---------------- credits & invites ----------------

def get_credits(user_id: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else 0

def add_credits(user_id: int, amount: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def consume_credit(user_id: int, amount: int = 1) -> bool:
    """
    Try to consume credits. Return True if success, False if insufficient credits.
    """
    if get_credits(user_id) < amount:
        return False
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET credits = credits - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()
    return True

def create_invite(code: str, inviter_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO invites (code, inviter_id) VALUES (?, ?)", (code, inviter_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def use_invite_for_user(code: str, new_user_id: int) -> bool:
    """
    If code exists and was not used by this user:
    - give inviter +5 credits
    - give new_user +5 credits (set initial credits to 5 if first create)
    - record usage in used_invites
    Return True if applied, False otherwise.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT inviter_id FROM invites WHERE code = ?", (code,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return False
    inviter_id = r[0]
    # check if new_user already used an invite
    cur.execute("SELECT code FROM used_invites WHERE user_id = ?", (new_user_id,))
    if cur.fetchone():
        conn.close()
        return False
    # apply credits
    cur.execute("INSERT OR REPLACE INTO users (user_id, credits) VALUES (?, COALESCE((SELECT credits FROM users WHERE user_id=?),0))", (new_user_id, new_user_id))
    # give new_user +5
    cur.execute("UPDATE users SET credits = credits + 5 WHERE user_id = ?", (new_user_id,))
    # give inviter +5
    cur.execute("UPDATE users SET credits = credits + 5 WHERE user_id = ?", (inviter_id,))
    # record used_invite
    cur.execute("INSERT INTO used_invites (user_id, code) VALUES (?, ?)", (new_user_id, code))
    conn.commit()
    conn.close()
    return True

# ---------------- status / matching ----------------

def set_status(user_id: int, status: str, partner_id: int = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET status = ?, partner_id = ? WHERE user_id = ?", (status, partner_id, user_id))
    conn.commit()
    conn.close()

def get_status(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT status, partner_id FROM users WHERE user_id = ?", (user_id,))
    r = cur.fetchone()
    conn.close()
    return r if r else ("idle", None)

def find_partner(user_id: int, gender: str = None, province: str = None):
    """
    Return a candidate user_id or None. Candidate must be status='searching' and not blocked.
    """
    conn = get_conn()
    cur = conn.cursor()
    query = "SELECT user_id FROM users WHERE status = 'searching' AND user_id != ?"
    params = [user_id]
    if gender:
        query += " AND gender = ?"
        params.append(gender)
    if province:
        query += " AND province = ?"
        params.append(province)
    query += " ORDER BY created_at LIMIT 1"
    cur.execute(query, tuple(params))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else None

def get_online_users(limit: int = 50):
    """
    Return list of dicts for users who are 'idle' (available).
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, gender, province, city FROM users WHERE status = 'idle' LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [{"user_id": r[0], "username": r[1], "gender": r[2], "province": r[3], "city": r[4]} for r in rows]

# ---------------- blocks / reports ----------------

def block_user(user_id: int, blocked_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO blocks (user_id, blocked_id) VALUES (?, ?)", (user_id, blocked_id))
    conn.commit()
    conn.close()

def is_blocked(a: int, b: int) -> bool:
    """
    Return True if a has blocked b or b has blocked a.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM blocks WHERE (user_id=? AND blocked_id=?) OR (user_id=? AND blocked_id=?) LIMIT 1", (a, b, b, a))
    r = cur.fetchone()
    conn.close()
    return bool(r)

def report_user(reporter_id: int, reported_id: int, reason: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO reports (reporter_id, reported_id, reason) VALUES (?, ?, ?)", (reporter_id, reported_id, reason))
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    init_db()