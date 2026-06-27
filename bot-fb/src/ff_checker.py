import requests
import hmac
import hashlib
import base64
import time
import math
import json

_SECRET = "GAMESKINBOFFIDCHECKERSECURITYPROTOCOL"

_session = requests.Session()
_session.headers.update({
    "authority": "gameskinbo.com",
    "accept": "*/*",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "x-api-client": "gameskinbo-web",
    "referer": "https://gameskinbo.com/free_fire_id_checker",
})

_RANK_MAP = {
    300: "Bronze", 301: "Bronze I", 302: "Bronze II", 303: "Bronze III",
    304: "Silver", 305: "Silver I", 306: "Silver II", 307: "Silver III",
    308: "Gold", 309: "Gold I", 310: "Gold II", 311: "Gold III",
    312: "Platinum", 313: "Platinum I", 314: "Platinum II", 315: "Platinum III",
    316: "Diamond", 317: "Diamond I", 318: "Diamond II", 319: "Diamond III",
    320: "Heroic", 321: "Heroic I", 322: "Heroic II", 323: "Grandmaster",
}

_REGION_MAP = {
    "vn": "vn", "vietnam": "vn",
    "ind": "ind", "in": "ind", "india": "ind",
    "sg": "sg", "singapore": "sg",
    "id": "id", "indonesia": "id",
    "br": "br", "brazil": "br",
    "us": "us", "usa": "us",
    "th": "th", "thailand": "th",
    "tw": "tw", "taiwan": "tw",
    "me": "me",
    "pk": "pk", "pakistan": "pk",
    "bd": "bd", "bangladesh": "bd",
    "ru": "ru", "russia": "ru",
    "cis": "cis",
}


def _gen_token(uid: str) -> str:
    ts = int(time.time() * 1000)
    block = math.floor(ts / 30000)
    nonce = hmac.new(_SECRET.encode(), str(block).encode(), hashlib.sha256).hexdigest()[:32]
    sig = hmac.new(nonce.encode(), f"{uid}|{ts}".encode(), hashlib.sha256).hexdigest()
    return base64.b64encode(f"{uid}|{ts}|{sig}".encode()).decode()


def normalize_region(raw: str) -> str:
    return _REGION_MAP.get(raw.strip().lower(), raw.strip().lower())


def rank_label(rank_id) -> str:
    if not rank_id:
        return "?"
    return _RANK_MAP.get(int(rank_id), f"Rank {rank_id}")


def check_ff(uid: str, region: str = "vn") -> dict | None:
    token = _gen_token(uid)
    url = f"https://gameskinbo.com/api/ff_id_checker?uid={uid}&token={token}&region={region}"
    try:
        r = _session.get(url, timeout=12)
        data = r.json()
        if "name" not in data:
            return None
        return data
    except Exception:
        return None


def format_profile(uid: str, data: dict) -> str:
    name       = data.get("name", "?")
    level      = data.get("level", "?")
    region     = data.get("region", "?")
    likes      = data.get("likes", "?")
    guild      = data.get("guild_name") or "Không có"
    guild_lv   = data.get("guild_level")
    br_pts     = data.get("br_rank_point")
    br_max     = data.get("br_max_rank")
    cs_pts     = data.get("cs_rank_point")
    credit     = data.get("credit_score", "?")
    sig        = data.get("signature") or ""
    last_login = (data.get("last_login") or "")[:10]

    rank_str = rank_label(br_max)
    if br_pts:
        rank_str += f" ({br_pts:,} pts)"

    cs_str = rank_label(data.get("cs_max_rank"))
    if cs_pts:
        cs_str += f" ({cs_pts:,} pts)"

    guild_str = guild
    if guild != "Không có" and guild_lv:
        guild_str += f" (Lv.{guild_lv})"

    try:
        likes_fmt = f"{int(likes):,}"
    except Exception:
        likes_fmt = str(likes)

    lines = [
        "🎮 Free Fire Profile",
        "",
        f"👤 Nickname : {name}",
        f"🆔 UID      : {uid}",
        f"🌍 Region   : {region}",
        f"⭐ Level    : {level}",
        f"🏆 BR Rank  : {rank_str}",
        f"⚔️ CS Rank  : {cs_str}",
        f"👥 Guild    : {guild_str}",
        f"❤️ Likes    : {likes_fmt}",
        f"🛡️ Credit   : {credit}",
    ]
    if last_login:
        lines.append(f"🕐 Last Login: {last_login}")
    if sig:
        lines.append(f"💬 Bio      : {sig[:60]}")

    return "\n".join(lines)
