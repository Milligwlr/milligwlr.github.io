# -*- coding: utf-8 -*-
"""Generador de datos del panel de control de Google Ads (alveos.mx/campana-ads/).

Que hace
  1. Lee Google Ads (cuenta 6354525352) por REST v22, solo googleAds:search (READ-ONLY).
  2. Lee GA4 (propiedad 527758587) por REST v1beta runReport con un JWT RS256 firmado
     con la cuenta de servicio (sin google-auth: solo stdlib + cryptography).
  3. Calcula el bloque "derivado" en Python puro (sin numpy): semanal, 30d vs 30d previos,
     bandas Poisson, pronostico, curva presupuesto->contactos y alertas.
  4. Escribe datos.json FUERA del repo (tmp), lo cifra a campana-ads/datos.enc
     (PBKDF2-SHA256 200000 it + AES-256-GCM, formato WebCrypto) y escribe
     campana-ads/meta.json sin cifras ni secretos.

Que NO hace (reglas duras del Dr.)
  - Jamas lee el calendario ni datos de pacientes: Ads y GA4 no los tienen y este script
    corre en GitHub Actions. La capa viva (citas, poligrafias) la consume la pagina
    directamente del Apps Script; nunca pasa por aqui.
  - Jamas muta nada: no hay mutate, no hay POST a Ads salvo googleAds:search.
  - Jamas escribe secretos: ni en el repo ni en la salida. La clave y las credenciales
    viven en variables de entorno o en archivos fuera del repo.

Manejo de errores
  - Si falla GA4: ga4 = null + alerta, el build sigue (exit 0).
  - Si falla una consulta secundaria de Ads: se registra en "ads.errores" y el build sigue.
  - Si falla la autenticacion o una consulta NUCLEAR de Ads (config o serie diaria): exit 1.
    Razon: sin serie diaria el panel mostraria un estado falso; mejor conservar el datos.enc
    anterior (meta.json delata la fecha).
"""
import argparse
import base64
import json
import math
import os
import secrets
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import zlib

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ----------------------------------------------------------------------------------
# Constantes
# ----------------------------------------------------------------------------------
VERSION = 2  # v2 = JSON comprimido con deflate (zlib) ANTES de cifrar; v1 = sin comprimir
ADS_API = "v22"
CID = "6354525352"
GA4_PROPERTY = "527758587"
# Etiquetas cortas por id de campana. Una campana nueva recibe "X<id>" hasta que se agregue aqui.
ETIQUETAS = {
    "23796879969": "C1",  # Consulta Neumologia
    "23800433236": "C2",  # Espirometria y Dejar de fumar
    "24026538372": "C3",  # Poligrafia / Estudio del sueno
}
# La CDMX no tiene horario de verano desde 2022: offset fijo -6 evita depender de tzdata en Windows.
TZ_CDMX = timezone(timedelta(hours=-6), name="CDMX")
DIAS_SERIE = 120
DIAS_CHANGE = 28
KDF_ITER = 200_000
# alpha 0.5: el backtest semanal del 22-ago (metodos-prediccion.md, A5) dio MAE/media 0.39 contra 0.36 del ingenuo
# y 0.40 de Holt; entre los planos la diferencia es ruido y 0.5 se explica ("cada semana pesa la mitad que la
# siguiente"). Con 0.3 el nivel arrastraba semanas de aprendizaje con presupuesto viejo (C3 pronosticaba 4.3/sem
# cuando la semana en curso llevaba 9 en 5 dias).
EWMA_ALPHA = 0.5
SEMANAS_PRONOSTICO = 4
SEMANAS_BASE = 8           # semanas completas que alimentan el pronostico y las medianas de alerta
SEMANAS_MIN_PRONOSTICO = 4  # con menos, Hyndman: cualquier modelo con parametros falla; no se pronostica
# Sobredispersion: indice varianza/media de conversiones semanales medido el 22-ago: C1 1.52, C2 0.71, C3 1.86,
# cuenta 2.18. Poisson puro (phi=1) daba bandas mas angostas que la realidad; phi se estima por campana y se acota.
PHI_MIN, PHI_MAX, PHI_DEFECTO = 1.0, 3.0, 1.5
# Elasticidad contactos/presupuesto medida en campaign_simulation (BUDGET) el 22-ago: conv C1 0.52, C2 0.49,
# C3 0.68; clics C1 0.72, C2 0.67, C3 0.61. Subir 10% el presupuesto trae ~5 a 7% mas contactos, no 10%.
ELASTICIDAD_CONV = 0.6
ELASTICIDAD_CLICS = 0.7
RATIO_PPTO_MIN, RATIO_PPTO_MAX = 0.5, 2.0   # fuera de este rango la elasticidad medida no vale
F_CONSUMO_DEFECTO = 0.95    # gasto/presupuesto tipico en el simulador (0.92 a 1.00); se usa si hay <3 dias post-cambio
DIAS_MIN_CONSUMO, DIAS_MAX_CONSUMO = 3, 14
# Techo fisico de poligrafia: 2 equipos, 10 a 12 estudios por semana como maximo (dato del consultorio).
# Los contactos por encima de ese ritmo no se convierten en estudios por mas presupuesto que se ponga.
ESTUDIOS_POLI_MAX_SEMANA = 12
P30_MIN_DIAS = 21           # con menos dias en el periodo previo, la comparacion 30d vs 30d no se publica
ALERTA_GASTO_X_PRESUPUESTO = 1.5
ALERTA_LOST_BUDGET = 0.40
ALERTA_LOST_BUDGET_DIAS = 3
ALERTA_CPC_SUBIDA = 0.30
ALERTA_MIN_CLICS_SEMANA = 10  # por debajo de esto el CPC semanal es ruido puro, no se alerta
ALERTA_CONV_ESPERADAS_MIN = 5  # la alerta de conv/clic exige >= 5 contactos esperados: con 10 clics y 10% de tasa,
                               # 0 contactos pasa 1 de cada 3 semanas por puro azar y disparaba una alerta "alta"

REPO = Path(__file__).resolve().parents[2]
DIR_SALIDA = REPO / "campana-ads"
RUTA_YAML = Path.home() / ".config" / "alveos" / "google-ads.yaml"
RUTA_GA4_KEY = Path.home() / "ga4-mcp-key.json"
RUTA_PANEL_KEY = Path.home() / ".config" / "alveos" / "panel-ads.key"


def log(msg):
    print(msg, file=sys.stderr, flush=True)


# El repo es PUBLICO y los logs de GitHub Actions de un repo publico los lee cualquiera (90 dias).
# Todo lo que se cifra en datos.enc (gasto, contactos, presupuestos) quedaria en claro en el log
# si se imprimiera ahi: en CI solo se registran conteos de filas y estados, nunca cifras.
EN_CI = os.environ.get("GITHUB_ACTIONS", "").lower() == "true"


# ----------------------------------------------------------------------------------
# Credenciales (env primero; archivos locales de respaldo; nunca se imprimen)
# ----------------------------------------------------------------------------------
def leer_yaml_plano(p):
    d = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def credenciales_ads():
    env = {k: os.environ.get(k, "").strip() for k in
           ("ADS_DEVELOPER_TOKEN", "ADS_CLIENT_ID", "ADS_CLIENT_SECRET", "ADS_REFRESH_TOKEN", "ADS_LOGIN_CUSTOMER_ID")}
    if all(env[k] for k in ("ADS_DEVELOPER_TOKEN", "ADS_CLIENT_ID", "ADS_CLIENT_SECRET", "ADS_REFRESH_TOKEN")):
        return {"developer_token": env["ADS_DEVELOPER_TOKEN"], "client_id": env["ADS_CLIENT_ID"],
                "client_secret": env["ADS_CLIENT_SECRET"], "refresh_token": env["ADS_REFRESH_TOKEN"],
                "login_customer_id": env["ADS_LOGIN_CUSTOMER_ID"] or CID}, "env"
    if RUTA_YAML.exists():
        y = leer_yaml_plano(RUTA_YAML)
        y.setdefault("login_customer_id", CID)
        return y, "yaml"
    raise SystemExit("Sin credenciales de Ads: faltan ADS_* en el entorno y no existe " + str(RUTA_YAML))


