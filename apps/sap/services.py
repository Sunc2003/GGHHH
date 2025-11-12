# apps/sap/services.py
from datetime import date, datetime
from .client import ServiceLayerClient, ServiceLayerError
import json


# ================================================================
# 🔹 Función auxiliar para formatear fechas
# ================================================================
def _ensure_date_str(d, for_sap=True):
    """
    Convierte fechas a string.
    - Para SAP: usa formato YYYY-MM-DD (requerido por el Service Layer).
    - Para PDF o visualización: usa DD-MM-YYYY.
    """
    if d is None:
        return None

    if isinstance(d, date):
        return d.strftime("%Y-%m-%d" if for_sap else "%d-%m-%Y")

    if isinstance(d, str):
        try:
            parsed = None
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
                try:
                    parsed = datetime.strptime(d[:10], fmt)
                    break
                except Exception:
                    continue
            if parsed:
                return parsed.strftime("%Y-%m-%d" if for_sap else "%d-%m-%Y")
            return d
        except Exception:
            return d

    return str(d)


# ================================================================
# 🔹 Normalización del payload de cotización
# ================================================================
def _normalize_quotation_payload(payload: dict) -> dict:
    """
    Limpia y valida el cuerpo de una cotización antes de enviarla al Service Layer.
    Se asegura de enviar fechas en formato ISO (YYYY-MM-DD).
    """
    if not isinstance(payload, dict):
        raise ValueError("El payload debe ser un dict válido.")

    out = dict(payload)
    out["DocDate"] = _ensure_date_str(out.get("DocDate"), for_sap=True)
    out["TaxDate"] = _ensure_date_str(out.get("TaxDate"), for_sap=True) or out["DocDate"]
    out["DocDueDate"] = _ensure_date_str(out.get("DocDueDate"), for_sap=True)

    if not out.get("CardCode"):
        raise ValueError("Falta el campo 'CardCode'.")
    if not out.get("DocDate") or not out.get("DocDueDate"):
        raise ValueError("Faltan 'DocDate' o 'DocDueDate'.")

    lines = out.get("DocumentLines") or []
    if not isinstance(lines, list) or not lines:
        raise ValueError("Debes incluir al menos una línea en DocumentLines.")

    norm_lines = []
    for i, l in enumerate(lines):
        if not l.get("ItemCode"):
            raise ValueError(f"Línea {i}: falta 'ItemCode'.")
        if float(l.get("Quantity", 0)) <= 0:
            raise ValueError(f"Línea {i}: 'Quantity' debe ser mayor que 0.")

        linea_normalizada = {
            "ItemCode": l["ItemCode"],
            "ItemDescription": l.get("ItemDescription"),
            "Quantity": float(l["Quantity"]),
            "UnitPrice": float(l.get("UnitPrice", 0)) if l.get("UnitPrice") else None,
            "WarehouseCode": l.get("WarehouseCode"),
            "TaxCode": l.get("TaxCode"),
        }

        # Incluir campos de usuario (U_)
        for k, v in l.items():
            if k.startswith("U_"):
                linea_normalizada[k] = v if v is not None else ""

        linea_normalizada = {k: v for k, v in linea_normalizada.items() if v is not None}
        norm_lines.append(linea_normalizada)

    out["DocumentLines"] = norm_lines
    out = {k: v for k, v in out.items() if v is not None}
    return out


