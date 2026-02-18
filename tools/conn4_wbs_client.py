#!/usr/bin/env python3
import os
import re
import json
from urllib.parse import urlparse, urlencode, unquote
from urllib.request import build_opener, HTTPCookieProcessor, Request
from http.cookiejar import CookieJar
from conn4_utils import setup_logging


class WbsApiClient:
    def __init__(self, base_url, opener=None, cookies=None, logger=None, curl_proxy=None):
        self.base_url = base_url or ""
        self.cookies = cookies or CookieJar()
        self.opener = opener or build_opener(HTTPCookieProcessor(self.cookies))
        self.logger = logger or setup_logging("wbs-api-client", "wbs_api_client.log")
        self.curl_proxy = curl_proxy
        self.session_storage = {}
        self.user_agent = os.environ.get(
            "NOJS_USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        self.page_html = None

    def default_headers(self, referer=None, ajax=False):
        hdrs = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": os.environ.get("NOJS_ACCEPT_LANGUAGE", "en-US,en;q=0.9"),
            "Accept-Encoding": "gzip, deflate",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }
        ref = referer or self.base_url
        if ref:
            hdrs["Referer"] = ref
            pu = urlparse(ref)
            if pu.scheme and pu.netloc:
                hdrs["Origin"] = f"{pu.scheme}://{pu.netloc}"
        if ajax:
            hdrs["X-Requested-With"] = "XMLHttpRequest"
            hdrs["Accept"] = "*/*"
        else:
            hdrs["Upgrade-Insecure-Requests"] = "1"
        return hdrs

    def req(self, url, data=None, referer=None, ajax=False):
        hdrs = self.default_headers(referer=referer, ajax=ajax)
        if data is not None and "Content-Type" not in hdrs:
            hdrs["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        return Request(url, data=data, headers=hdrs)

    def open(self, request, timeout=20):
        resp = self.opener.open(request, timeout=timeout)
        return resp

    def extract_wbs_token_from_html(self, html):
        m = re.search(r"conn4\.hotspot\.wbsToken\s*=\s*\{.*?\"token\"\s*:\s*\"([^\"]+)\"", html or "", flags=re.DOTALL)
        if m:
            return m.group(1)
        return None

    def extract_wbs_token_from_cookie(self):
        for c in self.cookies:
            if c.name == "himalaya-site-ident":
                val = unquote(c.value or "")
                try:
                    import base64
                    raw = base64.b64decode(val).decode("utf-8", "replace")
                    if raw.startswith("HSI*") or ("HSI*" in raw):
                        raw2 = raw.replace("HSI*", "HWA*")
                        return base64.b64encode(raw2.encode("utf-8")).decode("utf-8")
                except Exception:
                    pass
                if val.startswith("HSI*"):
                    return "HWA*" + val[4:]
                if "HSI*" in val:
                    return val.replace("HSI*", "HWA*")
                return val or None
        return None

    def _curl_post(self, url, data_str, headers):
        cmd = ["curl", "-s", "--compressed"]
        if self.curl_proxy:
            cmd.extend(["-x", self.curl_proxy])
        cmd.append(url)

        # Normalize headers and ensure no gzip decode issues
        hdrs = dict(headers or {})
        hdrs.setdefault("Accept", "*/*")
        hdrs["Accept-Encoding"] = "identity"
        hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
        hdrs.setdefault("X-Requested-With", "XMLHttpRequest")

        # Compose Cookie header from jar if missing
        try:
            from urllib.parse import urlparse as _u
            host = _u(url).netloc
            has_cookie = any(k.lower() == "cookie" for k in hdrs.keys())
            if not has_cookie:
                parts = []
                for c in self.cookies:
                    cd = (c.domain or "").lstrip('.')
                    if cd and (host.endswith(cd) or cd.endswith(host)):
                        parts.append(f"{c.name}={c.value}")
                if parts:
                    hdrs["Cookie"] = "; ".join(parts)
        except Exception:
            pass

        # Add headers
        for k, v in hdrs.items():
            cmd.extend(["-H", f"{k}: {v}"])

        # Add data (single argument)
        cmd.extend(["-d", data_str])

        # Log command (masked)
        self.logger.debug(f"[CURL POST] proxy={self.curl_proxy} url={url}")

        # Execute via subprocess to avoid text decode issues
        import subprocess
        try:
            r = subprocess.run(cmd, capture_output=True, text=False, timeout=30)
            if r.returncode != 0:
                msg = (r.stderr or b"").decode("utf-8", "replace")
                self.logger.error(f"[CURL POST] Curl failed rc={r.returncode} err={msg[:200]}")
                raise Exception(f"Curl failed rc={r.returncode}")
            return (r.stdout or b"").decode("utf-8", "replace")
        except Exception as e:
            self.logger.error(f"[CURL POST] Exec error: {e}")
            raise

    def create_session(self, token=None, site_id=None, locale="en_US", session_id=""):
        p = urlparse(self.base_url or "")
        domain = p.netloc
        scheme = p.scheme or "https"
        if not token and self.page_html:
            token = self.extract_wbs_token_from_html(self.page_html)
        if not token:
            token = self.extract_wbs_token_from_cookie()
        if not token:
            return {"ok": False, "error": "no_token"}
        session_url = f"{scheme}://{domain}/wbs/api/v1/create-session/"
        payload = {
            "session_id": session_id or "",
            "with-tariffs": "1",
            "locationId": (site_id or (p.netloc.split(".")[0] if "." in p.netloc else "1096")),
            "locale": locale,
            "authorization": f"token={token}",
        }
        req = self.req(session_url, data=urlencode(payload).encode("utf-8"), referer=self.base_url, ajax=True)
        
        body = ""
        if self.curl_proxy:
            try:
                # req.headers is a dict-like object
                body = self._curl_post(session_url, urlencode(payload), req.headers)
            except Exception as e:
                return {"ok": False, "error": f"curl_error: {e}"}
        else:
            try:
                resp = self.open(req)
                body = resp.read().decode("utf-8", "replace")
            except Exception as e:
                self.logger.error(f"[API ERROR] {e}")
                return {"ok": False, "error": str(e)}

        api_session_id = None
        try:
            j = json.loads(body)
            api_session_id = j.get("apiSessionId") or j.get("sessionId") or j.get("session")
        except Exception:
            m = re.search(r"apiSessionId[\"']?\s*[:=]\s*[\"']([A-Za-z0-9_\-]+)[\"']", body)
            if m:
                api_session_id = m.group(1)
        # Only try header-based fallback if we have a urllib response (non-curl path)
        if not api_session_id and not self.curl_proxy:
            try:
                hdr = resp.info()
                set_cookie = hdr.get_all("Set-Cookie") if hasattr(hdr, "get_all") else [hdr.get("Set-Cookie")]
                if isinstance(set_cookie, list):
                    for it in set_cookie:
                        if not it:
                            continue
                        mm = re.search(r"PHPSESSID=([^;]+)", it)
                        if mm:
                            api_session_id = mm.group(1)
                            break
            except Exception:
                pass

        # Fallback attempt: authorization without token= prefix
        if not api_session_id:
            try:
                payload2 = dict(payload)
                payload2["authorization"] = token or ""
                req2 = self.req(session_url, data=urlencode(payload2).encode("utf-8"), referer=self.base_url, ajax=True)
                if self.curl_proxy:
                    body2 = self._curl_post(session_url, urlencode(payload2), req.headers)
                else:
                    r2 = self.open(req2)
                    body2 = r2.read().decode("utf-8", "replace")
                try:
                    j2 = json.loads(body2)
                    api_session_id = j2.get("apiSessionId") or j2.get("sessionId") or j2.get("session")
                    if api_session_id:
                        body = body2
                        payload = payload2
                except Exception:
                    m2 = re.search(r"apiSessionId[\"']?\s*[:=]\s*[\"']([A-Za-z0-9_\-]+)[\"']", body2)
                    if m2:
                        api_session_id = m2.group(1)
                        body = body2
                        payload = payload2
            except Exception:
                pass
        if api_session_id:
            self.session_storage["conn4-hotspot-storage-apiSessionId"] = api_session_id
            return {"ok": True, "apiSessionId": api_session_id, "payload": payload, "body": body}
        return {"ok": False, "error": "no_api_session_id", "body": body, "payload": payload}
