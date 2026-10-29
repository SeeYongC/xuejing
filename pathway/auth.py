"""账号与个人档案。

账号存在独立的 users.db 里（可写目录），与随程序分发的只读参考数据
pathway.db 分开，避免程序升级时覆盖用户数据。

密码用 PBKDF2-HMAC-SHA256 加盐哈希后保存，数据库里不存明文。
"""

import hashlib
import os
import sqlite3

TABLE_SQL_CSY = """
CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    salt           TEXT NOT NULL,
    created_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id          INTEGER PRIMARY KEY,
    education_level  TEXT,                -- 专科 / 本科
    undergrad_type   TEXT,                -- 普通四年制本科 / 专插本本科 / 其他
    major            TEXT,                -- 专业
    grade            TEXT,                -- 大一 / 大二 / 大三 / 大四 / 已毕业
    goal             TEXT,                -- 升学 / 就业 / 还没想好
    score            TEXT,                -- 成绩水平（自评区间）
    budget           TEXT,                -- 可接受的教育预算
    region           TEXT,                -- 目标地区
    city             TEXT,                -- 当前所在城市
    onboarded        INTEGER DEFAULT 0,   -- 是否完成引导
    updated_at       TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_favorites (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    item_type   TEXT NOT NULL,
    item_key    TEXT NOT NULL,
    item_title  TEXT NOT NULL,
    note        TEXT DEFAULT '',
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, item_type, item_key)
);
"""

PBKDF2_ROUNDS_CSY = 120000

EDUCATION_LEVELS_CSY = ["专科", "本科"]
GRADES_CSY = ["大一", "大二", "大三", "大四", "已毕业"]
GOALS_CSY = ["升学（专插本 / 考研）", "直接就业", "还没想好"]
SCORE_BANDS_CSY = ["专业前 10%", "专业前 30%", "专业中游", "专业后 30%", "不确定"]
BUDGETS_CSY = ["1 万以内", "1-3 万", "3-6 万", "6 万以上", "没考虑过"]
REGIONS_CSY = ["广州", "深圳", "珠三角其他城市", "粤东", "粤西", "粤北", "广东省外", "没想好"]


def hash_password_csy(password: str, salt: str) -> str:
    """用 PBKDF2-HMAC-SHA256 计算密码哈希。"""
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                 bytes.fromhex(salt), PBKDF2_ROUNDS_CSY)
    return digest.hex()


