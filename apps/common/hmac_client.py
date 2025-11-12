
import time, hmac, hashlib, requests
BASE = "http://127.0.0.1:8000/api"
KEY_ID = "intramars"
SECRET = "super-secreto-largo"

ts  = str(int(time.time()))
sig = hmac.new(SECRET.encode(), f"{KEY_ID}.{ts}".encode(), hashlib.sha256).hexdigest()
headers = {
    "accept": "application/json",
    "X-API-KeyId": KEY_ID,
    "X-API-Timestamp": ts,
    "X-API-Signature": sig,
}
r = requests.get(f"{BASE}/productos", params={"q": "taladro"}, headers=headers, timeout=5)
print(r.status_code, r.text)

