import re
import json
from urllib.parse import urlparse
from conn4_shared import base_origin_from_url, extract_resource_urls_from_html, extract_urls_from_js_text, extract_tokens_from_html, choose_authorize_endpoint, safe_url
from html_form_parser import FormParser

def normalize_perf_logs(logs):
    items = []
    for entry in logs or []:
        try:
            msg = json.loads(entry.get('message') or '{}')
            m = msg.get('message') or {}
            method = m.get('method')
            params = m.get('params') or {}
            if method in ('Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished'):
                it = {"event": method}
                if method == 'Network.requestWillBeSent':
                    req = params.get('request') or {}
                    it["url"] = req.get('url') or params.get('documentURL') or ''
                    it["method"] = (req.get('method') or '').upper()
                    it["initiator"] = params.get('initiator') or {}
                elif method == 'Network.responseReceived':
                    res = params.get('response') or {}
                    it["status"] = res.get('status')
                    it["mimeType"] = res.get('mimeType')
                items.append(it)
        except Exception:
            pass
    return items

def extract_assets(html, current_url, js_bodies):
    base = base_origin_from_url(current_url or "")
    urls = []
    for u in extract_resource_urls_from_html(html or "", base):
        urls.append(u)
    for _, body in js_bodies or []:
        for u in extract_urls_from_js_text(body or "", base):
            urls.append(u)
    urls = list(dict.fromkeys(urls))
    filt = []
    for u in urls:
        p = urlparse(u)
        path = p.path or ""
        if re.search(r"\.(png|jpg|jpeg|gif|webp|svg)$", path, flags=re.IGNORECASE):
            continue
        filt.append(u)
    cats = {"scripts": [], "links": [], "iframes": [], "cache": [], "admon": [], "scenes": [], "static": []}
    for u in filt:
        path = urlparse(u).path or ""
        if "/cache/" in path:
            cats["cache"].append(u)
        elif "/admon/" in path:
            cats["admon"].append(u)
        elif "/scenes/" in path:
            cats["scenes"].append(u)
        elif re.search(r"\.(js)$", path, flags=re.IGNORECASE):
            cats["scripts"].append(u)
        elif re.search(r"\.(css|ico|woff|woff2|ttf|otf|eot)$", path, flags=re.IGNORECASE):
            cats["links"].append(u)
        else:
            cats["static"].append(u)
    for k in list(cats.keys()):
        cats[k] = list(dict.fromkeys(cats[k]))
    return cats

def find_time_call(events):
    cidx = None
    tidx = None
    for i, ev in enumerate(events or []):
        if (ev.get("event") or "").lower() == "network.requestwillsent":
            url = ev.get("url") or ""
            m = (ev.get("method") or "").upper()
            if "create-session" in url and m == "POST":
                cidx = i
            if "/_time" in url or re.search(r"/time/[^\\s]+", url):
                if tidx is None:
                    tidx = i
    initiators = []
    if tidx is not None:
        ini = (events[tidx] or {}).get("initiator") or {}
        stack = (ini.get("stack") or {}).get("callFrames") or ini.get("stackTrace") or []
        for fr in stack or []:
            u = (fr.get('url') if isinstance(fr, dict) else None) or ''
            if u:
                initiators.append(u)
    return {
        "url": (events[tidx] or {}).get("url") if tidx is not None else None,
        "after_create_session": bool(cidx is not None and tidx is not None and tidx > cidx),
        "initiators": list(dict.fromkeys(initiators))
    }

def build_schema(page_html, current_url, perf_events, js_bodies, cookies):
    base = base_origin_from_url(current_url or "")
    tokens = extract_tokens_from_html(page_html or "")
    fp = FormParser()
    try:
        fp.feed(page_html or "")
    except Exception:
        pass
    forms = []
    for f in fp.forms:
        forms.append({
            "method": f.method,
            "action": f.action,
            "inputs": [{"name": name, "value": value} for name, value in f.inputs],
        })
    assets = extract_assets(page_html or "", current_url or "", js_bodies or [])
    ident = None
    create_session = None
    for ev in perf_events or []:
        if (ev.get("event") or "").lower() == "network.requestwillsent":
            u = ev.get("url") or ""
            m = (ev.get("method") or "").upper()
            if "/ident" in u and m == "GET":
                ident = u
            if "create-session" in u and m == "POST":
                create_session = u
    authorize_candidates = []
    try:
        cand = choose_authorize_endpoint(page_html or "", current_url or "")
        if cand:
            authorize_candidates.append(cand)
    except Exception:
        pass
    time_call = find_time_call(perf_events or [])
    page = {"url": current_url, "title": "", "forms": forms, "tokens": tokens}
    try:
        page["title"] = ""
    except Exception:
        pass
    schema = {
        "portal": {
            "origin": base,
            "host": urlparse(current_url or "").netloc or "",
            "site_id": tokens.get("siteId") or tokens.get("site_id"),
            "client_ip": tokens.get("clientIp") or tokens.get("client_ip"),
            "client_mac": tokens.get("clientMac") or tokens.get("client_mac"),
            "signature": tokens.get("signature"),
            "loggedin": tokens.get("loggedin"),
            "remembered_mac": tokens.get("remembered_mac"),
        },
        "pages": [page],
        "resources": assets,
        "endpoints": {
            "ident": ident,
            "create_session": create_session,
            "authorize_candidates": authorize_candidates,
        },
        "network": {
            "events": perf_events,
            "time_call": time_call,
        },
        "flow": []
    }
    flow = []
    for ev in perf_events or []:
        e = (ev.get("event") or "").lower()
        if e == "network.requestwillsent":
            u = ev.get("url") or ""
            m = (ev.get("method") or "").upper()
            step = None
            if "msftconnecttest" in u:
                step = "redirect_msft"
            elif "/ident" in u and m == "GET":
                step = "ident_get"
            elif u and urlparse(u).netloc == urlparse(base).netloc and m == "GET":
                step = "base_get"
            elif "create-session" in u and m == "POST":
                step = "create_session"
            elif "/_time" in u:
                step = "time"
            elif any(x in u for x in ["registration", "free-login", "authenticate", "wbs"]):
                step = "authorize"
            if step:
                flow.append({"step": step, "url": safe_url(u), "method": m})
    schema["flow"] = flow
    return schema

