# apps/sap/services.py
from datetime import date, datetime
import json
from .client import ServiceLayerClient, ServiceLayerError

# ================================================================
# 🔹 Utilidades
# ================================================================
def _ensure_date_str(d, for_sap: bool = True):
    """Convierte fechas a string:
       - Para SAP (OData): YYYY-MM-DD
       - Para visualización/PDF: DD-MM-YYYY
    """
    if d is None:
        return None
    if isinstance(d, date):
        return d.strftime("%Y-%m-%d" if for_sap else "%d-%m-%Y")
    if isinstance(d, str):
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
    return str(d)

def _odata_escape(s: str) -> str:
    """Escapa comillas simples para filtros OData."""
    if s is None:
        return s
    return str(s).replace("'", "''")

def _norm_date_for_filter(d: str | None) -> str | None:
    """Normaliza una fecha cualquiera a 'YYYY-MM-DD' para usar en OData con comillas."""
    if not d:
        return None
    return _ensure_date_str(d, for_sap=True)

# ================================================================
# 🔹 Servicio principal SAP - Cotizaciones
# ================================================================
class SapQuotationsService:
    """Servicio de Cotizaciones usando SAP Service Layer."""

    # -------- Crear --------
    def create(self, payload: dict) -> dict:
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
            ln = {
                "ItemCode": l["ItemCode"],
                "ItemDescription": l.get("ItemDescription"),
                "Quantity": float(l["Quantity"]),
                "UnitPrice": float(l.get("UnitPrice", 0)) if l.get("UnitPrice") else None,
                "WarehouseCode": l.get("WarehouseCode"),
                "TaxCode": l.get("TaxCode"),
            }
            # campos U_
            for k, v in l.items():
                if k.startswith("U_"):
                    ln[k] = v if v is not None else ""
            ln = {k: v for k, v in ln.items() if v is not None}
            norm_lines.append(ln)

        out["DocumentLines"] = norm_lines
        body = {k: v for k, v in out.items() if v is not None}

        print("=== PAYLOAD ENVIADO A SAP ===")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        print("=============================")

        try:
            with ServiceLayerClient() as sl:
                created = sl.post("Quotations", body)
                doc_entry = created.get("DocEntry")
                if doc_entry:
                    q = sl.get(f"Quotations({int(doc_entry)})")
                    # si no trae líneas, cargarlas
                    try:
                        lines = q.get("DocumentLines")
                        if not lines:
                            lr = sl.get(f"Quotations({int(doc_entry)})/DocumentLines")
                            q["DocumentLines"] = lr.get("value", [])
                    except Exception as e:
                        print(f"⚠️ No se pudieron cargar las líneas: {e}")
                    return q
                return created
        except ServiceLayerError as e:
            print(f"❌ Error al crear cotización: {e}")
            raise

    # -------- Obtener simple --------
    def get(self, doc_entry: int) -> dict:
        try:
            with ServiceLayerClient() as sl:
                q = sl.get(f"Quotations({int(doc_entry)})")
                try:
                    lines = q.get("DocumentLines")
                    if not lines:
                        lr = sl.get(f"Quotations({int(doc_entry)})/DocumentLines")
                        q["DocumentLines"] = lr.get("value", [])
                except Exception as e:
                    print(f"⚠️ No se pudieron cargar las líneas: {e}")
                return q
        except ServiceLayerError as e:
            print(f"❌ Error al obtener cotización: {e}")
            raise

    # -------- Patch --------
    def patch(self, doc_entry: int, patch_body: dict) -> dict:
        if not isinstance(patch_body, dict) or not patch_body:
            raise ValueError("El cuerpo del patch debe ser un dict no vacío.")
        for k in ("DocDate", "TaxDate", "DocDueDate"):
            if k in patch_body:
                patch_body[k] = _ensure_date_str(patch_body[k], for_sap=True)
        try:
            with ServiceLayerClient() as sl:
                return sl.patch(f"Quotations({int(doc_entry)})", patch_body)
        except ServiceLayerError as e:
            print(f"❌ Error en patch de cotización {doc_entry}: {e}")
            raise

    # -------- Cerrar --------
    def close(self, doc_entry: int) -> dict | None:
        try:
            with ServiceLayerClient() as sl:
                return sl.post(f"Quotations({int(doc_entry)})/Close", {})
        except ServiceLayerError as e:
            print(f"❌ Error al cerrar cotización {doc_entry}: {e}")
            raise

    # -------- Cancelar --------
    def cancel(self, doc_entry: int) -> dict | None:
        try:
            with ServiceLayerClient() as sl:
                return sl.post(f"Quotations({int(doc_entry)})/Cancel", {})
        except ServiceLayerError as e:
            print(f"❌ Error al cancelar cotización {doc_entry}: {e}")
            raise

    # -------- Convertir a OV --------
    def to_order(self, doc_entry: int, warehouse: str | None = None, doc_date: str | None = None) -> dict:
        """Convierte una cotización en Orden de Venta referenciando líneas base (BaseType=23)."""
        try:
            with ServiceLayerClient() as sl:
                q = sl.get(f"Quotations({int(doc_entry)})")
                lines = q.get("DocumentLines") or []
                if not lines:
                    lr = sl.get(f"Quotations({int(doc_entry)})/DocumentLines",
                                params={"$select": "LineNum,Quantity,WarehouseCode"})
                    lines = lr.get("value", [])

                ov_lines = []
                for l in lines:
                    qty = float(l.get("Quantity") or 0)
                    if qty <= 0:
                        continue
                    ov_lines.append({
                        "BaseType": 23,
                        "BaseEntry": int(doc_entry),
                        "BaseLine": int(l.get("LineNum", 0)),
                        "Quantity": qty,
                        **({"WarehouseCode": warehouse} if warehouse else {}),
                    })

                body = {
                    "CardCode": q.get("CardCode"),
                    "DocDate": _ensure_date_str(doc_date or q.get("DocDate"), for_sap=True),
                    "DocDueDate": _ensure_date_str(q.get("DocDueDate"), for_sap=True),
                    "PaymentGroupCode": q.get("PaymentGroupCode"),
                    "SalesPersonCode": q.get("SalesPersonCode"),
                    "DocumentLines": ov_lines,
                }
                created = sl.post("Orders", body)
                return created
        except ServiceLayerError as e:
            print(f"❌ Error al convertir a OV desde cotización {doc_entry}: {e}")
            raise

    # -------- Detalle completo (PDF) --------
    def get_full_quotation(self, doc_entry: int) -> dict:
        try:
            with ServiceLayerClient() as sl:
                q = sl.get(f"Quotations({int(doc_entry)})")
                if not q:
                    raise ValueError(f"No se encontró la cotización {doc_entry}")

                # Cliente
                card_code = q.get("CardCode")
                cliente = sl.get(f"BusinessPartners('{card_code}')") if card_code else {}
                q["CardName"] = cliente.get("CardName", "-")
                q["FederalTaxID"] = cliente.get("FederalTaxID", "-")
                q["Address"] = cliente.get("Address", "-")
                q["Phone1"] = cliente.get("Phone1", "-")
                q["EmailAddress"] = cliente.get("EmailAddress", "-")
                q["SolicitadoPor"] = cliente.get("ContactPerson", "-")

                # Vendedor
                sp_code = q.get("SalesPersonCode")
                vendedor = sl.get(f"SalesPersons({int(sp_code)})") if sp_code else {}
                q["SalesPersonName"] = vendedor.get("SalesEmployeeName", "-")
                q["SalesPersonEmail"] = vendedor.get("Email", "-")

                # Forma de pago
                forma_pago = "No informado"
                payment_code = q.get("PaymentGroupCode")
                if payment_code is not None:
                    try:
                        pago = sl.get(f"PaymentTermsTypes({int(payment_code)})")
                        forma_pago = pago.get("PaymentTermsGroupName", "No informado")
                    except Exception as e:
                        print(f"⚠️ Error obteniendo forma de pago: {e}")
                q["FormaPago"] = forma_pago

                # Fechas formato humano
                q["DocDate"] = _ensure_date_str(q.get("DocDate"), for_sap=False)
                q["DocDueDate"] = _ensure_date_str(q.get("DocDueDate"), for_sap=False)

                # Totales formateados
                total = q.get("DocTotal", 0) or 0
                q["DocTotal_fmt"] = f"{total:,.0f}".replace(",", ".")

                # Líneas
                try:
                    lines = q.get("DocumentLines")
                    if not lines:
                        lr = sl.get(f"Quotations({int(doc_entry)})/DocumentLines")
                        q["DocumentLines"] = lr.get("value", [])
                except Exception as e:
                    print(f"⚠️ No se pudieron cargar las líneas: {e}")

                for l in q.get("DocumentLines", []):
                    if l.get("UnitPrice"):
                        l["UnitPrice_fmt"] = f"{l['UnitPrice']:,.0f}".replace(",", ".")
                    if l.get("LineTotal"):
                        l["LineTotal_fmt"] = f"{l['LineTotal']:,.0f}".replace(",", ".")
                    l["MeasureUnit"] = l.get("MeasureUnit", "-")

                return q
        except ServiceLayerError as e:
            print(f"❌ Error al obtener cotización completa {doc_entry}: {e}")
            raise
        except Exception as e:
            print(f"❌ Error general en get_full_quotation: {e}")
            raise

    # -------- Buscar (listado) --------
    def search(self, q=None, desde=None, hasta=None, estado=None, slp=None, page=1, size=20):
        page = max(1, int(page)); size = max(1, min(100, int(size)))
        skip = (page - 1) * size

        filters = []
        if estado in ("bost_Open", "bost_Close"):
            filters.append(f"DocumentStatus eq '{estado}'")

        if slp is not None:
            try:
                filters.append(f"SalesPersonCode eq {int(slp)}")
            except Exception:
                pass

        # ✅ FECHAS con comillas
        _d = _norm_date_for_filter(desde)
        _h = _norm_date_for_filter(hasta)
        if _d and _h:
            filters.append(f"DocDate ge '{_d}' and DocDate le '{_h}'")
        elif _d:
            filters.append(f"DocDate ge '{_d}'")
        elif _h:
            filters.append(f"DocDate le '{_h}'")

        # Texto: DocNum exacto o contains(CardName)
        if q:
            q = q.strip()
            try:
                n = int(q)
                filters.append(f"DocNum eq {n}")
            except ValueError:
                filters.append(f"contains(CardName,'{_odata_escape(q)}')")

        params = {
            "$select": "DocEntry,DocNum,CardName,DocTotal,DocCurrency",
            "$orderby": "DocNum desc",
            "$top": str(size),
            "$skip": str(skip),
        }
        if filters:
            params["$filter"] = " and ".join(filters)

        with ServiceLayerClient() as sl:
            data = sl.get("Quotations", params=params)

        items = (data or {}).get("value", [])

        def _row(row):
            return {
                "DocEntry": row.get("DocEntry"),
                "DocNum": row.get("DocNum"),
                "CardName": row.get("CardName"),
                "DocTotal": row.get("DocTotal", 0.0),
                "DocCurrency": row.get("DocCurrency") or "CLP",
            }

        return {
            "page": page,
            "size": size,
            "count": len(items),
            "results": [_row(it) for it in items],
        }


