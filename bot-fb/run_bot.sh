#!/bin/bash
set -e

BOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$BOT_DIR/src"
CONFIG_FILE="$SRC_DIR/config.json"

log() { echo "[$(date '+%H:%M:%S')] $1"; }

# Tạo config.json nếu chưa có
if [ ! -f "$CONFIG_FILE" ]; then
    log "⚙️  Tạo config.json mặc định..."
    python3 -c "
import json, os
cfg = {
    'botName': os.environ.get('BOT_NAME', 'Bot Mess'),
    'prefix': os.environ.get('BOT_PREFIX', '/'),
    'cookies': os.environ.get('FB_COOKIE', ''),
    'admins': [a.strip() for a in os.environ.get('BOT_ADMINS', '').split(',') if a.strip()],
    'version': '1.0.0'
}
with open('$CONFIG_FILE', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
print('[OK] Config đã được tạo')
"
fi

# Ghi FB_COOKIE từ env vào config nếu có
if [ -n "$FB_COOKIE" ]; then
    python3 -c "
import json, os
with open('$CONFIG_FILE', 'r', encoding='utf-8') as f:
    cfg = json.load(f)
cfg['cookies'] = os.environ.get('FB_COOKIE', '')
with open('$CONFIG_FILE', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
"
fi

log "🤖 Khởi động bot Facebook Messenger..."
cd "$SRC_DIR"
export PYTHONPATH="$SRC_DIR"
exec python3 main.py
