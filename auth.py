# auth.py

import json
import os
import hashlib
import secrets
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _load_db() -> dict:
    """Load the JSON database; seed two default users if the file doesn't exist."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    # ── seed data ──────────────────────────────────────────────
    db = {
        "users": {
            "alice": {
                "password": _hash_password("alice123"),
                "nickname": "Alice",
                "created_at": datetime.now().isoformat(),
                "friends": ["bob"],
                "friend_requests_in": [],
                "friend_requests_out": [],
            },
            "bob": {
                "password": _hash_password("bob123"),
                "nickname": "Bob",
                "created_at": datetime.now().isoformat(),
                "friends": ["alice"],
                "friend_requests_in": [],
                "friend_requests_out": [],
            },
        },
        "tokens": {},  # token -> username
    }
    _save_db(db)
    return db


def _save_db(db: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════

class Auth:

    @staticmethod
    def login(username: str, password: str) -> dict:
        db = _load_db()
        user = db["users"].get(username)
        if not user or user["password"] != _hash_password(password):
            return {"success": False, "error": "用户名或密码错误"}

        token = secrets.token_hex(16)
        db["tokens"][token] = username
        _save_db(db)
        return {
            "success": True,
            "token": token,
            "username": username,
            "nickname": user["nickname"],
        }

    @staticmethod
    def register(username: str, password: str, nickname: str = "") -> dict:
        db = _load_db()
        if username in db["users"]:
            return {"success": False, "error": "用户名已存在"}
        if len(username) < 2 or len(password) < 4:
            return {"success": False, "error": "用户名至少2位，密码至少4位"}

        db["users"][username] = {
            "password": _hash_password(password),
            "nickname": nickname or username,
            "created_at": datetime.now().isoformat(),
            "friends": [],
            "friend_requests_in": [],
            "friend_requests_out": [],
        }
        _save_db(db)

        token = secrets.token_hex(16)
        db["tokens"][token] = username
        _save_db(db)
        return {
            "success": True,
            "token": token,
            "username": username,
            "nickname": nickname or username,
        }

    @staticmethod
    def verify_token(token: str) -> str | None:
        """Return username if valid, else None."""
        db = _load_db()
        return db["tokens"].get(token)

    @staticmethod
    def logout(token: str):
        db = _load_db()
        db["tokens"].pop(token, None)
        _save_db(db)


# ══════════════════════════════════════════════════════════════
# FRIENDS
# ══════════════════════════════════════════════════════════════

class FriendManager:

    @staticmethod
    def send_request(from_user: str, to_user: str) -> dict:
        db = _load_db()
        if to_user not in db["users"]:
            return {"success": False, "error": "目标用户不存在"}
        if from_user == to_user:
            return {"success": False, "error": "不能添加自己为好友"}

        me     = db["users"][from_user]
        target = db["users"][to_user]

        if to_user in me["friends"]:
            return {"success": False, "error": "你们已经是好友了"}
        if to_user in me["friend_requests_out"]:
            return {"success": False, "error": "好友请求已发送，等待对方同意"}

        # if target already sent me a request → auto-accept
        if from_user in target["friend_requests_out"]:
            me["friends"].append(to_user)
            target["friends"].append(from_user)
            target["friend_requests_out"].remove(from_user)
            me["friend_requests_in"] = [
                u for u in me["friend_requests_in"] if u != to_user
            ]
            _save_db(db)
            return {"success": True, "message": f"已互相成为好友！"}

        me["friend_requests_out"].append(to_user)
        target["friend_requests_in"].append(from_user)
        _save_db(db)
        return {"success": True, "message": f"好友请求已发送给 {to_user}"}

    @staticmethod
    def accept_request(username: str, from_user: str) -> dict:
        db = _load_db()
        me     = db["users"][username]
        sender = db["users"].get(from_user)

        if not sender:
            return {"success": False, "error": "用户不存在"}
        if from_user not in me["friend_requests_in"]:
            return {"success": False, "error": "没有来自该用户的好友请求"}

        me["friend_requests_in"].remove(from_user)
        sender["friend_requests_out"].remove(username)
        me["friends"].append(from_user)
        sender["friends"].append(username)
        _save_db(db)
        return {"success": True, "message": f"已添加 {from_user} 为好友"}

    @staticmethod
    def reject_request(username: str, from_user: str) -> dict:
        db = _load_db()
        me     = db["users"][username]
        sender = db["users"].get(from_user)

        if not sender:
            return {"success": False, "error": "用户不存在"}
        if from_user not in me["friend_requests_in"]:
            return {"success": False, "error": "没有来自该用户的好友请求"}

        me["friend_requests_in"].remove(from_user)
        sender["friend_requests_out"].remove(username)
        _save_db(db)
        return {"success": True, "message": f"已拒绝 {from_user} 的好友请求"}

    @staticmethod
    def remove_friend(username: str, friend: str) -> dict:
        db = _load_db()
        me   = db["users"][username]
        them = db["users"].get(friend)

        if not them or friend not in me["friends"]:
            return {"success": False, "error": "该用户不是你的好友"}

        me["friends"].remove(friend)
        them["friends"].remove(username)
        _save_db(db)
        return {"success": True, "message": f"已删除好友 {friend}"}

    @staticmethod
    def get_friends(username: str) -> dict:
        db   = _load_db()
        user = db["users"][username]
        return {
            "friends": user["friends"],
            "requests_in": user["friend_requests_in"],
            "requests_out": user["friend_requests_out"],
        }
