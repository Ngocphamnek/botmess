import json, random, ssl, time
from threading import Event
from urllib.parse import urlparse
from _core._utils import gen_threading_id, mainRequests, formAll, generate_session_id, generate_client_id, json_minimal
import paho.mqtt.client as mqtt

MQTT_HOST = "edge-chat.facebook.com"
LS_TOPIC = "/ls_req"
APP_ID = "2220391788200892"
LS_VERSION_ID = "6903494529735864"
_DEFAULT_TIMEOUT = 15


def _j(data):
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _make_mqtt_client(dataFB):
    session_id = generate_session_id()
    user = {
        "u": str(dataFB["FacebookID"]),
        "s": session_id,
        "chat_on": json_minimal(True),
        "fg": False,
        "d": generate_client_id(),
        "ct": "websocket",
        "aid": 219994525426954,
        "mqtt_sid": "",
        "cp": 3,
        "ecp": 10,
        "st": "/t_ms",
        "pm": [],
        "dc": "",
        "no_auto_fg": True,
        "gas": None,
        "pack": [],
    }
    host = f"wss://{MQTT_HOST}/chat?region=eag&sid={session_id}"
    parsed = urlparse(host)
    client = mqtt.Client(
        client_id="mqttwsclient",
        clean_session=True,
        protocol=mqtt.MQTTv31,
        transport="websockets",
    )
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.tls_insecure_set(False)
    client.username_pw_set(username=json_minimal(user))
    client.ws_set_options(
        path=f"{parsed.path}?{parsed.query}",
        headers={
            "Cookie": dataFB["cookieFacebook"],
            "Origin": "https://www.facebook.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "Referer": "https://www.facebook.com/",
            "Host": MQTT_HOST,
        },
    )
    return client, host


def _publish_ls(dataFB, context, timeout=_DEFAULT_TIMEOUT):
    connected = Event()
    published = Event()
    responses = []
    state = {"errors": [], "published": 0}

    client, _ = _make_mqtt_client(dataFB)

    def on_connect(c, ud, flags, rc, *args):
        if int(rc) != 0:
            state["errors"].append(f"connect failed rc={rc}")
            connected.set()
            published.set()
            return
        connected.set()
        info = c.publish(LS_TOPIC, _j(context), qos=1)
        if getattr(info, "rc", 0) != mqtt.MQTT_ERR_SUCCESS:
            state["errors"].append(f"publish failed rc={info.rc}")
            published.set()

    def on_publish(c, ud, mid, *args):
        state["published"] += 1
        published.set()

    def on_message(c, ud, msg):
        try:
            responses.append(json.loads(msg.payload.decode()))
        except Exception:
            pass

    def on_disconnect(c, ud, rc, *args):
        if not published.is_set():
            connected.set()
            published.set()

    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        client.connect(MQTT_HOST, port=443, keepalive=10)
        client.loop_start()
        connected.wait(timeout=timeout)
        published.wait(timeout=timeout)
        time.sleep(2)
    except Exception as e:
        state["errors"].append(str(e))
    finally:
        try:
            client.disconnect()
        except Exception:
            pass
        try:
            client.loop_stop()
        except Exception:
            pass

    return state, responses


def send_group_ls(dataFB, content, thread_id, reply_message_id=None, timeout=_DEFAULT_TIMEOUT):
    """Gửi tin nhắn vào GROUP CHAT qua MQTT Lightspeed /ls_req (label 46)."""
    otid = gen_threading_id()
    task_payload = {
        "thread_id": str(thread_id),
        "otid": str(otid),
        "source": 0,
        "send_type": 1,
        "text": str(content),
        "initiating_source": 0,
    }
    if reply_message_id:
        task_payload["replied_to_message_id"] = str(reply_message_id)

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

    state, responses = _publish_ls(dataFB, context, timeout=timeout)
    if state["errors"]:
        return {"error": 1, "payload": {"errors": state["errors"]}}

    for resp in responses:
        payload_str = resp.get("payload", "")
        if isinstance(payload_str, str) and "markOptimisticMessageFailed" in payload_str:
            return {"error": 1, "payload": {"error-decription": "LS send failed (markOptimisticMessageFailed)", "response": payload_str[:300]}}

    return {"success": 1, "payload": {"messageID": str(otid), "timestamp": int(time.time() * 1000)}}


class api:

    def __init__(self):
        self.dataFB = None
        self.content = None
        self.ID = None
        self.typeAttachment = None
        self.attachmentID = None
        self.typeChat = None
        self.replyStatus = None
        self.messageID = None
        self.properties = [
            "is_unread", "is_cleared", "is_forward", "is_filtered_content",
            "is_filtered_content_bh", "is_filtered_content_account",
            "is_filtered_content_quasar", "is_filtered_content_invalid_app",
            "is_spoof_warning",
        ]
        self.dictAttachment = {
            "gif": "gif_ids", "image": "image_ids", "video": "video_ids",
            "file": "file_ids", "audio": "audio_ids",
            None: "this is not a Attachment we requested, try again later",
        }

    def send(self, dataFB, contentSend, threadID, typeAttachment=None, attachmentID=None,
             typeChat=None, replyMessage=None, messageID=None):
        self.dataFB = dataFB
        self.content = str(contentSend)
        self.ID = str(threadID)
        self.typeAttachment = typeAttachment
        self.attachmentID = attachmentID
        self.typeChat = typeChat
        self.replyStatus = replyMessage
        self.messageID = messageID

        if self.typeChat == "user":
            self.results = {
                "error": 1,
                "payload": {
                    "error-decription": (
                        "DM (1-1) yêu cầu E2EE kể từ tháng 11/2024. "
                        "Dùng _send_e2ee.api + Go bridge để gửi DM."
                    )
                },
            }
        else:
            reply_mid = self.messageID if self.replyStatus else None
            self.results = send_group_ls(
                self.dataFB,
                self.content,
                self.ID,
                reply_message_id=reply_mid,
            )

        self._reset()
        return self.results

    def _reset(self):
        self.typeAttachment = None
        self.attachmentID = None
        self.typeChat = None
        self.replyStatus = None
        self.messageID = None

    def removeValueToInputed(self):
        self._reset()
