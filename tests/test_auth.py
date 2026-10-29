"""账号与个人档案测试。"""

import sqlite3

import pytest

from pathway.auth import UserStore, hash_password_csy


@pytest.fixture()
def store_csy(tmp_path):
    """每个用例用独立的临时数据库。"""
    return UserStore(tmp_path / "users.db")


def test_register_and_login_csy(store_csy):
    """注册后能用同一组账号密码登录。"""
    ok, message, user = store_csy.register_csy("student", "123456")
    assert ok and user["username"] == "student"
    ok2, message2, user2 = store_csy.login_csy("student", "123456")
    assert ok2 and user2["user_id"] == user["user_id"]


def test_duplicate_username_rejected_csy(store_csy):
    """重复用户名应被拒绝。"""
    store_csy.register_csy("student", "123456")
    ok, message, _ = store_csy.register_csy("student", "abcdef")
    assert ok is False
    assert "已经" in message


def test_wrong_password_rejected_csy(store_csy):
    """密码错误应被拒绝。"""
    store_csy.register_csy("student", "123456")
    ok, message, _ = store_csy.login_csy("student", "654321")
    assert ok is False
    assert message == "密码不正确"


def test_unknown_user_rejected_csy(store_csy):
    """不存在的用户应被拒绝。"""
    ok, message, _ = store_csy.login_csy("nobody", "123456")
    assert ok is False
    assert "不存在" in message


def test_short_password_rejected_csy(store_csy):
    """密码太短应被拒绝。"""
    ok, message, _ = store_csy.register_csy("student", "123")
    assert ok is False
    assert "6" in message


def test_password_not_stored_in_plain_text_csy(store_csy):
    """数据库里不能出现明文密码。"""
    store_csy.register_csy("student", "mysecret123")
    with store_csy.connect_csy() as conn:
        row = conn.execute("SELECT password_hash, salt FROM users WHERE username='student'").fetchone()
    assert row["password_hash"] != "mysecret123"
    assert len(row["password_hash"]) == 64      # SHA-256 十六进制
    assert row["salt"]


def test_hash_is_salted_csy():
    """同一密码配不同盐应得到不同哈希。"""
    assert hash_password_csy("abc123", "00" * 16) != hash_password_csy("abc123", "11" * 16)


def test_profile_roundtrip_csy(store_csy):
    """个人档案保存后能读回，未填写字段为空。"""
    ok, _, user = store_csy.register_csy("student", "123456")
    assert store_csy.get_profile_csy(user["user_id"])["onboarded"] == 0
    store_csy.save_profile_csy(
        user["user_id"], education_level="专科", major="计算机",
        grade="大二", goal="升学（专插本 / 考研）", onboarded=1)
    profile = store_csy.get_profile_csy(user["user_id"])
    assert profile["education_level"] == "专科"
    assert profile["major"] == "计算机"
    assert profile["onboarded"] == 1


def test_profile_update_is_partial_csy(store_csy):
    """只传部分字段时，其他字段保持不变。"""
    ok, _, user = store_csy.register_csy("student", "123456")
    store_csy.save_profile_csy(user["user_id"], education_level="本科", grade="大三")
    store_csy.save_profile_csy(user["user_id"], major="会计")
    profile = store_csy.get_profile_csy(user["user_id"])
    assert profile["education_level"] == "本科"
    assert profile["grade"] == "大三"
    assert profile["major"] == "会计"


def test_profile_undergrad_type_roundtrip_csy(store_csy):
    """本科类型应能保存并通过个人档案重新读取。"""
    ok, _, user = store_csy.register_csy("student", "123456")
    store_csy.save_profile_csy(
        user["user_id"], education_level="本科", undergrad_type="专插本本科")
    profile = store_csy.get_profile_csy(user["user_id"])
    assert profile["undergrad_type"] == "专插本本科"


def test_old_profile_table_adds_undergrad_type_csy(tmp_path):
    """旧 users.db 启动时应自动补上本科类型字段，不要求用户重建数据库。"""
    path = tmp_path / "old_users.db"
    with sqlite3.connect(str(path)) as conn:
        conn.executescript("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT
            );
            CREATE TABLE user_profiles (
                user_id INTEGER PRIMARY KEY,
                education_level TEXT,
                major TEXT,
                grade TEXT,
                goal TEXT,
                onboarded INTEGER DEFAULT 0,
                updated_at TEXT
            );
        """)
    store = UserStore(path)
    with store.connect_csy() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(user_profiles)")}
    assert "undergrad_type" in columns


def test_favorite_crud_csy(store_csy):
    """收藏应支持新增、查询、修改备注和删除。"""
    _, _, user = store_csy.register_csy("student", "123456")
    favorite_id = store_csy.add_favorite_csy(
        user["user_id"], "zsb_major", "2026|080901",
        "计算机科学与技术", "初始备注")
    rows = store_csy.list_favorites_csy(user["user_id"])
    assert len(rows) == 1
    assert rows[0]["id"] == favorite_id
    assert rows[0]["note"] == "初始备注"
    assert store_csy.update_favorite_csy(user["user_id"], favorite_id, "目标专业")
    assert store_csy.list_favorites_csy(user["user_id"], "zsb_major")[0]["note"] == "目标专业"
    assert store_csy.delete_favorite_csy(user["user_id"], favorite_id)
    assert store_csy.list_favorites_csy(user["user_id"]) == []


def test_favorite_duplicate_upserts_csy(store_csy):
    """同一用户重复收藏同类项目时，不产生重复记录。"""
    _, _, user = store_csy.register_csy("student", "123456")
    first = store_csy.add_favorite_csy(
        user["user_id"], "kaogong_job", "job-1", "广州岗位", "旧备注")
    second = store_csy.add_favorite_csy(
        user["user_id"], "kaogong_job", "job-1", "广州岗位", "新备注")
    rows = store_csy.list_favorites_csy(user["user_id"], "kaogong_job")
    assert first == second
    assert len(rows) == 1
    assert rows[0]["note"] == "新备注"


def test_favorite_is_isolated_by_user_csy(store_csy):
    """一个用户不能修改或删除另一个用户的收藏。"""
    _, _, first = store_csy.register_csy("first", "123456")
    _, _, second = store_csy.register_csy("second", "123456")
    favorite_id = store_csy.add_favorite_csy(
        first["user_id"], "kaoyan_discipline", "工学", "工学考研国家线")
    assert store_csy.update_favorite_csy(second["user_id"], favorite_id, "越权修改") is False
    assert store_csy.delete_favorite_csy(second["user_id"], favorite_id) is False
    assert store_csy.list_favorites_csy(first["user_id"])[0]["note"] == ""