class UserStore:
    """用户账号与档案的本地存储。"""

    def __init__(self, db_path):
        self.db_path = str(db_path)
        self.ensure_tables_csy()

    def connect_csy(self) -> sqlite3.Connection:
        """建立连接，结果可按列名取值。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_tables_csy(self) -> None:
        """首次运行时建表。"""
        with self.connect_csy() as conn:
            conn.executescript(TABLE_SQL_CSY)
            # 旧版本的用户库没有这几个字段，启动时自动补列
            existing = {row[1] for row in conn.execute("PRAGMA table_info(user_profiles)")}
            for column in ("undergrad_type", "score", "budget", "region", "city"):
                if column not in existing:
                    conn.execute("ALTER TABLE user_profiles ADD COLUMN %s TEXT" % column)

    # ------------------------------------------------------ 注册 / 登录

    def register_csy(self, username: str, password: str) -> tuple:
        """注册新账号，返回 (是否成功, 提示信息, 用户信息或 None)。"""
        username = username.strip()
        if len(username) < 2:
            return False, "用户名至少 2 个字符", None
        if len(password) < 6:
            return False, "密码至少 6 位", None

        salt = os.urandom(16).hex()
        password_hash = hash_password_csy(password, salt)
        try:
            with self.connect_csy() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                    (username, password_hash, salt))
                user_id = cursor.lastrowid
                conn.execute("INSERT INTO user_profiles (user_id) VALUES (?)", (user_id,))
            return True, "注册成功", {"user_id": user_id, "username": username}
        except sqlite3.IntegrityError:
            return False, "这个用户名已经被注册了", None

    def login_csy(self, username: str, password: str) -> tuple:
        """校验账号密码，返回 (是否成功, 提示信息, 用户信息或 None)。"""
        username = username.strip()
        with self.connect_csy() as conn:
            row = conn.execute(
                "SELECT user_id, username, password_hash, salt FROM users "
                "WHERE username = ?", (username,)).fetchone()
        if row is None:
            return False, "用户名不存在", None
        if hash_password_csy(password, row["salt"]) != row["password_hash"]:
            return False, "密码不正确", None
        return True, "登录成功", {"user_id": row["user_id"], "username": row["username"]}

    def user_exists_csy(self, username: str) -> bool:
        """判断用户名是否已被占用。"""
        with self.connect_csy() as conn:
            row = conn.execute("SELECT 1 FROM users WHERE username = ?",
                               (username.strip(),)).fetchone()
        return row is not None

    # ------------------------------------------------------ 个人档案

    def get_profile_csy(self, user_id: int) -> dict:
        """读取个人档案；没有记录时返回空字段。"""
        with self.connect_csy() as conn:
            row = conn.execute(
                "SELECT education_level, undergrad_type, major, grade, goal, score, budget, "
                "region, city, onboarded "
                "FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            return {"education_level": "", "undergrad_type": "", "major": "", "grade": "",
                    "goal": "", "score": "", "budget": "", "region": "",
                    "city": "", "onboarded": 0}
        return dict(row)

    def save_profile_csy(self, user_id: int, **fields) -> None:
        """保存个人档案（只更新传入的字段）。"""
        allowed = {"education_level", "undergrad_type", "major", "grade", "goal", "score",
                   "budget", "region", "city", "onboarded"}
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return
        assignments = ", ".join("%s = ?" % key for key in updates)
        values = list(updates.values()) + [user_id]
        with self.connect_csy() as conn:
            conn.execute(
                "UPDATE user_profiles SET %s, updated_at = datetime('now') "
                "WHERE user_id = ?" % assignments, values)

    def delete_user_csy(self, user_id: int) -> None:
        """删除账号及其档案，仅用于测试。"""
        with self.connect_csy() as conn:
            conn.execute("DELETE FROM user_favorites WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    # ------------------------------------------------------ 我的关注

    def add_favorite_csy(self, user_id: int, item_type: str, item_key: str,
                         item_title: str, note: str = "") -> int:
        """新增收藏；同一用户重复收藏同类项目时更新标题和备注。"""
        with self.connect_csy() as conn:
            existing = conn.execute(
                "SELECT id FROM user_favorites "
                "WHERE user_id = ? AND item_type = ? AND item_key = ?",
                (user_id, item_type, item_key),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE user_favorites SET item_title = ?, note = ?, "
                    "updated_at = datetime('now') WHERE id = ? AND user_id = ?",
                    (item_title, note, existing["id"], user_id),
                )
                return int(existing["id"])
            cursor = conn.execute(
                "INSERT INTO user_favorites "
                "(user_id, item_type, item_key, item_title, note) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, item_type, item_key, item_title, note),
            )
            return int(cursor.lastrowid)

    def list_favorites_csy(self, user_id: int, item_type: str = "全部") -> list:
        """读取当前用户的收藏，可按类型筛选。"""
        sql = (
            "SELECT id, item_type, item_key, item_title, note, "
            "created_at, updated_at FROM user_favorites WHERE user_id = ?"
        )
        params = [user_id]
        if item_type and item_type != "全部":
            sql += " AND item_type = ?"
            params.append(item_type)
        sql += " ORDER BY updated_at DESC, id DESC"
        with self.connect_csy() as conn:
            return [dict(row) for row in conn.execute(sql, params)]

    def update_favorite_csy(self, user_id: int, favorite_id: int, note: str) -> bool:
        """只修改当前用户收藏的备注，返回是否更新成功。"""
        with self.connect_csy() as conn:
            cursor = conn.execute(
                "UPDATE user_favorites SET note = ?, updated_at = datetime('now') "
                "WHERE id = ? AND user_id = ?",
                (note, favorite_id, user_id),
            )
            return cursor.rowcount > 0

    def delete_favorite_csy(self, user_id: int, favorite_id: int) -> bool:
        """删除当前用户的一条收藏，返回是否删除成功。"""
        with self.connect_csy() as conn:
            cursor = conn.execute(
                "DELETE FROM user_favorites WHERE id = ? AND user_id = ?",
                (favorite_id, user_id),
            )
            return cursor.rowcount > 0