# ================================================================
# 🔹 Servicio principal para interactuar con SAP (Service Layer)
# ================================================================
class SapQuotationsService:
    """
    Servicio de Cotizaciones (Quotations) usando SAP Service Layer.
    Permite crear, consultar, modificar, cancelar y obtener detalle extendido.
    """

    # -------- Crear cotización --------
    def create(self, payload: dict) -> dict:
        body = _normalize_quotation_payload(payload)

        print("=== PAYLOAD ENVIADO A SAP ===")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        print("=============================")

        try:
            with ServiceLayerClient() as sl:
                created = sl.post("Quotations", body)
                doc_entry = created.get("DocEntry")

                if doc_entry:
                    print(f"✅ Cotización creada con DocEntry: {doc_entry}")
                    quotation = sl.get(f"Quotations({int(doc_entry)})")

                    # 🔹 Si SAP no devuelve las líneas, las traemos manualmente
                    try:
                        lines = quotation.get("DocumentLines")
                        if not lines:
                            lines_resp = sl.get(f"Quotations({int(doc_entry)})/DocumentLines")
                            quotation["DocumentLines"] = lines_resp.get("value", [])
                    except Exception as e:
                        print(f"⚠️ No se pudieron cargar las líneas: {e}")

                    return quotation

                return created
        except ServiceLayerError as e:
            print(f"❌ Error al crear cotización: {e}")
            raise


    # -------- Obtener cotización simple --------
    def get(self, doc_entry: int) -> dict:
        try:
            with ServiceLayerClient() as sl:
                print(f"📄 Consultando cotización {doc_entry}...")
                quotation = sl.get(f"Quotations({int(doc_entry)})")

                # 🔹 Carga manual de líneas si no vienen en la respuesta
                try:
                    lines = quotation.get("DocumentLines")
                    if not lines:
                        lines_resp = sl.get(f"Quotations({int(doc_entry)})/DocumentLines")
                        quotation["DocumentLines"] = lines_resp.get("value", [])
                except Exception as e:
                    print(f"⚠️ No se pudieron cargar las líneas: {e}")

                return quotation
        except ServiceLayerError as e:
            print(f"❌ Error al obtener cotización: {e}")
            raise


    # -------- Modificar --------
    def patch(self, doc_entry: int, patch_body: dict) -> dict:
        if not isinstance(patch_body, dict) or not patch_body:
            raise ValueError("El cuerpo del patch debe ser un dict no vacío.")
        for k in ("DocDate", "TaxDate", "DocDueDate"):
            if k in patch_body:
                patch_body[k] = _ensure_date_str(patch_body[k], for_sap=True)

        try:
            with ServiceLayerClient() as sl:
                print(f"✏️ Actualizando cotización {doc_entry}...")
                return sl.patch(f"Quotations({int(doc_entry)})", patch_body)
        except ServiceLayerError as e:
            print(f"❌ Error en patch de cotización {doc_entry}: {e}")
            raise


    # -------- Cancelar --------
    def cancel(self, doc_entry: int) -> dict | None:
        try:
            with ServiceLayerClient() as sl:
                print(f"🛑 Cancelando cotización {doc_entry}...")
                return sl.post(f"Quotations({int(doc_entry)})/Cancel", {})
        except ServiceLayerError as e:
            print(f"❌ Error al cancelar cotización: {e}")
            raise


    # ================================================================
    # 🔹 Obtener detalle completo de una cotización (para PDF)
    # ================================================================
    def get_full_quotation(self, doc_entry: int) -> dict:
        """
        Retorna la cotización con datos del cliente, contacto (ContactPerson),
        vendedor, forma de pago y líneas completas.
        Compatible con versiones de SAP que no soportan $expand.
        """
        try:
            with ServiceLayerClient() as sl:
                print(f"📦 Obteniendo detalle completo de la cotización {doc_entry}...")

                # 1️⃣ Cotización base
                quotation = sl.get(f"Quotations({int(doc_entry)})")

                if not quotation:
                    raise ValueError(f"No se encontró la cotización {doc_entry}")

                # 2️⃣ Cliente (BusinessPartner)
                card_code = quotation.get("CardCode")
                cliente = sl.get(f"BusinessPartners('{card_code}')") if card_code else {}

                quotation["CardName"] = cliente.get("CardName", "-")
                quotation["FederalTaxID"] = cliente.get("FederalTaxID", "-")
                quotation["Address"] = cliente.get("Address", "-")
                quotation["Phone1"] = cliente.get("Phone1", "-")
                quotation["EmailAddress"] = cliente.get("EmailAddress", "-")

                # ✅ Solicitado por (nombre real del contacto)
                quotation["SolicitadoPor"] = cliente.get("ContactPerson", "-")

                # 3️⃣ Vendedor
                sp_code = quotation.get("SalesPersonCode")
                vendedor = sl.get(f"SalesPersons({int(sp_code)})") if sp_code else {}
                quotation["SalesPersonName"] = vendedor.get("SalesEmployeeName", "-")
                quotation["SalesPersonEmail"] = vendedor.get("Email", "-")

                # 4️⃣ Forma de pago
                forma_pago = "No informado"
                payment_code = quotation.get("PaymentGroupCode")
                if payment_code is not None:
                    try:
                        pago = sl.get(f"PaymentTermsTypes({int(payment_code)})")
                        forma_pago = pago.get("PaymentTermsGroupName", "No informado")
                    except Exception as e:
                        print(f"⚠️ Error obteniendo forma de pago: {e}")
                quotation["FormaPago"] = forma_pago

                # 5️⃣ Fechas formateadas (para PDF)
                quotation["DocDate"] = _ensure_date_str(quotation.get("DocDate"), for_sap=False)
                quotation["DocDueDate"] = _ensure_date_str(quotation.get("DocDueDate"), for_sap=False)

                # 6️⃣ Totales
                total = quotation.get("DocTotal", 0) or 0
                quotation["DocTotal_fmt"] = f"{total:,.0f}".replace(",", ".")

                # 7️⃣ Líneas
                try:
                    lines = quotation.get("DocumentLines")
                    if not lines:
                        lines_resp = sl.get(f"Quotations({int(doc_entry)})/DocumentLines")
                        quotation["DocumentLines"] = lines_resp.get("value", [])
                except Exception as e:
                    print(f"⚠️ No se pudieron cargar las líneas: {e}")

                for l in quotation.get("DocumentLines", []):
                    if l.get("UnitPrice"):
                        l["UnitPrice_fmt"] = f"{l['UnitPrice']:,.0f}".replace(",", ".")
                    if l.get("LineTotal"):
                        l["LineTotal_fmt"] = f"{l['LineTotal']:,.0f}".replace(",", ".")
                    # 🔹 Nueva columna: unidad de medida
                    l["MeasureUnit"] = l.get("MeasureUnit", "-")

                print("✅ Detalle completo cargado correctamente.")
                return quotation

        except ServiceLayerError as e:
            print(f"❌ Error al obtener cotización completa {doc_entry}: {e}")
            raise
        except Exception as e:
            print(f"❌ Error general en get_full_quotation: {e}")
            raise
