"""
Liên Quân Mobile (Arena of Valor) — tra cứu tài khoản
Hỗ trợ tìm theo nickname (tên ingame).
"""

from __future__ import annotations

import requests
import json

_session = requests.Session()
_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.5",
    "Referer": "https://lienquan.garena.vn/",
    "Origin": "https://lienquan.garena.vn",
})

_SERVER_MAP = {
    "vn":  "vn",  "vietnam":    "vn",
    "sg":  "sg",  "singapore":  "sg",
    "th":  "th",  "thailand":   "th",
    "id":  "id",  "indonesia":  "id",
    "tw":  "tw",  "taiwan":     "tw",
    "my":  "my",  "malaysia":   "my",
    "ph":  "ph",  "philippines":"ph",
    "la":  "la",  "laos":       "la",
    "mm":  "mm",  "myanmar":    "mm",
    "kr":  "kr",  "korea":      "kr",
    "na":  "na",  "americas":   "na",
    "eu":  "eu",  "europe":     "eu",
}

_RANK_MAP = {
    1: "Đồng", 2: "Bạc", 3: "Vàng", 4: "Bạch Kim",
    5: "Kim Cương", 6: "Tinh Anh", 7: "Vinh Quang",
    8: "Chiến Thần", 9: "Huyền Thoại",
}

def normalize_server(raw: str) -> str:
    return _SERVER_MAP.get(raw.strip().lower(), raw.strip().lower())


def rank_label(rank_id) -> str:
    if rank_id is None:
        return "Chưa xếp hạng"
    try:
        return _RANK_MAP.get(int(rank_id), f"Hạng {rank_id}")
    except Exception:
        return str(rank_id)


def search_lq_by_nickname(nickname: str, server: str = "vn") -> list[dict] | None:
    """Tìm kiếm người chơi LQ theo nickname."""
    url = "https://lienquan.garena.vn/api/searchuser"
    params = {
        "keyword": nickname,
        "page": 1,
        "pageSize": 5,
        "server": server,
    }
    try:
        r = _session.get(url, params=params, timeout=12)
        data = r.json()
        users = data.get("data", {}).get("data") or data.get("data") or []
        if isinstance(users, list) and users:
            return users
        return None
    except Exception:
        return None


def get_lq_by_uid(uid: str, server: str = "vn") -> dict | None:
    """Lấy thông tin người chơi LQ theo UID (role_id)."""
    url = "https://lienquan.garena.vn/api/getplayerinfo"
    params = {"role_id": uid, "server": server}
    try:
        r = _session.get(url, params=params, timeout=12)
        data = r.json()
        info = data.get("data") or data.get("player_info")
        if info and isinstance(info, dict):
            return info
        return None
    except Exception:
        return None


def check_lq(keyword: str, server: str = "vn") -> dict | None:
    """
    Tra cứu tài khoản LQ.
    keyword: nickname hoặc UID (số).
    Trả về dict thông tin hoặc None nếu không tìm thấy.
    """
    keyword = keyword.strip()

    # Thử theo UID trước nếu keyword là số
    if keyword.isdigit():
        info = get_lq_by_uid(keyword, server)
        if info:
            return info

    # Tìm theo nickname
    results = search_lq_by_nickname(keyword, server)
    if not results:
        return None

    # Trả về kết quả đầu tiên khớp nickname (tìm chính xác trước)
    kw_lower = keyword.lower()
    for player in results:
        name = (player.get("name") or player.get("nickname") or "").lower()
        if name == kw_lower:
            return player
    # Không khớp chính xác → trả về kết quả đầu tiên
    return results[0]


def format_lq_profile(keyword: str, data: dict) -> str:
    """Định dạng thông tin tài khoản Liên Quân."""
    name     = data.get("name") or data.get("nickname") or keyword
    uid      = data.get("role_id") or data.get("uid") or data.get("id") or "?"
    level    = data.get("level") or data.get("lv") or "?"
    server   = data.get("server") or "vn"
    rank_id  = data.get("rank") or data.get("rank_id")
    rank     = rank_label(rank_id)
    guild    = data.get("guild_name") or data.get("clan_name") or "Không có"
    win      = data.get("win") or data.get("win_count") or "?"
    lose     = data.get("lose") or data.get("lose_count") or "?"
    mvp      = data.get("mvp") or data.get("mvp_count") or "?"
    gp       = data.get("gp") or data.get("gold") or "?"
    avatar   = data.get("avatar") or data.get("icon") or ""

    try:
        total = int(win) + int(lose)
        wr = f"{int(win)/total*100:.1f}%" if total > 0 else "N/A"
    except Exception:
        wr = "N/A"

    lines = [
        "⚔️ LIÊN QUÂN MOBILE — Thông tin tài khoản",
        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
        f"👤 Tên IGN   : {name}",
        f"🆔 UID       : {uid}",
        f"🌍 Server    : {str(server).upper()}",
        f"⭐ Cấp độ   : {level}",
        f"🏆 Hạng      : {rank}",
        f"🏰 Quân đoàn : {guild}",
        f"✅ Thắng     : {win}",
        f"❌ Thua      : {lose}",
        f"📊 Tỉ lệ TH  : {wr}",
        f"🌟 MVP        : {mvp}",
        f"💰 GP         : {gp}",
    ]

    return "\n".join(lines)


def format_lq_results(results: list[dict]) -> str:
    """Định dạng danh sách kết quả tìm kiếm (nhiều người)."""
    lines = [f"🔍 TÌM THẤY {len(results)} KẾT QUẢ:", "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"]
    for i, p in enumerate(results, 1):
        name   = p.get("name") or p.get("nickname") or "?"
        uid    = p.get("role_id") or p.get("uid") or p.get("id") or "?"
        level  = p.get("level") or p.get("lv") or "?"
        server = p.get("server") or "vn"
        rank   = rank_label(p.get("rank") or p.get("rank_id"))
        lines.append(f"  {i}. {name}  (UID: {uid}  |  Lv.{level}  |  {rank}  |  {str(server).upper()})")
    lines.append("")
    lines.append("👉 Dùng /lq <uid> để xem chi tiết.")
    return "\n".join(lines)