def credenciales_ga4():
    """Devuelve (dict, origen) o (None, motivo). Un JSON roto en el secret no debe tumbar el build:
    GA4 es tolerante por diseno."""
    raw = os.environ.get("GA4_SA_KEY_JSON", "").strip()
    origen = "env" if raw else ("archivo" if RUTA_GA4_KEY.exists() else None)
    if origen is None:
        return None, "GA4_SA_KEY_JSON ausente y no existe " + str(RUTA_GA4_KEY)
    try:
        sa = json.loads(raw) if raw else json.loads(RUTA_GA4_KEY.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return None, f"credencial GA4 ({origen}) ilegible: {str(e)[:120]}"
    if not all(k in sa for k in ("client_email", "private_key", "token_uri")):
        return None, f"credencial GA4 ({origen}) sin client_email/private_key/token_uri"
    return sa, origen


def clave_panel():
    k = os.environ.get("PANEL_ADS_KEY", "")
    if not k.strip() and RUTA_PANEL_KEY.exists():
        k = RUTA_PANEL_KEY.read_text(encoding="utf-8")
    k = k.strip()  # el archivo puede traer salto de linea final; la pagina hace trim() de lo tecleado
    if len(k) < 12:
        raise SystemExit("PANEL_ADS_KEY ausente o demasiado corta (minimo 12 caracteres)")
    return k


# ----------------------------------------------------------------------------------
# Google Ads REST
# ----------------------------------------------------------------------------------
def token_oauth_refresh(cfg):
    data = urllib.parse.urlencode({
        "client_id": cfg["client_id"], "client_secret": cfg["client_secret"],
        "refresh_token": cfg["refresh_token"], "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["access_token"]


class Ads:
    def __init__(self, cfg):
        self.cfg = cfg
        self.tok = token_oauth_refresh(cfg)
        self.errores = []

    def search(self, nombre, query, nuclear=False):
        """googleAds:search con pageToken y SIN pageSize (v22 ya no lo acepta). Devuelve lista de filas."""
        url = f"https://googleads.googleapis.com/{ADS_API}/customers/{CID}/googleAds:search"
        rows, page = [], None
        while True:
            body = {"query": query}
            if page:
                body["pageToken"] = page
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
                "Authorization": f"Bearer {self.tok}", "developer-token": self.cfg["developer_token"],
                "login-customer-id": self.cfg.get("login_customer_id", CID), "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    res = json.loads(r.read())
            except urllib.error.HTTPError as e:
                detalle = e.read().decode("utf-8", "replace")[:1500]
                if nuclear:
                    raise SystemExit(f"Consulta nuclear '{nombre}' fallo ({e.code}): {detalle}")
                self.errores.append({"consulta": nombre, "http": e.code, "detalle": detalle[:400]})
                log(f"  [aviso] {nombre}: HTTP {e.code}")
                return None
            except (urllib.error.URLError, TimeoutError) as e:
                if nuclear:
                    raise SystemExit(f"Consulta nuclear '{nombre}' sin respuesta: {e}")
                self.errores.append({"consulta": nombre, "http": 0, "detalle": str(e)[:400]})
                return None
            rows.extend(res.get("results", []))
            page = res.get("nextPageToken")
            if not page:
                break
        log(f"  {nombre}: {len(rows)} filas")
        return rows


def consultas_ads(f):
    """f = dict de fechas (YYYY-MM-DD). Todas las consultas son SELECT; ninguna muta."""
    return {
        "campanas_config": f"""
  SELECT campaign.id, campaign.name, campaign.status, campaign.bidding_strategy_type,
         campaign.maximize_conversions.target_cpa_micros, campaign.maximize_conversion_value.target_roas,
         campaign.target_spend.cpc_bid_ceiling_micros, campaign_budget.amount_micros, campaign_budget.id,
         campaign.geo_target_type_setting.positive_geo_target_type, campaign.advertising_channel_type,
         campaign.network_settings.target_search_network, campaign.network_settings.target_content_network,
         campaign.start_date
  FROM campaign WHERE campaign.status != 'REMOVED'""",
        "campanas_diario": f"""
  SELECT campaign.id, segments.date, metrics.cost_micros, metrics.impressions, metrics.clicks,
         metrics.conversions, metrics.conversions_value, metrics.search_impression_share,
         metrics.search_budget_lost_impression_share, metrics.search_rank_lost_impression_share,
         metrics.search_top_impression_share, metrics.search_absolute_top_impression_share
  FROM campaign WHERE segments.date BETWEEN '{f['ini120']}' AND '{f['fin']}' AND campaign.status != 'REMOVED'
  ORDER BY segments.date""",
        "cuenta_diario": f"""
  SELECT segments.date, metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.conversions,
         metrics.conversions_value
  FROM customer WHERE segments.date BETWEEN '{f['ini120']}' AND '{f['fin']}' ORDER BY segments.date""",
        "ad_groups_30d": f"""
  SELECT campaign.id, ad_group.id, ad_group.name, ad_group.status,
         metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.conversions, metrics.average_cpc, metrics.ctr
  FROM ad_group WHERE segments.date BETWEEN '{f['ini30']}' AND '{f['fin']}' AND ad_group.status != 'REMOVED'
  ORDER BY metrics.cost_micros DESC""",
        "keywords_30d": f"""
  SELECT campaign.id, ad_group.id, ad_group.name, ad_group_criterion.criterion_id, ad_group_criterion.keyword.text,
         ad_group_criterion.keyword.match_type, ad_group_criterion.status, ad_group_criterion.approval_status,
         ad_group_criterion.quality_info.quality_score, ad_group_criterion.quality_info.creative_quality_score,
         ad_group_criterion.quality_info.post_click_quality_score, ad_group_criterion.quality_info.search_predicted_ctr,
         metrics.impressions, metrics.clicks, metrics.conversions, metrics.cost_micros, metrics.average_cpc
  FROM keyword_view WHERE segments.date BETWEEN '{f['ini30']}' AND '{f['fin']}' AND ad_group_criterion.status != 'REMOVED'
  ORDER BY metrics.cost_micros DESC""",
        "terminos_30d": f"""
  SELECT campaign.id, ad_group.name, segments.search_term_match_type, search_term_view.search_term,
         search_term_view.status, metrics.impressions, metrics.clicks, metrics.conversions, metrics.cost_micros
  FROM search_term_view WHERE segments.date BETWEEN '{f['ini30']}' AND '{f['fin']}'
  ORDER BY metrics.cost_micros DESC""",
        "anuncios_30d": f"""
  SELECT campaign.id, ad_group.name, ad_group_ad.ad.id, ad_group_ad.status, ad_group_ad.ad_strength,
         ad_group_ad.policy_summary.approval_status, ad_group_ad.ad.final_urls,
         metrics.impressions, metrics.clicks, metrics.conversions, metrics.cost_micros, metrics.ctr
  FROM ad_group_ad WHERE segments.date BETWEEN '{f['ini30']}' AND '{f['fin']}' AND ad_group_ad.status != 'REMOVED'""",
        "acciones_conversion": """
  SELECT conversion_action.id, conversion_action.name, conversion_action.status, conversion_action.type,
         conversion_action.category, conversion_action.primary_for_goal, conversion_action.include_in_conversions_metric,
         conversion_action.counting_type, conversion_action.value_settings.default_value, conversion_action.origin
  FROM conversion_action WHERE conversion_action.status != 'REMOVED'""",
        "conv_por_accion_30d": f"""
  SELECT segments.conversion_action_name, segments.conversion_action_category, metrics.conversions,
         metrics.conversions_value
  FROM customer WHERE segments.date BETWEEN '{f['ini30']}' AND '{f['fin']}'""",
        "conv_por_campana_accion_30d": f"""
  SELECT campaign.id, segments.conversion_action_name, metrics.conversions, metrics.conversions_value
  FROM campaign WHERE segments.date BETWEEN '{f['ini30']}' AND '{f['fin']}' AND campaign.status != 'REMOVED'""",
        "dispositivo_30d": f"""
  SELECT campaign.id, segments.device, metrics.cost_micros, metrics.clicks, metrics.conversions, metrics.impressions
  FROM campaign WHERE segments.date BETWEEN '{f['ini30']}' AND '{f['fin']}' AND campaign.status != 'REMOVED'""",
        "dia_hora_30d": f"""
  SELECT campaign.id, segments.day_of_week, segments.hour, metrics.cost_micros, metrics.clicks, metrics.conversions,
         metrics.impressions
  FROM campaign WHERE segments.date BETWEEN '{f['ini30']}' AND '{f['fin']}' AND campaign.status != 'REMOVED'""",
        "negativos_campana": """
  SELECT campaign.id, campaign_criterion.keyword.text, campaign_criterion.keyword.match_type
  FROM campaign_criterion WHERE campaign_criterion.negative = TRUE AND campaign.status != 'REMOVED'
    AND campaign_criterion.type = 'KEYWORD'""",
        "cambios_28d": f"""
  SELECT change_event.change_date_time, change_event.change_resource_type, change_event.resource_change_operation,
         change_event.user_email, change_event.client_type, change_event.campaign, change_event.changed_fields,
         change_event.old_resource, change_event.new_resource
  FROM change_event WHERE change_event.change_date_time >= '{f['ini28']} 00:00:00'
    AND change_event.change_date_time <= '{f['hoy']} 23:59:59'
  ORDER BY change_event.change_date_time DESC LIMIT 400""",
        "assets_campana": """
  SELECT campaign.id, campaign.status, campaign_asset.field_type, campaign_asset.status, asset.id, asset.type,
         asset.sitelink_asset.link_text, asset.final_urls, asset.callout_asset.callout_text,
         asset.policy_summary.approval_status
  FROM campaign_asset WHERE campaign.status != 'REMOVED' AND campaign_asset.status != 'REMOVED'""",
        "recomendaciones": """
  SELECT recommendation.type, recommendation.campaign, recommendation.dismissed, recommendation.resource_name
  FROM recommendation WHERE recommendation.dismissed = FALSE""",
        "horario_anuncios": """
  SELECT campaign.id, campaign_criterion.ad_schedule.day_of_week, campaign_criterion.ad_schedule.start_hour,
         campaign_criterion.ad_schedule.end_hour, campaign_criterion.bid_modifier
  FROM campaign_criterion WHERE campaign_criterion.type = 'AD_SCHEDULE' AND campaign.status != 'REMOVED'""",
        "geo_objetivos": """
  SELECT campaign.id, campaign_criterion.location.geo_target_constant, campaign_criterion.negative,
         campaign_criterion.bid_modifier
  FROM campaign_criterion WHERE campaign_criterion.type = 'LOCATION' AND campaign.status != 'REMOVED'""",
        "geo_rendimiento_30d": f"""
  SELECT campaign.id, geographic_view.country_criterion_id, geographic_view.location_type,
         metrics.cost_micros, metrics.clicks, metrics.conversions, metrics.impressions
  FROM geographic_view WHERE segments.date BETWEEN '{f['ini30']}' AND '{f['fin']}'
  ORDER BY metrics.cost_micros DESC LIMIT 60""",
    }


# ----------------------------------------------------------------------------------
# Normalizacion de filas de Ads (micros -> MXN, strings -> numeros, etiquetas C1/C2/C3)
# ----------------------------------------------------------------------------------
def mxn(micros):
    return round(int(micros or 0) / 1e6, 2) if micros is not None else 0.0


def num(v, nd=3):
    if v is None:
        return 0
    try:
        x = float(v)
    except (TypeError, ValueError):
        return 0
    return int(x) if x.is_integer() else round(x, nd)


def ratio(v):
    """Impression share: la API omite el campo por debajo de 0.1 (lo reporta como '< 10%'). None = desconocido."""
    if v is None:
        return None
    return round(float(v), 4)


def etiqueta(cid):
    cid = str(cid)
    return ETIQUETAS.get(cid, "X" + cid)


def id_de_recurso(rn):
    return rn.rsplit("/", 1)[-1] if rn else None


def resume_cambio(e):
    """Traduce un change_event a (de, a, resumen) legible. La API NO expone los campos de puja en
    change_event: un UPDATE de CAMPAIGN con changed_fields vacio suele ser un cambio de estrategia de puja
    (asi aparecio la migracion de C3 del 13-ago-2026); se etiqueta como tal sin afirmar el valor."""
    tipo, op = e.get("changeResourceType"), (e.get("resourceChangeOperation") or "").lower()
    campos = e.get("changedFields") or ""
    viejo, nuevo = e.get("oldResource") or {}, e.get("newResource") or {}
    verbo = {"create": "agregado", "remove": "quitado", "update": "modificado"}.get(op, op)

    def kw_de(res, llave):
        k = (res.get(llave) or {}).get("keyword") or {}
        return f"'{k.get('text')}' ({k.get('matchType')})" if k.get("text") else None

    if tipo == "CAMPAIGN_BUDGET" and "amountMicros" in campos:
        de, a = mxn(viejo.get("campaignBudget", {}).get("amountMicros")), mxn(nuevo.get("campaignBudget", {}).get("amountMicros"))
        return de, a, f"presupuesto de ${de:,.0f} a ${a:,.0f} por dia"
    if tipo == "CAMPAIGN":
        c_v, c_n = viejo.get("campaign") or {}, nuevo.get("campaign") or {}
        if "status" in campos:
            return c_v.get("status"), c_n.get("status"), f"estado de campana de {c_v.get('status')} a {c_n.get('status')}"
        if "name" in campos:
            return c_v.get("name"), c_n.get("name"), "nombre de campana cambiado"
        if not campos:
            return None, None, "campana modificada (campos no expuestos por la API: normalmente estrategia de puja)"
        return None, None, f"campana modificada: {campos}"
    if tipo == "CAMPAIGN_CRITERION":
        kw = kw_de(nuevo if op == "create" else viejo, "campaignCriterion")
        if kw:
            neg = (nuevo if op == "create" else viejo).get("campaignCriterion", {}).get("negative")
            return None, None, f"{'negativo de campana' if neg else 'criterio de campana'} {verbo}: {kw}"
        return None, None, f"criterio de campana {verbo}: {campos}"
    if tipo == "AD_GROUP_CRITERION":
        res = nuevo if op == "create" else viejo
        kw = kw_de(res, "adGroupCriterion")
        if op == "update" and "status" in campos:
            de, a = (viejo.get("adGroupCriterion") or {}).get("status"), (nuevo.get("adGroupCriterion") or {}).get("status")
            return de, a, f"keyword de {de} a {a}"
        if kw:
            neg = res.get("adGroupCriterion", {}).get("negative")
            return None, None, f"{'negativo de grupo' if neg else 'keyword'} {verbo}: {kw}"
        return None, None, f"criterio de grupo {verbo}: {campos}"
    if tipo == "AD_GROUP":
        g_v, g_n = viejo.get("adGroup") or {}, nuevo.get("adGroup") or {}
        if op == "create":
            return None, None, f"grupo de anuncios creado: '{g_n.get('name')}'"
        if "status" in campos:
            return g_v.get("status"), g_n.get("status"), f"grupo de anuncios de {g_v.get('status')} a {g_n.get('status')}"
        return None, None, f"grupo de anuncios modificado: {campos}"
    if tipo == "AD_GROUP_AD":
        if op == "create":
            rsa = ((nuevo.get("adGroupAd") or {}).get("ad") or {}).get("responsiveSearchAd") or {}
            return None, None, f"anuncio creado ({len(rsa.get('headlines', []))} titulares, {len(rsa.get('descriptions', []))} descripciones)"
        if "status" in campos:
            de, a = (viejo.get("adGroupAd") or {}).get("status"), (nuevo.get("adGroupAd") or {}).get("status")
            return de, a, f"anuncio de {de} a {a}"
        return None, None, f"anuncio modificado: {campos}"
    if tipo in ("CAMPAIGN_ASSET", "AD_GROUP_ASSET", "CUSTOMER_ASSET"):
        res = (nuevo if op == "create" else viejo)
        ca = res.get("campaignAsset") or res.get("adGroupAsset") or res.get("customerAsset") or {}
        nivel = {"CAMPAIGN_ASSET": "campana", "AD_GROUP_ASSET": "grupo", "CUSTOMER_ASSET": "cuenta"}[tipo]
        return None, None, f"asset {ca.get('fieldType', '').lower() or 'sin tipo'} {'vinculado a' if op == 'create' else 'desvinculado de'} {nivel} (id {id_de_recurso(ca.get('asset')) or '?'})"
    if tipo == "ASSET" and op == "create":
        return None, None, "asset creado"
    return None, None, f"{verbo} {(tipo or '').lower().replace('_', ' ')}: {campos}".strip()


def normaliza_ads(raw):
    out = {}
    # --- configuracion de campanas
    camp = {}
    for r in raw["campanas_config"] or []:
        c, b = r["campaign"], r.get("campaignBudget", {})
        et = etiqueta(c["id"])
        camp[et] = {
            "id": c["id"], "nombre": c.get("name"), "estado": c.get("status"),
            "puja": c.get("biddingStrategyType"),
            "tcpa": mxn(c.get("maximizeConversions", {}).get("targetCpaMicros")) or None,
            "troas": c.get("maximizeConversionValue", {}).get("targetRoas"),
            "tope_cpc": mxn(c.get("targetSpend", {}).get("cpcBidCeilingMicros")) or None,
            "presupuesto_dia": mxn(b.get("amountMicros")), "presupuesto_id": b.get("id"),
            "geo_tipo": c.get("geoTargetTypeSetting", {}).get("positiveGeoTargetType"),
            "canal": c.get("advertisingChannelType"),
            "red_busqueda_socios": c.get("networkSettings", {}).get("targetSearchNetwork"),
            "red_display": c.get("networkSettings", {}).get("targetContentNetwork"),
            "inicio": c.get("startDate"),
            "geo": [], "horario": [], "negativos": [], "sitelinks": [], "callouts": [], "assets_otros": [],
        }
    por_id = {v["id"]: k for k, v in camp.items()}

    def et_de(r):
        cid = str(r.get("campaign", {}).get("id"))
        return por_id.get(cid, etiqueta(cid))

    # --- serie diaria por campana
    #     "valor_asignado" = conversions_value: es el valor FIJO que GTM asigna a cada pagina (sirve a la puja
    #     "maximizar valor"), NO es ingreso ni se divide entre el gasto: ROAS esta prohibido en este panel.
    diario = []
    for r in raw["campanas_diario"] or []:
        m = r["metrics"]
        diario.append({
            "fecha": r["segments"]["date"], "camp": et_de(r),
            "gasto": mxn(m.get("costMicros")), "imp": num(m.get("impressions")), "clk": num(m.get("clicks")),
            "conv": num(m.get("conversions")), "valor_asignado": num(m.get("conversionsValue"), 2),
            "is": ratio(m.get("searchImpressionShare")), "lb": ratio(m.get("searchBudgetLostImpressionShare")),
            "lr": ratio(m.get("searchRankLostImpressionShare")), "top": ratio(m.get("searchTopImpressionShare")),
            "abs_top": ratio(m.get("searchAbsoluteTopImpressionShare")),
        })
    out["diario"] = diario
    out["cuenta_diario"] = [{
        "fecha": r["segments"]["date"], "gasto": mxn(r["metrics"].get("costMicros")),
        "imp": num(r["metrics"].get("impressions")), "clk": num(r["metrics"].get("clicks")),
        "conv": num(r["metrics"].get("conversions")), "valor_asignado": num(r["metrics"].get("conversionsValue"), 2)}
        for r in raw["cuenta_diario"] or []]

    # --- ad groups
    out["ad_groups_30d"] = [{
        "camp": et_de(r), "id": r["adGroup"]["id"], "nombre": r["adGroup"]["name"], "estado": r["adGroup"].get("status"),
        "gasto": mxn(r["metrics"].get("costMicros")), "imp": num(r["metrics"].get("impressions")),
        "clk": num(r["metrics"].get("clicks")), "conv": num(r["metrics"].get("conversions")),
        "cpc": mxn(r["metrics"].get("averageCpc")), "ctr": num(r["metrics"].get("ctr"), 4)}
        for r in raw["ad_groups_30d"] or []]

    # --- keywords con calidad: solo las que tuvieron impresiones (las activas sin impresiones se cuentan
    #     por campana; 242 renglones con ceros no aportan nada al panel y pesaban 55 KB)
    kws = []
    sin_imp = {}
    for r in raw["keywords_30d"] or []:
        cr, q, m = r["adGroupCriterion"], r["adGroupCriterion"].get("qualityInfo", {}), r["metrics"]
        if num(m.get("impressions")) == 0:
            if cr.get("status") == "ENABLED":
                sin_imp[et_de(r)] = sin_imp.get(et_de(r), 0) + 1
            continue
        kws.append({
            "camp": et_de(r), "grupo": r["adGroup"]["name"], "kw": cr["keyword"]["text"],
            "tipo": cr["keyword"].get("matchType"), "estado": cr.get("status"), "aprobacion": cr.get("approvalStatus"),
            "qs": q.get("qualityScore"), "ad_rel": q.get("creativeQualityScore"), "lpe": q.get("postClickQualityScore"),
            "ectr": q.get("searchPredictedCtr"),
            "imp": num(m.get("impressions")), "clk": num(m.get("clicks")), "conv": num(m.get("conversions")),
            "gasto": mxn(m.get("costMicros")), "cpc": mxn(m.get("averageCpc"))})
    out["keywords_30d"] = kws
    out["keywords_activas_sin_impresiones"] = sin_imp

    # --- terminos de busqueda: top 60 por gasto y top 60 con clics y cero conversiones
    terms = []
    for r in raw["terminos_30d"] or []:
        m = r["metrics"]
        terms.append({"camp": et_de(r), "grupo": r["adGroup"]["name"], "termino": r["searchTermView"]["searchTerm"],
                      "tipo": r["segments"].get("searchTermMatchType"), "estado": r["searchTermView"].get("status"),
                      "imp": num(m.get("impressions")), "clk": num(m.get("clicks")),
                      "conv": num(m.get("conversions")), "gasto": mxn(m.get("costMicros"))})
    terms.sort(key=lambda t: -t["gasto"])
    out["terminos_30d"] = {
        "total_terminos": len(terms),
        "gasto_total": round(sum(t["gasto"] for t in terms), 2),
        "gasto_cero_conv": round(sum(t["gasto"] for t in terms if t["conv"] == 0), 2),
        "top_gasto": terms[:60],
        "top_cero_conv": [t for t in terms if t["conv"] == 0 and t["clk"] > 0][:60],
    }

    # --- anuncios
    out["anuncios_30d"] = [{
        "camp": et_de(r), "grupo": r["adGroup"]["name"], "id": r["adGroupAd"]["ad"]["id"],
        "estado": r["adGroupAd"].get("status"), "fuerza": r["adGroupAd"].get("adStrength"),
        "aprobacion": r["adGroupAd"].get("policySummary", {}).get("approvalStatus"),
        "url": (r["adGroupAd"]["ad"].get("finalUrls") or [None])[0],
        "imp": num(r["metrics"].get("impressions")), "clk": num(r["metrics"].get("clicks")),
        "conv": num(r["metrics"].get("conversions")), "gasto": mxn(r["metrics"].get("costMicros")),
        "ctr": num(r["metrics"].get("ctr"), 4)} for r in raw["anuncios_30d"] or []]

    # --- conversiones
    out["acciones_conversion"] = [{
        "id": r["conversionAction"]["id"], "nombre": r["conversionAction"]["name"],
        "estado": r["conversionAction"].get("status"), "tipo": r["conversionAction"].get("type"),
        "categoria": r["conversionAction"].get("category"), "primaria": r["conversionAction"].get("primaryForGoal"),
        "cuenta_en_conversiones": r["conversionAction"].get("includeInConversionsMetric"),
        "conteo": r["conversionAction"].get("countingType"),
        "valor_defecto": r["conversionAction"].get("valueSettings", {}).get("defaultValue"),
        "origen": r["conversionAction"].get("origin")} for r in raw["acciones_conversion"] or []]
    # all_conversions NO se consulta: mezcla acciones secundarias y de otras cuentas; la doctrina solo admite
    # metrics.conversions (acciones primarias). Si alguien lo reintroduce, el panel inflaria los contactos.
    out["conv_por_accion_30d"] = [{
        "accion": r["segments"].get("conversionActionName"), "categoria": r["segments"].get("conversionActionCategory"),
        "conv": num(r["metrics"].get("conversions")),
        "valor_asignado": num(r["metrics"].get("conversionsValue"), 2)} for r in raw["conv_por_accion_30d"] or []]
    out["conv_por_campana_accion_30d"] = [{
        "camp": et_de(r), "accion": r["segments"].get("conversionActionName"),
        "conv": num(r["metrics"].get("conversions")), "valor_asignado": num(r["metrics"].get("conversionsValue"), 2)}
        for r in raw["conv_por_campana_accion_30d"] or []]

    # --- dispositivo y dia/hora
    out["dispositivo_30d"] = [{
        "camp": et_de(r), "dispositivo": r["segments"].get("device"), "gasto": mxn(r["metrics"].get("costMicros")),
        "imp": num(r["metrics"].get("impressions")), "clk": num(r["metrics"].get("clicks")),
        "conv": num(r["metrics"].get("conversions"))} for r in raw["dispositivo_30d"] or []]
    out["dia_hora_30d"] = [{
        "camp": et_de(r), "dia": r["segments"].get("dayOfWeek"), "hora": num(r["segments"].get("hour")),
        "gasto": mxn(r["metrics"].get("costMicros")), "imp": num(r["metrics"].get("impressions")),
        "clk": num(r["metrics"].get("clicks")), "conv": num(r["metrics"].get("conversions"))}
        for r in raw["dia_hora_30d"] or []]

    # --- config anexa por campana: negativos, horario, geo, assets
    for r in raw["negativos_campana"] or []:
        et = et_de(r)
        if et in camp:
            k = r["campaignCriterion"]["keyword"]
            camp[et]["negativos"].append({"kw": k["text"], "tipo": k.get("matchType")})
    for r in raw["horario_anuncios"] or []:
        et = et_de(r)
        if et in camp:
            s = r["campaignCriterion"]["adSchedule"]
            camp[et]["horario"].append({"dia": s.get("dayOfWeek"), "de": num(s.get("startHour")),
                                        "a": num(s.get("endHour")), "ajuste": r["campaignCriterion"].get("bidModifier")})
    nombres_geo = raw.get("geo_nombres") or {}
    for r in raw["geo_objetivos"] or []:
        et = et_de(r)
        gid = id_de_recurso(r["campaignCriterion"]["location"]["geoTargetConstant"])
        if et in camp:
            camp[et]["geo"].append({"id": gid, "nombre": nombres_geo.get(gid),
                                    "negativo": r["campaignCriterion"].get("negative", False),
                                    "ajuste": r["campaignCriterion"].get("bidModifier")})
    for r in raw["assets_campana"] or []:
        et = et_de(r)
        if et not in camp:
            continue
        a, ca = r["asset"], r["campaignAsset"]
        item = {"id": a["id"], "estado": ca.get("status"), "aprobacion": a.get("policySummary", {}).get("approvalStatus")}
        if ca.get("fieldType") == "SITELINK":
            item["texto"] = a.get("sitelinkAsset", {}).get("linkText")
            item["url"] = (a.get("finalUrls") or [None])[0]
            camp[et]["sitelinks"].append(item)
        elif ca.get("fieldType") == "CALLOUT":
            item["texto"] = a.get("calloutAsset", {}).get("calloutText")
            camp[et]["callouts"].append(item)
        else:
            item["tipo"] = ca.get("fieldType")
            camp[et]["assets_otros"].append(item)
    out["campanas"] = camp

    # --- change events con resumen legible; las rachas (misma hora:minuto, tipo, operacion, usuario y
    #     campana) se colapsan en una entrada con n y hasta 8 detalles: un alta masiva de 50 keywords
    #     no merece 50 renglones en el panel
    cambios = []
    for r in raw["cambios_28d"] or []:
        e = r["changeEvent"]
        cid = id_de_recurso(e.get("campaign"))
        et = por_id.get(cid, etiqueta(cid) if cid else None)
        de, a, resumen = resume_cambio(e)
        cambios.append({
            "fecha": (e.get("changeDateTime") or "")[:19], "quien": e.get("userEmail"), "cliente": e.get("clientType"),
            "camp": et, "tipo": e.get("changeResourceType"), "operacion": e.get("resourceChangeOperation"),
            "de": de, "a": a, "resumen": resumen})
    colapsados = []
    for ch in cambios:
        u = colapsados[-1] if colapsados else None
        llave = (ch["fecha"][:16], ch["tipo"], ch["operacion"], ch["quien"], ch["camp"])
        if u and u["_llave"] == llave and ch["tipo"] != "CAMPAIGN_BUDGET":
            u["n"] += 1
            if len(u["detalles"]) < 8:
                u["detalles"].append(ch["resumen"])
            continue
        nuevo = dict(ch)
        nuevo["_llave"] = llave
        nuevo["n"] = 1
        nuevo["detalles"] = [ch["resumen"]]
        colapsados.append(nuevo)
    for u in colapsados:
        del u["_llave"]
        if u["n"] > 1:
            u["resumen"] = f"{u['n']} cambios: " + u["detalles"][0] + ("..." if u["n"] > 1 else "")
    out["cambios_28d"] = colapsados
    out["cambios_28d_total"] = len(cambios)

    out["recomendaciones"] = [{
        "tipo": r["recommendation"].get("type"),
        "camp": por_id.get(id_de_recurso(r["recommendation"].get("campaign")), None)}
        for r in raw["recomendaciones"] or []]
    out["geo_rendimiento_30d"] = [{
        "camp": et_de(r), "pais_id": r["geographicView"].get("countryCriterionId"),
        "tipo_ubicacion": r["geographicView"].get("locationType"), "gasto": mxn(r["metrics"].get("costMicros")),
        "clk": num(r["metrics"].get("clicks")), "conv": num(r["metrics"].get("conversions")),
        "imp": num(r["metrics"].get("impressions"))} for r in raw["geo_rendimiento_30d"] or []]
    return out


# ----------------------------------------------------------------------------------
# GA4 REST v1beta con JWT RS256 (cuenta de servicio)
# ----------------------------------------------------------------------------------
def b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def token_ga4(sa):
    now = int(time.time())
    hdr = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claims = b64url(json.dumps({
        "iss": sa["client_email"], "scope": "https://www.googleapis.com/auth/analytics.readonly",
        "aud": sa["token_uri"], "iat": now, "exp": now + 3600}).encode())
    key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
    firma = key.sign(f"{hdr}.{claims}".encode(), padding.PKCS1v15(), hashes.SHA256())
    jwt = f"{hdr}.{claims}.{b64url(firma)}"
    data = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": jwt}).encode()
    with urllib.request.urlopen(urllib.request.Request(sa["token_uri"], data=data), timeout=30) as r:
        return json.loads(r.read())["access_token"]


def ga4_run(tok, body):
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{GA4_PROPERTY}:runReport"
    body = dict(body)
    body.setdefault("limit", 100000)
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        res = json.loads(r.read())
    dims = [d["name"] for d in res.get("dimensionHeaders", [])]
    mets = [m["name"] for m in res.get("metricHeaders", [])]
    filas = []
    for row in res.get("rows", []):
        d = {k: v["value"] for k, v in zip(dims, row.get("dimensionValues", []))}
        for k, v in zip(mets, row.get("metricValues", [])):
            d[k] = num(v["value"], 4)
        filas.append(d)
    return filas


def filtro_pagado():
    return {"filter": {"fieldName": "sessionSourceMedium", "stringFilter": {"matchType": "EXACT", "value": "google / cpc"}}}


def extrae_ga4(sa, f):
    tok = token_ga4(sa)

    def rango(a, b):
        return [{"startDate": a, "endDate": b}]

    def dim(*n):
        return [{"name": x} for x in n]

    def met(*n):
        return [{"name": x} for x in n]

    def landing_body(a, b):
        return {"dateRanges": rango(a, b), "dimensions": dim("landingPagePlusQueryString"),
                "metrics": met("sessions", "keyEvents", "engagementRate", "averageSessionDuration", "bounceRate"),
                "dimensionFilter": filtro_pagado(), "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}]}

    g = {"propiedad": GA4_PROPERTY, "zona_horaria": "America/Mexico_City"}
    g["diario_canal"] = ga4_run(tok, {
        "dateRanges": rango(f["ini120"], f["fin"]), "dimensions": dim("date", "sessionDefaultChannelGroup"),
        "metrics": met("sessions", "keyEvents", "totalUsers"), "orderBys": [{"dimension": {"dimensionName": "date"}}]})
    g["landings_pagadas_30d"] = ga4_run(tok, landing_body(f["ini30"], f["fin"]))
    g["landings_pagadas_30d_prev"] = ga4_run(tok, landing_body(f["ini30prev"], f["fin30prev"]))
    g["eventos_landing_pagado_30d"] = ga4_run(tok, {
        "dateRanges": rango(f["ini30"], f["fin"]), "dimensions": dim("landingPagePlusQueryString", "eventName"),
        "metrics": met("eventCount", "sessions"),
        "dimensionFilter": {"andGroup": {"expressions": [filtro_pagado(), {"filter": {
            "fieldName": "eventName",
            "inListFilter": {"values": ["clic_whatsapp", "agendar_cita", "llamada", "agenda_modal_open"]}}}]}}})
    g["dispositivo_30d"] = ga4_run(tok, {
        "dateRanges": rango(f["ini30"], f["fin"]), "dimensions": dim("deviceCategory", "sessionDefaultChannelGroup"),
        "metrics": met("sessions", "keyEvents")})
    g["campana_diario_pagado"] = ga4_run(tok, {
        "dateRanges": rango(f["ini120"], f["fin"]), "dimensions": dim("sessionCampaignName", "date"),
        "metrics": met("sessions", "keyEvents"), "dimensionFilter": filtro_pagado(),
        "orderBys": [{"dimension": {"dimensionName": "date"}}]})
    return g


# ----------------------------------------------------------------------------------
# Estadistica sin numpy: Poisson, mediana, EWMA
# ----------------------------------------------------------------------------------
def poisson_cdf(k, lam):
    """P(X <= k) para X ~ Poisson(lam), en espacio log para no desbordar."""
    if lam <= 0:
        return 1.0
    k = int(math.floor(k))
    if k < 0:
        return 0.0
    s = 0.0
    for i in range(k + 1):
        s += math.exp(-lam + i * math.log(lam) - math.lgamma(i + 1))
    return min(1.0, s)


def _biseccion_decreciente(fn, lo, hi, objetivo, it=60):
    """fn decreciente en lambda; devuelve lambda con fn(lambda) = objetivo."""
    for _ in range(it):
        mid = (lo + hi) / 2
        if fn(mid) > objetivo:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def banda_poisson_tasa(n, nivel=0.90):
    """Intervalo exacto (Garwood) al 90% para la tasa lambda dado un conteo observado n: colas de 5% cada una.
    lo: P(X >= n | lo) = 5%   (1 - cdf(n-1, L) crece con L, asi que se bisecciona su negativo)
    hi: P(X <= n | hi) = 5%   (cdf(n, L) decrece con L)"""
    a = (1 - nivel) / 2
    n = max(0, int(round(n)))
    if n == 0:
        lo = 0.0
    else:
        lo = _biseccion_decreciente(lambda L: -(1 - poisson_cdf(n - 1, L)), 0.0, float(n), -a)
    hi = _biseccion_decreciente(lambda L: poisson_cdf(n, L), float(n), float(n) + 10 * math.sqrt(n + 1) + 20, a)
    return [round(lo, 2), round(hi, 2)]


def cuantiles_poisson(lam, nivel=0.90):
    """Cuantiles 5% y 95% de un conteo futuro X ~ Poisson(lam)."""
    a = (1 - nivel) / 2
    if lam <= 0:
        return [0, 0]
    k_lo = k_hi = None
    k = 0
    tope = int(lam + 10 * math.sqrt(lam) + 20)
    while k <= tope:
        c = poisson_cdf(k, lam)
        if k_lo is None and c >= a:
            k_lo = k
        if c >= 1 - a:
            k_hi = k
            break
        k += 1
    return [k_lo or 0, k_hi if k_hi is not None else tope]


def mediana(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def ewma(xs, alpha=EWMA_ALPHA):
    nivel = None
    for x in xs:
        nivel = x if nivel is None else alpha * x + (1 - alpha) * nivel
    return nivel


def div(a, b, nd=2):
    return round(a / b, nd) if b else None


# ----------------------------------------------------------------------------------
# Bloque derivado
# ----------------------------------------------------------------------------------
def agrega(filas):
    """Suma metricas y agrega IS/LB/LR por impresiones elegibles (imp/IS), no por promedio simple.
    Razon: el promedio simple de IS diario da el mismo peso a un dia de 10 impresiones que a uno de 400."""
    t = {"gasto": 0.0, "imp": 0, "clk": 0, "conv": 0.0, "valor": 0.0, "dias": 0}
    eleg = lb = lr = top = 0.0
    for f in filas:
        t["gasto"] += f["gasto"]
        t["imp"] += f["imp"]
        t["clk"] += f["clk"]
        t["conv"] += f["conv"]
        t["valor"] += f.get("valor", 0) or 0
        t["dias"] += 1
        if f.get("is") and f["imp"]:
            e = f["imp"] / f["is"]
            eleg += e
            lb += (f.get("lb") or 0) * e
            lr += (f.get("lr") or 0) * e
            top += (f.get("top") or 0) * e
    t["gasto"] = round(t["gasto"], 2)
    t["conv"] = round(t["conv"], 2)
    t["valor"] = round(t["valor"], 2)
    t["cpc"] = div(t["gasto"], t["clk"])
    t["ctr"] = div(t["clk"], t["imp"], 4)
    t["conv_clic"] = div(t["conv"], t["clk"], 4)
    t["costo_contacto"] = div(t["gasto"], t["conv"])
    t["is"] = div(t["imp"], eleg, 4) if eleg else None
    t["lb"] = div(lb, eleg, 4) if eleg else None
    t["lr"] = div(lr, eleg, 4) if eleg else None
    t["top"] = div(top, eleg, 4) if eleg else None
    if t["gasto"] > 0:
        b = banda_poisson_tasa(t["conv"])
        t["banda_contactos"] = b
        t["banda_costo_contacto"] = [div(t["gasto"], b[1]), div(t["gasto"], b[0]) if b[0] > 0 else None]
    return t


def lunes(d):
    return d - timedelta(days=d.weekday())


def fecha(s):
    return date.fromisoformat(s)


def deriva(ads, f):
    fin = fecha(f["fin"])
    ini30, ini30p, fin30p = fecha(f["ini30"]), fecha(f["ini30prev"]), fecha(f["fin30prev"])
    ult_lunes_completo = lunes(fin) if fin.weekday() == 6 else lunes(fin) - timedelta(days=7)
    camps = list(ads["campanas"].keys())
    por_camp = {c: [x for x in ads["diario"] if x["camp"] == c] for c in camps}
    D = {"metodo": {}, "campanas": {}, "cuenta": {}, "alertas": []}

    def semanal(filas):
        """Semanas de lunes a domingo; solo semanas completas hasta 'fin'."""
        grupos = {}
        for x in filas:
            l = lunes(fecha(x["fecha"]))
            if l > ult_lunes_completo:
                continue
            grupos.setdefault(l, []).append(x)
        sem = []
        for l in sorted(grupos):
            a = agrega(grupos[l])
            a["semana"] = l.isoformat()
            sem.append(a)
        return sem

    def en(filas, a, b):
        return [x for x in filas if a <= fecha(x["fecha"]) <= b]

    D["cuenta"]["semanal"] = semanal(ads["cuenta_diario"])
    D["cuenta"]["u30"] = agrega(en(ads["cuenta_diario"], ini30, fin))
    D["cuenta"]["p30"] = agrega(en(ads["cuenta_diario"], ini30p, fin30p))
    D["cuenta"]["u7"] = agrega(en(ads["cuenta_diario"], fin - timedelta(days=6), fin))
    D["cuenta"]["presupuesto_dia_total"] = round(sum(c["presupuesto_dia"] for c in ads["campanas"].values()
                                                     if c["estado"] == "ENABLED"), 2)

    for c in camps:
        filas = por_camp[c]
        cfg = ads["campanas"][c]
        sem = semanal(filas)
        u30 = agrega(en(filas, ini30, fin))
        p30 = agrega(en(filas, ini30p, fin30p))
        u7 = agrega(en(filas, fin - timedelta(days=6), fin))

        def delta(k):
            a, b = u30.get(k), p30.get(k)
            return round((a - b) / b, 3) if (a is not None and b) else None
        comparacion = {k: delta(k) for k in ("gasto", "clk", "conv", "cpc", "conv_clic", "costo_contacto", "is")}

        # pronostico: EWMA de las ultimas 8 semanas completas, 4 semanas planas, banda Poisson sobre la media
        base = sem[-SEMANAS_BASE:]
        pron = None
        if len(base) >= 3:
            conv_fc = ewma([s["conv"] for s in base])
            gasto_fc = ewma([s["gasto"] for s in base])
            clk_fc = ewma([s["clk"] for s in base])
            q = cuantiles_poisson(conv_fc)
            semanas = []
            for i in range(1, SEMANAS_PRONOSTICO + 1):
                semanas.append({"semana": (ult_lunes_completo + timedelta(days=7 * i)).isoformat(),
                                "contactos": round(conv_fc, 1), "banda_contactos": q,
                                "gasto": round(gasto_fc, 0), "clk": round(clk_fc, 0),
                                "costo_contacto": div(gasto_fc, conv_fc),
                                "banda_costo_contacto": [div(gasto_fc, q[1]), div(gasto_fc, q[0]) if q[0] else None]})
            # la semana en curso (incompleta) va aparte para que el panel compare "va en X" contra lo previsto
            en_curso = en(filas, ult_lunes_completo + timedelta(days=7), fin)
            curso = None
            if en_curso:
                ag = agrega(en_curso)
                curso = {"semana": (ult_lunes_completo + timedelta(days=7)).isoformat(), "dias": ag["dias"],
                         "contactos": ag["conv"], "gasto": ag["gasto"], "clk": ag["clk"],
                         "contactos_esperados_a_la_fecha": round(conv_fc * ag["dias"] / 7, 1)}
            pron = {"semanas": semanas, "semana_en_curso": curso, "semanas_base": len(base), "alpha": EWMA_ALPHA,
                    "contactos_4sem": round(conv_fc * SEMANAS_PRONOSTICO, 0),
                    "banda_contactos_4sem": cuantiles_poisson(conv_fc * SEMANAS_PRONOSTICO),
                    "gasto_4sem": round(gasto_fc * SEMANAS_PRONOSTICO, 0), "marca": "[Heuristica]"}

        # curva presupuesto -> contactos [Heuristica]
        curva = None
        if u30["gasto"] > 0 and u30.get("is") and cfg["presupuesto_dia"] > 0:
            IS, LB = u30["is"], u30.get("lb") or 0
            B0 = cfg["presupuesto_dia"]
            dias = u30["dias"] or 30
            gasto_tope = u30["gasto"] * min(1.0, IS + LB) / IS  # lo que se gastaria si el presupuesto no cortara
            cont_max = u30["conv"] / IS                         # cota absoluta: 100% de impresiones
            puntos = []
            for m in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0):
                tope_m = m * B0 * dias
                gasto_m = min(tope_m, gasto_tope) if m >= 1 else min(tope_m, u30["gasto"])
                cont_m = min(u30["conv"] * gasto_m / u30["gasto"], cont_max)
                puntos.append({"x": m, "presupuesto_dia": round(m * B0, 0), "gasto_30d": round(gasto_m, 0),
                               "contactos_30d": round(cont_m, 1), "costo_contacto": div(gasto_m, cont_m)})
            curva = {"puntos": puntos, "contactos_max_teorico": round(cont_max, 1),
                     "contactos_recuperables_por_presupuesto": round(u30["conv"] * min(1.0, IS + LB) / IS - u30["conv"], 1),
                     "perdida_dominante": "presupuesto" if LB > (u30.get("lr") or 0) else "ranking",
                     "marca": "[Heuristica]"}

        # --- alertas por campana
        alertas = []
        if cfg["estado"] == "ENABLED":
            for x in en(filas, fin - timedelta(days=6), fin):
                if cfg["presupuesto_dia"] and x["gasto"] > ALERTA_GASTO_X_PRESUPUESTO * cfg["presupuesto_dia"]:
                    alertas.append({"nivel": "media", "regla": "gasto_diario", "camp": c,
                                    "texto": f"{c}: el {x['fecha']} gasto ${x['gasto']:,.0f}, mas de {ALERTA_GASTO_X_PRESUPUESTO}x el presupuesto diario (${cfg['presupuesto_dia']:,.0f}). Google puede gastar hasta 2x en un dia; revisar si se repite."})
            racha = 0
            for x in sorted(en(filas, fin - timedelta(days=13), fin), key=lambda r: r["fecha"]):
                racha = racha + 1 if (x.get("lb") or 0) > ALERTA_LOST_BUDGET else 0
                if racha == ALERTA_LOST_BUDGET_DIAS:
                    alertas.append({"nivel": "media", "regla": "lost_budget", "camp": c,
                                    "texto": f"{c}: {ALERTA_LOST_BUDGET_DIAS} dias seguidos perdiendo mas del {int(ALERTA_LOST_BUDGET * 100)}% de impresiones por presupuesto (hasta el {x['fecha']}). El tope diario esta cortando demanda."})
                    break
            if len(sem) >= 4:
                ult, prev = sem[-1], sem[-SEMANAS_BASE - 1:-1]
                med_cc = mediana([s["conv_clic"] for s in prev if s["clk"] >= ALERTA_MIN_CLICS_SEMANA])
                if ult["clk"] >= ALERTA_MIN_CLICS_SEMANA and med_cc and ult["conv_clic"] is not None and ult["conv_clic"] < 0.5 * med_cc:
                    alertas.append({"nivel": "alta", "regla": "conv_clic", "camp": c,
                                    "texto": f"{c}: la semana del {ult['semana']} convirtio {ult['conv_clic'] * 100:.1f}% de los clics, menos de la mitad de lo normal ({med_cc * 100:.1f}%). Revisar landing, medicion (GTM) y terminos de busqueda."})
                med_cpc = mediana([s["cpc"] for s in prev if s["clk"] >= ALERTA_MIN_CLICS_SEMANA])
                if ult["clk"] >= ALERTA_MIN_CLICS_SEMANA and med_cpc and ult["cpc"] and ult["cpc"] > (1 + ALERTA_CPC_SUBIDA) * med_cpc:
                    alertas.append({"nivel": "media", "regla": "cpc", "camp": c,
                                    "texto": f"{c}: el clic costo ${ult['cpc']:.0f} la semana del {ult['semana']}, {int((ult['cpc'] / med_cpc - 1) * 100)}% mas que lo normal (${med_cpc:.0f}). Puede ser competencia nueva o una puja mas agresiva."})
        for ch in ads["cambios_28d"]:
            if ch["camp"] == c and ch["tipo"] == "CAMPAIGN_BUDGET" and ch["de"] is not None:
                alertas.append({"nivel": "info", "regla": "cambio_presupuesto", "camp": c,
                                "texto": f"{c}: {ch['fecha'][:10]} {ch['resumen']} ({ch['quien'] or 'sin usuario'}, {ch['cliente']})."})
        semaforo = "rojo" if any(a["nivel"] == "alta" for a in alertas) else (
            "amarillo" if any(a["nivel"] == "media" for a in alertas) else "verde")
        if cfg["estado"] != "ENABLED":
            semaforo = "gris"
        D["campanas"][c] = {"semanal": sem, "u30": u30, "p30": p30, "u7": u7, "comparacion_30d": comparacion,
                            "pronostico": pron, "curva_presupuesto": curva, "alertas": alertas, "semaforo": semaforo}
        D["alertas"].extend(alertas)

    # pronostico de cuenta = suma de campanas activas con pronostico
    act = [D["campanas"][c]["pronostico"] for c in camps
           if D["campanas"][c]["pronostico"] and ads["campanas"][c]["estado"] == "ENABLED"]
    if act:
        conv4 = sum(p["contactos_4sem"] for p in act)
        D["cuenta"]["pronostico_4sem"] = {"contactos": conv4, "banda_contactos": cuantiles_poisson(conv4),
                                          "gasto": sum(p["gasto_4sem"] for p in act), "marca": "[Heuristica]"}
    D["metodo"] = {
        "semanas": "semanas de lunes a domingo; solo semanas completas hasta la fecha fin; IS/LB/LR agregados por impresiones elegibles (imp/IS), no por promedio simple",
        "banda_contactos": "intervalo exacto de Poisson (Garwood) al 90% para la tasa dado el conteo observado; costo por contacto = gasto / banda invertida",
        "pronostico": f"media ponderada exponencial (alpha={EWMA_ALPHA}) de las ultimas {SEMANAS_BASE} semanas completas, proyectada plana {SEMANAS_PRONOSTICO} semanas; banda = cuantiles 5%-95% de Poisson sobre la media pronosticada. No modela estacionalidad ni cambios de presupuesto. [Heuristica]",
        "curva_presupuesto": "contactos proporcionales al gasto hasta recuperar la parte perdida por presupuesto (IS+LB); cota absoluta contactos/IS; la parte perdida por ranking no se compra con presupuesto. [Heuristica]",
        "alertas": {"gasto_diario": f">{ALERTA_GASTO_X_PRESUPUESTO}x presupuesto en los ultimos 7 dias",
                    "lost_budget": f">{int(ALERTA_LOST_BUDGET * 100)}% perdido por presupuesto {ALERTA_LOST_BUDGET_DIAS} dias seguidos (ventana 14 d)",
                    "conv_clic": f"semana completa mas reciente < 50% de la mediana de las {SEMANAS_BASE} previas (min {ALERTA_MIN_CLICS_SEMANA} clics)",
                    "cpc": f"CPC semanal > +{int(ALERTA_CPC_SUBIDA * 100)}% sobre la mediana de las {SEMANAS_BASE} semanas previas",
                    "cambio_presupuesto": f"cualquier cambio de presupuesto en change_event ({DIAS_CHANGE} d)"},
        "marcas": "las cifras de Ads y GA4 son [Documentado] (API); pronostico y curva son [Heuristica]",
    }
    return D


# ----------------------------------------------------------------------------------
# Cifrado: PBKDF2-SHA256 (200000 it, salt 16 B) -> AES-256-GCM (iv 12 B), ct||tag como WebCrypto
# ----------------------------------------------------------------------------------
def cifra(texto_json, clave):
    # Se comprime ANTES de cifrar (deflate con cabecera zlib, que es lo que entiende
    # DecompressionStream('deflate') en el navegador). Razon: sin comprimir, cada corrida
    # diaria sumaba ~450 KB al historial del repo publico (~160 MB/ano).
    salt, iv = secrets.token_bytes(16), secrets.token_bytes(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=KDF_ITER)
    k = kdf.derive(clave.encode("utf-8"))
    claro = zlib.compress(texto_json.encode("utf-8"), 9)
    ct = AESGCM(k).encrypt(iv, claro, None)  # cryptography anexa el tag de 16 B al final
    return {"v": VERSION, "kdf": "PBKDF2-SHA256", "iter": KDF_ITER, "comp": "deflate",
            "salt": base64.b64encode(salt).decode(), "iv": base64.b64encode(iv).decode(),
            "ct": base64.b64encode(ct).decode()}


def descifra(enc, clave):
    """Inverso de cifra(); acepta v1 (sin comprimir) y v2 (deflate). Se usa para heredar
    el bloque de estrategia del datos.enc anterior cuando el build corre en Actions."""
    salt, iv, ct = (base64.b64decode(enc[k]) for k in ("salt", "iv", "ct"))
    k = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=int(enc["iter"])).derive(clave.encode("utf-8"))
    claro = AESGCM(k).decrypt(iv, ct, None)
    if enc.get("comp") == "deflate":
        claro = zlib.decompress(claro)
    return json.loads(claro.decode("utf-8"))


# La estrategia (texto del asesor: decisiones, gates, doctrina) contiene cifras de gasto, asi que
# NO vive en claro en el repo publico. Fuente local: _internal/panel-ads/estrategia.json (gitignorado).
# En Actions ese archivo no existe: se hereda el bloque del datos.enc anterior para no borrarlo.
RUTA_ESTRATEGIA = REPO / "_internal" / "panel-ads" / "estrategia.json"


def carga_estrategia(clave):
    if RUTA_ESTRATEGIA.exists():
        try:
            e = json.loads(RUTA_ESTRATEGIA.read_text(encoding="utf-8"))
            log(f"Estrategia: local ({RUTA_ESTRATEGIA.name}, generado {e.get('generado')})")
            return e
        except Exception as ex:
            log(f"  [aviso] estrategia local ilegible: {str(ex)[:200]}")
    ruta_prev = DIR_SALIDA / "datos.enc"
    if ruta_prev.exists():
        try:
            prev = descifra(json.loads(ruta_prev.read_text(encoding="utf-8")), clave)
            e = prev.get("estrategia")
            if e:
                log(f"Estrategia: heredada del datos.enc anterior (generado {e.get('generado')})")
                return e
        except Exception as ex:
            log(f"  [aviso] no se pudo heredar la estrategia anterior: {str(ex)[:200]}")
    log("Estrategia: ninguna (la pagina mostrara 'sin estrategia cargada')")
    return None


# ----------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------
def ventanas(hoy):
    fin = hoy - timedelta(days=1)  # el dia en curso esta incompleto en Ads y GA4
    return {
        "hoy": hoy.isoformat(), "fin": fin.isoformat(),
        "ini120": (fin - timedelta(days=DIAS_SERIE - 1)).isoformat(),
        "ini30": (fin - timedelta(days=29)).isoformat(),
        "ini30prev": (fin - timedelta(days=59)).isoformat(), "fin30prev": (fin - timedelta(days=30)).isoformat(),
        "ini28": (hoy - timedelta(days=DIAS_CHANGE)).isoformat(),
    }


def main():
    ap = argparse.ArgumentParser(description="Genera datos.json (tmp), campana-ads/datos.enc y campana-ads/meta.json")
    ap.add_argument("--json", help="ruta del datos.json en claro (por defecto en el tmp del sistema; NUNCA dentro del repo)")
    ap.add_argument("--sin-ga4", action="store_true", help="omite GA4 (pruebas)")
    ap.add_argument("--hoy", help="fecha de corte YYYY-MM-DD (pruebas; por defecto hoy en CDMX)")
    args = ap.parse_args()

    hoy = fecha(args.hoy) if args.hoy else datetime.now(TZ_CDMX).date()
    f = ventanas(hoy)
    log(f"Ventana: {f['ini120']}..{f['fin']} (hoy {f['hoy']} CDMX)")
    clave = clave_panel()  # falla temprano si no hay clave: no tiene caso consultar APIs
    ruta_json = Path(args.json) if args.json else Path(tempfile.gettempdir()) / "panel-ads" / "datos.json"
    if REPO in ruta_json.resolve().parents:
        raise SystemExit("datos.json en claro no puede vivir dentro del repo: " + str(ruta_json))

    # --- Ads
    cfg, origen = credenciales_ads()
    log(f"Ads: credenciales por {origen}")
    try:
        ads = Ads(cfg)
    except Exception as e:
        raise SystemExit(f"Ads: no se pudo obtener access token: {str(e)[:300]}")
    raw = {}
    for nombre, q in consultas_ads(f).items():
        raw[nombre] = ads.search(nombre, q, nuclear=nombre in ("campanas_config", "campanas_diario"))
    geo_ids = sorted({id_de_recurso(r["campaignCriterion"]["location"]["geoTargetConstant"])
                      for r in raw["geo_objetivos"] or []})
    raw["geo_nombres"] = {}
    if geo_ids:
        gq = ("SELECT geo_target_constant.id, geo_target_constant.canonical_name FROM geo_target_constant "
              f"WHERE geo_target_constant.id IN ({', '.join(geo_ids)})")
        for r in ads.search("geo_nombres", gq) or []:
            raw["geo_nombres"][r["geoTargetConstant"]["id"]] = r["geoTargetConstant"].get("canonicalName")
    datos_ads = normaliza_ads(raw)
    datos_ads["errores"] = ads.errores
    if not datos_ads["diario"]:
        raise SystemExit("Ads: la serie diaria vino vacia; no se sobreescribe datos.enc")

    # --- GA4 (tolerante)
    ga4 = None
    alertas_extra = []
    if not args.sin_ga4:
        sa, origen_ga4 = credenciales_ga4()
        if sa is None:
            log(f"  [aviso] GA4 omitido: {origen_ga4}")
            alertas_extra.append({"nivel": "media", "regla": "ga4", "camp": None,
                                  "texto": "GA4 sin credenciales utilizables; la seccion de GA4 no se actualizo. Detalle: " + origen_ga4})
        else:
            try:
                log(f"GA4: credenciales por {origen_ga4}")
                ga4 = extrae_ga4(sa, f)
                log(f"  GA4 ok: {len(ga4['diario_canal'])} filas diario_canal")
            except Exception as e:
                detalle = str(e)[:300]
                if isinstance(e, urllib.error.HTTPError):
                    detalle = f"HTTP {e.code}: " + e.read().decode("utf-8", "replace")[:300]
                log(f"  [aviso] GA4 fallo: {detalle}")
                alertas_extra.append({"nivel": "media", "regla": "ga4", "camp": None,
                                      "texto": "GA4 no respondio en esta corrida; las cifras de GA4 del panel no estan actualizadas. Detalle: " + detalle})

    derivado = deriva(datos_ads, f)
    derivado["alertas"].extend(alertas_extra)
    generado = datetime.now(timezone.utc).isoformat(timespec="seconds")
    datos = {
        "version": VERSION, "generado": generado, "cuenta": CID, "moneda": "MXN",
        "ventana": {"inicio": f["ini120"], "fin": f["fin"], "u30": [f["ini30"], f["fin"]],
                    "p30": [f["ini30prev"], f["fin30prev"]], "cambios_desde": f["ini28"]},
        "etiquetas": {v: k for k, v in ETIQUETAS.items()},
        "ads": datos_ads, "ga4": ga4, "derivado": derivado,
        "estrategia": carga_estrategia(clave),
    }
    texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))

    ruta_json.parent.mkdir(parents=True, exist_ok=True)
    ruta_json.write_text(texto, encoding="utf-8")

    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    enc = cifra(texto, clave)
    (DIR_SALIDA / "datos.enc").write_text(json.dumps(enc, separators=(",", ":")), encoding="utf-8")
    meta = {"generado": generado, "version": VERSION, "ventana": f"{f['ini120']}..{f['fin']}",
            "ga4": ga4 is not None, "consultas_con_error": len(ads.errores)}
    (DIR_SALIDA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    u30 = derivado["cuenta"]["u30"]
    log(f"OK datos.json {len(texto.encode('utf-8')):,} B -> {ruta_json}")
    log(f"OK datos.enc  {os.path.getsize(DIR_SALIDA / 'datos.enc'):,} B ; meta.json escrito")
    if EN_CI:
        # Log publico: solo frescura y estados, sin una sola cifra de dinero o contactos.
        log(f"Control: campanas {', '.join(f'{c} {v['estado']}' for c, v in datos_ads['campanas'].items())}"
            + f" | alertas {len(derivado['alertas'])} | ga4 {'ok' if ga4 else 'null'} | errores Ads {len(ads.errores)}")
    else:
        log(f"Control 30d: gasto ${u30['gasto']:,.0f} | conv {u30['conv']} | presupuestos "
            + ", ".join(f"{c} ${v['presupuesto_dia']:.0f}" for c, v in datos_ads['campanas'].items())
            + f" | alertas {len(derivado['alertas'])} | ga4 {'ok' if ga4 else 'null'} | errores Ads {len(ads.errores)}")


if __name__ == "__main__":
    main()
