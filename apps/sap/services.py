from datetime import date
from .client import ServiceLayerClient, ServiceLayerError
import json


# ================================================================
# 🔹 Función auxiliar para formatear fechas
# ================================================================
def _ensure_date_str(d):
    """
    Acepta date | str | None y devuelve 'YYYY-MM-DD' o None.
    """
    if d is None:
        return None
    if isinstance(d, date):
        return d.strftime("%Y-%m-%d")
    # Asume que el string ya está correcto
    return str(d)


# ================================================================
# 🔹 Normalización de payload de cotización
# ================================================================
def _normalize_quotation_payload(payload: dict) -> dict:
    """
    Limpia y valida lo mínimo para crear/actualizar cotización.
    Requiere: DocDate, DocDueDate, CardCode, DocumentLines (>=1).
    También conserva todos los campos personalizados (UDF), incluyendo U_GGH_TIM,
    y respeta la descripción manual (ItemDescription) que viene del frontend.
    """
    if not isinstance(payload, dict):
        raise ValueError("El payload debe ser dict.")

    out = dict(payload)  # copia superficial

    # ===== Normalización de fechas =====
    out["DocDate"] = _ensure_date_str(out.get("DocDate"))
    out["TaxDate"] = _ensure_date_str(out.get("TaxDate")) or out["DocDate"]
    out["DocDueDate"] = _ensure_date_str(out.get("DocDueDate"))

    # ===== Validaciones mínimas =====
    if not out.get("CardCode"):
        raise ValueError("Falta CardCode.")
    if not out.get("DocDate") or not out.get("DocDueDate"):
        raise ValueError("Faltan DocDate y/o DocDueDate.")

    lines = out.get("DocumentLines") or []
    if not isinstance(lines, list) or not lines:
        raise ValueError("Debes incluir al menos una línea en DocumentLines.")

    # ===== Normalizar líneas =====
    norm_lines = []
    for i, l in enumerate(lines):
        if not l.get("ItemCode"):
            raise ValueError(f"Línea {i}: falta ItemCode.")
        if float(l.get("Quantity", 0)) <= 0:
            raise ValueError(f"Línea {i}: Quantity debe ser > 0.")

        # Campos base esperados por SAP (ahora incluye ItemDescription)
        linea_normalizada = {
            "ItemCode": l["ItemCode"],
            "ItemDescription": l.get("ItemDescription"),
            "Quantity": float(l["Quantity"]),
            "UnitPrice": (
                float(l.get("UnitPrice", 0))
                if l.get("UnitPrice") is not None else None
            ),
            "WarehouseCode": l.get("WarehouseCode"),
            "TaxCode": l.get("TaxCode"),
        }

        # 🔹 Mantener todos los User Defined Fields (U_)
        for k, v in l.items():
            if k.startswith("U_"):
                linea_normalizada[k] = v if v is not None else ""

        # 💡 Mantiene strings vacíos, elimina solo None
        linea_normalizada = {
            k: v for k, v in linea_normalizada.items() if v is not None
        }

        norm_lines.append(linea_normalizada)

    out["DocumentLines"] = norm_lines

    # ===== Limpiar claves None en raíz =====
    out = {k: v for k, v in out.items() if v is not None}

    return out


