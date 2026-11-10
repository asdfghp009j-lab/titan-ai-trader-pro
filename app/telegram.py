import json
import urllib.parse
import urllib.request


def send_telegram(token: str, chat_id: str, text: str) -> bool:
    """Send a plain-text alert; no Telegram polling or trade commands are implemented."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            result = json.loads(response.read().decode("utf-8"))
        return bool(result.get("ok"))
    except Exception:
        return False
