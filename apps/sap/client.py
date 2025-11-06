import json
import requests
from django.conf import settings


class ServiceLayerError(Exception):
    def __init__(self, status, code=None, message=None, payload=None):
        self.status = status
        self.code = code
        self.message = message or "Service Layer error"
        self.payload = payload
        super().__init__(f"HTTP {status} [{code}]: {self.message}" if code else f"HTTP {status}: {self.message}")


class ServiceLayerClient:
    """
    Cliente para SAP Business One Service Layer.
    Uso recomendado:
        with ServiceLayerClient() as sl:
            q = sl.post("Quotations", {...})
    """
    def __init__(self):
        # ✅ En lugar de settings.SAP_SL usamos variables sueltas (compatibles con tu sistema actual)
        self.base = getattr(settings, "SAP_BASE_URL", "https://192.168.0.23:50000/b1s/v1").rstrip("/")
        self.company = getattr(settings, "SAP_COMPANY", "SBO_MARSELLA_TEST_DESARROLLO")
        self.user = getattr(settings, "SAP_USER", "manager")
        self.password = getattr(settings, "SAP_PASS", "Manzana")
        self.timeout = int(getattr(settings, "SAP_TIMEOUT", 20))
        self.verify = getattr(settings, "SAP_VERIFY_SSL", False)

        self.s = requests.Session()
        # Headers básicos para OData v4
        self.s.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "return=representation",
        })

        # Si quieres que PATCH de colecciones reemplace en vez de merge:
        if getattr(settings, "SAP_REPLACE_COLLECTIONS_ON_PATCH", True):
            self.s.headers["B1S-ReplaceCollectionsOnPatch"] = "true"

        self._logged_in = False

    # -------- Context manager --------
    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.logout()
        finally:
            return False

    # -------- Autenticación --------
    def login(self):
        r = self.s.post(
            f"{self.base}/Login",
            json={
                "CompanyDB": self.company,
                "UserName": self.user,
                "Password": self.password
            },
            timeout=self.timeout,
            verify=self.verify
        )
        self._raise_if_error(r)
        self._logged_in = True
        return r.json()

    def logout(self):
        try:
            self.s.post(f"{self.base}/Logout", timeout=self.timeout, verify=self.verify)
        finally:
            self._logged_in = False

    # -------- Métodos públicos --------
    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, json=None):
        return self._request("POST", path, json=json)

    def patch(self, path, json=None):
        return self._request("PATCH", path, json=json)

    def put(self, path, json=None):
        return self._request("PUT", path, json=json)

    def delete(self, path):
        return self._request("DELETE", path)

    # -------- Núcleo de requests con reintento 401 --------
    def _request(self, method, path, params=None, json=None, _retry=False):
        url = f"{self.base}/{path.lstrip('/')}"
        r = self.s.request(
            method=method,
            url=url,
            params=params or {},
            json=json,
            timeout=self.timeout,
            verify=self.verify,
        )

        # Si la sesión expiró, intenta 1 relogin y repite
        if r.status_code == 401 and not _retry:
            self.login()
            return self._request(method, path, params=params, json=json, _retry=True)

        self._raise_if_error(r)
        if r.status_code == 204 or not r.content:
            return None

        ctype = r.headers.get("content-type", "")
        if "application/json" not in ctype.lower():
            try:
                return r.json()
            except ValueError:
                raise ServiceLayerError(r.status_code, message="Respuesta no-JSON del Service Layer", payload=r.text[:500])

        return r.json()

    # -------- Errores --------
    def _raise_if_error(self, resp):
        if resp.status_code < 400:
            return
        try:
            data = resp.json()
            code = data.get("error", {}).get("code")
            msg = data.get("error", {}).get("message", {}).get("value")
            if not msg:
                msg = data.get("Message") or data.get("message") or json.dumps(data)[:500]
            raise ServiceLayerError(resp.status_code, code=code, message=msg, payload=data)
        except ValueError:
            raise ServiceLayerError(resp.status_code, message=resp.text[:500])