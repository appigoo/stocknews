# auth.py
import streamlit as st
import gspread
import hashlib
import hmac
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# ── 常數設定 ──────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]
SESSION_TIMEOUT_MINUTES = 60  # 登入逾時時間


# ── 連接 Google Sheets ────────────────────────────────
@st.cache_resource(ttl=300)
def _get_user_sheet():
    """從 Streamlit Secrets 讀取憑證並連接 Google Sheets"""
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet_url = st.secrets["auth_sheet"]["url"]
    return client.open_by_url(sheet_url).sheet1


def _fetch_users() -> dict:
    """讀取所有用戶（username -> {password_hash, role, active}）"""
    try:
        sheet = _get_user_sheet()
        records = sheet.get_all_records()
        return {
            r["username"]: {
                "password_hash": r["password_hash"],
                "role": r.get("role", "user"),
                "active": str(r.get("active", "TRUE")).upper() == "TRUE",
            }
            for r in records
            if r.get("username")
        }
    except Exception as e:
        st.error(f"無法讀取用戶資料：{e}")
        return {}


# ── 密碼工具 ──────────────────────────────────────────
def hash_password(password: str) -> str:
    """產生密碼 hash（SHA-256 + secret pepper）"""
    pepper = st.secrets.get("auth_sheet", {}).get("pepper", "default_pepper_change_me")
    return hashlib.sha256(f"{password}{pepper}".encode()).hexdigest()


def _verify_password(password: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), stored_hash)


# ── Session 管理 ──────────────────────────────────────
def _init_session():
    defaults = {
        "authenticated": False,
        "username": None,
        "role": None,
        "login_time": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _is_session_valid() -> bool:
    if not st.session_state.get("authenticated"):
        return False
    login_time = st.session_state.get("login_time")
    if login_time is None:
        return False
    elapsed = datetime.now() - login_time
    return elapsed < timedelta(minutes=SESSION_TIMEOUT_MINUTES)


def logout():
    """登出並清除 Session"""
    for key in ["authenticated", "username", "role", "login_time"]:
        st.session_state[key] = None
    st.session_state["authenticated"] = False
    st.rerun()


# ── 登入 UI ───────────────────────────────────────────
def _show_login_form():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 請登入")
        username = st.text_input("用戶名稱", key="login_username")
        password = st.text_input("密碼", type="password", key="login_password")

        if st.button("登入", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("請輸入用戶名稱及密碼")
                return

            users = _fetch_users()

            if username not in users:
                st.error("用戶名稱或密碼錯誤")
                return

            user = users[username]

            if not user["active"]:
                st.error("此帳號已被停用，請聯絡管理員")
                return

            if not _verify_password(password, user["password_hash"]):
                st.error("用戶名稱或密碼錯誤")
                return

            # 登入成功
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["role"] = user["role"]
            st.session_state["login_time"] = datetime.now()
            st.rerun()


# ── 頂部登入狀態欄 ────────────────────────────────────
def _show_user_bar():
    col1, col2, col3 = st.columns([6, 2, 1])
    with col2:
        st.caption(f"👤 {st.session_state['username']} ({st.session_state['role']})")
    with col3:
        if st.button("登出", key="logout_btn"):
            logout()


# ── 主入口：require_auth() ────────────────────────────
def require_auth():
    """
    在主程式頂部呼叫此函數。
    - 未登入 → 顯示登入頁面，阻止繼續執行
    - Session 逾時 → 自動登出
    - 已登入 → 顯示頂部用戶欄，繼續執行主程式
    """
    _init_session()

    if not _is_session_valid():
        if st.session_state.get("authenticated"):
            st.warning("⏰ 登入已逾時，請重新登入")
            logout()
        _show_login_form()
        st.stop()  # ← 阻止主程式繼續執行

    _show_user_bar()


# ── 權限控制工具 ──────────────────────────────────────
def get_current_user() -> str:
    return st.session_state.get("username", "")


def get_current_role() -> str:
    return st.session_state.get("role", "")


def require_role(allowed_roles: list):
    """用於保護特定區塊，例如管理員功能"""
    if get_current_role() not in allowed_roles:
        st.error("🚫 你沒有權限查看此內容")
        st.stop()
