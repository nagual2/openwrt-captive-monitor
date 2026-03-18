import re
from urllib.parse import urlparse

def base_origin_from_url(u):
    try:
        p = urlparse(u or "")
        if p.scheme and p.netloc:
            return f"{p.scheme}://{p.netloc}"
    except Exception:
        pass
    return ""

def make_absolute(base, u):
    try:
        p = urlparse(u or "")
        if p.scheme:
            return u
        return f"{base}{u}"
    except Exception:
        return u

def extract_resource_urls_from_html(html, base_origin):
    try:
        urls = []
        for m in re.finditer(r"<script[^>]*src=['\"]([^'\"\s]+)['\"][^>]*>", html, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"<link[^>]*href=['\"]([^'\"\s]+)['\"][^>]*>", html, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"<img[^>]*src=['\"]([^'\"\s]+)['\"][^>]*>", html, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"<iframe[^>]*src=['\"]([^'\"\s]+)['\"][^>]*>", html, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/cache/[^'\"\s]+)['\"]", html, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/admon/[^'\"\s]+)['\"]", html, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/scenes/[^'\"\s]+)['\"]", html, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/_time(?:\?[^'\"\s]*)?)['\"]", html, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/time/[^'\"\s]+)['\"]", html, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/admon-assets/[^'\"\s]+)['\"]", html, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/ident(?:\?[^'\"\s]*)?)['\"]", html, flags=re.IGNORECASE):
            urls.append(m.group(1))
        out = []
        for u in urls:
            out.append(make_absolute(base_origin, u))
        return list(dict.fromkeys(out))
    except Exception:
        return []

def extract_urls_from_js_text(text, base_origin):
    try:
        urls = []
        for m in re.finditer(r"['\"](/cache/[^'\"\s]+)['\"]", text, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/admon/[^'\"\s]+)['\"]", text, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/scenes/[^'\"\s]+)['\"]", text, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/_time(?:\?[^'\"\s]*)?)['\"]", text, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/time/[^'\"\s]+)['\"]", text, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/admon-assets/[^'\"\s]+)['\"]", text, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/ident(?:\?[^'\"\s]*)?)['\"]", text, flags=re.IGNORECASE):
            urls.append(m.group(1))
        for m in re.finditer(r"['\"](/[^'\"\s]+\.(?:js|css|ico|png|jpg|jpeg|gif|webp|svg|woff|woff2|ttf|otf|eot))['\"]", text, flags=re.IGNORECASE):
            urls.append(m.group(1))
        out = []
        for u in urls:
            out.append(make_absolute(base_origin, u))
        return list(dict.fromkeys(out))
    except Exception:
        return []

def extract_tokens_from_html(html):
    tokens = {}
    try:
        for mm in re.finditer(r"<input[^>]*type=['\"]hidden['\"][^>]*name=['\"]([^'\"]+)['\"][^>]*value=['\"]([^'\"]*)['\"]", html, flags=re.IGNORECASE):
            n = mm.group(1)
            v = mm.group(2)
            nl = (n or "").lower()
            if nl in ("csrf","csrf_token","token","_token","nonce","_nonce","scene","tpl","wbs","wbs_scene","scene_id","tpl_id"):
                tokens[n] = v
        for mm in re.finditer(r"data-(csrf|csrf_token|token|nonce|scene|tpl)=['\"]([^'\"]*)['\"]", html, flags=re.IGNORECASE):
            n = mm.group(1)
            v = mm.group(2)
            tokens[n] = v
        for mm in re.finditer(r"(?:sessionStorage|localStorage)\s*\.\s*setItem\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]", html):
            n = mm.group(1)
            v = mm.group(2)
            if n and v and ("apiSessionId" in n or "paymentReturnProxyUrl" in n or "conn4-hotspot" in n):
                tokens[n] = v
    except Exception:
        pass
    return tokens

def collect_tokens_from_text(text):
    return extract_tokens_from_html(text)

def build_consent_body(qs, tokens, tariff="381", phpsessid=None):
    body = {
        "agree": "1",
        "accept": "1",
        "terms": "1",
        "policy": "1",
        "consent": "1",
        "tariff": tariff
    }
    if isinstance(qs, dict):
        for k, v in qs.items():
            if v is not None:
                body[k] = v
    if isinstance(tokens, dict):
        for k, v in tokens.items():
            if v is not None:
                body[k] = v
    
    if phpsessid and "authorization" not in body:
        body["authorization"] = f"session={phpsessid}"
        
    return body

def choose_authorize_endpoint(html, base_url):
    try:
        if "login/free" in html:
            if base_url:
                p = urlparse(base_url)
                return f"{p.scheme}://{p.netloc}/wbs/api/v1/login/free/"
            return "/wbs/api/v1/login/free/"
    except Exception:
        pass
    return None

def safe_url(u):
    try:
        p = urlparse(u)
        return f"{p.scheme}://{p.netloc}{p.path}"
    except Exception:
        return u