class SapOrdersService:
    """Servicio para crear Órdenes de Venta (ORDR) desde la intranet."""

    def create(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("El payload debe ser un dict válido.")

        out = dict(payload)

        out["DocDate"]    = _ensure_date_str(out.get("DocDate"), for_sap=True)
        out["TaxDate"]    = _ensure_date_str(out.get("TaxDate") or out.get("DocDate"), for_sap=True)
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

            ln = {
                "ItemCode": l["ItemCode"],
                "ItemDescription": l.get("ItemDescription"),
                "Quantity": float(l["Quantity"]),
                "UnitPrice": float(l.get("UnitPrice", 0)) if l.get("UnitPrice") else None,
                "WarehouseCode": l.get("WarehouseCode"),
                "TaxCode": l.get("TaxCode"),
            }

            # 🔹 Campos U_ por línea (margen, comisión, etc.)
            for k, v in l.items():
                if k.startswith("U_"):
                    ln[k] = v if v is not None else ""

            ln = {k: v for k, v in ln.items() if v is not None}
            norm_lines.append(ln)

        out["DocumentLines"] = norm_lines
        body = {k: v for k, v in out.items() if v is not None}

        print("=== PAYLOAD ORDR ENVIADO A SAP ===")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        print("===================================")

        try:
            with ServiceLayerClient() as sl:
                created = sl.post("Orders", body)
                doc_entry = created.get("DocEntry")
                if doc_entry:
                    # Recarga para tener todo el documento
                    o = sl.get(f"Orders({int(doc_entry)})")
                    try:
                        lines = o.get("DocumentLines")
                        if not lines:
                            lr = sl.get(f"Orders({int(doc_entry)})/DocumentLines")
                            o["DocumentLines"] = lr.get("value", [])
                    except Exception as e:
                        print(f"⚠️ No se pudieron cargar las líneas OV: {e}")
                    return o
                return created
        except ServiceLayerError as e:
            print(f"❌ Error al crear OV: {e}")
            raise
        
        
        
class SapBusinessPartnerService:
    def search_partners(self, query):
        """
        Busca socios por nombre o código y devuelve CardCode, CardName y Direcciones.
        """
        # Filtro OData: busca en Nombre O en Código
        # Nota: 'contains' suele ser case-sensitive en HANA a menos que se configure lo contrario.
        odata_filter = f"contains(CardName, '{query}') or contains(CardCode, '{query}')"
        
        params = {
            "$filter": odata_filter,
            # IMPORTANTE: Traemos BPAddresses para poder poblar el select
            "$select": "CardCode,CardName,BPAddresses"
        }

        try:
            with ServiceLayerClient() as sl:
                # Top 20 para no saturar
                data = sl.get("BusinessPartners", params={**params, "$top": "20"})
                return data.get("value", [])
        except ServiceLayerError as e:
            print(f"❌ Error buscando socios: {e}")
            return []
        
        
        



