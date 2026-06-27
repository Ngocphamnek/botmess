"""
╔══════════════════════════════════════════════════════════╗
║         🤖 FACEBOOK GROUP BOT — fbchat-v2              ║
║         Được tạo bởi AI · Mọi quyền được bảo lưu       ║
╚══════════════════════════════════════════════════════════╝

📋 THÔNG TIN
    /ping              → kiểm tra độ trễ
    /help              → danh sách lệnh
    /help2             → trang 2 lệnh
    /help3             → trang 3 lệnh
    /id                → xem threadID + userID
    /info              → thông tin bot
    /uptime            → thời gian bot đã chạy
    /userinfo <uid>    → thông tin người dùng Facebook

👥 QUẢN LÝ NHÓM (admin bot)
    /tengroup <tên>    → đổi tên nhóm
    /emoji <emoji>     → đổi emoji nhóm
    /nick <uid> <tên>  → đổi biệt danh thành viên
    /themadmin <uid>   → thêm admin nhóm
    /xoadmin <uid>     → bỏ quyền admin nhóm
    /tagall [msg]      → nhắc tất cả thành viên
    /members           → liệt kê thành viên nhóm
    /announce <text>   → gửi thông báo nổi bật

🔧 CÔNG CỤ (admin bot)
    /spam <n> <text>   → gửi lặp lại n lần (max 10)
    /echo <text>       → lặp lại nội dung
    /react <emoji>     → react vào tin nhắn
    /unsend            → thu hồi tin nhắn cuối của bot
    /search <từ>       → tìm user Facebook

⚙️ CÀI ĐẶT BOT (admin bot)
    /addadmin <uid>    → thêm admin bot
    /removeadmin <uid> → xoá admin bot
    /adminlist         → danh sách admin bot
    /setprefix <ký tự> → đổi prefix lệnh
    /setrules <text>   → đặt nội quy nhóm
    /setgreeting <text>→ đặt tin chào thành viên mới
    /blacklist <uid>   → chặn uid dùng bot
    /whitelist <uid>   → bỏ chặn uid
    /autoreply <on/off>→ bật/tắt tự động trả lời

📜 KIỂM DUYỆT (admin bot)
    /rules             → xem nội quy nhóm
    /warn <uid> [lý do]→ cảnh cáo thành viên
    /warnlist          → danh sách cảnh cáo
    /clearwarn <uid>   → xoá cảnh cáo
    /ban <uid> [lý do] → ban thành viên
    /unban <uid>       → bỏ ban
    /banlist           → danh sách bị ban

🎮 VUI CHƠI & TRẮC NGHIỆM
    /tung              → tung đồng xu
    /random <min> <max>→ số ngẫu nhiên
    /roll <NdM>        → tung xúc xắc (vd: 2d6)
    /choose <a>|<b>    → chọn ngẫu nhiên
    /8ball <câu hỏi>   → bói 8 quả bóng
    /trivia            → câu hỏi kiến thức
    /rps <kéo/búa/bao> → oẳn tù tì với bot

🌤 TIỆN ÍCH
    /thoitiet <tp>     → xem thời tiết thành phố
    /dich <lang> <text>→ dịch văn bản (vi/en/ja/ko...)
    /tinhtoan <bthuc>  → máy tính
    /wiki <từ khoá>    → tìm Wikipedia
    /qr <text>         → tạo mã QR
    /base64 <text>     → mã hoá Base64
    /decode64 <text>   → giải mã Base64
    /hash <text>       → băm MD5/SHA256

🖼 ẢNH & STICKER
    /genanh <mô tả>    → tạo ảnh AI từ mô tả (Pollinations)
    /anh <từ khoá>     → tìm ảnh ngẫu nhiên
    /meme <text>       → tạo meme chữ trắng nền đen
    /avatar <uid>      → lấy avatar người dùng

🎵 ÂM NHẠC & VIDEO
    /nhac <tên bài>    → tìm nhạc trên YouTube
    /youtube <từ khoá> → tìm video YouTube
    /videoinfo <link>  → thông tin video từ link YouTube
    /lyric <tên bài>   → tìm lời bài hát

📊 THỐNG KÊ
    /stats             → thống kê nhóm và bot
    /topwarn           → top người bị cảnh cáo nhiều nhất
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import random
import re
import sys
import tempfile
import time
import threading
import traceback
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

try:
    import requests
except ImportError:
    requests = None

try:
    import qrcode
    from PIL import Image as PILImage
    HAS_QR = True
except ImportError:
    HAS_QR = False

from _core._session import dataGetHome
from _core._utils import gen_threading_id, json_minimal, generate_session_id, generate_client_id
from _features._facebook import _search
from _features._facebook import _get_user_info
from _features._thread import _all_thread_data
from _features._thread import _changeNameThread
from _features._thread import _changeEmoji
from _features._thread import _changeNickname
from _features._thread import _addAdmin
from _messaging._send import api as SendAPI, send_group_ls, _make_mqtt_client, _j, LS_TOPIC, APP_ID, LS_VERSION_ID, _DEFAULT_TIMEOUT
from _messaging._attachments import func as upload_attachment
from _messaging._unsend import func as unsend_message
from _messaging._reactions import func as react_message
from _messaging._listening import listeningEvent
from _messaging._listening_e2ee import listeningE2EEEvent
from ff_checker import check_ff, format_profile, normalize_region


CONFIG_PATH = HERE / "config.json"
KEYS_PATH   = HERE / "keys.json"
BOT_START_TIME = time.time()

# ─── KEY SYSTEM ───────────────────────────────────────────────────
def load_keys() -> dict:
    if KEYS_PATH.exists():
        try:
            return json.loads(KEYS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"keys": {}, "user_keys": {}, "pending": {}, "group_owners": {}}

def save_keys(data: dict) -> None:
    KEYS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def gen_key(days: int = 30) -> str:
    import secrets, string
    chars = string.ascii_uppercase + string.digits
    return "HARU-" + "".join(secrets.choice(chars) for _ in range(4)) + \
           "-" + "".join(secrets.choice(chars) for _ in range(4)) + \
           "-" + "".join(secrets.choice(chars) for _ in range(4))

def _days_to_max_groups(days: int) -> int:
    """Số nhóm tối đa theo số ngày của gói."""
    if days <= 30:  return 1
    if days <= 90:  return 3
    return 99


# ─── GỬI ẢNH TRỰC TIẾP QUA FACEBOOK UPLOAD API ─────────────────
def send_group_ls_image(dataFB, thread_id: str, attachment_id, caption: str = "") -> dict:
    """Gửi ảnh vào nhóm với attachment_id đã upload lên Facebook."""
    from threading import Event
    otid = gen_threading_id()
    task_payload: dict = {
        "thread_id": str(thread_id),
        "otid": str(otid),
        "source": 0,
        "send_type": 1,
        "text": caption,
        "initiating_source": 0,
        "attachment_fbids": [str(attachment_id)],
    }
    task = {
        "failure_count": None,
        "label": "46",
        "payload": _j(task_payload),
        "queue_name": str(thread_id),
        "task_id": 1,
    }
    context = {
        "app_id": APP_ID,
        "payload": _j({
            "epoch_id": int(otid),
            "tasks": [task],
            "version_id": LS_VERSION_ID,
        }),
        "request_id": 1,
        "type": 3,
    }

    import ssl, paho.mqtt.client as mqtt
    connected = Event()
    published = Event()
    state: dict = {"errors": []}
    client, _ = _make_mqtt_client(dataFB)

    def on_connect(c, ud, flags, rc, *args):
        if int(rc) != 0:
            state["errors"].append(f"connect rc={rc}")
            connected.set(); published.set(); return
        connected.set()
        info = c.publish(LS_TOPIC, _j(context), qos=1)
        if getattr(info, "rc", 0) != mqtt.MQTT_ERR_SUCCESS:
            state["errors"].append(f"publish rc={info.rc}")
            published.set()

    def on_publish(c, ud, mid, *args):
        published.set()

    def on_disconnect(c, ud, rc, *args):
        connected.set(); published.set()

    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    try:
        client.connect("edge-chat.facebook.com", port=443, keepalive=10)
        client.loop_start()
        connected.wait(timeout=15)
        published.wait(timeout=15)
        import time as _time; _time.sleep(1.5)
    except Exception as e:
        state["errors"].append(str(e))
    finally:
        try: client.disconnect()
        except Exception: pass
        try: client.loop_stop()
        except Exception: pass

    if state["errors"]:
        return {"error": 1, "payload": {"errors": state["errors"]}}
    return {"success": 1, "payload": {"messageID": str(otid)}}

DIVIDER = "═" * 30

# ─── 8BALL ANSWERS ───────────────────────────────────────────────
BALL8_YES = [
    "✅ Chắc chắn rồi!", "✅ Tất nhiên là có!", "✅ Theo quan điểm của tôi, có!",
    "✅ Triển vọng rất tốt!", "✅ Khả năng cao!", "✅ Dấu hiệu rất tốt!",
    "✅ Cứ tiến thôi!", "✅ Bạn có thể tin vào điều này!",
]
BALL8_NO = [
    "❌ Quan điểm của tôi: Không.", "❌ Rất nghi ngờ.", "❌ Câu trả lời là Không.",
    "❌ Đừng trông chờ vào điều đó.", "❌ Triển vọng không tốt.",
    "❌ Nguồn tin nói: Không.", "❌ Tôi sẽ nói Không.",
]
BALL8_MAYBE = [
    "🔮 Hãy hỏi lại sau.", "🔮 Tôi không thể đoán bây giờ.",
    "🔮 Tập trung và hỏi lại.", "🔮 Câu trả lời mờ nhạt.",
    "🔮 Tốt hơn không nên nói bây giờ.", "🔮 Không thể đoán được.",
]

# ─── TRIVIA ──────────────────────────────────────────────────────
TRIVIA_POOL = [
    ("Thủ đô của Nhật Bản là gì?", "Tokyo"),
    ("Hành tinh nào lớn nhất trong hệ Mặt Trời?", "Sao Mộc"),
    ("Ai là người đầu tiên đặt chân lên Mặt Trăng?", "Neil Armstrong"),
    ("Ngôn ngữ lập trình nào được dùng để xây dựng bot này?", "Python"),
    ("Nước nào có diện tích lớn nhất thế giới?", "Nga"),
    ("Nguyên tố hóa học nào có ký hiệu Au?", "Vàng"),
    ("Facebook được thành lập năm nào?", "2004"),
    ("1 GB bằng bao nhiêu MB?", "1024"),
    ("Bức tường nào nổi tiếng nhất Trung Quốc?", "Vạn Lý Trường Thành"),
    ("Loài động vật nào chạy nhanh nhất trên cạn?", "Báo săn"),
    ("Sông dài nhất thế giới?", "Sông Nile"),
    ("Ai viết truyện Kiều?", "Nguyễn Du"),
    ("Thủ đô của Việt Nam là gì?", "Hà Nội"),
    ("Đơn vị tiền tệ của Nhật Bản?", "Yên"),
    ("Trái Đất có bao nhiêu châu lục?", "7"),
]
_trivia_pending: dict[str, dict] = {}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        template = {
            "cookies": "",
            "prefix": "#",
            "admins": [],
            "rules": "",
            "blacklist": [],
            "greeting": "",
            "autoreply": False,
        }
        CONFIG_PATH.write_text(
            json.dumps(template, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    env_cookie = os.environ.get("FB_COOKIE", "").strip()
    if env_cookie:
        cfg["cookies"] = env_cookie

    if not cfg.get("cookies") or "PASTE_YOUR" in str(cfg.get("cookies", "")):
        print("[config] ❌ Bạn chưa cung cấp cookie Facebook.")
        print("[config] Hãy điền 'cookies' vào config.json hoặc đặt env FB_COOKIE.")
        sys.exit(1)

    cfg.setdefault("prefix", "#")
    cfg.setdefault("admins", [])
    cfg.setdefault("rules", "")
    cfg.setdefault("blacklist", [])
    cfg.setdefault("greeting", "")
    cfg.setdefault("autoreply", False)
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def is_valid_datafb(dataFB: object) -> bool:
    if not isinstance(dataFB, dict):
        return False
    facebook_id = str(dataFB.get("FacebookID") or "").strip()
    if not facebook_id.isdigit():
        return False
    required_fields = ("fb_dtsg", "jazoest", "sessionID", "clientRevision", "cookieFacebook")
    return all(str(dataFB.get(field) or "").strip() for field in required_fields)


def log(tag: str, msg: str) -> None:
    icons = {
        "bot": "🤖", "recv": "📩", "send": "📤", "err": "❌",
        "boot": "🚀", "warn": "⚠️", "react": "💬", "unsend": "🗑",
        "info": "ℹ️",
    }
    icon = icons.get(tag, "•")
    print(f"[{datetime.now():%H:%M:%S}] {icon} [{tag.upper()}] {msg}")


def format_uptime(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {sec}s"
    if m:
        return f"{m}m {sec}s"
    return f"{sec}s"


def box(title: str, lines: list[str]) -> str:
    content = "\n".join(lines)
    return f"╔{'═'*34}╗\n║  {title:<32}║\n╠{'═'*34}╣\n{content}\n╚{'═'*34}╝"


def section(title: str) -> str:
    return f"\n{'─'*3} {title} {'─'*3}"


# ─── HTTP HELPER ─────────────────────────────────────────────────
def http_get(url: str, timeout: int = 8) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def http_get_bytes(url: str, timeout: int = 10) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


class GroupBot:

    def __init__(self, dataFB: dict, prefix: str = "/", admins: list | None = None,
                 cfg: dict | None = None):
        self.dataFB = dataFB
        self.prefix = prefix
        self.admins = set(map(str, admins or []))
        self.cfg = cfg or {}

        self.sender = SendAPI()
        self.listener = listeningEvent(dataFB)

        self._last_seen_message_id: str | None = None
        self._last_bot_message: dict[str, str] = {}
        self._warn_list: dict[str, list[str]] = {}
        self._ban_set: set[str] = set(self.cfg.get("banlist", []))
        self._blacklist: set[str] = set(self.cfg.get("blacklist", []))
        self._msg_count: int = 0
        # activity_tracker[thread_id][uid] = số tin nhắn đã gửi
        self._activity_tracker: dict[str, dict[str, int]] = {}
        # activity_first[thread_id][uid] = timestamp tin nhắn đầu tiên
        self._activity_first: dict[str, dict[str, float]] = {}
        # name cache: uid → tên hiển thị
        self._name_cache: dict[str, str] = {}
        # fb_admins_cache: thread_id → (timestamp, set of admin UIDs)
        self._fb_admins_cache: dict[str, tuple[float, set[str]]] = {}
        self._menu_state: dict[str, float] = {}   # thread_id → timestamp khi /menu được gọi
        self._key_data: dict = load_keys()         # hệ thống key
        self._key_nagged: set[str] = set()         # "uid:thread_id" đã được nhắc mua key
        self._announced_groups: set[str] = set(   # nhóm đã gửi tin chào
            self._key_data.get("announced_groups", [])
        )

        # ── Anti-spam & Anti-link state ──────────────────────────
        # anti_spam[thread_id][uid] = [timestamps...]
        self._spam_tracker: dict[str, dict[str, list[float]]] = {}
        # anti_link[thread_id] = True/False
        self._antilink_enabled: dict[str, bool] = {}
        # anti_spam per group
        self._antispam_enabled: dict[str, bool] = {}
        # spam warn count before kick: spam_warns[thread_id][uid] = count
        self._spam_warns: dict[str, dict[str, int]] = {}
        # known members greeting: greeted[uid:thread_id] = True
        self._greeted_members: set[str] = set()

        # ── Tính năng quản lý nhóm nâng cao ──────────────────────
        # sendrules[thread_id] = True/False — tự gửi nội quy khi TV mới vào
        self._sendrules_enabled: dict[str, bool] = {}
        # slowmode[thread_id] = số giây phải chờ (0 = tắt)
        self._slowmode_secs: dict[str, int] = {}
        # slowmode_last[thread_id][uid] = timestamp tin nhắn cuối
        self._slowmode_last: dict[str, dict[str, float]] = {}
        # badwords[thread_id] = set của các từ bị cấm
        self._badwords: dict[str, set[str]] = {}
        # autokick[thread_id] = True/False — tự kick người không có key
        self._autokick_enabled: dict[str, bool] = {}
        # pending_schedules: [{thread_id, msg, send_at}]
        self._pending_schedules: list[dict] = []

        # ── Phân cấp quyền lệnh (6 cấp) ─────────────────────────
        # Super Owner — chỉ chủ bot
        cfg_so = self.cfg.get("super_owner", "")
        self.super_owner: str = str(cfg_so) if cfg_so else (
            str(sorted(self.admins)[0]) if self.admins else ""
        )

        # ── NHÓM KÊNH: lệnh nào dùng ở đâu ──────────────────────
        # Lệnh PUBLIC: không cần key, hoạt động mọi nơi (DM + nhóm)
        self._public_cmds: set[str] = {
            "ping", "info", "menu", "nhapkey", "muakey", "id", "uptime",
            # AI — full quyền, không cần key, hoạt động mọi nơi
            "ai", "gpt", "ask",
            # Thành viên có thể đổi biệt danh của chính mình
            "mynick",
            # Xem admin thực của nhóm Facebook
            "fbadmins",
            # Tiện ích công cộng
            "thoitiet", "dich", "tinhtoan", "wiki",
            "qr", "base64", "decode64", "hash",
            "tung", "random", "roll", "choose", "8ball", "rps", "trivia",
            "genanh", "anh", "meme", "avatar",
            "nhac", "youtube", "videoinfo", "lyric",
            "userinfo", "search", "echo",
            # Free Fire — public
            "ff",
        }

        # Lệnh DM: dùng được trong tin nhắn riêng (không cần nhóm)
        self._dm_allowed_cmds: set[str] = self._public_cmds | {
            # Key Owner tự quản lý key của mình (DM + nhóm)
            "checkkey", "nhom", "giahan",
            # Bot Admin / Super Owner (DM + nhóm)
            "createkey", "revokekey", "checkuser", "checkgroup",
            "addbotadmin", "removebotadmin",
            "taokey", "xoakey", "danhsachkey", "xacnhan",
        }

        # Lệnh CHỈ DÙNG TRONG NHÓM (group-only)
        self._group_only_cmds: set[str] = {
            "tagall", "members", "announce",
            "warn", "warnlist", "clearwarn",
            "ban", "unban", "banlist", "topwarn",
            "themtv", "xoatv",
            "tengroup", "emoji", "nick", "themadmin", "xoadmin",
            "addgroupadmin", "removegroupadmin", "groupadminlist",
            "addadmin", "removeadmin", "adminlist",
            "setprefix", "setrules", "setgreeting", "setjoinmsg", "autoreply",
            "antilink", "antispam",
            "blacklist", "whitelist",
            "daten", "thongtinnhom", "chunhom", "chuyennhom",
            "rules", "stats", "topchat", "hoatdong",
            "spam", "react", "unsend",
            "sendrules", "slowmode", "badword", "autokick", "schedule", "welcome",
        }

        # ── PHÂN CẤP TRONG NHÓM ──────────────────────────────────
        # Tier 3 — Group Admin (được Key Owner cấp)
        self._groupadmin_cmds: set[str] = {
            "tagall", "members", "announce",
            "warn", "warnlist", "clearwarn",
            "ban", "unban", "banlist", "topwarn",
            "spam", "echo", "react", "unsend",
            "rules", "stats",
            "themtv", "xoatv",
            "slowmode", "schedule",
        }

        # Tier 4 — Key Owner (chủ nhóm, người mua key)
        self._keyowner_cmds: set[str] = {
            "tengroup", "emoji", "nick", "themadmin", "xoadmin",
            "setprefix", "setrules", "setgreeting", "setjoinmsg",
            "blacklist", "whitelist", "autoreply",
            "daten",
            "addgroupadmin", "removegroupadmin", "groupadminlist",
            "antilink", "antispam",
            "thongtinnhom", "chunhom", "chuyennhom",
            # Tính năng quản lý nhóm mới
            "sendrules", "badword", "autokick", "welcome",
            # nhom/checkkey/giahan có thể dùng cả DM nên xử lý riêng
        }

        # Tier 5 — Bot Admin only (không cho Key Owner / Group Admin dùng)
        self._botadmin_only_cmds: set[str] = {
            "addadmin", "removeadmin", "adminlist",
            "taokey", "xoakey", "danhsachkey", "xacnhan",
            "createkey", "revokekey", "checkuser", "checkgroup",
            "addbotadmin", "removebotadmin",
        }

        # Lệnh Member: tất cả lệnh không nằm trong groupadmin/keyowner
        # → mặc định khi có key hợp lệ trong nhóm

        self._handlers = {
            # Thông tin (public)
            "ping":             self._cmd_ping,
            "menu":             self._cmd_menu,
            "id":               self._cmd_id,
            "info":             self._cmd_info,
            "uptime":           self._cmd_uptime,
            # Member
            "userinfo":         self._cmd_userinfo,
            # Group Admin
            "tagall":           self._cmd_tagall,
            "members":          self._cmd_members,
            "announce":         self._cmd_announce,
            "spam":             self._cmd_spam,
            "echo":             self._cmd_echo,
            "react":            self._cmd_react,
            "unsend":           self._cmd_unsend,
            "search":           self._cmd_search,
            "rules":            self._cmd_rules,
            "warn":             self._cmd_warn,
            "warnlist":         self._cmd_warnlist,
            "clearwarn":        self._cmd_clearwarn,
            "ban":              self._cmd_ban,
            "unban":            self._cmd_unban,
            "banlist":          self._cmd_banlist,
            "stats":            self._cmd_stats,
            "topwarn":          self._cmd_topwarn,
            "topchat":          self._cmd_topchat,
            "hoatdong":         self._cmd_hoatdong,
            # Key Owner
            "tengroup":         self._cmd_tengroup,
            "emoji":            self._cmd_emoji,
            "nick":             self._cmd_nick,
            "themadmin":        self._cmd_themadmin,
            "xoadmin":          self._cmd_xoadmin,
            "daten":            self._cmd_daten,
            "setjoinmsg":       self._cmd_setjoinmsg,
            "addgroupadmin":    self._cmd_addgroupadmin,
            "removegroupadmin": self._cmd_removegroupadmin,
            "groupadminlist":   self._cmd_groupadminlist,
            "addadmin":         self._cmd_addadmin,
            "removeadmin":      self._cmd_removeadmin,
            "adminlist":        self._cmd_adminlist,
            "setprefix":        self._cmd_setprefix,
            "setrules":         self._cmd_setrules,
            "setgreeting":      self._cmd_setgreeting,
            "blacklist":        self._cmd_blacklist,
            "whitelist":        self._cmd_whitelist,
            "autoreply":        self._cmd_autoreply,
            # Thành viên đổi biệt danh của chính mình
            "mynick":           self._cmd_mynick,
            # Xem admin thực của nhóm Facebook
            "fbadmins":         self._cmd_fbadmins,
            # Key system (public + member)
            "nhapkey":          self._cmd_nhapkey,
            "muakey":           self._cmd_muakey,
            # Vui chơi (member)
            "tung":             self._cmd_tung,
            "random":           self._cmd_random,
            "roll":             self._cmd_roll,
            "choose":           self._cmd_choose,
            "8ball":            self._cmd_8ball,
            "trivia":           self._cmd_trivia,
            "rps":              self._cmd_rps,
            # Tiện ích (member)
            "thoitiet":         self._cmd_thoitiet,
            "dich":             self._cmd_dich,
            "tinhtoan":         self._cmd_tinhtoan,
            "wiki":             self._cmd_wiki,
            "qr":               self._cmd_qr,
            "base64":           self._cmd_base64,
            "decode64":         self._cmd_decode64,
            "hash":             self._cmd_hash,
            # Ảnh & Video (member)
            "genanh":           self._cmd_genanh,
            "anh":              self._cmd_anh,
            "meme":             self._cmd_meme,
            "avatar":           self._cmd_avatar,
            # Âm nhạc & Video (member)
            "nhac":             self._cmd_nhac,
            "youtube":          self._cmd_youtube,
            "videoinfo":        self._cmd_videoinfo,
            "lyric":            self._cmd_lyric,
            # Thêm/xóa thành viên (group admin)
            "themtv":           self._cmd_themtv,
            "xoatv":            self._cmd_xoatv,
            # Anti-link / Anti-spam (key owner)
            "antilink":         self._cmd_antilink,
            "antispam":         self._cmd_antispam,
            # Quản lý nhóm nâng cao
            "sendrules":        self._cmd_sendrules,
            "slowmode":         self._cmd_slowmode,
            "badword":          self._cmd_badword,
            "autokick":         self._cmd_autokick,
            "schedule":         self._cmd_schedule,
            "welcome":          self._cmd_welcome,
            # Free Fire API
            "ff":               self._cmd_ff,
            # AI — full quyền, không cần key, DM + nhóm
            "ai":               self._cmd_ai,
            "gpt":              self._cmd_ai,
            "ask":              self._cmd_ai,
            # Key Owner — quản lý key & nhóm
            "checkkey":         self._cmd_checkkey,
            "nhom":             self._cmd_nhom,
            "chunhom":          self._cmd_chunhom,
            "thongtinnhom":     self._cmd_thongtinnhom,
            "giahan":           self._cmd_giahan,
            "chuyennhom":       self._cmd_chuyennhom,
            # Bot Admin / Super Owner
            "createkey":        self._cmd_createkey,
            "revokekey":        self._cmd_revokekey,
            "checkuser":        self._cmd_checkuser,
            "checkgroup":       self._cmd_checkgroup,
            "addbotadmin":      self._cmd_addbotadmin,
            "removebotadmin":   self._cmd_removebotadmin,
        }

    def run(self) -> None:
        log("boot", f"✅ Đăng nhập thành công — UID = {self.dataFB.get('FacebookID')}")
        self.listener.get_last_seq_id()

        t = threading.Thread(
            target=self.listener.connect_mqtt,
            name="fbchat-listener",
            daemon=True,
        )
        t.start()
        log("bot", f"Listener khởi động. Prefix: '{self.prefix}' | Admins: {self.admins or 'tất cả'}")
        log("bot", f"Tổng số lệnh: {len(self._handlers)}")

        # Auto-lock: mỗi 30 phút kiểm tra key, chủ key, bot còn trong nhóm
        al = threading.Thread(target=self._autolock_loop, name="autolock", daemon=True)
        al.start()
        log("bot", "✅ Auto-lock thread đã khởi động (chu kỳ 30 phút)")

        # Schedule: gửi tin nhắn hẹn giờ
        sc = threading.Thread(target=self._schedule_loop, name="schedule", daemon=True)
        sc.start()
        log("bot", "✅ Schedule thread đã khởi động")

        try:
            while True:
                self._poll_once()
                time.sleep(0.3)
        except KeyboardInterrupt:
            log("bot", "Đã dừng theo yêu cầu người dùng.")

    def _autolock_loop(self) -> None:
        """Chạy nền: mỗi 30 phút kiểm tra tất cả nhóm đang dùng bot."""
        import time as _time
        _time.sleep(300)  # chờ 5 phút sau boot trước khi check lần đầu
        while True:
            try:
                self._autolock_check_all()
            except Exception as exc:
                log("err", f"Auto-lock lỗi: {exc}")
            _time.sleep(1800)  # 30 phút

    def _autolock_check_all(self) -> None:
        """Kiểm tra toàn bộ nhóm — nếu vi phạm thì gửi cảnh báo vào nhóm."""
        kd = self._key_data
        group_owners = kd.get("group_owners", {})
        user_keys = kd.get("user_keys", {})
        blacklist = kd.get("blacklist_uids", set())
        now = time.time()

        for thread_id, owner_uid in list(group_owners.items()):
            reasons = []
            uk = user_keys.get(owner_uid)
            # 1. Key hết hạn
            if not uk or now >= uk.get("expires", 0):
                reasons.append("Key đã hết hạn")
            # 2. Chủ key trong blacklist
            elif str(owner_uid) in (kd.get("blacklist_uids") or set()):
                reasons.append("Chủ key bị blacklist")
            if reasons:
                msg = (
                    "🔒 CẢNH BÁO TỰ ĐỘNG\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    "  Bot phát hiện vi phạm:\n"
                )
                for r in reasons:
                    msg += f"  ⚠️ {r}\n"
                msg += (
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"  Gia hạn key: {self.prefix}giahan\n"
                    f"  Mua key mới: {self.prefix}muakey"
                )
                try:
                    fake_snap = {"replyToID": thread_id, "type": "group"}
                    self._reply(fake_snap, msg)
                    log("bot", f"Auto-lock cảnh báo nhóm {thread_id}: {reasons}")
                except Exception:
                    pass

    # ── KEY HELPERS ───────────────────────────────────────────────
    def _key_valid(self, uid: str) -> bool:
        """Kiểm tra uid có key hợp lệ chưa. Admin luôn pass."""
        if uid in self.admins:
            return True
        uk = self._key_data.get("user_keys", {}).get(uid)
        if not uk:
            return False
        return time.time() < uk.get("expires", 0)

    def _check_group_access(self, thread_id: str, sender_id: str) -> tuple[bool, str]:
        """Kiểm tra nhóm có quyền dùng bot không. Trả về (ok, thông báo lỗi)."""
        p = self.prefix
        if sender_id in self.admins:
            return True, ""
        kd = self._key_data
        group_owners = kd.get("group_owners", {})

        # Nhóm đã đăng ký → check key chủ nhóm
        if thread_id in group_owners:
            owner_uid = group_owners[thread_id]
            uk = kd.get("user_keys", {}).get(owner_uid)
            if uk and time.time() < uk.get("expires", 0):
                return True, ""
            exp_str = datetime.fromtimestamp(uk.get("expires", 0)).strftime("%d/%m/%Y") if uk else "?"
            return False, (
                "🔐 KEY NHÓM ĐÃ HẾT HẠN!\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Hết hạn: {exp_str}\n"
                f"  Gia hạn: {p}muakey\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )

        # Nhóm chưa đăng ký → người gửi cần có key hợp lệ
        uk = kd.get("user_keys", {}).get(sender_id)
        if not uk or time.time() >= uk.get("expires", 0):
            return False, (
                "🔐 BẠN CHƯA CÓ KEY KÍCH HOẠT!\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Nhập key: {p}nhapkey <KEY>\n"
                f"  Mua key : {p}muakey\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )

        # Kiểm tra giới hạn số nhóm
        max_groups = uk.get("max_groups", 1)
        groups = uk.get("groups", [])
        if len(groups) >= max_groups:
            return False, (
                "❌ ĐÃ VƯỢT GIỚI HẠN SỐ NHÓM!\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Gói của bạn: {max_groups} nhóm\n"
                f"  Đang dùng : {len(groups)} nhóm\n"
                f"  Mua thêm  : {p}muakey\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )

        # Đăng ký nhóm mới (auto)
        groups.append(thread_id)
        uk["groups"] = groups
        kd.setdefault("group_owners", {})[thread_id] = sender_id
        save_keys(kd)
        log("bot", f"Nhóm {thread_id} đã được đăng ký cho UID {sender_id} ({len(groups)}/{max_groups})")
        return True, ""

    def _get_bot_name(self, thread_id: str) -> str:
        """Trả tên bot tuỳ chỉnh của chủ nhóm, hoặc 'HARU88' nếu chưa đặt."""
        kd = self._key_data
        owner = kd.get("group_owners", {}).get(thread_id)
        if owner:
            uk = kd.get("user_keys", {}).get(owner, {})
            name = uk.get("bot_name", "").strip()
            if name:
                return name
        return "HARU88"

    def _is_key_owner(self, thread_id: str, uid: str) -> bool:
        """Kiểm tra uid có phải chủ nhóm (người đã đăng ký key cho nhóm)."""
        if uid in self.admins:
            return True
        return self._key_data.get("group_owners", {}).get(thread_id) == uid

    def _get_fb_admins(self, thread_id: str) -> set[str]:
        """Lấy danh sách admin THỰC của nhóm từ Facebook (cache 10 phút)."""
        now = time.time()
        cached = self._fb_admins_cache.get(thread_id)
        if cached and now - cached[0] < 600:
            return cached[1]
        try:
            data = _all_thread_data.func(self.dataFB)
            if isinstance(data, dict):
                data = [data]
            if isinstance(data, list):
                for thread in data:
                    if str(thread.get("threadID", "")) == thread_id:
                        admins: set[str] = set()
                        for a in thread.get("thread_admins", []):
                            uid_a = str(a.get("id", "") or a) if isinstance(a, dict) else str(a)
                            if uid_a:
                                admins.add(uid_a)
                        self._fb_admins_cache[thread_id] = (now, admins)
                        return admins
        except Exception as e:
            log("err", f"_get_fb_admins lỗi: {e}")
        empty: set[str] = set()
        self._fb_admins_cache[thread_id] = (now, empty)
        return empty

    def _is_group_admin(self, thread_id: str, uid: str) -> bool:
        """Bot admin / key owner luôn pass. Admin nhóm (bot hoặc FB thực) cũng pass."""
        if uid in self.admins:
            return True
        if self._is_key_owner(thread_id, uid):
            return True
        # Admin được Key Owner cấp trong bot
        ga = self._key_data.get("group_admins", {}).get(thread_id, [])
        if uid in ga:
            return True
        # Admin THỰC của nhóm trên Facebook
        return uid in self._get_fb_admins(thread_id)

    def _is_super_owner(self, uid: str) -> bool:
        """Chỉ Super Owner (chủ bot) mới pass."""
        return str(uid) == self.super_owner

    def _is_bot_admin(self, uid: str) -> bool:
        """Super Owner + Bot Admin đều pass."""
        return str(uid) in self.admins

    def _check_access(self, thread_id: str, sender_id: str, cmd: str,
                      is_group: bool = True) -> tuple[bool, str]:
        """Kiểm tra quyền 6 cấp + phân biệt DM vs nhóm.

        Luồng:
          public → (DM check) → bot admin bypass → group-only check →
          group access check → member / group_admin / key_owner
        """
        p = self.prefix

        # ── 1. LỆNH PUBLIC — luôn cho phép mọi nơi ───────────────
        if cmd in self._public_cmds:
            return True, ""

        # ── 2. BOT ADMIN / SUPER OWNER — bypass tất cả ───────────
        if sender_id in self.admins:
            # Trong DM, chỉ cho phép các lệnh DM-allowed
            if not is_group and cmd in self._group_only_cmds:
                return False, (
                    "⚠️ Lệnh này chỉ dùng được trong NHÓM!\n"
                    f"  Vào nhóm rồi gõ {p}{cmd}"
                )
            return True, ""

        # ── 2.5. BOT ADMIN ONLY — chặn non-admin ngay lập tức ────
        if cmd in self._botadmin_only_cmds:
            return False, (
                "⛔ KHÔNG ĐỦ QUYỀN — CẦN: 🛠 Bot Admin\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                "  Lệnh này chỉ BOT ADMIN / SUPER OWNER mới dùng được.\n"
                "  Liên hệ chủ bot để được cấp quyền.\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )

        # ── 3. TRONG TIN NHẮN RIÊNG (DM) ─────────────────────────
        if not is_group:
            if cmd in self._dm_allowed_cmds:
                return True, ""
            if cmd in self._group_only_cmds:
                return False, (
                    "⚠️ LỆNH CHỈ DÙNG TRONG NHÓM!\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"  {p}{cmd} chỉ hoạt động trong nhóm.\n"
                    "  Vui lòng vào nhóm và thử lại."
                )
            return False, (
                f"⚠️ Lệnh {p}{cmd} không khả dụng trong DM.\n"
                f"  Gõ {p}menu để xem lệnh."
            )

        # ── 4. TRONG NHÓM: kiểm tra key + đăng ký nhóm ───────────
        ok, msg = self._check_group_access(thread_id, sender_id)
        if not ok:
            return False, msg

        # ── 5. TIER 2: Member — chỉ cần key hợp lệ ───────────────
        if cmd not in self._groupadmin_cmds and cmd not in self._keyowner_cmds:
            return True, ""

        # ── 6. TIER 3: Group Admin ────────────────────────────────
        if cmd in self._groupadmin_cmds:
            if not self._is_group_admin(thread_id, sender_id):
                return False, (
                    "⛔ KHÔNG ĐỦ QUYỀN — CẦN: 🛡 Group Admin\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    "  Lệnh này chỉ ADMIN NHÓM mới dùng được.\n"
                    "  Yêu cầu chủ nhóm (Key Owner) chạy:\n"
                    f"  {p}addgroupadmin <UID của bạn>\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
            return True, ""

        # ── 7. TIER 4: Key Owner ──────────────────────────────────
        if cmd in self._keyowner_cmds:
            if not self._is_key_owner(thread_id, sender_id):
                return False, (
                    "⛔ KHÔNG ĐỦ QUYỀN — CẦN: 👑 Key Owner\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    "  Lệnh này chỉ CHỦ NHÓM mới dùng được\n"
                    "  (người đã mua & kích hoạt key cho nhóm).\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
            return True, ""

        return True, ""

    def _send_dm(self, uid: str, content: str) -> bool:
        """Gửi tin nhắn riêng trực tiếp cho uid."""
        try:
            result = send_group_ls(self.dataFB, content, str(uid))
            return isinstance(result, dict) and result.get("success") == 1
        except Exception as e:
            log("err", f"DM tới {uid} thất bại: {e}")
            return False

    def _poll_once(self) -> None:
        get_message = getattr(self.listener, "get_message", None)
        snap = get_message() if callable(get_message) else self.listener.bodyResults
        if snap is None:
            return
        mid = snap.get("messageID")
        body = (snap.get("body", "") or "").strip()

        if not mid or mid == self._last_seen_message_id:
            return
        self._last_seen_message_id = mid

        sender_id = str(snap.get("userID") or "")
        if sender_id == str(self.dataFB.get("FacebookID")):
            return

        # Blacklist check
        if sender_id in self._blacklist:
            return

        self._msg_count += 1
        thread_id = str(snap.get("replyToID", ""))

        # ── Đếm hoạt động (tin nhắn) theo user / nhóm ────────────
        if sender_id and thread_id:
            grp = self._activity_tracker.setdefault(thread_id, {})
            grp[sender_id] = grp.get(sender_id, 0) + 1
            first = self._activity_first.setdefault(thread_id, {})
            if sender_id not in first:
                first[sender_id] = time.time()

        # ── Lần đầu bot xuất hiện trong nhóm → gửi tin chào ──────
        is_group = snap.get("type") != "user"
        if is_group and thread_id and thread_id not in self._announced_groups:
            self._announced_groups.add(thread_id)
            kd = self._key_data
            ann_list = kd.setdefault("announced_groups", [])
            if thread_id not in ann_list:
                ann_list.append(thread_id)
                save_keys(kd)
            p = self.prefix
            bot_name = self._get_bot_name(thread_id)
            # Kiểm tra tin chào tùy chỉnh của chủ nhóm
            owner = kd.get("group_owners", {}).get(thread_id)
            custom_join = ""
            if owner:
                uk = kd.get("user_keys", {}).get(owner, {})
                custom_join = uk.get("join_message", "").strip()
            if custom_join:
                join_msg = custom_join.replace("{bot_name}", bot_name).replace("{prefix}", p)
            else:
                join_msg = (
                    f"👋 Xin chào mọi người!\n"
                    f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"  Tôi là bot {bot_name}!\n"
                    f"  ✅ Kích hoạt key: {p}nhapkey <KEY>\n"
                    f"  🛒 Mua key      : {p}muakey\n"
                    f"  📋 Xem lệnh    : {p}menu\n"
                    f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )
            try:
                self.sender.send(self.dataFB, join_msg, thread_id)
                log("bot", f"📢 Đã gửi tin chào nhóm {thread_id}")
            except Exception as _je:
                log("err", f"Gửi tin chào nhóm {thread_id} thất bại: {_je}")

        # Trivia answer check
        if thread_id in _trivia_pending:
            t_data = _trivia_pending[thread_id]
            answer = body.lower()
            correct = t_data["answer"].lower()
            if correct in answer or answer in correct:
                self._reply(snap, f"🎉 Chính xác! Câu trả lời đúng là: **{t_data['answer']}**\n✨ Bạn thật thông minh!")
            else:
                self._reply(snap, f"❌ Sai rồi! Đáp án đúng là: **{t_data['answer']}**\n💡 Cố lên lần sau nhé!")
            del _trivia_pending[thread_id]
            return

        if not body:
            return

        # Menu số response (1–10) — luôn phản hồi trong 10 phút sau /menu
        menu_ts = self._menu_state.get(thread_id, 0)
        if body.strip() in {str(i) for i in range(1, 12)} and time.time() - menu_ts < 600:
            self._handle_menu_reply(snap, body.strip())
            return

        # Auto reply mode
        if self.cfg.get("autoreply") and not body.startswith(self.prefix):
            ar_replies = [
                "Chào bạn! Gõ /menu để xem danh sách lệnh nhé! 😊",
                "Tôi là bot tự động. Dùng /menu để biết thêm! 🤖",
                "Xin chào! Tôi không hiểu. Thử /menu xem nào! 👋",
            ]
            self._reply(snap, random.choice(ar_replies))
            return

        if not body.startswith(self.prefix):
            # ── Anti-link check ───────────────────────────────────
            if is_group and thread_id and self._antilink_enabled.get(thread_id, False):
                if sender_id not in self.admins and not self._is_group_admin(thread_id, sender_id):
                    URL_RE = re.compile(
                        r"(https?://|www\.|fb\.com|t\.me|zalo\.me|bit\.ly|tiktok\.com|youtube\.com|youtu\.be)",
                        re.IGNORECASE
                    )
                    if URL_RE.search(body):
                        self._reply(snap, (
                            f"⛔ ANTI-LINK\n"
                            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                            f"  @{sender_id} — Không được phép đăng link!\n"
                            f"  Tin nhắn chứa link đã bị phát hiện.\n"
                            f"  Vi phạm lần {self._spam_warns.get(thread_id, {}).get(sender_id, 0) + 1}/3"
                        ))
                        t_warns = self._spam_warns.setdefault(thread_id, {})
                        t_warns[sender_id] = t_warns.get(sender_id, 0) + 1
                        if t_warns[sender_id] >= 3:
                            self._do_kick_member(thread_id, sender_id, "Đăng link 3 lần")
                            t_warns[sender_id] = 0
                        return

            # ── Anti-spam check ───────────────────────────────────
            if is_group and thread_id and self._antispam_enabled.get(thread_id, False):
                if sender_id not in self.admins and not self._is_group_admin(thread_id, sender_id):
                    now = time.time()
                    tracker = self._spam_tracker.setdefault(thread_id, {})
                    user_times = tracker.setdefault(sender_id, [])
                    user_times = [t for t in user_times if now - t < 5]  # cửa sổ 5 giây
                    user_times.append(now)
                    tracker[sender_id] = user_times
                    if len(user_times) >= 5:  # 5 tin/5 giây = spam
                        t_warns = self._spam_warns.setdefault(thread_id, {})
                        t_warns[sender_id] = t_warns.get(sender_id, 0) + 1
                        warn_count = t_warns[sender_id]
                        self._reply(snap, (
                            f"⚠️ ANTI-SPAM\n"
                            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                            f"  @{sender_id} — Vui lòng không spam!\n"
                            f"  Cảnh cáo lần {warn_count}/3"
                        ))
                        tracker[sender_id] = []  # reset
                        if warn_count >= 3:
                            self._do_kick_member(thread_id, sender_id, "Spam 3 lần")
                            t_warns[sender_id] = 0

            # ── Slowmode check ────────────────────────────────────
            if is_group and thread_id and self._slowmode_secs.get(thread_id, 0) > 0:
                if sender_id not in self.admins and not self._is_group_admin(thread_id, sender_id):
                    now_t = time.time()
                    last_map = self._slowmode_last.setdefault(thread_id, {})
                    last_t = last_map.get(sender_id, 0)
                    wait = self._slowmode_secs[thread_id]
                    if now_t - last_t < wait:
                        remaining = int(wait - (now_t - last_t))
                        self._reply(snap, (
                            f"⏱️ SLOWMODE\n"
                            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                            f"  Vui lòng chờ {remaining}s nữa\n"
                            f"  trước khi gửi tin tiếp theo!"
                        ))
                        return
                    last_map[sender_id] = now_t

            # ── Bad word filter ───────────────────────────────────
            if is_group and thread_id and self._badwords.get(thread_id):
                if sender_id not in self.admins and not self._is_group_admin(thread_id, sender_id):
                    body_lower = body.lower()
                    bw_hit = next(
                        (w for w in self._badwords[thread_id] if w in body_lower), None
                    )
                    if bw_hit:
                        self._warn_list.setdefault(sender_id, [])
                        self._warn_list[sender_id].append(
                            f"{datetime.now():%d/%m %H:%M} — Từ ngữ không phù hợp"
                        )
                        count = len(self._warn_list[sender_id])
                        self._reply(snap, (
                            f"⚠️ TỪ NGỮ KHÔNG PHÙ HỢP\n"
                            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                            f"  Tin nhắn chứa từ bị cấm!\n"
                            f"  Cảnh cáo tự động: {count} lần\n"
                            f"{'  ⛔ Tiếp tục vi phạm → bị kick!' if count >= 3 else ''}"
                        ))
                        return

            # ── Lần đầu thành viên xuất hiện trong nhóm ──────────
            nag_key = f"{sender_id}:{thread_id}"
            if is_group and nag_key not in self._key_nagged and sender_id not in self.admins:
                kd = self._key_data
                uk = kd.get("user_keys", {}).get(sender_id)
                has_key = bool(uk) and time.time() < uk.get("expires", 0)
                # Kiểm tra nhóm đã kích hoạt chưa (Key Owner có key hợp lệ)
                _g_owner = kd.get("group_owners", {}).get(thread_id)
                _o_uk = kd.get("user_keys", {}).get(_g_owner, {}) if _g_owner else {}
                group_active = bool(_o_uk) and time.time() < _o_uk.get("expires", 0)
                self._key_nagged.add(nag_key)
                # 1. Gửi tin chào mừng
                self._greet_new_member(thread_id, sender_id)
                # 2. Tự động gửi nội quy (nếu bật)
                if self._sendrules_enabled.get(thread_id, False):
                    owner = kd.get("group_owners", {}).get(thread_id)
                    rules_txt = ""
                    if owner:
                        owner_uk = kd.get("user_keys", {}).get(owner, {})
                        rules_txt = owner_uk.get("rules", "").strip()
                    if not rules_txt:
                        rules_txt = self.cfg.get("rules", "").strip()
                    if rules_txt:
                        try:
                            time.sleep(0.8)
                            self.sender.send(self.dataFB, (
                                f"📜 NỘI QUY NHÓM\n"
                                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                                f"{rules_txt}\n"
                                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                                f"  ✅ Vui lòng đọc và tuân thủ!"
                            ), thread_id)
                        except Exception as _re:
                            log("err", f"Gửi nội quy tự động lỗi: {_re}")
                # 3. Nhóm đã kích hoạt → TV dùng được không cần key riêng
                if group_active:
                    return
                # 4. Auto-kick nếu bật và không có key (chỉ khi nhóm chưa active)
                if self._autokick_enabled.get(thread_id, False) and not has_key:
                    time.sleep(1.5)
                    self._do_kick_member(thread_id, sender_id, "Không có key — auto kick")
                    return
                # 5. Nhắc mua key (chỉ khi nhóm chưa active và không autokick)
                if not has_key:
                    p = self.prefix
                    bot_name = self._get_bot_name(thread_id)
                    self._reply(snap, (
                        f"🔐 CHƯA CÓ KEY!\n"
                        f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                        f"  Để dùng đầy đủ bot {bot_name}, bạn cần KEY!\n"
                        f"  ✅ Nhập key: {p}nhapkey <KEY>\n"
                        f"  🛒 Mua key : {p}muakey\n"
                        f"  📋 Xem lệnh: {p}menu\n"
                        f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                    ))

            # ── DM non-command: auto-welcome & menu ───────────────
            elif not is_group and body:
                p = self.prefix
                kd = self._key_data
                uk = kd.get("user_keys", {}).get(sender_id, {})
                has_key_dm = bool(uk) and time.time() < uk.get("expires", 0)
                bot_name = uk.get("bot_name", "").strip() if has_key_dm else "HARU88"
                if not bot_name:
                    bot_name = "HARU88"
                if has_key_dm:
                    days_left = max(0, int((uk.get("expires", 0) - time.time()) / 86400))
                    exp_str = datetime.fromtimestamp(uk.get("expires", 0)).strftime("%d/%m/%Y")
                    groups_used = len(uk.get("groups", []))
                    max_g = uk.get("max_groups", 1)
                    self._reply(snap, (
                        f"🤖 BOT {bot_name.upper()} — TIN NHẮN RIÊNG\n"
                        f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                        f"  🔑 Key còn {days_left} ngày (hết {exp_str})\n"
                        f"  📌 Nhóm đang dùng: {groups_used}/{max_g}\n"
                        f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                        f"  {p}menu        — Danh sách lệnh\n"
                        f"  {p}checkkey    — Chi tiết key\n"
                        f"  {p}daten <tên> — Đổi tên bot\n"
                        f"  {p}nhom        — Nhóm đang dùng\n"
                        f"  {p}giahan      — Gia hạn key\n"
                        f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                    ))
                else:
                    self._reply(snap, (
                        f"👋 XIN CHÀO! Tôi là bot {bot_name}.\n"
                        f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                        f"  Bạn chưa có key kích hoạt!\n"
                        f"  🛒 Mua key : {p}muakey\n"
                        f"  ✅ Nhập key: {p}nhapkey <KEY>\n"
                        f"  📋 Lệnh    : {p}menu\n"
                        f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                        f"  Liên hệ admin để được hỗ trợ!"
                    ))
            return

        without_prefix = body[len(self.prefix):].strip()
        if not without_prefix:
            return
        parts = without_prefix.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        handler = self._handlers.get(cmd)
        if handler is None:
            return

        # Phân cấp quyền — kiểm tra theo tier + kênh (DM/nhóm)
        ok, msg = self._check_access(thread_id, sender_id, cmd, is_group=is_group)
        if not ok:
            self._reply(snap, msg)
            return

        log("recv", f"/{cmd} từ {sender_id}: {arg!r}")
        try:
            handler(snap, arg)
        except Exception as exc:
            log("err", f"Lỗi khi xử lý lệnh /{cmd}: {exc}")
            traceback.print_exc()
            self._reply(snap, f"❌ Lỗi khi thực thi lệnh /{cmd}:\n{exc}")

    def _get_display_name(self, uid: str) -> str:
        """Trả về tên hiển thị của uid, dùng cache để tránh gọi API lặp lại."""
        if uid in self._name_cache:
            return self._name_cache[uid]
        try:
            info = _get_user_info.func(self.dataFB, uid)
            name = (info.get("nameUser") or "").strip()
            if name:
                self._name_cache[uid] = name
                return name
        except Exception:
            pass
        short = f"...{uid[-6:]}" if len(uid) > 6 else uid
        self._name_cache[uid] = short
        return short

    def _is_admin(self, snap: dict) -> bool:
        if not self.admins:
            return True
        return str(snap.get("userID") or "") in self.admins

    def _reply(self, snap: dict, content: str) -> None:
        thread_id = str(snap["replyToID"])
        result = self.sender.send(
            self.dataFB, content, thread_id,
            replyMessage=True,
            messageID=snap.get("messageID"),
        )
        if isinstance(result, dict) and result.get("success") == 1:
            try:
                self._last_bot_message[thread_id] = result["payload"]["messageID"]
            except (KeyError, TypeError):
                pass
            log("send", f"→ {thread_id}: {content[:60]!r}{'...' if len(content)>60 else ''}")
        else:
            log("send", f"FAIL → {thread_id}: {result}")

    def _send_plain(self, snap: dict, content: str) -> None:
        thread_id = str(snap["replyToID"])
        result = self.sender.send(self.dataFB, content, thread_id)
        if isinstance(result, dict) and result.get("success") == 1:
            try:
                self._last_bot_message[thread_id] = result["payload"]["messageID"]
            except (KeyError, TypeError):
                pass

    # ── Thư mục lưu ảnh tạm ─────────────────────────────
    _TMP_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp")

    def _download_image_with_retry(self, url: str, max_tries: int = 4,
                                   wait_secs: float = 6, timeout: int = 30) -> bytes | None:
        """
        Tải ảnh từ URL, thử lại nếu server AI chưa tạo xong.
        Pollinations.ai render không đồng bộ → lần đầu có thể trả về trang HTML
        hoặc ảnh nhỏ "loading". Thử lại cho đến khi nhận được ảnh thật (>10KB).
        """
        last: bytes | None = None
        for attempt in range(1, max_tries + 1):
            data = http_get_bytes(url, timeout=timeout)
            if data and len(data) > 10_000:   # ảnh thật luôn > 10KB
                log("bot", f"🌐 Tải ảnh OK lần {attempt} ({len(data)//1024}KB)")
                return data
            last = data
            size_kb = len(data) // 1024 if data else 0
            log("bot", f"⏳ Ảnh chưa sẵn sàng lần {attempt} ({size_kb}KB), chờ {wait_secs}s...")
            if attempt < max_tries:
                time.sleep(wait_secs)
        # Trả về kết quả cuối cùng dù nhỏ (caller kiểm tra kích thước)
        return last

    def _send_image_url(self, snap: dict, image_url: str, caption: str = "") -> bool:
        """
        Quy trình: tải ảnh AI → lưu vào _tmp/ → upload Facebook → gửi → TỰ XOÁ file.
        Hoạt động cả trong nhóm lẫn DM.
        """
        thread_id = str(snap["replyToID"])
        tmp_path: str | None = None
        try:
            # 1️⃣ Tải ảnh (có retry cho AI generation chậm)
            data = self._download_image_with_retry(image_url)
            if not data or len(data) < 500:
                log("err", f"Tải ảnh thất bại hoặc quá nhỏ: {len(data) if data else 0} bytes")
                return False

            # 2️⃣ Lưu vào thư mục _tmp/
            os.makedirs(self._TMP_DIR, exist_ok=True)
            if "png" in image_url.lower():
                ext = ".png"
            elif "gif" in image_url.lower():
                ext = ".gif"
            else:
                ext = ".jpg"
            fname = f"img_{int(time.time()*1000)}_{random.randint(100, 999)}{ext}"
            tmp_path = os.path.join(self._TMP_DIR, fname)
            with open(tmp_path, "wb") as fh:
                fh.write(data)
            log("bot", f"💾 Lưu ảnh tạm: {fname} ({len(data)//1024}KB)")

            # 3️⃣ Upload lên Facebook, lấy attachment ID
            upload_result = upload_attachment([tmp_path], self.dataFB)
            if not upload_result or not upload_result.get("attachmentID"):
                log("err", f"Upload thất bại: {upload_result}")
                return False
            attach_id = upload_result["attachmentID"]
            log("send", f"☁️ Upload thành công, attachmentID={attach_id}")

            # 4️⃣ Gửi ảnh vào cuộc trò chuyện
            result = send_group_ls_image(self.dataFB, thread_id, attach_id, caption)
            if isinstance(result, dict) and result.get("success") == 1:
                log("send", f"🖼 Đã gửi ảnh vào {thread_id} (caption: {caption[:40]})")
                return True
            else:
                log("err", f"Gửi ảnh thất bại: {result}")
                return False

        except Exception as e:
            log("err", f"_send_image_url lỗi: {e}")
            return False

        finally:
            # 5️⃣ TỰ XOÁ file tạm (luôn chạy dù thành công hay lỗi)
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                    log("bot", f"🗑 Đã xoá file ảnh tạm: {os.path.basename(tmp_path)}")
                except Exception as _del_err:
                    log("err", f"Xóa file tạm lỗi: {_del_err}")

    # ══════════════════════════════════════════════════════
    # 📋 THÔNG TIN
    # ══════════════════════════════════════════════════════

    def _cmd_ping(self, snap: dict, arg: str) -> None:
        sent_ts = int(snap.get("timestamp") or 0)
        latency_ms = max(0, int(time.time() * 1000) - sent_ts) if sent_ts else 0
        bar = "█" * min(10, latency_ms // 20) + "░" * (10 - min(10, latency_ms // 20))
        self._reply(snap, (
            f"🏓 PONG!\n"
            f"{DIVIDER}\n"
            f"  Độ trễ : {latency_ms} ms\n"
            f"  [{bar}]\n"
            f"  {'🟢 Rất nhanh' if latency_ms < 300 else '🟡 Bình thường' if latency_ms < 1000 else '🔴 Chậm'}"
        ))

    # ══════════════════════════════════════════════════════
    # 🤖 AI CHAT — /ai /gpt /ask
    # ══════════════════════════════════════════════════════

    _AI_SYSTEM_PROMPT = (
        "Bạn là trợ lý AI thông minh, thân thiện, hỗ trợ tiếng Việt lẫn tiếng Anh. "
        "Bạn có thể: trả lời mọi câu hỏi kiến thức, tra cứu giá cả & thị trường (crypto, vàng, hàng hoá), "
        "viết code mọi ngôn ngữ lập trình, giải toán, phân tích văn bản, dịch ngôn ngữ, "
        "tư vấn sức khoẻ/pháp lý/tài chính cơ bản, sáng tác thơ/truyện/nội dung sáng tạo. "
        "Luôn trả lời ngắn gọn, dễ hiểu, đúng trọng tâm. "
        "Nếu không biết thì nói thẳng, không bịa thông tin. "
        "Khi viết code, luôn bọc trong khối ``` với ngôn ngữ tương ứng."
    )

    def _cmd_ai(self, snap: dict, arg: str) -> None:
        """Hỏi AI — không cần key, DM + nhóm, trả lời mọi thứ."""
        p = self.prefix
        if not arg.strip():
            self._reply(snap, (
                f"🤖 AI THÔNG MINH\n"
                f"{DIVIDER}\n"
                f"  Cách dùng: {p}ai <câu hỏi>\n\n"
                f"  Có thể hỏi về:\n"
                f"    💰 Giá vàng, crypto, hàng hoá\n"
                f"    💻 Viết code mọi ngôn ngữ\n"
                f"    📚 Kiến thức, học tập, tra cứu\n"
                f"    ✍️ Sáng tác thơ, truyện, nội dung\n"
                f"    🌐 Dịch ngôn ngữ, giải thích\n"
                f"{DIVIDER}\n"
                f"  VD: {p}ai Giá Bitcoin hôm nay?\n"
                f"      {p}gpt Viết hàm sắp xếp bong bóng bằng Python\n"
                f"      {p}ask 1 đô la bằng bao nhiêu tiền Việt?"
            ))
            return

        self._reply(snap, "🤖 AI đang xử lý... ⏳")

        prompt = arg.strip()
        answer = self._ai_call(prompt)

        if not answer:
            self._reply(snap, "❌ AI không trả lời được lúc này. Thử lại sau!")
            return

        if len(answer) > 2500:
            answer = answer[:2500] + "\n\n...(đã cắt bớt do quá dài)"

        q_short = prompt[:80] + ("..." if len(prompt) > 80 else "")
        self._reply(snap, (
            f"🤖 AI TRẢ LỜI\n"
            f"{DIVIDER}\n"
            f"❓ {q_short}\n"
            f"{DIVIDER}\n"
            f"{answer}"
        ))

    def _ai_call(self, prompt: str) -> str | None:
        """
        Gọi AI qua Pollinations OpenAI-compatible API (POST, có system prompt).
        Fallback sang GET nếu POST thất bại.
        """
        import json as _json

        # ── Phương án 1: POST với system prompt (thông minh hơn) ──
        try:
            payload = _json.dumps({
                "model": "openai",
                "messages": [
                    {"role": "system", "content": self._AI_SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 1500,
            }).encode("utf-8")

            req = requests.post(
                "https://text.pollinations.ai/openai",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0",
                },
                timeout=45,
            )
            if req.status_code == 200:
                data = req.json()
                text = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    or data.get("text", "")
                ).strip()
                if text:
                    log("bot", f"AI POST OK ({len(text)} ký tự)")
                    return text
        except Exception as e1:
            log("err", f"AI POST lỗi: {e1}")

        # ── Fallback: GET đơn giản ──
        try:
            encoded = urllib.parse.quote(prompt, safe="")
            seed = random.randint(1, 99999)
            url = f"https://text.pollinations.ai/{encoded}?model=openai&seed={seed}"
            resp = requests.get(url, timeout=40, headers={"User-Agent": "Mozilla/5.0"})
            text = resp.text.strip()
            if text:
                log("bot", f"AI GET fallback OK ({len(text)} ký tự)")
                return text
        except Exception as e2:
            log("err", f"AI GET lỗi: {e2}")

        return None

    # ── MENU DANH MỤC ────────────────────────────────────────────
    _MENU_CATS = [
        ("1️⃣",  "📋 Công cộng (DM+Nhóm)",  ["ping","id","info","uptime","nhapkey","muakey","checkkey","nhom","giahan"]),
        ("2️⃣",  "🤖 AI Chat (DM+Nhóm)",    ["ai","gpt","ask"]),
        ("3️⃣",  "🎮 Vui chơi (DM+Nhóm)",   ["tung","random","roll","choose","8ball","trivia","rps"]),
        ("4️⃣",  "🌤 Tiện ích (DM+Nhóm)",   ["thoitiet","dich","tinhtoan","wiki","qr","base64","decode64","hash"]),
        ("5️⃣",  "🖼 Ảnh & Nhạc (DM+Nhóm)", ["genanh","anh","meme","avatar","nhac","youtube","videoinfo","lyric"]),
        ("6️⃣",  "🎮 Free Fire (DM+Nhóm)",  ["ff"]),
        ("7️⃣",  "🛡 Group Admin (Nhóm)",   ["warn","clearwarn","ban","unban","banlist","tagall","announce","spam","themtv","xoatv","stats","rules"]),
        ("8️⃣",  "👑 Key Owner (Nhóm+DM)",  ["thongtinnhom","chunhom","chuyennhom","daten","setjoinmsg","addgroupadmin","removegroupadmin","setprefix","setrules","antilink","antispam"]),
        ("9️⃣",  "🛠 Bot Admin (DM+Nhóm)",  ["createkey","revokekey","checkuser","checkgroup","taokey","xoakey","danhsachkey","xacnhan","addbotadmin","removebotadmin"]),
        ("🔟", "⚙️ Cài đặt nhóm (Nhóm)",  ["tengroup","emoji","nick","themadmin","xoadmin","blacklist","whitelist","autoreply","addadmin","removeadmin","adminlist"]),
    ]

    _CAT_DETAIL = {
        "1": (
            "📋 CÔNG CỘNG — DM + Nhóm, không cần key",
            ["ping               — Kiểm tra độ trễ bot",
             "id                 — Xem Thread ID / User ID",
             "info               — Thông tin bot",
             "uptime             — Thời gian bot đã chạy",
             "userinfo <uid>     — Thông tin user Facebook",
             "nhapkey <KEY>      — Kích hoạt key vào tài khoản",
             "muakey             — Xem thông tin & mua key",
             "checkkey           — Xem thông tin key của mình",
             "nhom               — Danh sách nhóm đang dùng",
             "giahan <KEY_MỚI>   — Gia hạn key"]
        ),
        "2": (
            "🤖 AI CHAT — DM + Nhóm, miễn phí, không cần key",
            ["ai <câu hỏi>      — Hỏi AI (ChatGPT)",
             "gpt <câu hỏi>     — Alias của /ai",
             "ask <câu hỏi>     — Alias của /ai",
             "",
             "Ví dụ:",
             "  /ai Python là gì?",
             "  /gpt Viết code hello world bằng C",
             "  /ask Thủ đô nước Pháp là gì?",
             "",
             "✅ Full quyền — không cần key, dùng ở mọi nơi"]
        ),
        "3": (
            "🎮 VUI CHƠI — DM + Nhóm, không cần key",
            ["tung               — Tung đồng xu (Sấp/Ngửa)",
             "random <min> <max> — Số ngẫu nhiên",
             "roll <NdM>         — Xúc xắc (vd: 2d6)",
             "choose <a>|<b>|<c> — Bot chọn ngẫu nhiên",
             "8ball <câu hỏi>    — Bói 8 quả bóng",
             "trivia             — Câu hỏi trắc nghiệm IQ",
             "rps k/b/b          — Oẳn tù tì với bot"]
        ),
        "4": (
            "🌤 TIỆN ÍCH — DM + Nhóm, không cần key",
            ["thoitiet <tỉnh/tp> — Thời tiết hiện tại",
             "dich <lang> <text> — Dịch văn bản (vi/en/ja/ko…)",
             "tinhtoan <biểu thức>— Máy tính (vd: 2+3*4)",
             "wiki <từ khoá>     — Tìm kiếm Wikipedia",
             "qr <nội dung>      — Tạo mã QR (ảnh)",
             "base64 <text>      — Mã hoá Base64",
             "decode64 <text>    — Giải mã Base64",
             "hash <text>        — Băm MD5 + SHA256",
             "search <tên>       — Tìm user Facebook",
             "echo <text>        — Bot lặp lại nội dung"]
        ),
        "5": (
            "🖼 ẢNH & NHẠC — DM + Nhóm, không cần key",
            ["genanh <mô tả>     — Tạo ảnh AI từ mô tả",
             "anh <từ khoá>      — Ảnh ngẫu nhiên theo chủ đề",
             "meme <trên>|<dưới> — Tạo ảnh meme",
             "avatar <uid>       — Lấy avatar Facebook",
             "nhac <tên bài>     — Tìm nhạc trên YouTube",
             "youtube <từ khoá>  — Tìm video YouTube",
             "videoinfo <link>   — Thông tin video YouTube",
             "lyric <tên bài>    — Lời bài hát"]
        ),
        "6": (
            "🎮 FREE FIRE — DM + Nhóm, không cần key",
            ["ff <uid>           — Thông tin người chơi FF",
             "ff <uid> <server>  — Chỉ định server",
             "",
             "Server hỗ trợ:",
             "  VN IND SG ID TH BR BD RU TW US ME PK CIS",
             "",
             "Ví dụ:",
             "  /ff 2579249340",
             "  /ff 2579249340 SG"]
        ),
        "7": (
            "🛡 GROUP ADMIN — Chỉ nhóm, cần được Key Owner cấp quyền",
            ["warn <uid> [lý do] — Cảnh cáo thành viên",
             "warnlist           — Danh sách cảnh cáo",
             "clearwarn <uid>    — Xoá cảnh cáo",
             "ban <uid> [lý do]  — Ban thành viên",
             "unban <uid>        — Bỏ ban",
             "banlist            — Danh sách bị ban",
             "themtv <uid>       — Thêm thành viên vào nhóm",
             "xoatv <uid> [lý]   — Kick thành viên",
             "tagall [msg]       — Tag tất cả thành viên",
             "announce <text>    — Gửi thông báo nhóm",
             "spam <n> <text>    — Gửi lặp lại (max 10)",
             "react <emoji>      — React vào tin nhắn",
             "unsend             — Thu hồi tin nhắn cuối bot",
             "stats              — Thống kê nhóm",
             "rules              — Xem nội quy nhóm",
             "",
             "Cấp quyền: Key Owner gõ /addgroupadmin <uid>"]
        ),
        "8": (
            "👑 KEY OWNER — Nhóm + DM, chủ nhóm (người mua key)",
            ["checkkey           — Xem key: còn ngày / nhóm / trạng thái",
             "nhom               — Danh sách nhóm đang dùng bot",
             "thongtinnhom       — Thông tin chi tiết nhóm hiện tại",
             "chunhom [id]       — Huỷ đăng ký nhóm (giải phóng slot)",
             "giahan <KEY_MỚI>   — Gia hạn key (cộng thêm ngày)",
             "chuyennhom <cũ> <mới>— Chuyển slot nhóm sang ID mới",
             "daten <tên>        — Đổi tên hiển thị của bot",
             "setjoinmsg <text>  — Tin chào khi bot vào nhóm",
             "setjoinmsg reset   — Xoá tin chào tùy chỉnh",
             "addgroupadmin <uid>— Cấp quyền Group Admin",
             "removegroupadmin <uid>— Thu hồi quyền Group Admin",
             "groupadminlist     — Danh sách Group Admin",
             "setprefix <ký>     — Đổi ký tự prefix lệnh",
             "setrules <text>    — Đặt nội quy nhóm",
             "setgreeting <text> — Tin chào thành viên mới vào nhóm",
             "antilink on/off    — Bật/tắt chặn link tự động",
             "antispam on/off    — Bật/tắt chống spam tự động"]
        ),
        "9": (
            "🛠 BOT ADMIN — DM + Nhóm (Super Owner / Bot Admin)",
            ["createkey <ngày> <nhóm>— Tạo key tuỳ chỉnh",
             "  VD: createkey 30 1   — 30 ngày, 1 nhóm",
             "  VD: createkey 90 3   — 90 ngày, 3 nhóm",
             "revokekey <KEY>        — Thu hồi & vô hiệu hoá key",
             "taokey <ngày>          — Tạo key nhanh (dùng công thức)",
             "xoakey <KEY>           — Xoá hẳn key khỏi hệ thống",
             "danhsachkey            — Xem toàn bộ key đã tạo",
             "xacnhan <uid> [ngày]   — Xác nhận mua key cho user",
             "checkuser <uid>        — Kiểm tra key & nhóm của user",
             "checkgroup <thread_id> — Kiểm tra nhóm & key",
             "addbotadmin <uid>      — Thêm Bot Admin (SO only)",
             "removebotadmin <uid>   — Xoá Bot Admin (SO only)",
             "topwarn                — Top người bị cảnh cáo"]
        ),
        "10": (
            "⚙️ CÀI ĐẶT NHÓM — Chỉ nhóm, cần Key Owner",
            ["tengroup <tên>     — Đổi tên nhóm",
             "emoji <emoji>      — Đổi emoji đại diện nhóm",
             "nick <uid> <tên>   — Đổi biệt danh thành viên",
             "themadmin <uid>    — Thêm admin nhóm (FB admin)",
             "xoadmin <uid>      — Bỏ quyền admin nhóm",
             "blacklist <uid>    — Chặn user dùng bot",
             "whitelist <uid>    — Bỏ chặn user",
             "autoreply on/off   — Bật/tắt auto reply",
             "addadmin <uid>     — Thêm Bot Admin (legacy)",
             "removeadmin <uid>  — Xoá Bot Admin (legacy)",
             "adminlist          — Danh sách Bot Admin"]
        ),
    }

    def _cmd_menu(self, snap: dict, arg: str) -> None:
        p = self.prefix
        thread_id = str(snap.get("replyToID", ""))
        self._menu_state[thread_id] = time.time()
        uid = str(snap.get("userID", ""))
        bot_name = self._get_bot_name(thread_id)
        total = sum(len(c[2]) for c in self._MENU_CATS)

        # Xác định cấp quyền của người gửi
        if self._is_super_owner(uid):
            tier_label = "👑 Super Owner"
        elif self._is_bot_admin(uid):
            tier_label = "🛠 Bot Admin"
        elif self._is_key_owner(thread_id, uid):
            tier_label = "👑 Key Owner"
        elif self._is_group_admin(thread_id, uid):
            tier_label = "🛡 Group Admin"
        elif self._key_valid(uid):
            tier_label = "⭐ VIP Member" if uid in self._key_data.get("vip_members", []) else "👤 Member"
        else:
            tier_label = "🔐 Chưa có key"

        lines = [
            f"🎰〖 BOT {bot_name} 〗🎰",
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
            f"  Prefix : {p}    Tổng: {total}+ lệnh",
            f"  Cấp    : {tier_label}",
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
            "  HỆ THỐNG PHÂN QUYỀN:",
            "  👑 Super Owner  → Bot Admin",
            "  🛠 Bot Admin    → Key Owner",
            "  👑 Key Owner    → Group Admin",
            "  🛡 Group Admin  → VIP Member",
            "  ⭐ VIP Member   → Member",
            "  👤 Member",
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
        ]
        for num, title, cmds in self._MENU_CATS:
            lines.append(f"  {num}  {title}  ({len(cmds)} lệnh)")
        lines += [
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
            "  Trả lời số 1-10 để xem chi tiết",
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
        ]
        self._reply(snap, "\n".join(lines))

    def _handle_menu_reply(self, snap: dict, num: str) -> None:
        p = self.prefix
        detail = self._CAT_DETAIL.get(num)
        if not detail:
            return
        title, cmds = detail
        thread_id = str(snap.get("replyToID", ""))
        bot_name = self._get_bot_name(thread_id)
        lines = [
            f"🎰〖 BOT {bot_name} 〗🎰",
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
            f"  {title}",
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
        ]
        for cmd_line in cmds:
            lines.append(f"  {p}{cmd_line}")
        lines += [
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
            f"  Gõ {p}menu để quay lại danh sách",
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
        ]
        self._reply(snap, "\n".join(lines))

    # _cmd_help2 / _cmd_help3 đã được gộp vào _cmd_menu + _handle_menu_reply

    # ══════════════════════════════════════════════════════
    # 🔑 HỆ THỐNG KEY
    # ══════════════════════════════════════════════════════

    def _cmd_nhapkey(self, snap: dict, arg: str) -> None:
        uid = str(snap.get("userID", ""))
        key = arg.strip().upper()
        if not key:
            self._reply(snap, f"❌ Dùng: {self.prefix}nhapkey <KEY>")
            return
        kd = self._key_data
        if key not in kd.get("keys", {}):
            self._reply(snap, "❌ Key không tồn tại hoặc đã bị xoá!")
            return
        k_info = kd["keys"][key]
        if k_info.get("used") and k_info.get("uid") != uid:
            self._reply(snap, "❌ Key này đã được dùng bởi người khác!")
            return
        if k_info.get("revoked"):
            self._reply(snap, "❌ Key này đã bị thu hồi!")
            return
        days = k_info.get("days", 30)
        expires = time.time() + days * 86400
        kd["keys"][key] = {**k_info, "used": True, "uid": uid}
        if "user_keys" not in kd:
            kd["user_keys"] = {}
        # Đọc max_groups từ key info (createkey có thể lưu sẵn)
        max_groups = k_info.get("max_groups") or _days_to_max_groups(days)
        old_uk = kd["user_keys"].get(uid, {})
        kd["user_keys"][uid] = {
            "key": key, "expires": expires, "days": days,
            "max_groups": max_groups,
            "groups": old_uk.get("groups", []),
            "bot_name": old_uk.get("bot_name", ""),
        }
        save_keys(kd)
        exp_str = datetime.fromtimestamp(expires).strftime("%d/%m/%Y %H:%M")
        groups_used = len(old_uk.get("groups", []))
        days_left = days  # mới kích hoạt, còn nguyên
        p = self.prefix
        self._reply(snap, (
            "╔══════════════════════════════════╗\n"
            "║   ✅ KEY KÍCH HOẠT THÀNH CÔNG!   ║\n"
            "╚══════════════════════════════════╝\n"
            f"  🔑 Mã key   : {key}\n"
            f"  📦 Gói      : {days} ngày\n"
            f"  📅 Hết hạn  : {exp_str}\n"
            f"  👥 Số nhóm  : {groups_used}/{max_groups} nhóm đã dùng\n"
            f"  ⏳ Còn lại  : {days_left} ngày\n"
            "────────────────────────────────────\n"
            f"  📋 Xem lệnh  : {p}menu\n"
            f"  🏷️  Đổi tên bot : {p}daten <tên>\n"
            f"  📢 Tin chào nhóm: {p}setjoinmsg <text>\n"
            "────────────────────────────────────"
        ))

    def _cmd_muakey(self, snap: dict, arg: str) -> None:
        uid = str(snap.get("userID", ""))
        bank = self.cfg.get("bank_info", {})
        bank_name  = bank.get("name",   "BIDV")
        bank_stk   = bank.get("stk",    "1234567890")
        bank_owner = bank.get("owner",  "ADMIN HARU88")
        price_30   = bank.get("price_30",  "50.000đ")
        price_90   = bank.get("price_90",  "120.000đ")
        price_365  = bank.get("price_365", "400.000đ")
        kd = self._key_data
        if "pending" not in kd:
            kd["pending"] = {}
        kd["pending"][uid] = {"ts": time.time()}
        save_keys(kd)
        self._reply(snap, (
            "🛒 MUA KEY BOT\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  GÓI 30  ngày : {price_30}  (1 nhóm)\n"
            f"  GÓI 90  ngày : {price_90}  (3 nhóm)\n"
            f"  GÓI 365 ngày : {price_365}  (∞ nhóm)\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            "  THÔNG TIN CHUYỂN KHOẢN\n"
            f"  Ngân hàng: {bank_name}\n"
            f"  STK      : {bank_stk}\n"
            f"  Chủ TK   : {bank_owner}\n"
            f"  Nội dung : HARU88 {uid}\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            "  Sau khi CK admin sẽ xác nhận\n"
            "  và bot tự gửi KEY cho bạn!\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        ))

    def _cmd_taokey(self, snap: dict, arg: str) -> None:
        if not self._is_admin(snap):
            self._reply(snap, "❌ Chỉ admin mới dùng được lệnh này!")
            return
        try:
            days = int(arg.strip()) if arg.strip().isdigit() else 30
        except ValueError:
            days = 30
        key = gen_key(days)
        kd = self._key_data
        if "keys" not in kd:
            kd["keys"] = {}
        kd["keys"][key] = {"days": days, "used": False, "uid": None,
                           "created": time.time()}
        save_keys(kd)
        max_groups = _days_to_max_groups(days)
        self._reply(snap, (
            "✅ TẠO KEY THÀNH CÔNG!\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  KEY    : {key}\n"
            f"  Gói    : {days} ngày\n"
            f"  Nhóm   : tối đa {max_groups} nhóm\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        ))

    # ══════════════════════════════════════════════════════
    # 🔑 /createkey — Tạo key với số nhóm tùy chỉnh (Super Owner / Bot Admin)
    # ══════════════════════════════════════════════════════

    def _cmd_createkey(self, snap: dict, arg: str) -> None:
        """/createkey <ngày> <nhóm> — Tạo key với số ngày và số nhóm tùy chỉnh."""
        sender_id = str(snap.get("userID", ""))
        if not self._is_bot_admin(sender_id):
            self._reply(snap, "❌ Chỉ Bot Admin / Super Owner mới dùng được!")
            return
        parts = arg.strip().split()
        try:
            days = int(parts[0]) if parts else 30
        except ValueError:
            days = 30
        try:
            max_groups = int(parts[1]) if len(parts) > 1 else _days_to_max_groups(days)
        except ValueError:
            max_groups = _days_to_max_groups(days)
        key = gen_key(days)
        kd = self._key_data
        kd.setdefault("keys", {})[key] = {
            "days": days, "used": False, "uid": None,
            "created": time.time(), "max_groups": max_groups,
        }
        save_keys(kd)
        self._reply(snap, (
            "✅ TẠO KEY THÀNH CÔNG!\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  🔑 KEY  : {key}\n"
            f"  📦 Gói  : {days} ngày\n"
            f"  👥 Nhóm : tối đa {max_groups} nhóm\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Dùng: {self.prefix}nhapkey {key}"
        ))

    def _cmd_revokekey(self, snap: dict, arg: str) -> None:
        """/revokekey <KEY> — Thu hồi key (vô hiệu hoá, không xoá)."""
        sender_id = str(snap.get("userID", ""))
        if not self._is_bot_admin(sender_id):
            self._reply(snap, "❌ Chỉ Bot Admin / Super Owner mới dùng được!")
            return
        key = arg.strip().upper()
        kd = self._key_data
        k_info = kd.get("keys", {}).get(key)
        if not k_info:
            self._reply(snap, f"❌ Không tìm thấy key: {key}")
            return
        uid = k_info.get("uid")
        # Xoá user_key của người đang dùng
        if uid and uid in kd.get("user_keys", {}):
            del kd["user_keys"][uid]
        # Đánh dấu key đã bị thu hồi
        kd["keys"][key]["revoked"] = True
        kd["keys"][key]["used"] = True
        save_keys(kd)
        self._reply(snap, (
            f"✅ ĐÃ THU HỒI KEY!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  KEY : {key}\n"
            f"  UID : {uid or 'Chưa dùng'}\n"
            f"  Trạng thái: Đã vô hiệu hoá"
        ))

    def _cmd_checkuser(self, snap: dict, arg: str) -> None:
        """/checkuser <uid> — Xem thông tin key & nhóm của user (Bot Admin)."""
        sender_id = str(snap.get("userID", ""))
        if not self._is_bot_admin(sender_id):
            self._reply(snap, "❌ Chỉ Bot Admin / Super Owner mới dùng được!")
            return
        uid = arg.strip()
        if not uid:
            self._reply(snap, f"❌ Dùng: {self.prefix}checkuser <uid>")
            return
        kd = self._key_data
        uk = kd.get("user_keys", {}).get(uid)
        banned = uid in self._ban_set
        blacklisted = uid in self._blacklist
        if not uk:
            self._reply(snap, (
                f"👤 USER {uid}\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Key     : Không có\n"
                f"  Ban     : {'✅ Đang bị ban' if banned else '—'}\n"
                f"  Blacklist: {'✅ Đang blacklist' if blacklisted else '—'}"
            ))
            return
        key = uk.get("key", "—")
        expires = uk.get("expires", 0)
        days_left = max(0, int((expires - time.time()) / 86400))
        exp_str = datetime.fromtimestamp(expires).strftime("%d/%m/%Y") if expires else "—"
        groups = uk.get("groups", [])
        max_g = uk.get("max_groups", 1)
        self._reply(snap, (
            f"👤 USER {uid}\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  🔑 Key      : {key}\n"
            f"  📅 Hết hạn  : {exp_str} (còn {days_left} ngày)\n"
            f"  📦 Nhóm     : {len(groups)}/{max_g}\n"
            f"  🚫 Ban      : {'Có' if banned else 'Không'}\n"
            f"  ⛔ Blacklist: {'Có' if blacklisted else 'Không'}"
        ))

    def _cmd_checkgroup(self, snap: dict, arg: str) -> None:
        """/checkgroup [thread_id] — Xem thông tin nhóm (Bot Admin)."""
        sender_id = str(snap.get("userID", ""))
        if not self._is_bot_admin(sender_id):
            self._reply(snap, "❌ Chỉ Bot Admin / Super Owner mới dùng được!")
            return
        thread_id = arg.strip() or str(snap.get("replyToID", ""))
        if not thread_id:
            self._reply(snap, f"❌ Dùng: {self.prefix}checkgroup <thread_id>")
            return
        kd = self._key_data
        owner_uid = kd.get("group_owners", {}).get(thread_id)
        uk = kd.get("user_keys", {}).get(owner_uid) if owner_uid else None
        bot_name = self._get_bot_name(thread_id)
        admins_g = kd.get("group_admins", {}).get(thread_id, [])
        antilink = self._antilink_enabled.get(thread_id, False)
        antispam = self._antispam_enabled.get(thread_id, False)
        if uk:
            expires = uk.get("expires", 0)
            days_left = max(0, int((expires - time.time()) / 86400))
            exp_str = datetime.fromtimestamp(expires).strftime("%d/%m/%Y") if expires else "—"
            status = "✅ Đang hoạt động" if time.time() < expires else "❌ Hết hạn"
        else:
            exp_str = "—"; days_left = 0; status = "⚠️ Không có key"
        self._reply(snap, (
            f"🏘 THÔNG TIN NHÓM\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Thread ID  : {thread_id}\n"
            f"  Bot Name   : {bot_name}\n"
            f"  Chủ nhóm   : {owner_uid or 'Chưa đăng ký'}\n"
            f"  Key hết hạn: {exp_str} ({days_left} ngày)\n"
            f"  Trạng thái : {status}\n"
            f"  Admin nhóm : {len(admins_g)} người\n"
            f"  Anti-link  : {'Bật' if antilink else 'Tắt'}\n"
            f"  Anti-spam  : {'Bật' if antispam else 'Tắt'}"
        ))

    def _cmd_addbotadmin(self, snap: dict, arg: str) -> None:
        """/addbotadmin <uid> — Thêm Bot Admin (chỉ Super Owner)."""
        sender_id = str(snap.get("userID", ""))
        if not self._is_super_owner(sender_id):
            self._reply(snap, "❌ Chỉ Super Owner mới dùng được lệnh này!")
            return
        uid = arg.strip()
        if not uid:
            self._reply(snap, f"❌ Dùng: {self.prefix}addbotadmin <uid>")
            return
        self.admins.add(uid)
        # Lưu vào config (nếu muốn persist qua restart cần update file config)
        kd = self._key_data
        kd.setdefault("bot_admins", [])
        if uid not in kd["bot_admins"]:
            kd["bot_admins"].append(uid)
        save_keys(kd)
        self._reply(snap, (
            f"✅ ĐÃ THÊM BOT ADMIN!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  UID  : {uid}\n"
            f"  Cấp  : 🛠 Bot Admin\n"
            f"  Tổng : {len(self.admins)} admin"
        ))

    def _cmd_removebotadmin(self, snap: dict, arg: str) -> None:
        """/removebotadmin <uid> — Xoá Bot Admin (chỉ Super Owner)."""
        sender_id = str(snap.get("userID", ""))
        if not self._is_super_owner(sender_id):
            self._reply(snap, "❌ Chỉ Super Owner mới dùng được lệnh này!")
            return
        uid = arg.strip()
        if not uid or uid == self.super_owner:
            self._reply(snap, "❌ Không thể xoá Super Owner!")
            return
        self.admins.discard(uid)
        kd = self._key_data
        balist = kd.get("bot_admins", [])
        if uid in balist:
            balist.remove(uid)
        save_keys(kd)
        self._reply(snap, f"✅ Đã xoá Bot Admin UID: {uid}")

    # ══════════════════════════════════════════════════════
    # 👑 KEY OWNER — Quản lý key & nhóm
    # ══════════════════════════════════════════════════════

    def _cmd_checkkey(self, snap: dict, arg: str) -> None:
        """/checkkey — Hiển thị thông tin key hiện tại của mình."""
        sender_id = str(snap.get("userID", ""))
        thread_id = str(snap.get("replyToID", ""))
        kd = self._key_data
        # Xác định uid cần check (mặc định là chính mình)
        uid = arg.strip() if arg.strip() and self._is_bot_admin(sender_id) else sender_id
        uk = kd.get("user_keys", {}).get(uid)
        if not uk:
            self._reply(snap, (
                f"❌ UID {uid} chưa có key!\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Nhập key  : {self.prefix}nhapkey <KEY>\n"
                f"  Mua key   : {self.prefix}muakey"
            ))
            return
        key = uk.get("key", "—")
        expires = uk.get("expires", 0)
        days_left = max(0, int((expires - time.time()) / 86400))
        exp_str = datetime.fromtimestamp(expires).strftime("%d/%m/%Y") if expires else "—"
        groups = uk.get("groups", [])
        max_g = uk.get("max_groups", 1)
        is_active = time.time() < expires
        status = "✅ Hoạt động" if is_active else "❌ Hết hạn"
        self._reply(snap, (
            f"🔑 THÔNG TIN KEY\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  🔑 Key    : {key}\n"
            f"  👑 Chủ   : {uid}\n"
            f"  📅 Còn   : {days_left} ngày (hết {exp_str})\n"
            f"  📦 Nhóm  : {len(groups)}/{max_g}\n"
            f"  📊 Trạng thái: {status}\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Gia hạn : {self.prefix}giahan <KEY_MỚI>\n"
            f"  Nhóm    : {self.prefix}nhom"
        ))

    def _cmd_nhom(self, snap: dict, arg: str) -> None:
        """/nhom — Danh sách nhóm đang dùng bot theo key của mình."""
        sender_id = str(snap.get("userID", ""))
        thread_id = str(snap.get("replyToID", ""))
        kd = self._key_data
        # Key Owner xem nhóm của mình, Bot Admin có thể xem của người khác
        uid = arg.strip() if arg.strip() and self._is_bot_admin(sender_id) else sender_id
        # Cũng cho phép chủ nhóm hiện tại xem
        if not self._is_bot_admin(sender_id):
            owner_uid = kd.get("group_owners", {}).get(thread_id, "")
            if sender_id != owner_uid and not self._is_key_owner(thread_id, sender_id):
                self._reply(snap, "❌ Chỉ chủ nhóm / Key Owner mới xem được!")
                return
            uid = sender_id
        uk = kd.get("user_keys", {}).get(uid)
        if not uk:
            self._reply(snap, f"❌ UID {uid} chưa có key đăng ký nhóm nào!")
            return
        groups = uk.get("groups", [])
        max_g = uk.get("max_groups", 1)
        if not groups:
            self._reply(snap, (
                f"📊 DANH SÁCH NHÓM\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Chưa đăng ký nhóm nào!\n"
                f"  Đã dùng: 0/{max_g}\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            ))
            return
        emojis = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        lines = [
            f"📊 DANH SÁCH NHÓM",
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
        ]
        for i, gid in enumerate(groups):
            em = emojis[i] if i < len(emojis) else f"{i+1}."
            bot_name = self._get_bot_name(gid)
            lines.append(f"  {em} {bot_name}")
            lines.append(f"      ID: {gid}")
        lines += [
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
            f"  Đã dùng: {len(groups)}/{max_g}",
        ]
        self._reply(snap, "\n".join(lines))

    def _cmd_chunhom(self, snap: dict, arg: str) -> None:
        """/chunhom [thread_id] — Rời/huỷ đăng ký nhóm, giải phóng slot."""
        sender_id = str(snap.get("userID", ""))
        thread_id = str(snap.get("replyToID", ""))
        kd = self._key_data
        # Nếu có arg thì huỷ nhóm đó, không thì huỷ nhóm hiện tại
        target_gid = arg.strip() or thread_id
        owner_uid = kd.get("group_owners", {}).get(target_gid)
        # Chỉ chủ nhóm hoặc bot admin mới huỷ được
        if sender_id != owner_uid and not self._is_bot_admin(sender_id):
            self._reply(snap, "❌ Chỉ chủ nhóm hoặc Bot Admin mới dùng được!")
            return
        if not owner_uid:
            self._reply(snap, f"❌ Nhóm {target_gid} chưa đăng ký!")
            return
        # Xoá nhóm khỏi group_owners
        del kd["group_owners"][target_gid]
        # Xoá khỏi danh sách groups của user
        uk = kd.get("user_keys", {}).get(owner_uid)
        if uk:
            uk["groups"] = [g for g in uk.get("groups", []) if g != target_gid]
        # Xoá group admins
        kd.get("group_admins", {}).pop(target_gid, None)
        save_keys(kd)
        self._reply(snap, (
            f"✅ ĐÃ HUỶ ĐĂNG KÝ NHÓM!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Thread ID: {target_gid}\n"
            f"  Slot đã được giải phóng.\n"
            f"  Dùng {self.prefix}nhom để xem danh sách còn lại."
        ))

    def _cmd_thongtinnhom(self, snap: dict, arg: str) -> None:
        """/thongtinnhom — Xem thông tin nhóm hiện tại (Key Owner)."""
        thread_id = str(snap.get("replyToID", ""))
        sender_id = str(snap.get("userID", ""))
        # Cho phép group admin trở lên
        if not self._is_group_admin(thread_id, sender_id):
            self._reply(snap, "❌ Chỉ Group Admin trở lên mới dùng được!")
            return
        kd = self._key_data
        owner_uid = kd.get("group_owners", {}).get(thread_id)
        uk = kd.get("user_keys", {}).get(owner_uid) if owner_uid else None
        bot_name = self._get_bot_name(thread_id)
        admins_g = kd.get("group_admins", {}).get(thread_id, [])
        antilink = self._antilink_enabled.get(thread_id, False)
        antispam = self._antispam_enabled.get(thread_id, False)
        if uk:
            expires = uk.get("expires", 0)
            days_left = max(0, int((expires - time.time()) / 86400))
            exp_str = datetime.fromtimestamp(expires).strftime("%d/%m/%Y") if expires else "—"
            status = "✅ Đang hoạt động" if time.time() < expires else "❌ Hết hạn"
            key_str = uk.get("key", "—")
        else:
            exp_str = "—"; days_left = 0; status = "⚠️ Không có key"; key_str = "—"
        self._reply(snap, (
            f"🏘 THÔNG TIN NHÓM\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  🤖 Bot Name  : {bot_name}\n"
            f"  🔑 Key       : {key_str}\n"
            f"  👑 Chủ nhóm  : {owner_uid or 'Chưa đăng ký'}\n"
            f"  📅 Còn       : {days_left} ngày (hết {exp_str})\n"
            f"  📊 Trạng thái: {status}\n"
            f"  👮 Admin nhóm: {len(admins_g)} người\n"
            f"  🔗 Anti-link : {'Bật' if antilink else 'Tắt'}\n"
            f"  🚨 Anti-spam : {'Bật' if antispam else 'Tắt'}"
        ))

    def _cmd_giahan(self, snap: dict, arg: str) -> None:
        """/giahan <KEY_MỚI> — Gia hạn key (chuyển key mới vào tài khoản hiện tại)."""
        sender_id = str(snap.get("userID", ""))
        new_key = arg.strip().upper()
        if not new_key:
            self._reply(snap, f"❌ Dùng: {self.prefix}giahan <KEY_MỚI>")
            return
        kd = self._key_data
        k_info = kd.get("keys", {}).get(new_key)
        if not k_info:
            self._reply(snap, "❌ Key không tồn tại hoặc đã bị xoá!")
            return
        if k_info.get("revoked"):
            self._reply(snap, "❌ Key này đã bị thu hồi!")
            return
        if k_info.get("used") and k_info.get("uid") != sender_id:
            self._reply(snap, "❌ Key này đã được dùng bởi người khác!")
            return
        days = k_info.get("days", 30)
        max_groups_new = k_info.get("max_groups") or _days_to_max_groups(days)
        old_uk = kd.get("user_keys", {}).get(sender_id, {})
        old_expires = old_uk.get("expires", time.time())
        # Gia hạn: cộng thêm số ngày vào key cũ (nếu còn hạn), hoặc tính từ bây giờ
        base = max(old_expires, time.time())
        new_expires = base + days * 86400
        max_groups_final = max(old_uk.get("max_groups", 1), max_groups_new)
        kd.setdefault("user_keys", {})[sender_id] = {
            **old_uk,
            "key": new_key,
            "expires": new_expires,
            "days": days,
            "max_groups": max_groups_final,
        }
        kd["keys"][new_key] = {**k_info, "used": True, "uid": sender_id}
        save_keys(kd)
        exp_str = datetime.fromtimestamp(new_expires).strftime("%d/%m/%Y %H:%M")
        days_total = max(0, int((new_expires - time.time()) / 86400))
        self._reply(snap, (
            f"✅ GIA HẠN THÀNH CÔNG!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  🔑 Key mới   : {new_key}\n"
            f"  ➕ Cộng thêm : {days} ngày\n"
            f"  📅 Hết hạn   : {exp_str}\n"
            f"  ⏳ Tổng còn  : {days_total} ngày\n"
            f"  👥 Nhóm      : {len(old_uk.get('groups', []))}/{max_groups_final}"
        ))

    def _cmd_chuyennhom(self, snap: dict, arg: str) -> None:
        """/chuyennhom <thread_id_cu> <thread_id_moi> — Chuyển slot nhóm sang ID mới."""
        sender_id = str(snap.get("userID", ""))
        parts = arg.strip().split()
        if len(parts) < 2:
            self._reply(snap, f"❌ Dùng: {self.prefix}chuyennhom <id_cũ> <id_mới>")
            return
        old_gid, new_gid = parts[0], parts[1]
        kd = self._key_data
        owner_uid = kd.get("group_owners", {}).get(old_gid)
        if sender_id != owner_uid and not self._is_bot_admin(sender_id):
            self._reply(snap, "❌ Chỉ chủ nhóm hoặc Bot Admin mới dùng được!")
            return
        if not owner_uid:
            self._reply(snap, f"❌ Nhóm {old_gid} chưa đăng ký!")
            return
        # Cập nhật group_owners
        del kd["group_owners"][old_gid]
        kd["group_owners"][new_gid] = owner_uid
        # Cập nhật danh sách groups của user
        uk = kd.get("user_keys", {}).get(owner_uid)
        if uk:
            groups = uk.get("groups", [])
            if old_gid in groups:
                groups[groups.index(old_gid)] = new_gid
            uk["groups"] = groups
        # Chuyển group_admins
        old_gadmins = kd.get("group_admins", {}).pop(old_gid, [])
        if old_gadmins:
            kd.setdefault("group_admins", {})[new_gid] = old_gadmins
        save_keys(kd)
        self._reply(snap, (
            f"✅ ĐÃ CHUYỂN NHÓM!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Cũ : {old_gid}\n"
            f"  Mới: {new_gid}\n"
            f"  Admin nhóm đã được chuyển theo."
        ))

    def _cmd_xoakey(self, snap: dict, arg: str) -> None:
        if not self._is_admin(snap):
            self._reply(snap, "❌ Chỉ admin mới dùng được lệnh này!")
            return
        key = arg.strip().upper()
        kd = self._key_data
        if key in kd.get("keys", {}):
            del kd["keys"][key]
            save_keys(kd)
            self._reply(snap, f"✅ Đã xoá key: {key}")
        else:
            self._reply(snap, f"❌ Không tìm thấy key: {key}")

    def _cmd_danhsachkey(self, snap: dict, arg: str) -> None:
        if not self._is_admin(snap):
            self._reply(snap, "❌ Chỉ admin mới dùng được lệnh này!")
            return
        kd = self._key_data
        keys = kd.get("keys", {})
        if not keys:
            self._reply(snap, "📭 Chưa có key nào được tạo.")
            return
        lines = ["🔑 DANH SÁCH KEY\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"]
        for k, info in list(keys.items())[:20]:
            used = "✅ Dùng" if info.get("used") else "⏳ Chưa"
            lines.append(f"  {k}  [{info.get('days',30)}d] {used}")
        pending = kd.get("pending", {})
        if pending:
            lines.append(f"\n📥 Chờ xác nhận: {len(pending)} người")
            for uid in list(pending.keys())[:5]:
                lines.append(f"  UID: {uid}")
        self._reply(snap, "\n".join(lines))

    def _cmd_xacnhan(self, snap: dict, arg: str) -> None:
        """Admin xác nhận mua key: /xacnhan <uid> [ngày]"""
        if not self._is_admin(snap):
            self._reply(snap, "❌ Chỉ admin mới dùng được lệnh này!")
            return
        parts = arg.strip().split()
        if not parts:
            self._reply(snap, f"❌ Dùng: {self.prefix}xacnhan <uid> [ngày]")
            return
        target_uid = parts[0]
        try:
            days = int(parts[1]) if len(parts) > 1 else 30
        except ValueError:
            days = 30
        key = gen_key(days)
        kd = self._key_data
        if "keys" not in kd:
            kd["keys"] = {}
        if "user_keys" not in kd:
            kd["user_keys"] = {}
        expires = time.time() + days * 86400
        max_groups = _days_to_max_groups(days)
        kd["keys"][key] = {"days": days, "used": True, "uid": target_uid,
                           "created": time.time()}
        old_uk = kd["user_keys"].get(target_uid, {})
        kd["user_keys"][target_uid] = {
            "key": key, "expires": expires, "days": days,
            "max_groups": max_groups,
            "groups": old_uk.get("groups", []),
            "bot_name": old_uk.get("bot_name", ""),
        }
        kd.get("pending", {}).pop(target_uid, None)
        save_keys(kd)
        exp_str = datetime.fromtimestamp(expires).strftime("%d/%m/%Y %H:%M")
        # Gửi key cho người mua qua DM
        dm_ok = self._send_dm(target_uid, (
            "🎉 THANH TOÁN THÀNH CÔNG!\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  KEY của bạn:\n"
            f"  {key}\n"
            f"  Gói    : {days} ngày\n"
            f"  Hết hạn: {exp_str}\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Nhập key: /nhapkey {key}\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        ))
        self._reply(snap, (
            f"✅ Đã xác nhận và gửi key cho UID {target_uid}\n"
            f"  KEY: {key}  ({days} ngày)\n"
            f"  DM: {'✅ Thành công' if dm_ok else '⚠️ Gửi DM thất bại — báo key thủ công'}"
        ))

    def _cmd_id(self, snap: dict, arg: str) -> None:
        self._reply(snap, (
            f"🆔 THÔNG TIN ID\n"
            f"{DIVIDER}\n"
            f"  Loại      : {'Nhóm' if snap.get('type') != 'user' else 'Người dùng'}\n"
            f"  Thread ID : {snap.get('replyToID')}\n"
            f"  User ID   : {snap.get('userID')}\n"
            f"  Message ID: {snap.get('messageID')}\n"
            f"  Thời gian : {datetime.now():%d/%m/%Y %H:%M:%S}"
        ))

    def _cmd_info(self, snap: dict, arg: str) -> None:
        uid = self.dataFB.get("FacebookID")
        uptime = format_uptime(time.time() - BOT_START_TIME)
        admin_count = len(self.admins) if self.admins else "Tất cả"
        self._reply(snap, (
            f"🤖 THÔNG TIN BOT\n"
            f"{DIVIDER}\n"
            f"  UID Bot   : {uid}\n"
            f"  Uptime    : {uptime}\n"
            f"  Prefix    : '{self.prefix}'\n"
            f"  Admins    : {admin_count}\n"
            f"  Lệnh      : {len(self._handlers)}\n"
            f"  Tin nhận  : {self._msg_count}\n"
            f"  Framework : fbchat-v2\n"
            f"  Tác giả   : MinhHuyDev\n"
            f"  Build     : Python {sys.version.split()[0]}"
        ))

    def _cmd_uptime(self, snap: dict, arg: str) -> None:
        uptime = format_uptime(time.time() - BOT_START_TIME)
        since = datetime.fromtimestamp(BOT_START_TIME).strftime("%d/%m/%Y %H:%M")
        self._reply(snap, (
            f"⏱️ UPTIME BOT\n"
            f"{DIVIDER}\n"
            f"  Thời gian: {uptime}\n"
            f"  Từ lúc  : {since}"
        ))

    def _cmd_userinfo(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}userinfo <userID>")
            return
        uid = arg.strip().split()[0]
        try:
            info = _get_user_info.func(self.dataFB, uid)
        except Exception as e:
            self._reply(snap, f"❌ Lỗi: {e}")
            return
        if info.get("err") == 0:
            self._reply(snap, f"❌ Không tìm thấy user ID: {uid}")
            return
        gender = info.get("genderUser", "Không rõ")
        fb_url = info.get("urlProfile", f"https://facebook.com/{uid}")
        self._reply(snap, (
            f"👤 THÔNG TIN NGƯỜI DÙNG\n"
            f"{DIVIDER}\n"
            f"  Tên       : {info.get('nameUser')}\n"
            f"  First name: {info.get('firstName')}\n"
            f"  Username  : @{info.get('Username') or 'Không có'}\n"
            f"  UID       : {info.get('idUser')}\n"
            f"  Giới tính : {gender}\n"
            f"  Link      : {fb_url}"
        ))

    # ══════════════════════════════════════════════════════
    # 👥 QUẢN LÝ NHÓM
    # ══════════════════════════════════════════════════════

    def _cmd_tengroup(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}tengroup <tên mới>")
            return
        thread_id = str(snap["replyToID"])
        try:
            result = _changeNameThread.func(self.dataFB, thread_id, arg)
            if result.get("status") == "success":
                self._reply(snap, f"✅ Đã đổi tên nhóm thành:\n📝 {arg}")
            else:
                self._reply(snap, f"❌ {result.get('message', 'Không đổi được tên nhóm.')}")
        except Exception as e:
            self._reply(snap, f"❌ Lỗi: {e}")

    def _cmd_emoji(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}emoji <emoji>")
            return
        thread_id = str(snap["replyToID"])
        emoji = arg.strip().split()[0]
        try:
            result = _changeEmoji.func(self.dataFB, thread_id, emoji)
            if result.get("status") == "success":
                self._reply(snap, f"✅ Đã đổi emoji nhóm thành: {emoji}")
            else:
                self._reply(snap, f"❌ {result.get('message', 'Không đổi được emoji.')}")
        except Exception as e:
            self._reply(snap, f"❌ Lỗi: {e}")

    def _cmd_mynick(self, snap: dict, arg: str) -> None:
        """Thành viên tự đổi biệt danh của chính mình trong nhóm."""
        if not arg.strip():
            self._reply(snap, (
                f"ℹ️ {self.prefix}mynick <biệt danh>\n"
                f"  Đổi biệt danh của bạn trong nhóm này.\n"
                f"  Ví dụ: {self.prefix}mynick Cún Cưng 🐶"
            ))
            return
        uid = str(snap.get("userID", ""))
        thread_id = str(snap["replyToID"])
        nickname = arg.strip()
        if not uid:
            self._reply(snap, "❌ Không xác định được UID của bạn.")
            return
        try:
            result = _changeNickname.func(self.dataFB, thread_id, uid, nickname)
            if result.get("status") == "success":
                name = self._get_display_name(uid)
                self._reply(snap, f"✅ Đã đổi biệt danh của {name}:\n📝 {nickname}")
            else:
                self._reply(snap, f"❌ {result.get('message', 'Không đổi được biệt danh.')}")
        except Exception as e:
            self._reply(snap, f"❌ Lỗi: {e}")

    def _cmd_nick(self, snap: dict, arg: str) -> None:
        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}nick <userID> <biệt danh>")
            return
        uid, nickname = parts[0], parts[1]
        thread_id = str(snap["replyToID"])
        try:
            result = _changeNickname.func(self.dataFB, thread_id, uid, nickname)
            if result.get("status") == "success":
                name = self._get_display_name(uid)
                self._reply(snap, f"✅ Đã đổi biệt danh của {name}:\n📝 {nickname}")
            else:
                self._reply(snap, f"❌ {result.get('message', 'Không đổi được biệt danh.')}")
        except Exception as e:
            self._reply(snap, f"❌ Lỗi: {e}")

    def _cmd_themadmin(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}themadmin <userID>")
            return
        uid = arg.strip().split()[0]
        thread_id = str(snap["replyToID"])
        try:
            result = _addAdmin.func(self.dataFB, thread_id, uid, statusChoice=True)
            if result.get("status") == "success":
                self._reply(snap, f"✅ Đã thêm UID {uid} làm admin nhóm! 👑")
            else:
                self._reply(snap, f"❌ {result.get('message', 'Không thêm được admin.')}")
        except Exception as e:
            self._reply(snap, f"❌ Lỗi: {e}")

    def _cmd_xoadmin(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}xoadmin <userID>")
            return
        uid = arg.strip().split()[0]
        thread_id = str(snap["replyToID"])
        try:
            result = _addAdmin.func(self.dataFB, thread_id, uid, statusChoice=False)
            if result.get("status") == "success":
                self._reply(snap, f"✅ Đã bỏ quyền admin của UID {uid}.")
            else:
                self._reply(snap, f"❌ {result.get('message', 'Không bỏ được admin.')}")
        except Exception as e:
            self._reply(snap, f"❌ Lỗi: {e}")

    def _cmd_tagall(self, snap: dict, arg: str) -> None:
        thread_id = str(snap["replyToID"])
        try:
            data = _all_thread_data.func(self.dataFB)
            members_info = _all_thread_data.features(
                data.get("dataGet", "{}"),
                thread_id,
                "exportMemberListToJson",
            )
            if not isinstance(members_info, list):
                self._reply(snap, "❌ Không lấy được danh sách thành viên.")
                return

            names = []
            for item in members_info:
                try:
                    user = json.loads(item)
                    for uid_key, udata in user.items():
                        name = udata.get("nameFB", "").strip()
                        if name:
                            names.append(name)
                except Exception:
                    continue

            if not names:
                self._reply(snap, "❌ Không có thành viên nào để tag.")
                return

            note = f"📢 {arg}" if arg else f"📢 TAG TẤT CẢ ({len(names)} người)"
            chunk_size = 20
            for i in range(0, len(names), chunk_size):
                batch = names[i:i + chunk_size]
                msg = note + "\n" + "  ".join(f"@{n}" for n in batch)
                self._send_plain(snap, msg)
                time.sleep(0.6)
        except Exception as e:
            self._reply(snap, f"❌ Lỗi: {e}")

    def _cmd_members(self, snap: dict, arg: str) -> None:
        thread_id = str(snap["replyToID"])
        try:
            data = _all_thread_data.func(self.dataFB)
            members_info = _all_thread_data.features(
                data.get("dataGet", "{}"),
                thread_id,
                "exportMemberListToJson",
            )
            if not isinstance(members_info, list):
                self._reply(snap, "❌ Không lấy được danh sách thành viên.")
                return

            lines = [f"👥 THÀNH VIÊN NHÓM ({len(members_info)} người)\n{DIVIDER}"]
            for i, item in enumerate(members_info[:30], 1):
                try:
                    user = json.loads(item)
                    for uid_key, udata in user.items():
                        name = udata.get("nameFB", "?")
                        uid_val = udata.get("idFacebook", uid_key)
                        role = " 👑" if uid_val in self.admins else ""
                        lines.append(f"  {i:02d}. {name}{role}\n      UID: {uid_val}")
                except Exception:
                    continue

            if len(members_info) > 30:
                lines.append(f"\n  ... và {len(members_info) - 30} người khác")

            self._reply(snap, "\n".join(lines))
        except Exception as e:
            self._reply(snap, f"❌ Lỗi: {e}")

    def _cmd_announce(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}announce <nội dung>")
            return
        self._send_plain(snap, (
            f"📣 ══════════════════════════ 📣\n"
            f"             THÔNG BÁO QUAN TRỌNG\n"
            f"📣 ══════════════════════════ 📣\n\n"
            f"{arg}\n\n"
            f"─────────────────────────────\n"
            f"🕐 {datetime.now():%d/%m/%Y %H:%M}"
        ))

    # ══════════════════════════════════════════════════════
    # 🔧 CÔNG CỤ
    # ══════════════════════════════════════════════════════

    def _cmd_spam(self, snap: dict, arg: str) -> None:
        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}spam <số lần> <nội dung>")
            return
        try:
            count = min(int(parts[0]), 10)
        except ValueError:
            self._reply(snap, "❌ Số lần phải là số nguyên (tối đa 10).")
            return
        content = parts[1]
        self._reply(snap, f"📤 Đang gửi {count} tin nhắn...")
        for i in range(count):
            self._send_plain(snap, f"[{i+1}/{count}] {content}")
            time.sleep(0.5)

    def _cmd_echo(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}echo <nội dung>")
            return
        self._reply(snap, f"🔁 {arg}")

    def _cmd_react(self, snap: dict, arg: str) -> None:
        emoji = arg.strip().split()[0] if arg.strip() else "👍"
        mid = snap.get("messageID")
        if not mid:
            self._reply(snap, "❌ Không lấy được messageID.")
            return
        try:
            react_message(self.dataFB, "add", mid, emoji)
            log("react", f"Đã react {emoji} vào {mid}")
        except Exception as e:
            self._reply(snap, f"❌ Lỗi react: {e}")

    def _cmd_unsend(self, snap: dict, arg: str) -> None:
        thread_id = str(snap["replyToID"])
        target = self._last_bot_message.get(thread_id)
        if not target:
            self._reply(snap, "ℹ️ Chưa có tin nào để thu hồi trong nhóm này.")
            return
        result = unsend_message(target, self.dataFB)
        log("unsend", f"{target} → {result}")
        self._last_bot_message.pop(thread_id, None)

    def _cmd_search(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}search <từ khoá>")
            return
        try:
            res = _search.func(self.dataFB, arg)
        except Exception as e:
            self._reply(snap, f"❌ Lỗi tìm kiếm: {e}")
            return
        users = res.get("searchResultsDict") if isinstance(res, dict) else None
        if not users:
            self._reply(snap, f"🔍 Không tìm thấy kết quả cho: {arg}")
            return
        lines = [f"🔍 KẾT QUẢ TÌM KIẾM: '{arg}'\n{DIVIDER}"]
        for i, u in enumerate(users[:5], 1):
            lines.append(f"  {i}. {u.get('name')}\n     UID: {u.get('id')}")
        self._reply(snap, "\n".join(lines))

    # ══════════════════════════════════════════════════════
    # ⚙️ CÀI ĐẶT BOT
    # ══════════════════════════════════════════════════════

    def _cmd_addadmin(self, snap: dict, arg: str) -> None:
        if not self._is_admin(snap):
            self._reply(snap, "⛔ Chỉ admin bot mới dùng được lệnh này.")
            return
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}addadmin <userID>")
            return
        uid = arg.strip().split()[0]
        self.admins.add(uid)
        self.cfg.setdefault("admins", [])
        if uid not in self.cfg["admins"]:
            self.cfg["admins"].append(uid)
            save_config(self.cfg)
        self._reply(snap, f"✅ Đã thêm UID {uid} làm admin bot! 👑")

    def _cmd_removeadmin(self, snap: dict, arg: str) -> None:
        if not self._is_admin(snap):
            self._reply(snap, "⛔ Chỉ admin bot mới dùng được lệnh này.")
            return
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}removeadmin <userID>")
            return
        uid = arg.strip().split()[0]
        self.admins.discard(uid)
        cfg_admins = self.cfg.get("admins", [])
        if uid in cfg_admins:
            cfg_admins.remove(uid)
            save_config(self.cfg)
        self._reply(snap, f"✅ Đã xoá UID {uid} khỏi admin bot.")

    def _cmd_adminlist(self, snap: dict, arg: str) -> None:
        if not self.admins:
            self._reply(snap, "ℹ️ Chưa có admin bot nào — mọi người đều dùng được tất cả lệnh.")
            return
        lines = [f"👑 DANH SÁCH ADMIN BOT ({len(self.admins)} người)\n{DIVIDER}"]
        for i, uid in enumerate(sorted(self.admins), 1):
            lines.append(f"  {i}. UID: {uid}")
        self._reply(snap, "\n".join(lines))

    def _cmd_daten(self, snap: dict, arg: str) -> None:
        """Đổi tên bot hiển thị trong /menu của nhóm này."""
        thread_id = str(snap.get("replyToID", ""))
        sender_id = str(snap.get("userID", ""))
        name = arg.strip()
        if not name:
            self._reply(snap, "❌ Nhập tên bot!")
            return
        if len(name) > 30:
            self._reply(snap, "❌ Tên quá dài (tối đa 30 ký tự)!")
            return
        # Xác định chủ nhóm (người đã đăng ký nhóm, hoặc chính người gửi nếu là admin)
        kd = self._key_data
        owner_uid = kd.get("group_owners", {}).get(thread_id) or sender_id
        uk = kd.setdefault("user_keys", {}).get(owner_uid)
        if not uk and sender_id not in self.admins:
            self._reply(snap, "❌ Nhóm chưa có key kích hoạt!")
            return
        if uk is None:
            uk = {}
            kd["user_keys"][owner_uid] = uk
        uk["bot_name"] = name
        save_keys(kd)
        self._reply(snap, (
            f"✅ ĐÃ ĐỔI TÊN BOT!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Tên mới: {name}\n"
            f"  Gõ {self.prefix}menu để xem thay đổi!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        ))

    def _cmd_setjoinmsg(self, snap: dict, arg: str) -> None:
        """Đặt tin nhắn chào khi bot vào nhóm. Hỗ trợ {bot_name} và {prefix}."""
        thread_id = str(snap.get("replyToID", ""))
        sender_id = str(snap.get("userID", ""))
        kd = self._key_data
        owner_uid = kd.get("group_owners", {}).get(thread_id) or sender_id

        # Phải là chủ nhóm hoặc admin
        if owner_uid != sender_id and sender_id not in self.admins:
            self._reply(snap, "❌ Chỉ chủ nhóm (người đăng ký key) hoặc admin mới dùng được!")
            return

        uk = kd.setdefault("user_keys", {}).get(owner_uid)
        if not uk and sender_id not in self.admins:
            self._reply(snap, "❌ Nhóm chưa có key kích hoạt!")
            return

        text = arg.strip()
        if not text:
            # Xem tin chào hiện tại
            current = (uk or {}).get("join_message", "").strip() if uk else ""
            if current:
                self._reply(snap, (
                    f"📢 TIN CHÀO HIỆN TẠI:\n"
                    f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"{current}\n"
                    f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"  Dùng {self.prefix}setjoinmsg reset để xoá về mặc định\n"
                    f"  Dùng {self.prefix}setjoinmsg <nội dung> để đổi"
                ))
            else:
                self._reply(snap, (
                    f"📢 HƯỚNG DẪN ĐẶT TIN CHÀO:\n"
                    f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"  {self.prefix}setjoinmsg <nội dung>\n"
                    f"  Biến hỗ trợ: {{bot_name}} {{prefix}}\n"
                    f"  Ví dụ: {self.prefix}setjoinmsg Chào! Bot {{bot_name}} đã vào nhóm!\n"
                    f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                ))
            return

        if text.lower() == "reset":
            if uk:
                uk.pop("join_message", None)
                save_keys(kd)
            # Xoá nhóm khỏi announced để bot gửi lại tin chào mặc định lần tới (nếu muốn)
            self._reply(snap, "✅ Đã xoá tin chào tùy chỉnh. Bot sẽ dùng tin chào mặc định!")
            return

        if len(text) > 500:
            self._reply(snap, "❌ Tin chào quá dài (tối đa 500 ký tự)!")
            return

        if uk is None:
            uk = {}
            kd["user_keys"][owner_uid] = uk
        uk["join_message"] = text
        save_keys(kd)

        p = self.prefix
        bot_name = self._get_bot_name(thread_id)
        preview = text.replace("{bot_name}", bot_name).replace("{prefix}", p)
        self._reply(snap, (
            f"✅ ĐÃ ĐẶT TIN CHÀO BOT!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Xem trước:\n"
            f"{preview}\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Tin này sẽ hiển thị khi bot vào nhóm mới!"
        ))

    # ══════════════════════════════════════════════════════
    # 👥 QUẢN LÝ ADMIN NHÓM (Key Owner only)
    # ══════════════════════════════════════════════════════

    def _cmd_addgroupadmin(self, snap: dict, arg: str) -> None:
        """Thêm admin nhóm (chỉ chủ nhóm/key owner)."""
        thread_id = str(snap.get("replyToID", ""))
        target_uid = arg.strip().split()[0] if arg.strip() else ""
        if not target_uid:
            self._reply(snap, f"❌ Dùng: {self.prefix}addgroupadmin <uid>")
            return
        kd = self._key_data
        ga = kd.setdefault("group_admins", {}).setdefault(thread_id, [])
        if target_uid in ga:
            self._reply(snap, f"⚠️ UID {target_uid} đã là admin nhóm!")
            return
        ga.append(target_uid)
        save_keys(kd)
        self._reply(snap, (
            f"✅ ĐÃ THÊM ADMIN NHÓM!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  UID: {target_uid}\n"
            f"  Họ có thể dùng: tagall, ban, warn,\n"
            f"  announce, members, spam và các lệnh admin khác\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        ))

    def _cmd_removegroupadmin(self, snap: dict, arg: str) -> None:
        """Xoá admin nhóm (chỉ chủ nhóm/key owner)."""
        thread_id = str(snap.get("replyToID", ""))
        target_uid = arg.strip().split()[0] if arg.strip() else ""
        if not target_uid:
            self._reply(snap, f"❌ Dùng: {self.prefix}removegroupadmin <uid>")
            return
        kd = self._key_data
        ga = kd.get("group_admins", {}).get(thread_id, [])
        if target_uid not in ga:
            self._reply(snap, f"❌ UID {target_uid} không phải admin nhóm!")
            return
        ga.remove(target_uid)
        kd.setdefault("group_admins", {})[thread_id] = ga
        save_keys(kd)
        self._reply(snap, f"✅ Đã xoá admin nhóm UID: {target_uid}")

    def _cmd_groupadminlist(self, snap: dict, arg: str) -> None:
        """Xem danh sách admin nhóm."""
        thread_id = str(snap.get("replyToID", ""))
        kd = self._key_data
        owner = kd.get("group_owners", {}).get(thread_id, "?")
        ga = kd.get("group_admins", {}).get(thread_id, [])
        lines = [
            f"👑 PHÂN QUYỀN NHÓM\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
            f"  Chủ nhóm (Key Owner):",
            f"  → UID: {owner}",
            f"\n  Admin nhóm ({len(ga)} người):",
        ]
        if ga:
            for uid in ga:
                lines.append(f"  → UID: {uid}")
        else:
            lines.append("  (Chưa có admin nhóm nào)")
        lines += [
            f"\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
            f"  Thêm admin: {self.prefix}addgroupadmin <uid>",
            f"  Xoá admin : {self.prefix}removegroupadmin <uid>",
        ]
        self._reply(snap, "\n".join(lines))

    def _cmd_fbadmins(self, snap: dict, arg: str) -> None:
        """Hiển thị admin THỰC (trên Facebook) của nhóm hiện tại."""
        thread_id = str(snap.get("replyToID", ""))
        if not thread_id or snap.get("type") == "user":
            self._reply(snap, "⚠️ Lệnh này chỉ dùng trong nhóm!")
            return
        self._reply(snap, "🔍 Đang kiểm tra danh sách admin nhóm...")
        # Xóa cache để lấy dữ liệu mới nhất
        self._fb_admins_cache.pop(thread_id, None)
        fb_admins = self._get_fb_admins(thread_id)
        if not fb_admins:
            self._reply(snap, (
                "⚠️ ADMIN NHÓM FACEBOOK\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                "  Không lấy được danh sách admin.\n"
                "  (Bot cần là thành viên nhóm để đọc thông tin)"
            ))
            return
        lines = [
            f"👑 ADMIN NHÓM FACEBOOK\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
            f"  Tổng: {len(fb_admins)} admin",
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
        ]
        for i, uid in enumerate(sorted(fb_admins), 1):
            name = self._get_display_name(uid)
            lines.append(f"  {i}. {name}")
        lines += [
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔",
            f"  ℹ️ Admin thực Facebook tự động được cấp",
            f"  quyền Group Admin trong bot.",
        ]
        self._reply(snap, "\n".join(lines))

    def _cmd_setprefix(self, snap: dict, arg: str) -> None:
        new_prefix = arg.strip().split()[0] if arg.strip() else ""
        if not new_prefix:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}setprefix <ký tự>")
            return
        old = self.prefix
        self.prefix = new_prefix
        self.cfg["prefix"] = new_prefix
        save_config(self.cfg)
        self._reply(snap, f"✅ Đã đổi prefix: '{old}' → '{new_prefix}'")

    def _cmd_setrules(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}setrules <nội dung nội quy>")
            return
        self.cfg["rules"] = arg
        save_config(self.cfg)
        self._reply(snap, "✅ Đã cập nhật nội quy nhóm!")

    def _cmd_setgreeting(self, snap: dict, arg: str) -> None:
        if not arg:
            self.cfg["greeting"] = ""
            save_config(self.cfg)
            self._reply(snap, "✅ Đã tắt tin nhắn chào mừng.")
            return
        self.cfg["greeting"] = arg
        save_config(self.cfg)
        self._reply(snap, f"✅ Đã đặt tin chào:\n💬 {arg}")

    def _cmd_blacklist(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}blacklist <userID>")
            return
        uid = arg.strip().split()[0]
        self._blacklist.add(uid)
        bl = self.cfg.setdefault("blacklist", [])
        if uid not in bl:
            bl.append(uid)
            save_config(self.cfg)
        self._reply(snap, f"🚫 Đã chặn UID {uid} khỏi bot.")

    def _cmd_whitelist(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}whitelist <userID>")
            return
        uid = arg.strip().split()[0]
        self._blacklist.discard(uid)
        bl = self.cfg.get("blacklist", [])
        if uid in bl:
            bl.remove(uid)
            save_config(self.cfg)
        self._reply(snap, f"✅ Đã bỏ chặn UID {uid}.")

    def _cmd_autoreply(self, snap: dict, arg: str) -> None:
        status = arg.strip().lower()
        if status in ("on", "bật", "1", "true"):
            self.cfg["autoreply"] = True
            save_config(self.cfg)
            self._reply(snap, "✅ Đã BẬT chế độ tự động trả lời.")
        elif status in ("off", "tắt", "0", "false"):
            self.cfg["autoreply"] = False
            save_config(self.cfg)
            self._reply(snap, "✅ Đã TẮT chế độ tự động trả lời.")
        else:
            current = "BẬT" if self.cfg.get("autoreply") else "TẮT"
            self._reply(snap, f"ℹ️ Trạng thái hiện tại: {current}\nDùng: {self.prefix}autoreply on/off")

    # ══════════════════════════════════════════════════════
    # 📜 KIỂM DUYỆT
    # ══════════════════════════════════════════════════════

    def _cmd_rules(self, snap: dict, arg: str) -> None:
        rules = self.cfg.get("rules", "").strip()
        if not rules:
            self._reply(snap, f"ℹ️ Chưa có nội quy. Admin dùng {self.prefix}setrules <nội dung>")
            return
        self._reply(snap, (
            f"📜 NỘI QUY NHÓM\n"
            f"{DIVIDER}\n"
            f"{rules}\n"
            f"{DIVIDER}\n"
            f"📅 Vi phạm sẽ bị xử lý theo quy định!"
        ))

    def _cmd_warn(self, snap: dict, arg: str) -> None:
        parts = arg.split(maxsplit=1)
        if not parts:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}warn <userID> [lý do]")
            return
        uid = parts[0]
        reason = parts[1] if len(parts) > 1 else "Không có lý do"
        self._warn_list.setdefault(uid, [])
        self._warn_list[uid].append(f"{datetime.now():%d/%m %H:%M} — {reason}")
        count = len(self._warn_list[uid])
        warn_bar = "🟡" * min(count, 3) + "🔴" * max(0, count - 3)
        self._reply(snap, (
            f"⚠️ CẢNH CÁO\n"
            f"{DIVIDER}\n"
            f"  UID    : {uid}\n"
            f"  Lý do  : {reason}\n"
            f"  Lần này: {count}\n"
            f"  {warn_bar}\n"
            f"{'  ⚠️ Cảnh cáo nghiêm trọng! Cân nhắc ban!' if count >= 3 else ''}"
        ))

    def _cmd_warnlist(self, snap: dict, arg: str) -> None:
        if not self._warn_list:
            self._reply(snap, "✅ Không có thành viên nào bị cảnh cáo.")
            return
        lines = [f"⚠️ DANH SÁCH CẢNH CÁO\n{DIVIDER}"]
        for uid, warns in sorted(self._warn_list.items(), key=lambda x: -len(x[1])):
            name = self._get_display_name(uid)
            lines.append(f"\n  👤 {name} — {len(warns)} lần:")
            for w in warns[-3:]:
                lines.append(f"    • {w}")
        self._reply(snap, "\n".join(lines))

    def _cmd_clearwarn(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}clearwarn <userID>")
            return
        uid = arg.strip().split()[0]
        if uid in self._warn_list:
            del self._warn_list[uid]
            self._reply(snap, f"✅ Đã xoá toàn bộ cảnh cáo của UID {uid}.")
        else:
            self._reply(snap, f"ℹ️ UID {uid} chưa có cảnh cáo nào.")

    def _cmd_ban(self, snap: dict, arg: str) -> None:
        parts = arg.split(maxsplit=1)
        if not parts:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}ban <userID> [lý do]")
            return
        uid = parts[0]
        reason = parts[1] if len(parts) > 1 else "Vi phạm nội quy"
        self._ban_set.add(uid)
        self._blacklist.add(uid)
        cfg_ban = self.cfg.setdefault("banlist", [])
        if uid not in cfg_ban:
            cfg_ban.append(uid)
        bl = self.cfg.setdefault("blacklist", [])
        if uid not in bl:
            bl.append(uid)
        save_config(self.cfg)
        self._reply(snap, (
            f"🔨 ĐÃ BAN\n"
            f"{DIVIDER}\n"
            f"  UID   : {uid}\n"
            f"  Lý do : {reason}\n"
            f"  Thời gian: {datetime.now():%d/%m/%Y %H:%M}\n"
            f"  Người ban: UID {snap.get('userID')}"
        ))

    def _cmd_unban(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}unban <userID>")
            return
        uid = arg.strip().split()[0]
        self._ban_set.discard(uid)
        self._blacklist.discard(uid)
        for key in ("banlist", "blacklist"):
            lst = self.cfg.get(key, [])
            if uid in lst:
                lst.remove(uid)
        save_config(self.cfg)
        self._reply(snap, f"✅ Đã bỏ ban UID {uid}.")

    def _cmd_banlist(self, snap: dict, arg: str) -> None:
        if not self._ban_set:
            self._reply(snap, "✅ Không có ai bị ban.")
            return
        lines = [f"🔨 DANH SÁCH BAN ({len(self._ban_set)} người)\n{DIVIDER}"]
        for i, uid in enumerate(sorted(self._ban_set), 1):
            name = self._get_display_name(uid)
            lines.append(f"  {i}. 👤 {name}")
        self._reply(snap, "\n".join(lines))

    # ══════════════════════════════════════════════════════
    # 🎮 VUI CHƠI
    # ══════════════════════════════════════════════════════

    def _cmd_tung(self, snap: dict, arg: str) -> None:
        result = random.choice(["🌕 MẶT", "🌑 NGỬA"])
        count = random.randint(1, 5)
        flip_anim = "🪙" * count
        self._reply(snap, (
            f"🪙 TUNG ĐỒNG XU\n"
            f"{DIVIDER}\n"
            f"  {flip_anim} ...\n\n"
            f"  Kết quả: {result}!"
        ))

    def _cmd_random(self, snap: dict, arg: str) -> None:
        parts = arg.split()
        try:
            if len(parts) >= 2:
                lo, hi = int(parts[0]), int(parts[1])
            elif len(parts) == 1:
                lo, hi = 1, int(parts[0])
            else:
                lo, hi = 1, 100
            if lo > hi:
                lo, hi = hi, lo
            result = random.randint(lo, hi)
            total = hi - lo + 1
            pos = result - lo
            pct = int((pos / total) * 10) if total > 1 else 5
            bar = "█" * pct + "░" * (10 - pct)
            self._reply(snap, (
                f"🎲 SỐ NGẪU NHIÊN\n"
                f"{DIVIDER}\n"
                f"  Phạm vi: {lo} → {hi}\n"
                f"  Kết quả: {result}\n"
                f"  [{bar}]"
            ))
        except ValueError:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}random <min> <max>")

    def _cmd_roll(self, snap: dict, arg: str) -> None:
        if not arg:
            arg = "1d6"
        match = re.match(r"(\d+)d(\d+)", arg.lower().strip())
        if not match:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}roll <NdM>  (ví dụ: 2d6, 1d20)")
            return
        n, m = int(match.group(1)), int(match.group(2))
        n = min(n, 20)
        m = max(m, 2)
        rolls = [random.randint(1, m) for _ in range(n)]
        total = sum(rolls)
        roll_str = " + ".join(str(r) for r in rolls)
        self._reply(snap, (
            f"🎲 TUNG XÚC XẮC ({n}d{m})\n"
            f"{DIVIDER}\n"
            f"  Kết quả: {roll_str}\n"
            f"  Tổng   : {total}\n"
            f"  Min/Max: {min(rolls)} / {max(rolls)}"
        ))

    def _cmd_choose(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}choose <a>|<b>|<c>...")
            return
        choices = [c.strip() for c in arg.split("|") if c.strip()]
        if len(choices) < 2:
            self._reply(snap, "❌ Cần ít nhất 2 lựa chọn, ngăn cách bằng |")
            return
        picked = random.choice(choices)
        lines = [f"🤔 CÂU HỎI KHÓ QUÁ...\n{DIVIDER}"]
        for c in choices:
            lines.append(f"  {'👉' if c == picked else '  '} {c}")
        lines.append(f"\n✅ Tôi chọn: {picked}!")
        self._reply(snap, "\n".join(lines))

    def _cmd_8ball(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}8ball <câu hỏi>")
            return
        r = random.random()
        if r < 0.4:
            answer = random.choice(BALL8_YES)
        elif r < 0.7:
            answer = random.choice(BALL8_NO)
        else:
            answer = random.choice(BALL8_MAYBE)
        self._reply(snap, (
            f"🔮 BÓI BÁT QUÁI\n"
            f"{DIVIDER}\n"
            f"  Câu hỏi: {arg}\n\n"
            f"  {answer}"
        ))

    def _cmd_trivia(self, snap: dict, arg: str) -> None:
        thread_id = str(snap["replyToID"])
        q, a = random.choice(TRIVIA_POOL)
        _trivia_pending[thread_id] = {"answer": a, "question": q}
        self._reply(snap, (
            f"🧠 CÂU HỎI KIẾN THỨC\n"
            f"{DIVIDER}\n"
            f"  {q}\n\n"
            f"  💬 Trả lời trong nhóm này!\n"
            f"  ⏱️ (Gợi ý sẽ tự lộ sau khi trả lời)"
        ))
        # Tự xoá sau 60s nếu chưa trả lời
        def expire():
            time.sleep(60)
            if thread_id in _trivia_pending and _trivia_pending[thread_id]["question"] == q:
                del _trivia_pending[thread_id]
        threading.Thread(target=expire, daemon=True).start()

    def _cmd_rps(self, snap: dict, arg: str) -> None:
        moves = {"kéo": "✂️ Kéo", "búa": "🪨 Búa", "bao": "🪣 Bao",
                 "k": "✂️ Kéo", "b": "🪨 Búa", "ba": "🪣 Bao"}
        user_move = arg.strip().lower()
        if user_move not in moves:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}rps kéo/búa/bao")
            return
        bot_choice = random.choice(["kéo", "búa", "bao"])
        user_display = moves[user_move]
        bot_display = moves[bot_choice]

        # Chuẩn hoá
        um = user_move if user_move in ("kéo", "búa", "bao") else {"k": "kéo", "b": "búa", "ba": "bao"}[user_move]

        win_map = {"kéo": "bao", "búa": "kéo", "bao": "búa"}
        if um == bot_choice:
            result = "🤝 HÒA!"
        elif win_map[um] == bot_choice:
            result = "🎉 BẠN THẮNG!"
        else:
            result = "🤖 BOT THẮNG!"

        self._reply(snap, (
            f"✊ OẲN TÙ TÌ\n"
            f"{DIVIDER}\n"
            f"  Bạn  : {user_display}\n"
            f"  Bot  : {bot_display}\n"
            f"  {DIVIDER}\n"
            f"  {result}"
        ))

    # ══════════════════════════════════════════════════════
    # 🌤 TIỆN ÍCH
    # ══════════════════════════════════════════════════════

    def _cmd_thoitiet(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}thoitiet <tên thành phố>")
            return
        city = urllib.parse.quote(arg.strip())
        url = f"https://wttr.in/{city}?format=4&lang=vi"
        data = http_get(url, timeout=10)
        if data:
            self._reply(snap, f"🌤 THỜI TIẾT: {arg}\n{DIVIDER}\n{data.strip()}")
        else:
            # Fallback format
            url2 = f"https://wttr.in/{city}?format=%l:+%C+%t+%h+humidity&lang=vi"
            data2 = http_get(url2, timeout=10)
            if data2:
                self._reply(snap, f"🌤 Thời tiết tại {arg}:\n{data2.strip()}")
            else:
                self._reply(snap, f"❌ Không lấy được thời tiết cho '{arg}'. Thử lại sau!")

    def _cmd_dich(self, snap: dict, arg: str) -> None:
        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            self._reply(snap, (
                f"ℹ️ Cách dùng: {self.prefix}dich <ngôn ngữ> <văn bản>\n"
                f"Ví dụ: {self.prefix}dich en Xin chào\n"
                f"Mã ngôn ngữ: vi, en, ja, ko, zh, fr, de, es..."
            ))
            return
        target_lang = parts[0].strip().lower()
        text = parts[1].strip()
        encoded = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={encoded}"
        data = http_get(url, timeout=10)
        if data:
            try:
                result_json = json.loads(data)
                translated = "".join(part[0] for part in result_json[0] if part[0])
                src_lang = result_json[2] if len(result_json) > 2 else "auto"
                self._reply(snap, (
                    f"🌐 DỊCH VĂN BẢN\n"
                    f"{DIVIDER}\n"
                    f"  Từ  : {src_lang} → {target_lang}\n"
                    f"  Gốc : {text[:100]}\n"
                    f"  Dịch: {translated}"
                ))
            except Exception:
                self._reply(snap, "❌ Không dịch được. Thử lại sau!")
        else:
            self._reply(snap, "❌ Không kết nối được đến dịch vụ dịch thuật.")

    def _cmd_tinhtoan(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}tinhtoan <biểu thức>\nVí dụ: {self.prefix}tinhtoan 2+2*3")
            return
        safe_chars = set("0123456789+-*/().^ %")
        expr = arg.strip().replace("^", "**").replace(",", ".")
        if not all(c in safe_chars or c.isspace() for c in expr):
            self._reply(snap, "❌ Biểu thức không hợp lệ. Chỉ dùng số và + - * / ^ ( )")
            return
        try:
            result = eval(expr, {"__builtins__": {}, "math": math}, {})
            if isinstance(result, float):
                result = round(result, 10)
            self._reply(snap, (
                f"🧮 MÁY TÍNH\n"
                f"{DIVIDER}\n"
                f"  Biểu thức: {arg}\n"
                f"  Kết quả  : {result}"
            ))
        except ZeroDivisionError:
            self._reply(snap, "❌ Lỗi: Chia cho 0!")
        except Exception:
            self._reply(snap, "❌ Biểu thức không hợp lệ.")

    def _cmd_wiki(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}wiki <từ khoá>")
            return
        query = urllib.parse.quote(arg.strip())
        url = f"https://vi.wikipedia.org/api/rest_v1/page/summary/{query}"
        data = http_get(url, timeout=10)
        if data:
            try:
                info = json.loads(data)
                title = info.get("title", arg)
                extract = info.get("extract", "Không có mô tả.")
                extract = extract[:400] + ("..." if len(extract) > 400 else "")
                page_url = info.get("content_urls", {}).get("desktop", {}).get("page", "")
                self._reply(snap, (
                    f"📖 WIKIPEDIA: {title}\n"
                    f"{DIVIDER}\n"
                    f"{extract}\n"
                    f"{DIVIDER}\n"
                    f"🔗 {page_url}"
                ))
            except Exception:
                self._reply(snap, "❌ Không tìm thấy thông tin trên Wikipedia.")
        else:
            # Try English
            url_en = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
            data_en = http_get(url_en, timeout=10)
            if data_en:
                try:
                    info = json.loads(data_en)
                    extract = info.get("extract", "")[:400]
                    self._reply(snap, f"📖 Wikipedia (EN): {info.get('title')}\n{DIVIDER}\n{extract}")
                except Exception:
                    self._reply(snap, "❌ Không tìm thấy trên Wikipedia.")
            else:
                self._reply(snap, "❌ Không tìm thấy trên Wikipedia.")

    def _cmd_qr(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}qr <nội dung>\nVí dụ: {self.prefix}qr https://facebook.com")
            return
        # Dùng API online để tạo QR
        encoded = urllib.parse.quote(arg.strip())
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded}"
        sent = self._send_image_url(snap, qr_url, f"📷 Mã QR cho: {arg[:50]}")
        if not sent:
            self._reply(snap, (
                f"📷 MÃ QR\n"
                f"{DIVIDER}\n"
                f"  Nội dung: {arg[:80]}\n"
                f"  Link ảnh QR:\n"
                f"  {qr_url}"
            ))

    def _cmd_base64(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}base64 <văn bản>")
            return
        encoded = base64.b64encode(arg.encode("utf-8")).decode()
        self._reply(snap, (
            f"🔐 MÃ HOÁ BASE64\n"
            f"{DIVIDER}\n"
            f"  Gốc : {arg[:60]}\n"
            f"  B64 : {encoded}"
        ))

    def _cmd_decode64(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}decode64 <base64 string>")
            return
        try:
            decoded = base64.b64decode(arg.strip()).decode("utf-8")
            self._reply(snap, (
                f"🔓 GIẢI MÃ BASE64\n"
                f"{DIVIDER}\n"
                f"  B64 : {arg[:60]}\n"
                f"  Gốc : {decoded}"
            ))
        except Exception:
            self._reply(snap, "❌ Chuỗi Base64 không hợp lệ.")

    def _cmd_hash(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}hash <văn bản>")
            return
        text = arg.strip()
        md5 = hashlib.md5(text.encode()).hexdigest()
        sha256 = hashlib.sha256(text.encode()).hexdigest()
        sha1 = hashlib.sha1(text.encode()).hexdigest()
        self._reply(snap, (
            f"#️⃣ BĂM (HASH)\n"
            f"{DIVIDER}\n"
            f"  Văn bản: {text[:50]}\n\n"
            f"  MD5    : {md5}\n"
            f"  SHA1   : {sha1}\n"
            f"  SHA256 : {sha256}"
        ))

    # ══════════════════════════════════════════════════════
    # 🖼 ẢNH & VIDEO
    # ══════════════════════════════════════════════════════

    def _cmd_genanh(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}genanh <mô tả bằng tiếng Anh hoặc tiếng Việt>")
            return
        self._reply(snap, f"🎨 Đang tạo ảnh AI cho: '{arg}'\n⏳ Chờ một chút...")
        prompt_encoded = urllib.parse.quote(arg.strip())
        seed = random.randint(1, 9999999)
        img_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=768&height=768&seed={seed}&nologo=true"
        sent = self._send_image_url(snap, img_url, f"🖼 AI: {arg[:50]}")
        if not sent:
            self._reply(snap, (
                f"🎨 ẢNH AI ĐÃ TẠO XONG!\n"
                f"{DIVIDER}\n"
                f"  Mô tả: {arg[:80]}\n"
                f"  🔗 Link ảnh:\n"
                f"  {img_url}"
            ))

    def _cmd_anh(self, snap: dict, arg: str) -> None:
        keywords = arg.strip() if arg else "nature beautiful"
        encoded = urllib.parse.quote(keywords)
        seed = random.randint(1, 9999999)
        img_url = f"https://source.unsplash.com/featured/800x600/?{encoded}"
        # Fallback to Pollinations
        poll_url = f"https://image.pollinations.ai/prompt/{encoded}+photo+realistic?width=800&height=600&seed={seed}&nologo=true"
        sent = self._send_image_url(snap, poll_url, f"📸 {keywords}")
        if not sent:
            self._reply(snap, (
                f"📸 ẢNH: {keywords}\n"
                f"{DIVIDER}\n"
                f"  🔗 {poll_url}"
            ))

    def _cmd_meme(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}meme <dòng 1>|<dòng 2>")
            return
        parts = arg.split("|", 1)
        top = urllib.parse.quote(parts[0].strip())
        bottom = urllib.parse.quote(parts[1].strip() if len(parts) > 1 else "")
        meme_url = f"https://apimeme.com/meme?meme=Drake-Hotline-Bling&top={top}&bottom={bottom}"
        alt_url = f"https://api.memegen.link/images/drake/{top}/{bottom}.png"
        sent = self._send_image_url(snap, alt_url, f"😂 Meme: {arg[:40]}")
        if not sent:
            self._reply(snap, (
                f"😂 MEME\n"
                f"{DIVIDER}\n"
                f"  🔗 Link meme:\n"
                f"  {alt_url}"
            ))

    def _cmd_avatar(self, snap: dict, arg: str) -> None:
        if not arg:
            uid = str(snap.get("userID", ""))
        else:
            uid = arg.strip().split()[0]
        if not uid:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}avatar <userID>")
            return
        avatar_url = f"https://graph.facebook.com/{uid}/picture?width=512&height=512&type=large"
        sent = self._send_image_url(snap, avatar_url, f"👤 Avatar UID: {uid}")
        if not sent:
            self._reply(snap, (
                f"👤 AVATAR\n"
                f"{DIVIDER}\n"
                f"  UID: {uid}\n"
                f"  🔗 Link ảnh:\n"
                f"  {avatar_url}"
            ))

    # ══════════════════════════════════════════════════════
    # 🎵 ÂM NHẠC & VIDEO
    # ══════════════════════════════════════════════════════

    def _cmd_nhac(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}nhac <tên bài hát>")
            return
        self._youtube_search(snap, arg + " official audio", kind="nhạc")

    def _cmd_youtube(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}youtube <từ khoá>")
            return
        self._youtube_search(snap, arg, kind="video")

    def _youtube_search(self, snap: dict, query: str, kind: str = "video") -> None:
        encoded = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        html = http_get(url, timeout=12)
        if not html:
            self._reply(snap, "❌ Không tìm kiếm được trên YouTube. Thử lại sau!")
            return
        # Trích video IDs từ HTML
        ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        titles = re.findall(r'"title":\{"runs":\[{"text":"([^"]+)"', html)
        channels = re.findall(r'"shortBylineText":\{"runs":\[{"text":"([^"]+)"', html)
        durations = re.findall(r'"lengthText":\{"accessibility":\{"accessibilityData":\{"label":"[^"]+"\},"simpleText":"([^"]+)"', html)

        if not ids:
            self._reply(snap, f"❌ Không tìm thấy {kind} nào cho: {query}")
            return

        icon = "🎵" if kind == "nhạc" else "▶️"
        lines = [f"{icon} KẾT QUẢ {kind.upper()}: '{query}'\n{DIVIDER}"]
        shown = 0
        for i, vid_id in enumerate(ids[:10]):
            if shown >= 5:
                break
            title = titles[i] if i < len(titles) else "Không rõ"
            channel = channels[i] if i < len(channels) else ""
            duration = durations[i] if i < len(durations) else ""
            link = f"https://youtu.be/{vid_id}"
            lines.append(
                f"\n  {shown+1}. {title}\n"
                f"     👤 {channel}  ⏱️ {duration}\n"
                f"     🔗 {link}"
            )
            shown += 1

        self._reply(snap, "\n".join(lines))

    def _cmd_videoinfo(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}videoinfo <link YouTube>")
            return
        link = arg.strip()
        vid_match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", link)
        if not vid_match:
            self._reply(snap, "❌ Link YouTube không hợp lệ.")
            return
        vid_id = vid_match.group(1)
        oembed_url = f"https://www.youtube.com/oembed?url=https://youtu.be/{vid_id}&format=json"
        data = http_get(oembed_url, timeout=10)
        if data:
            try:
                info = json.loads(data)
                self._reply(snap, (
                    f"▶️ THÔNG TIN VIDEO\n"
                    f"{DIVIDER}\n"
                    f"  Tiêu đề : {info.get('title', 'N/A')}\n"
                    f"  Kênh    : {info.get('author_name', 'N/A')}\n"
                    f"  Link    : https://youtu.be/{vid_id}\n"
                    f"  Thumbnail: {info.get('thumbnail_url', 'N/A')}"
                ))
            except Exception:
                self._reply(snap, f"❌ Không lấy được thông tin video.")
        else:
            self._reply(snap, f"❌ Không lấy được thông tin video: {link}")

    def _cmd_lyric(self, snap: dict, arg: str) -> None:
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}lyric <tên bài hát>")
            return
        encoded = urllib.parse.quote(arg.strip())
        url = f"https://api.lyrics.ovh/suggest/{encoded}"
        data = http_get(url, timeout=10)
        if data:
            try:
                info = json.loads(data)
                results = info.get("data", [])
                if not results:
                    raise ValueError("empty")
                song = results[0]
                artist = song.get("artist", {}).get("name", "?")
                title = song.get("title", "?")
                # Lấy lời từ lyrics.ovh
                lyric_url = f"https://api.lyrics.ovh/v1/{urllib.parse.quote(artist)}/{urllib.parse.quote(title)}"
                lyric_data = http_get(lyric_url, timeout=10)
                if lyric_data:
                    lyr = json.loads(lyric_data)
                    lyrics = lyr.get("lyrics", "")[:600]
                    self._reply(snap, (
                        f"🎵 LỜI BÀI HÁT\n"
                        f"{DIVIDER}\n"
                        f"  Bài  : {title}\n"
                        f"  Ca sĩ: {artist}\n"
                        f"{DIVIDER}\n"
                        f"{lyrics}{'...' if len(lyr.get('lyrics',''))>600 else ''}"
                    ))
                else:
                    self._reply(snap, f"✅ Tìm thấy bài: {title} — {artist}\n❌ Không lấy được lời bài hát.")
            except Exception:
                self._reply(snap, f"❌ Không tìm thấy lời bài hát '{arg}'. Thử lại với tên chính xác hơn!")
        else:
            self._reply(snap, "❌ Không kết nối được đến dịch vụ lời nhạc.")

    # ══════════════════════════════════════════════════════
    # 📊 THỐNG KÊ
    # ══════════════════════════════════════════════════════

    def _cmd_stats(self, snap: dict, arg: str) -> None:
        uptime = format_uptime(time.time() - BOT_START_TIME)
        warn_total = sum(len(v) for v in self._warn_list.values())
        thread_id = str(snap.get("replyToID", ""))
        sender_id = str(snap.get("userID", ""))

        # Thông tin key của người dùng
        kd = self._key_data
        uk = kd.get("user_keys", {}).get(sender_id, {})
        has_key = bool(uk) and time.time() < uk.get("expires", 0)
        if has_key:
            key_code = uk.get("key", "?")
            expires_ts = uk.get("expires", 0)
            days_left = max(0, int((expires_ts - time.time()) / 86400))
            groups_used = len(uk.get("groups", []))
            max_groups = uk.get("max_groups", 1)
            exp_str = datetime.fromtimestamp(expires_ts).strftime("%d/%m/%Y")
            key_block = (
                f"  🔑 Key     : {key_code}\n"
                f"  📅 Hết hạn: {exp_str}  ({days_left} ngày còn lại)\n"
                f"  👥 Nhóm   : {groups_used}/{max_groups} nhóm đã dùng"
            )
        else:
            key_block = f"  🔐 Key     : Chưa kích hoạt\n  Gõ {self.prefix}nhapkey <KEY> để kích hoạt"

        # Admin nhóm
        is_owner = self._is_key_owner(thread_id, sender_id)
        is_gadmin = self._is_group_admin(thread_id, sender_id)
        if is_owner:
            role = "👑 Chủ nhóm"
        elif is_gadmin:
            role = "🛡️ Admin nhóm"
        elif sender_id in self.admins:
            role = "⭐ Super-Admin"
        elif has_key:
            role = "✅ Thành viên có key"
        else:
            role = "❌ Chưa có key"

        ga_count = len(kd.get("group_admins", {}).get(thread_id, []))

        self._reply(snap, (
            f"📊 THỐNG KÊ BOT\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  🏷️  Vai trò   : {role}\n"
            f"{key_block}\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  ⏱️  Uptime    : {uptime}\n"
            f"  📩 Tin nhận  : {self._msg_count}\n"
            f"  ⚠️  Cảnh cáo  : {warn_total} người\n"
            f"  🔨 Bị ban    : {len(self._ban_set)} người\n"
            f"  🛡️  Admin nhóm: {ga_count} người\n"
            f"  🤖 Prefix    : '{self.prefix}'\n"
            f"  🔄 Auto reply: {'BẬT' if self.cfg.get('autoreply') else 'TẮT'}"
        ))

    def _cmd_topwarn(self, snap: dict, arg: str) -> None:
        if not self._warn_list:
            self._reply(snap, "✅ Chưa có ai bị cảnh cáo!")
            return
        sorted_warns = sorted(self._warn_list.items(), key=lambda x: -len(x[1]))[:10]
        lines = [f"🏆 TOP CẢNH CÁO\n{DIVIDER}"]
        medals = ["🥇", "🥈", "🥉"] + ["4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, (uid, warns) in enumerate(sorted_warns):
            bar = "🟡" * min(len(warns), 5)
            name = self._get_display_name(uid)
            lines.append(f"  {medals[i]} {name}: {len(warns)} lần {bar}")
        self._reply(snap, "\n".join(lines))

    def _cmd_topchat(self, snap: dict, arg: str) -> None:
        """Hiển thị top người nhắn tin nhiều nhất trong nhóm."""
        thread_id = str(snap.get("replyToID", ""))
        grp = self._activity_tracker.get(thread_id, {})
        if not grp:
            self._reply(snap, "📊 Chưa có dữ liệu hoạt động trong nhóm này!\n  Bot cần lắng nghe ít nhất 1 tin nhắn.")
            return
        try:
            limit = max(1, min(int(arg.strip()), 20)) if arg.strip().isdigit() else 10
        except Exception:
            limit = 10
        sorted_users = sorted(grp.items(), key=lambda x: -x[1])[:limit]
        medals = ["🥇", "🥈", "🥉"] + [f"{i}️⃣" for i in range(4, 11)]
        total_msgs = sum(grp.values())
        lines = [
            f"💬 TOP {limit} NGƯỜI HOẠT ĐỘNG NHẤT",
            f"{'═' * 30}",
            f"  📊 Tổng tin nhắn trong phiên: {total_msgs}",
            f"{'─' * 30}",
        ]
        for i, (uid, count) in enumerate(sorted_users):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            pct = count * 100 // total_msgs if total_msgs else 0
            bar = "🟦" * min(count * 10 // max(sorted_users[0][1], 1), 8)
            name = self._get_display_name(uid)
            lines.append(f"  {medal} {name}")
            lines.append(f"      💬 {count} tin  ({pct}%)  {bar}")
        lines.append(f"{'═' * 30}")
        lines.append(f"  💡 Gõ /hoatdong <uid> để xem chi tiết")
        self._reply(snap, "\n".join(lines))

    def _cmd_hoatdong(self, snap: dict, arg: str) -> None:
        """Xem thống kê hoạt động của 1 người dùng trong nhóm."""
        thread_id = str(snap.get("replyToID", ""))
        sender_id = str(snap.get("userID", ""))
        target_uid = arg.strip() if arg.strip().isdigit() else sender_id
        grp = self._activity_tracker.get(thread_id, {})
        count = grp.get(target_uid, 0)
        total = sum(grp.values()) or 1
        pct = count * 100 // total
        # Xếp hạng
        sorted_users = sorted(grp.items(), key=lambda x: -x[1])
        rank = next((i + 1 for i, (u, _) in enumerate(sorted_users) if u == target_uid), None)
        # Thời điểm bắt đầu
        first_ts = self._activity_first.get(thread_id, {}).get(target_uid)
        if first_ts:
            since_str = datetime.fromtimestamp(first_ts).strftime("%d/%m/%Y %H:%M")
        else:
            since_str = "Không rõ"
        bar_len = count * 10 // max(sorted_users[0][1], 1) if sorted_users else 0
        bar = "🟦" * min(bar_len, 10) + "⬜" * (10 - min(bar_len, 10))
        is_self = target_uid == sender_id
        label = "bạn" if is_self else self._get_display_name(target_uid)
        self._reply(snap, (
            f"📊 HOẠT ĐỘNG — {label}\n"
            f"{'═' * 30}\n"
            f"  💬 Số tin nhắn : {count}\n"
            f"  📈 Tỉ lệ      : {pct}% tổng nhóm\n"
            f"  🏆 Xếp hạng   : #{rank or '?'} / {len(grp)} người\n"
            f"  📅 Ghi nhận từ: {since_str}\n"
            f"  {bar}\n"
            f"{'═' * 30}\n"
            f"  💡 /topchat — xem BXH cả nhóm"
        ))

    # ══════════════════════════════════════════════════════
    # 👥 THÊM / XÓA THÀNH VIÊN
    # ══════════════════════════════════════════════════════

    def _do_add_member(self, thread_id: str, uid: str) -> dict:
        """Thêm thành viên vào nhóm qua Facebook API."""
        try:
            from _core._utils import formAll, mainRequests
            import requests as _req
            dataForm = formAll(self.dataFB, requireGraphql=False)
            dataForm["uid"] = str(uid)
            dataForm["tid"] = str(thread_id)
            resp = _req.post(
                **mainRequests(
                    f"https://www.facebook.com/chat/add_participants/?dpr=1",
                    {**dataForm, "to_add": str(uid), "thread_fbid": str(thread_id)},
                    self.dataFB["cookieFacebook"],
                )
            )
            raw = resp.text.split("for (;;);")[-1] if "for (;;);" in resp.text else resp.text
            return json.loads(raw)
        except Exception as e:
            return {"error": str(e)}

    def _do_kick_member(self, thread_id: str, uid: str, reason: str = "") -> bool:
        """Xóa/kick thành viên khỏi nhóm qua Facebook API."""
        try:
            from _core._utils import formAll, mainRequests
            import requests as _req
            dataForm = formAll(self.dataFB, requireGraphql=False)
            dataForm["uid"] = str(uid)
            dataForm["tid"] = str(thread_id)
            resp = _req.post(
                **mainRequests(
                    "https://www.facebook.com/chat/remove_participants/?dpr=1",
                    {**dataForm, "uid": str(uid), "thread_fbid": str(thread_id)},
                    self.dataFB["cookieFacebook"],
                )
            )
            raw = resp.text.split("for (;;);")[-1] if "for (;;);" in resp.text else resp.text
            result = json.loads(raw)
            ok = not result.get("error")
            if ok:
                log("bot", f"✅ Đã kick {uid} khỏi nhóm {thread_id} — Lý do: {reason}")
            return ok
        except Exception as e:
            log("err", f"Kick {uid} lỗi: {e}")
            return False

    def _cmd_themtv(self, snap: dict, arg: str) -> None:
        """Thêm thành viên vào nhóm: /themtv <uid>"""
        if not arg:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}themtv <userID>")
            return
        thread_id = str(snap["replyToID"])
        uid = arg.strip().split()[0]
        result = self._do_add_member(thread_id, uid)
        if result.get("error"):
            self._reply(snap, f"❌ Không thể thêm UID {uid}:\n  {result.get('error')}")
        else:
            self._reply(snap, (
                f"✅ ĐÃ THÊM THÀNH VIÊN\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  UID : {uid}\n"
                f"  Nhóm: {thread_id}\n"
                f"  Người thêm: {snap.get('userID')}"
            ))

    def _cmd_xoatv(self, snap: dict, arg: str) -> None:
        """Xóa/kick thành viên khỏi nhóm: /xoatv <uid> [lý do]"""
        parts = arg.split(maxsplit=1)
        if not parts:
            self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}xoatv <userID> [lý do]")
            return
        thread_id = str(snap["replyToID"])
        uid = parts[0]
        reason = parts[1] if len(parts) > 1 else "Vi phạm nội quy"
        ok = self._do_kick_member(thread_id, uid, reason)
        if ok:
            self._reply(snap, (
                f"🚫 ĐÃ XÓA THÀNH VIÊN\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  UID   : {uid}\n"
                f"  Lý do : {reason}\n"
                f"  Người xóa: {snap.get('userID')}"
            ))
        else:
            self._reply(snap, f"❌ Không thể xóa UID {uid}.\n  (Bot cần quyền Admin nhóm)")

    # ══════════════════════════════════════════════════════
    # 🛡 ANTI-LINK / ANTI-SPAM
    # ══════════════════════════════════════════════════════

    def _cmd_antilink(self, snap: dict, arg: str) -> None:
        """Bật/tắt anti-link: /antilink on|off"""
        thread_id = str(snap["replyToID"])
        mode = arg.strip().lower()
        if mode not in ("on", "off", "bật", "tắt"):
            status = "BẬT" if self._antilink_enabled.get(thread_id, False) else "TẮT"
            self._reply(snap, (
                f"🔗 ANTI-LINK — Hiện: {status}\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Bật : {self.prefix}antilink on\n"
                f"  Tắt : {self.prefix}antilink off\n"
                f"  Khi BẬT: thành viên đăng link sẽ bị cảnh cáo.\n"
                f"  Vi phạm 3 lần → tự động kick."
            ))
            return
        enable = mode in ("on", "bật")
        self._antilink_enabled[thread_id] = enable
        status = "BẬT" if enable else "TẮT"
        self._reply(snap, (
            f"🔗 ANTI-LINK ĐÃ {status}!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Thành viên {'KHÔNG được' if enable else 'được'} đăng link.\n"
            f"  {'3 lần vi phạm → tự động kick.' if enable else 'Anti-link đã tắt.'}"
        ))

    def _cmd_antispam(self, snap: dict, arg: str) -> None:
        """Bật/tắt anti-spam: /antispam on|off"""
        thread_id = str(snap["replyToID"])
        mode = arg.strip().lower()
        if mode not in ("on", "off", "bật", "tắt"):
            status = "BẬT" if self._antispam_enabled.get(thread_id, False) else "TẮT"
            self._reply(snap, (
                f"🚫 ANTI-SPAM — Hiện: {status}\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Bật : {self.prefix}antispam on\n"
                f"  Tắt : {self.prefix}antispam off\n"
                f"  Khi BẬT: gửi ≥5 tin/5s = spam.\n"
                f"  Vi phạm 3 lần → tự động kick."
            ))
            return
        enable = mode in ("on", "bật")
        self._antispam_enabled[thread_id] = enable
        status = "BẬT" if enable else "TẮT"
        self._reply(snap, (
            f"🚫 ANTI-SPAM ĐÃ {status}!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  {'Phát hiện spam ≥5 tin/5 giây.' if enable else 'Anti-spam đã tắt.'}\n"
            f"  {'3 lần vi phạm → tự động kick.' if enable else ''}"
        ))

    # ══════════════════════════════════════════════════════
    # 🎮 FREE FIRE API  (local: github.com/0xMe/FreeFire-Api)
    # ══════════════════════════════════════════════════════

    _FF_API_PORT = 3001
    _FF_SERVERS  = {"IND", "SG", "RU", "ID", "TW", "US", "VN", "TH", "ME", "PK", "CIS", "BR", "BD"}
    # Map common aliases to canonical server codes
    _FF_SERVER_MAP = {
        "IN": "IND", "INDIA": "IND",
        "SINGAPORE": "SG",
        "RUSSIA": "RU",
        "INDONESIA": "ID",
        "TAIWAN": "TW",
        "VIETNAM": "VN",
        "THAILAND": "TH",
        "MIDDLE EAST": "ME",
        "PAKISTAN": "PK",
        "BRAZIL": "BR",
        "BANGLADESH": "BD",
    }

    def _ff_server(self, raw: str) -> str:
        """Chuẩn hóa server code Free Fire."""
        s = raw.strip().upper()
        return self._FF_SERVER_MAP.get(s, s) if s not in self._FF_SERVERS else s

    def _ff_get(self, endpoint: str, params: dict) -> dict | None:
        """Gọi Free Fire API local Flask, trả về JSON hoặc None nếu lỗi."""
        qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
        url = f"http://localhost:{self._FF_API_PORT}{endpoint}?{qs}"
        try:
            data = http_get(url, timeout=15)
            if not data:
                return None
            return json.loads(data)
        except Exception as e:
            log("err", f"FF API lỗi ({endpoint}): {e}")
            return None

    def _ff_unavailable(self, snap: dict) -> None:
        self._reply(snap, (
            "⚠️ FREE FIRE API CHƯA KHỞI ĐỘNG!\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            "  Admin cần khởi động workflow:\n"
            "  'Free Fire API Server'\n"
            "  rồi thử lại lệnh."
        ))

    def _cmd_ff(self, snap: dict, arg: str) -> None:
        """Xem thông tin người chơi Free Fire: /ff <uid> [region]"""
        parts = arg.strip().split()
        if not parts:
            self._reply(snap, (
                f"ℹ️ Cách dùng: {self.prefix}ff <uid> [region]\n"
                f"  Ví dụ: {self.prefix}ff 2392597564 vn\n"
                f"  Region: vn ind sg id th br bd ru tw us me pk"
            ))
            return
        uid    = parts[0]
        region = normalize_region(parts[1]) if len(parts) > 1 else "vn"
        self._reply(snap, f"🎮 Đang tra cứu UID {uid}...")
        data = check_ff(uid, region)
        if data is None:
            self._reply(snap, f"❌ Không tìm thấy UID {uid} (region: {region})\nKiểm tra lại UID hoặc thử region khác.")
            return
        self._reply(snap, format_profile(uid, data))


    # ══════════════════════════════════════════════════════
    # 🛡 QUẢN LÝ NHÓM NÂNG CAO
    # ══════════════════════════════════════════════════════

    def _cmd_sendrules(self, snap: dict, arg: str) -> None:
        """Bật/tắt tự động gửi nội quy khi thành viên mới xuất hiện: /sendrules on|off"""
        thread_id = str(snap["replyToID"])
        mode = arg.strip().lower()
        if mode not in ("on", "off", "bật", "tắt"):
            status = "BẬT" if self._sendrules_enabled.get(thread_id, False) else "TẮT"
            rules_set = "✅ Đã có nội quy" if self.cfg.get("rules", "").strip() else "❌ Chưa có (dùng /setrules)"
            self._reply(snap, (
                f"📜 TỰ ĐỘNG GỬI NỘI QUY — Hiện: {status}\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Nội quy: {rules_set}\n"
                f"  Bật : {self.prefix}sendrules on\n"
                f"  Tắt : {self.prefix}sendrules off\n"
                f"  Khi BẬT: thành viên mới xuất hiện\n"
                f"  sẽ tự nhận nội quy nhóm."
            ))
            return
        enable = mode in ("on", "bật")
        self._sendrules_enabled[thread_id] = enable
        status = "BẬT" if enable else "TẮT"
        rules_ok = bool(self.cfg.get("rules", "").strip())
        extra = "" if rules_ok else f"\n  ⚠️ Chưa có nội quy! Dùng {self.prefix}setrules <nội dung>"
        self._reply(snap, (
            f"📜 TỰ ĐỘNG GỬI NỘI QUY ĐÃ {status}!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  {'Thành viên mới sẽ nhận nội quy tự động.' if enable else 'Đã tắt gửi nội quy tự động.'}"
            f"{extra}"
        ))

    def _cmd_slowmode(self, snap: dict, arg: str) -> None:
        """Bật/tắt slowmode: /slowmode <giây> hoặc /slowmode off"""
        thread_id = str(snap["replyToID"])
        mode = arg.strip().lower()
        if not mode:
            secs = self._slowmode_secs.get(thread_id, 0)
            status = f"BẬT — {secs}s" if secs > 0 else "TẮT"
            self._reply(snap, (
                f"⏱️ SLOWMODE — Hiện: {status}\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Bật : {self.prefix}slowmode <số giây>\n"
                f"  Tắt : {self.prefix}slowmode off\n"
                f"  Ví dụ: {self.prefix}slowmode 10\n"
                f"  Khi BẬT: mỗi thành viên phải chờ\n"
                f"  N giây giữa các tin nhắn."
            ))
            return
        if mode in ("off", "tắt", "0"):
            self._slowmode_secs[thread_id] = 0
            self._slowmode_last.pop(thread_id, None)
            self._reply(snap, (
                f"⏱️ SLOWMODE ĐÃ TẮT!\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Thành viên có thể nhắn tự do."
            ))
            return
        try:
            secs = int(mode)
            if secs < 1 or secs > 3600:
                raise ValueError
        except ValueError:
            self._reply(snap, "❌ Số giây không hợp lệ! (1 – 3600)")
            return
        self._slowmode_secs[thread_id] = secs
        self._reply(snap, (
            f"⏱️ SLOWMODE ĐÃ BẬT!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Mỗi thành viên phải chờ {secs}s\n"
            f"  giữa các tin nhắn.\n"
            f"  Tắt: {self.prefix}slowmode off"
        ))

    def _cmd_badword(self, snap: dict, arg: str) -> None:
        """Quản lý từ cấm: /badword add <từ> | del <từ> | list | clear"""
        thread_id = str(snap["replyToID"])
        parts = arg.strip().split(maxsplit=1)
        action = parts[0].lower() if parts else ""
        word = parts[1].strip().lower() if len(parts) > 1 else ""

        bw = self._badwords.setdefault(thread_id, set())

        if action in ("add", "thêm"):
            if not word:
                self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}badword add <từ>")
                return
            bw.add(word)
            self._reply(snap, (
                f"🚫 TỪ CẤM ĐÃ THÊM\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Từ: '{word}'\n"
                f"  Tổng: {len(bw)} từ cấm trong nhóm này."
            ))
        elif action in ("del", "xóa", "remove"):
            if not word:
                self._reply(snap, f"ℹ️ Cách dùng: {self.prefix}badword del <từ>")
                return
            if word in bw:
                bw.discard(word)
                self._reply(snap, f"✅ Đã xóa từ cấm: '{word}'")
            else:
                self._reply(snap, f"ℹ️ '{word}' không có trong danh sách từ cấm.")
        elif action in ("list", "ds", "danh sách"):
            if not bw:
                self._reply(snap, "✅ Chưa có từ cấm nào được thêm.")
                return
            words_list = ", ".join(sorted(bw))
            self._reply(snap, (
                f"🚫 DANH SÁCH TỪ CẤM ({len(bw)} từ)\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  {words_list}"
            ))
        elif action in ("clear", "xóahết"):
            count = len(bw)
            bw.clear()
            self._reply(snap, f"✅ Đã xóa toàn bộ {count} từ cấm.")
        else:
            status = f"BẬT ({len(bw)} từ)" if bw else "TẮT (chưa có từ cấm)"
            self._reply(snap, (
                f"🚫 LỌC TỪ NGỮ XẤU — {status}\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  {self.prefix}badword add <từ>   — Thêm từ cấm\n"
                f"  {self.prefix}badword del <từ>   — Xóa từ cấm\n"
                f"  {self.prefix}badword list        — Xem danh sách\n"
                f"  {self.prefix}badword clear       — Xóa tất cả\n"
                f"  Khi có từ cấm: tự cảnh cáo người vi phạm."
            ))

    def _cmd_autokick(self, snap: dict, arg: str) -> None:
        """Bật/tắt tự kick người không có key: /autokick on|off"""
        thread_id = str(snap["replyToID"])
        mode = arg.strip().lower()
        if mode not in ("on", "off", "bật", "tắt"):
            status = "BẬT" if self._autokick_enabled.get(thread_id, False) else "TẮT"
            self._reply(snap, (
                f"🥾 TỰ ĐỘNG KICK — Hiện: {status}\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Bật : {self.prefix}autokick on\n"
                f"  Tắt : {self.prefix}autokick off\n"
                f"  Khi BẬT: thành viên không có key\n"
                f"  sẽ bị kick tự động khi gửi tin đầu tiên.\n"
                f"  ⚠️ Cần bot có quyền Admin trong nhóm FB!"
            ))
            return
        enable = mode in ("on", "bật")
        self._autokick_enabled[thread_id] = enable
        status = "BẬT" if enable else "TẮT"
        self._reply(snap, (
            f"🥾 TỰ ĐỘNG KICK ĐÃ {status}!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  {'Thành viên không có key sẽ bị kick tự động.' if enable else 'Đã tắt auto-kick.'}\n"
            f"  {'⚠️ Cần bot có quyền Admin trong nhóm!' if enable else ''}"
        ))

    def _cmd_schedule(self, snap: dict, arg: str) -> None:
        """Hẹn giờ gửi thông báo: /schedule <phút> <nội dung>"""
        thread_id = str(snap["replyToID"])
        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            # Xem danh sách lịch đang chờ
            pending = [s for s in self._pending_schedules if s["thread_id"] == thread_id]
            if not pending:
                self._reply(snap, (
                    f"⏰ HẸN GIỜ GỬI TIN\n"
                    f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"  Cách dùng: {self.prefix}schedule <phút> <nội dung>\n"
                    f"  Ví dụ: {self.prefix}schedule 30 Nhắc nhở: họp nhóm lúc 8h!\n"
                    f"  Giới hạn: 1–1440 phút (tối đa 24h).\n"
                    f"  Hiện chưa có lịch hẹn nào."
                ))
            else:
                lines = [f"⏰ LỊCH HẸN GỬI TIN ({len(pending)} lịch)\n{DIVIDER}"]
                for i, s in enumerate(pending, 1):
                    remaining = int((s["send_at"] - time.time()) / 60)
                    lines.append(f"  {i}. Còn ~{remaining}ph: {s['msg'][:40]}")
                self._reply(snap, "\n".join(lines))
            return
        try:
            minutes = int(parts[0])
            if minutes < 1 or minutes > 1440:
                raise ValueError
        except ValueError:
            self._reply(snap, "❌ Số phút không hợp lệ! (1 – 1440)")
            return
        msg = parts[1].strip()
        send_at = time.time() + minutes * 60
        self._pending_schedules.append({
            "thread_id": thread_id,
            "msg": msg,
            "send_at": send_at,
        })
        from datetime import datetime as _dt
        send_time = _dt.fromtimestamp(send_at).strftime("%H:%M %d/%m")
        self._reply(snap, (
            f"⏰ ĐÃ ĐẶT HẸN GỬI TIN!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Sau  : {minutes} phút ({send_time})\n"
            f"  Nội dung: {msg[:60]}\n"
            f"  Nhóm: {thread_id}"
        ))

    def _schedule_loop(self) -> None:
        """Thread nền: kiểm tra và gửi tin nhắn đã hẹn giờ."""
        while True:
            try:
                now = time.time()
                fired = [s for s in self._pending_schedules if s["send_at"] <= now]
                for s in fired:
                    try:
                        self.sender.send(self.dataFB, (
                            f"⏰ THÔNG BÁO HẸN GIỜ\n"
                            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                            f"{s['msg']}\n"
                            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                            f"  🕐 {datetime.now():%d/%m/%Y %H:%M}"
                        ), s["thread_id"])
                        log("bot", f"⏰ Đã gửi tin hẹn giờ vào nhóm {s['thread_id']}")
                    except Exception as _se:
                        log("err", f"Gửi tin hẹn giờ lỗi: {_se}")
                    self._pending_schedules.remove(s)
            except Exception as _le:
                log("err", f"Schedule loop lỗi: {_le}")
            time.sleep(10)

    def _cmd_welcome(self, snap: dict, arg: str) -> None:
        """Xem trước tin chào mừng hiện tại: /welcome"""
        thread_id = str(snap["replyToID"])
        kd = self._key_data
        owner = kd.get("group_owners", {}).get(thread_id)
        custom_greeting = ""
        if owner:
            uk = kd.get("user_keys", {}).get(owner, {})
            custom_greeting = uk.get("greeting", "").strip()

        p = self.prefix
        bot_name = self._get_bot_name(thread_id)
        sendrules_on = self._sendrules_enabled.get(thread_id, False)
        autokick_on = self._autokick_enabled.get(thread_id, False)
        slowmode_secs = self._slowmode_secs.get(thread_id, 0)
        badword_count = len(self._badwords.get(thread_id, set()))

        if custom_greeting:
            preview = (custom_greeting
                       .replace("{uid}", "123456789")
                       .replace("{bot_name}", bot_name)
                       .replace("{prefix}", p))
        else:
            preview = (
                f"👋 CHÀO MỪNG THÀNH VIÊN MỚI!\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Chào UID 123456789!\n"
                f"  Bạn đã tham gia nhóm này.\n"
                f"  Gõ {p}menu để xem các lệnh của bot {bot_name}.\n"
                f"  Chúc bạn vui vẻ! 🎉\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )

        self._reply(snap, (
            f"👁️ XEM TRƯỚC TIN CHÀO MỪNG\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"{preview}\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  📐 Cấu hình nhóm:\n"
            f"  📜 Gửi nội quy: {'BẬT' if sendrules_on else 'TẮT'}\n"
            f"  🥾 Auto-kick  : {'BẬT' if autokick_on else 'TẮT'}\n"
            f"  ⏱️ Slowmode   : {f'{slowmode_secs}s' if slowmode_secs else 'TẮT'}\n"
            f"  🚫 Từ cấm    : {badword_count} từ\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Đổi tin chào: {p}setgreeting <nội dung>\n"
            f"  Biến hỗ trợ: {{uid}} {{bot_name}} {{prefix}}"
        ))

    # ══════════════════════════════════════════════════════
    # 👋 CHÀO THÀNH VIÊN MỚI (helper gọi từ event log:subscribe)
    # ══════════════════════════════════════════════════════

    def _greet_new_member(self, thread_id: str, new_uid: str) -> None:
        """Gửi tin chào thành viên mới khi họ vào nhóm."""
        greet_key = f"{new_uid}:{thread_id}"
        if greet_key in self._greeted_members:
            return
        self._greeted_members.add(greet_key)

        kd = self._key_data
        owner = kd.get("group_owners", {}).get(thread_id)
        custom_greeting = ""
        if owner:
            uk = kd.get("user_keys", {}).get(owner, {})
            custom_greeting = uk.get("greeting", "").strip()

        p = self.prefix
        bot_name = self._get_bot_name(thread_id)

        if custom_greeting:
            msg = (custom_greeting
                   .replace("{uid}", new_uid)
                   .replace("{bot_name}", bot_name)
                   .replace("{prefix}", p))
        else:
            msg = (
                f"👋 CHÀO MỪNG THÀNH VIÊN MỚI!\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Chào UID {new_uid}!\n"
                f"  Bạn đã tham gia nhóm này.\n"
                f"  Gõ {p}menu để xem các lệnh của bot {bot_name}.\n"
                f"  Chúc bạn vui vẻ! 🎉\n"
                f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
            )
        try:
            self.sender.send(self.dataFB, msg, thread_id)
            log("bot", f"👋 Đã chào thành viên mới {new_uid} trong nhóm {thread_id}")
        except Exception as e:
            log("err", f"Chào thành viên mới lỗi: {e}")


# ─── PRIVATE MESSAGE BOT (E2EE) ──────────────────────────────────

class PrivateMsgBot:
    """Xử lý tin nhắn riêng 1-1 qua E2EE bridge.
    Chạy trong thread riêng song song với GroupBot.
    """

    BINARY_PATH = str(Path(__file__).resolve().parents[1] / "build" / "fbchat-bridge-e2ee")

    def __init__(self, dataFB: dict, prefix: str = "/", admins: list | None = None,
                 cfg: dict | None = None) -> None:
        self.dataFB   = dataFB
        self.prefix   = prefix
        self.admins   = set(map(str, admins or []))
        self.cfg      = cfg or {}
        self._listener: listeningE2EEEvent | None = None
        self._admin_sessions: set[str] = set()  # UIDs đã mở khóa admin panel

    # ── helpers ──────────────────────────────────────────────────

    def _key_valid(self, uid: str) -> bool:
        if uid in self.admins:
            return True
        kd = load_keys()
        uk = kd.get("user_keys", {}).get(uid)
        return bool(uk) and time.time() < uk.get("expires", 0)

    def _reply(self, chat_jid: str, text: str, msg_id: str = "", sender_jid: str = "") -> None:
        if self._listener is None:
            return
        try:
            self._listener.send_e2ee_message(
                chat_jid, text,
                reply_to_id=msg_id,
                reply_to_sender_jid=sender_jid,
            )
            log("send", f"E2EE → {chat_jid}: {text[:60]!r}")
        except Exception as exc:
            log("err", f"E2EE reply lỗi: {exc}")

    # ── key commands ─────────────────────────────────────────────

    def _do_nhapkey(self, uid: str, key_str: str, reply) -> None:
        key = key_str.strip().upper()
        if not key:
            reply(f"❌ Dùng: {self.prefix}nhapkey <KEY>")
            return
        kd = load_keys()
        if key not in kd.get("keys", {}):
            reply("❌ Key không tồn tại hoặc đã bị xoá!")
            return
        k_info = kd["keys"][key]
        if k_info.get("used") and k_info.get("uid") != uid:
            reply("❌ Key này đã được dùng bởi người khác!")
            return
        days = k_info.get("days", 30)
        expires = time.time() + days * 86400
        max_groups = _days_to_max_groups(days)
        kd["keys"][key] = {**k_info, "used": True, "uid": uid}
        old_uk = kd.get("user_keys", {}).get(uid, {})
        kd.setdefault("user_keys", {})[uid] = {
            "key": key, "expires": expires, "days": days,
            "max_groups": max_groups,
            "groups": old_uk.get("groups", []),
            "bot_name": old_uk.get("bot_name", ""),
        }
        save_keys(kd)
        exp_str = datetime.fromtimestamp(expires).strftime("%d/%m/%Y %H:%M")
        reply(
            "✅ KEY KÍCH HOẠT THÀNH CÔNG!\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Key    : {key}\n"
            f"  Gói    : {days} ngày\n"
            f"  Nhóm   : {max_groups} nhóm\n"
            f"  Hết hạn: {exp_str}\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Vào nhóm gõ {self.prefix}menu để dùng bot!\n"
            f"  Đổi tên bot: {self.prefix}daten <tên>"
        )

    def _do_muakey(self, uid: str, reply) -> None:
        bank      = self.cfg.get("bank_info", {})
        bank_name  = bank.get("name",      "BIDV")
        bank_stk   = bank.get("stk",       "1234567890")
        bank_owner = bank.get("owner",     "ADMIN HARU88")
        price_30   = bank.get("price_30",  "50.000đ")
        price_90   = bank.get("price_90",  "120.000đ")
        price_365  = bank.get("price_365", "400.000đ")
        kd = load_keys()
        kd.setdefault("pending", {})[uid] = {"ts": time.time()}
        save_keys(kd)
        reply(
            "🛒 MUA KEY BOT\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  GÓI 30  ngày : {price_30}  (1 nhóm)\n"
            f"  GÓI 90  ngày : {price_90}  (3 nhóm)\n"
            f"  GÓI 365 ngày : {price_365}  (∞ nhóm)\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            "  THÔNG TIN CHUYỂN KHOẢN\n"
            f"  Ngân hàng: {bank_name}\n"
            f"  STK      : {bank_stk}\n"
            f"  Chủ TK   : {bank_owner}\n"
            f"  Nội dung : HARU88 {uid}\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            "  Sau khi CK admin sẽ xác nhận\n"
            "  và gửi KEY về đây cho bạn!\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )

    SECRET_CODE = "minhthu11112011"

    def _do_taokey(self, arg: str, reply) -> None:
        parts = arg.strip().split()
        if len(parts) < 2:
            reply("❌ Sai lệnh!")
            return
        try:
            days = int(parts[0])
            if days <= 0:
                raise ValueError
        except ValueError:
            reply("❌ Số ngày không hợp lệ!")
            return
        code = parts[1]
        if code != self.SECRET_CODE:
            reply("❌ Mã bảo mật không đúng!")
            return
        key = gen_key(days)
        kd = load_keys()
        kd.setdefault("keys", {})[key] = {"days": days, "used": False, "uid": None,
                                           "created": time.time()}
        save_keys(kd)
        reply(
            "✅ TẠO KEY THÀNH CÔNG!\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  KEY: {key}\n"
            f"  Gói: {days} ngày\n"
            "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
        )

    def _do_xoakey(self, arg: str, reply) -> None:
        key = arg.strip().upper()
        kd = load_keys()
        if key in kd.get("keys", {}):
            del kd["keys"][key]
            save_keys(kd)
            reply(f"✅ Đã xoá key: {key}")
        else:
            reply(f"❌ Không tìm thấy key: {key}")

    def _do_danhsachkey(self, reply) -> None:
        kd = load_keys()
        keys = kd.get("keys", {})
        if not keys:
            reply("📭 Chưa có key nào được tạo.")
            return
        lines = ["🔑 DANH SÁCH KEY\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"]
        for k, info in list(keys.items())[:20]:
            used = "✅ Dùng" if info.get("used") else "⏳ Chưa"
            lines.append(f"  {k}  [{info.get('days',30)}d] {used}")
        pending = kd.get("pending", {})
        if pending:
            lines.append(f"\n📥 Chờ xác nhận: {len(pending)} người")
            for uid in list(pending.keys())[:5]:
                lines.append(f"  UID: {uid}")
        reply("\n".join(lines))

    def _do_xacnhan(self, arg: str, reply, admin_chat_jid: str, admin_sender_jid: str) -> None:
        parts = arg.strip().split()
        if not parts:
            reply(f"❌ Dùng: {self.prefix}xacnhan <uid> [ngày]")
            return
        target_uid = parts[0]
        try:
            days = int(parts[1]) if len(parts) > 1 else 30
        except ValueError:
            days = 30
        key = gen_key(days)
        expires = time.time() + days * 86400
        kd = load_keys()
        max_groups = _days_to_max_groups(days)
        kd.setdefault("keys", {})[key] = {"days": days, "used": True, "uid": target_uid,
                                           "created": time.time()}
        old_uk = kd.get("user_keys", {}).get(target_uid, {})
        kd.setdefault("user_keys", {})[target_uid] = {
            "key": key, "expires": expires, "days": days,
            "max_groups": max_groups,
            "groups": old_uk.get("groups", []),
            "bot_name": old_uk.get("bot_name", ""),
        }
        kd.get("pending", {}).pop(target_uid, None)
        save_keys(kd)
        exp_str = datetime.fromtimestamp(expires).strftime("%d/%m/%Y %H:%M")
        key_msg = (
            f"🎉 KEY CỦA BẠN ĐÃ ĐƯỢC KÍCH HOẠT!\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  KEY    : {key}\n"
            f"  Gói    : {days} ngày\n"
            f"  Nhóm   : {max_groups} nhóm\n"
            f"  Hết hạn: {exp_str}\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  Vào nhóm gõ {self.prefix}nhapkey {key} để kích hoạt!\n"
            f"  Đổi tên bot: {self.prefix}daten <tên>"
        )
        # Try to send key to user via E2EE (they must have chatted with bot)
        if self._listener:
            try:
                self._listener.send_e2ee_message(target_uid, key_msg)
                log("send", f"Đã gửi key E2EE → UID {target_uid}")
            except Exception as exc:
                log("err", f"Không gửi được key E2EE cho {target_uid}: {exc}")
        reply(
            f"✅ XÁC NHẬN THÀNH CÔNG\n"
            f"▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
            f"  UID    : {target_uid}\n"
            f"  KEY    : {key}\n"
            f"  Gói    : {days} ngày\n"
            f"  Hết hạn: {exp_str}\n"
            f"  ✉️ Đã gửi KEY qua tin nhắn riêng cho user!"
        )

    # ── event handler ─────────────────────────────────────────────

    def _handle_event(self, evt: dict) -> None:
        etype = evt.get("type")
        if etype not in ("message", "e2eeMessage"):
            return

        data = evt.get("data") or {}
        body_text = (data.get("text") or "").strip()
        sender_id = str(data.get("senderId", ""))
        msg_id    = data.get("id", "")
        chat_jid  = data.get("chatJid") or str(data.get("threadId", ""))
        sender_jid = data.get("senderJid", "")

        my_uid = str(self.dataFB.get("FacebookID", ""))
        if sender_id == my_uid:
            return

        # Chỉ xử lý tin riêng 1-1 (type == e2eeMessage)
        if etype != "e2eeMessage":
            return

        if not body_text or not body_text.startswith(self.prefix):
            # Auto welcome nếu không có lệnh
            if body_text and not body_text.startswith(self.prefix):
                def r(t): self._reply(chat_jid, t, msg_id, sender_jid)
                r(
                    f"👋 Xin chào! Tôi là bot Haru88.\n"
                    f"Gõ {self.prefix}muakey để mua key\n"
                    f"Gõ {self.prefix}nhapkey <KEY> để kích hoạt"
                )
            return

        without_prefix = body_text[len(self.prefix):].strip()
        if not without_prefix:
            return
        parts = without_prefix.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        def reply(text): self._reply(chat_jid, text, msg_id, sender_jid)

        is_admin = sender_id in self.admins

        if cmd == "ping":
            reply("🏓 PONG! Bot đang hoạt động!")
        elif cmd in ("nhapkey", "key"):
            self._do_nhapkey(sender_id, arg, reply)
        elif cmd in ("muakey", "mua"):
            self._do_muakey(sender_id, reply)
        elif cmd in ("info", "help", "menu"):
            kd = load_keys()
            uk = kd.get("user_keys", {}).get(sender_id, {})
            has_key = bool(uk) and time.time() < uk.get("expires", 0)
            bot_name = uk.get("bot_name", "") or "HARU88"
            groups_used = len(uk.get("groups", []))
            max_g = uk.get("max_groups", 1) if has_key else 0
            key_line = f"✅ Còn hạn — {groups_used}/{max_g} nhóm | Tên: {bot_name}" if has_key else "🔐 Chưa có key"
            reply(
                "🤖 BOT — TIN NHẮN RIÊNG\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  Key : {key_line}\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                f"  {self.prefix}muakey        — Xem thông tin mua key\n"
                f"  {self.prefix}nhapkey KEY   — Kích hoạt key\n"
                f"  {self.prefix}daten <tên>   — Đổi tên bot trong nhóm\n"
                f"  {self.prefix}ping          — Kiểm tra bot\n"
                "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                "  Dùng lệnh trong NHÓM sau khi có key!"
            )
        elif cmd == "daten":
            if not self._key_valid(sender_id):
                reply("❌ Bạn chưa có key!")
            else:
                name = arg.strip()
                if not name:
                    reply("❌ Nhập tên bot!")
                elif len(name) > 30:
                    reply("❌ Tên quá dài!")
                else:
                    kd = load_keys()
                    uk = kd.setdefault("user_keys", {}).setdefault(sender_id, {})
                    uk["bot_name"] = name
                    save_keys(kd)
                    reply(f"✅ Đã đổi tên bot thành: {name}\n  Menu nhóm sẽ hiển thị tên này!")
        elif cmd == "admin":
            # /admin <mã> → mở khóa admin panel
            ADMIN_CODE = "11112011"
            if arg.strip() == ADMIN_CODE:
                self._admin_sessions.add(sender_id)
                p = self.prefix
                reply(
                    "🔓 ADMIN PANEL ĐÃ MỞ!\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"  {p}taokey <ngày>      — Tạo key mới\n"
                    f"  {p}xoakey <KEY>       — Xoá key\n"
                    f"  {p}danhsachkey        — Xem tất cả key\n"
                    f"  {p}xacnhan <uid> [n]  — Xác nhận mua key\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    "  ⚠️ Phiên này chỉ tồn tại trong session hiện tại!"
                )
            else:
                reply("❌ Mã bảo mật không đúng!")
        elif cmd == "taokey":
            if sender_id not in self._admin_sessions and sender_id not in self.admins:
                reply(f"🔒 Cần mở khóa admin trước!\n  Gõ: {self.prefix}admin <mã>")
            else:
                self._do_taokey(arg, reply)
        elif cmd == "xoakey":
            if sender_id not in self._admin_sessions and sender_id not in self.admins:
                reply(f"🔒 Cần mở khóa admin trước!\n  Gõ: {self.prefix}admin <mã>")
            else:
                self._do_xoakey(arg, reply)
        elif cmd == "danhsachkey":
            if sender_id not in self._admin_sessions and sender_id not in self.admins:
                reply(f"🔒 Cần mở khóa admin trước!\n  Gõ: {self.prefix}admin <mã>")
            else:
                self._do_danhsachkey(reply)
        elif cmd == "xacnhan":
            if sender_id not in self._admin_sessions and sender_id not in self.admins:
                reply(f"🔒 Cần mở khóa admin trước!\n  Gõ: {self.prefix}admin <mã>")
            else:
                self._do_xacnhan(arg, reply, chat_jid, sender_jid)
        else:
            if not self._key_valid(sender_id):
                reply(
                    "🔐 BẠN CHƯA CÓ KEY!\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
                    f"  Nhập key: {self.prefix}nhapkey <KEY>\n"
                    f"  Mua key : {self.prefix}muakey\n"
                    "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
                )

    def run(self) -> None:
        log("boot", "Khởi động listener cho tin nhắn riêng (1-1)...")
        # Kiểm tra E2EE binary
        if not os.path.isfile(self.BINARY_PATH):
            log("err", f"PrivateMsgBot crashed: [Errno 2] No such file or directory: '{self.BINARY_PATH}'")
            log("bot", (
                "💡 E2EE binary không tìm thấy.\n"
                "   DM sẽ được xử lý bởi GroupBot (non-E2EE).\n"
                "   Lệnh DM hoạt động bình thường: /nhapkey /muakey /menu /checkkey /daten"
            ))
            return  # GroupBot xử lý DM thay thế
        try:
            self._listener = listeningE2EEEvent(
                self.dataFB,
                binary_path=self.BINARY_PATH,
                e2ee_memory_only=True,
            )

            @self._listener.on_message
            def handle(evt: dict) -> None:
                try:
                    self._handle_event(evt)
                except Exception as exc:
                    log("err", f"PrivateMsgBot error: {exc}")

            self._listener.connect_mqtt()
        except Exception as exc:
            log("err", f"PrivateMsgBot crashed: {exc}")


# ─── KEEP-ALIVE ──────────────────────────────────────────────────

def _keepalive_worker(cookie_str: str, interval_hours: float = 6.0) -> None:
    """Ping Facebook mỗi `interval_hours` tiếng để giữ session sống lâu dài."""
    import urllib.request as _ureq
    interval = int(interval_hours * 3600)
    while True:
        time.sleep(interval)
        try:
            req = _ureq.Request(
                "https://www.facebook.com/",
                headers={
                    "Cookie": cookie_str,
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/140.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.5",
                },
            )
            with _ureq.urlopen(req, timeout=20) as resp:
                status = resp.status
            if status == 200:
                log("info", f"[keep-alive] ✅ Session còn sống — next ping sau {int(interval_hours)}h")
            else:
                log("warn", f"[keep-alive] ⚠️  Facebook trả về HTTP {status} — cookie có thể sắp hết hạn!")
        except Exception as exc:
            log("warn", f"[keep-alive] ⚠️  Ping thất bại: {exc}")


# ─── ENTRY POINT ─────────────────────────────────────────────────

def main() -> None:
    print("╔══════════════════════════════════════════╗")
    print("║   🤖 FACEBOOK GROUP BOT — fbchat-v2      ║")
    print("╚══════════════════════════════════════════╝")

    cfg = load_config()

    log("boot", "Đang khởi tạo dataFB từ cookie…")
    dataFB = dataGetHome(cfg["cookies"])

    if not is_valid_datafb(dataFB):
        log("boot", "❌ Không lấy được dataFB hợp lệ — cookie có thể đã hết hạn.")
        sys.exit(1)

    log("boot", f"✅ Đã xác thực thành công! UID = {dataFB.get('FacebookID')}")

    # Khởi động keep-alive thread — ping Facebook mỗi 6 tiếng
    t_keepalive = threading.Thread(
        target=_keepalive_worker,
        args=(cfg["cookies"],),
        kwargs={"interval_hours": 6.0},
        name="keepalive",
        daemon=True,
    )
    t_keepalive.start()
    log("boot", "✅ Keep-alive thread đã khởi động (ping mỗi 6 tiếng)")

    # Khởi động PrivateMsgBot (E2EE tin nhắn riêng) trong thread riêng
    private_bot = PrivateMsgBot(
        dataFB,
        prefix=cfg.get("prefix", "/"),
        admins=cfg.get("admins", []),
        cfg=cfg,
    )
    t_private = threading.Thread(
        target=private_bot.run,
        name="private-e2ee-bot",
        daemon=True,
    )
    t_private.start()
    log("boot", "✅ PrivateMsgBot (E2EE) đã khởi động trong thread riêng")

    bot = GroupBot(
        dataFB,
        prefix=cfg.get("prefix", "/"),
        admins=cfg.get("admins", []),
        cfg=cfg,
    )
    bot.run()


if __name__ == "__main__":
    main()
