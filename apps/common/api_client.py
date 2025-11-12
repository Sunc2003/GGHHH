# apps/common/api_client.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings
from apps.common.hmac_client import build_hmac_headers

class ApiError(Exception):
    pass

class SapApiClient:
    def __init__(self, base_url=None, key_id=None, key_secret=None, timeout=None):
        self.base_url = (base_url or settings.API_BASE_URL).rstrip("/")
        self.key_id = key_id or settings.API_KEY_ID
        self.key_secret = key_secret or settings.API_KEY_SECRET
        self.timeout = timeout or settings.API_TIMEOUT

        self.sess = requests.Session()
        retry = Retry(
            total=2, backoff_factor=0.2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        self.sess.mount("http://", HTTPAdapter(max_retries=retry))
        self.sess.mount("https://", HTTPAdapter(max_retries=retry))

    def _headers(self):
        h = build_hmac_headers(self.key_id, self.key_secret)
        h["accept"] = "application/json"
        # Si usas ngrok:
        h["ngrok-skip-browser-warning"] = "true"
        h["User-Agent"] = "DjangoClient/1.0"
        return h

    def _get(self, path: str, params=None):
        url = f"{self.base_url}{path}"
        resp = self.sess.get(url, params=params or {}, headers=self._headers(), timeout=self.timeout)
        if resp.status_code == 401:
            raise ApiError(f"401 Unauthorized: {resp.text}")
        if resp.status_code >= 400:
            raise ApiError(f"HTTP {resp.status_code}: {resp.text}")
        return resp.json()

    # ---------- Endpoints ----------
    def buscar_productos(self, q: str):
        # GET /api/productos?q=...  (protegido por HMAC) 
        return self._get("/productos", params={"q": q})

    def detalle_producto(self, itemcode: str):
        # GET /api/productos/{itemcode}  (usa {itemcode:path} en la API)
        return self._get(f"/productos/{itemcode}")

    def buscar_socios(self, q: str = ""):
        # GET /api/socios?q=...
        return self._get("/socios", params={"q": q})

    def detalle_socio(self, cardcode: str):
        # GET /api/socios/{cardcode}
        return self._get(f"/socios/{cardcode}")

    def kpi_ventas_mes_actual(self, agrupacion="dia", neto=True):
        # GET /api/kpis/ventas-mes-actual?agrupacion=...&neto=true|false
        return self._get("/kpis/ventas-mes-actual", params={"agrupacion": agrupacion, "neto": str(neto).lower()})