# ================================================================
# 🔹 Servicio principal para interactuar con SAP (Service Layer)
# ================================================================
class SapQuotationsService:
    """
    Servicio de Cotizaciones (Quotations) usando Service Layer.
    """

    # -------- Crear --------
    def create(self, payload: dict) -> dict:
        """
        Crea una cotización en SAP y retorna el documento completo (no solo el DocEntry).
        """
        body = _normalize_quotation_payload(payload)

        print("=== PAYLOAD ENVIADO A SAP ===")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        print("=============================")

        try:
            with ServiceLayerClient() as sl:
                created = sl.post("Quotations", body)
                doc_entry = created.get("DocEntry")

                if doc_entry:
                    full_doc = sl.get(f"Quotations({int(doc_entry)})")
                    print("=== COTIZACIÓN COMPLETA DESDE SAP ===")
                    print(json.dumps(full_doc, indent=2, ensure_ascii=False))
                    print("====================================")
                    return full_doc

                return created
        except ServiceLayerError as e:
            print(f"❌ Error al crear cotización: {e}")
            raise


    # -------- Obtener una cotización simple --------
    def get(self, doc_entry: int) -> dict:
        try:
            with ServiceLayerClient() as sl:
                return sl.get(f"Quotations({int(doc_entry)})")
        except ServiceLayerError:
            raise


    # -------- Modificar --------
    def patch(self, doc_entry: int, patch_body: dict) -> dict:
        if not isinstance(patch_body, dict) or not patch_body:
            raise ValueError("patch_body debe ser un dict no vacío.")

        for k in ("DocDate", "TaxDate", "DocDueDate"):
            if k in patch_body:
                patch_body[k] = _ensure_date_str(patch_body[k])

        try:
            with ServiceLayerClient() as sl:
                return sl.patch(f"Quotations({int(doc_entry)})", patch_body)
        except ServiceLayerError:
            raise


    # -------- Cancelar --------
    def cancel(self, doc_entry: int) -> dict | None:
        try:
            with ServiceLayerClient() as sl:
                return sl.post(f"Quotations({int(doc_entry)})/Cancel", {})
        except ServiceLayerError:
            raise


    # ================================================================
    # 🔹 Obtener detalle completo de una cotización (para PDF)
    # ================================================================
def get_full_quotation(self, doc_entry: int) -> dict:
    """
    Retorna la cotización con datos del cliente, contacto, vendedor y forma de pago.
    Incluye RUT del cliente y 'Solicitado por' con el nombre del contacto.
    Ideal para generar el PDF.
    """
    try:
        with ServiceLayerClient() as sl:
            # 1️⃣ Obtener la cotización base
            quotation = sl.get(f"Quotations({int(doc_entry)})")

            # 2️⃣ Obtener datos del cliente (BusinessPartner)
            card_code = quotation.get("CardCode")
            cliente = sl.get(f"BusinessPartners('{card_code}')") if card_code else {}
            quotation["Cliente"] = cliente

            quotation["CardName"] = cliente.get("CardName")
            quotation["FederalTaxID"] = cliente.get("FederalTaxID")
            quotation["Address"] = cliente.get("Address")
            quotation["Phone1"] = cliente.get("Phone1")

            # 3️⃣ Obtener el contacto (Solicitado por)
            contact_code = quotation.get("ContactPersonCode")
            solicitado_por = "-"
            if cliente and contact_code:
                for contacto in cliente.get("ContactEmployees", []):
                    if contacto.get("InternalCode") == contact_code:
                        solicitado_por = contacto.get("FirstName", "")
                        if contacto.get("LastName"):
                            solicitado_por += " " + contacto["LastName"]
                        break
            quotation["SolicitadoPor"] = solicitado_por

            # 4️⃣ Obtener vendedor (SalesPersons)
            sp_code = quotation.get("SalesPersonCode")
            vendedor = sl.get(f"SalesPersons({int(sp_code)})") if sp_code else {}
            quotation["SalesPersonName"] = vendedor.get("SalesEmployeeName")
            quotation["SalesPersonEmail"] = vendedor.get("Email")

            # 5️⃣ Obtener forma de pago (PaymentTermsTypes)
            payment_code = quotation.get("PaymentGroupCode")
            forma_pago = "No especificada"
            if payment_code is not None:
                try:
                    payment_data = sl.get(f"PaymentTermsTypes({int(payment_code)})")
                    forma_pago = payment_data.get("PaymentTermsGroupName", "No especificada")
                except Exception as e:
                    print(f"⚠️ Error al obtener forma de pago: {e}")

            quotation["FormaPago"] = forma_pago

            return quotation

    except ServiceLayerError as e:
        print(f"❌ Error al obtener cotización completa {doc_entry}: {e}")
        raise
