import sys
import os
import time
import json
import logging
import shutil
from urllib.parse import urlparse, parse_qs
sys.path.append(os.path.dirname(__file__))
from conn4_utils import setup_logging, run_shell_cmd, SocksProxyManager
from conn4_shared import extract_tokens_from_html, build_consent_body
from conn4_auth_lib import WbsTokenBuilder

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright не установлен. Установите: pip3 install playwright и python3 -m playwright install chromium")
    sys.exit(1)

is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
if not is_wsl:
    print("Этот скрипт должен запускаться только в WSL")
    sys.exit(1)

class Conn4PortalPlaywrightTester:
    def __init__(self, ssh_host=None, ssh_user=None):
        self.logger = setup_logging(__name__, "conn4_playwright_debug.log")
        self.socks_manager = SocksProxyManager(self.logger, ssh_host, ssh_user)
        self.ssh_host = self.socks_manager.ssh_host
        self.ssh_user = self.socks_manager.ssh_user
        self.noform = False
        self.browser = None
        self.context = None
        self.page = None
        self.captured_requests = []
        self.msn_detected = False
        self.msn_stop_done = False
        try:
            self.nav_timeout_ms = int((os.environ.get("CPM_NAV_TIMEOUT_MS") or "15000").strip())
        except Exception:
            self.nav_timeout_ms = 15000
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        except Exception:
            project_root = os.getcwd()
        base_dir = os.environ.get("MCP_ARTIFACTS_DIR") or os.path.join(project_root, "mcp_artifacts", "conn4_playwright")
        label = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        run_id = f"{label}_{os.getpid()}"
        self.artifact_dir = os.path.join(base_dir, run_id)
        try:
            os.makedirs(self.artifact_dir, exist_ok=True)
            self.logger.info(f"Артефакты: {self.artifact_dir}")
        except Exception as e:
            self.logger.error(f"Ошибка создания артефактов: {e}")
            self.artifact_dir = os.getcwd()

    def check_environment(self):
        try:
            if self.socks_manager.check_router_ping():
                self.logger.info("Проверка роутера: OK")
            else:
                self.logger.info("Проверка роутера: FAIL")
            if self.socks_manager.verify_socks_proxy():
                self.logger.info(f"Проверка SOCKS {self.socks_manager.socks_port}: OK")
            else:
                self.logger.info(f"Проверка SOCKS {self.socks_manager.socks_port}: FAIL")
            return True
        except Exception:
            return False

    def verify_socks_proxy(self):
        try:
            if self.socks_manager.verify_socks_proxy(silent=True):
                self.logger.info(f"[SOCKS CHECK] порт {self.socks_manager.socks_port} активен")
                return True
            port = os.environ.get("NOJS_SOCKS_PORT") or "10800"
            rc1, ip1, _ = run_shell_cmd(["bash","-lc","which curl >/dev/null 2>&1 && curl -s --max-time 8 https://api.ipify.org || echo NA"], timeout=12)
            rc2, ip2, _ = run_shell_cmd(["bash","-lc",f"which curl >/dev/null 2>&1 && curl -x socks5h://127.0.0.1:{port} -s --max-time 8 https://api.ipify.org || echo NA"], timeout=12)
            ip1 = (ip1 or "").strip()
            ip2 = (ip2 or "").strip()
            self.logger.info(f"[SOCKS CHECK] ip direct={ip1 or 'NA'} ip socks={ip2 or 'NA'}")
            if ip2 and ip2 != "NA":
                return True
            return self.socks_manager.verify_socks_proxy(silent=True)
        except Exception:
            return self.socks_manager.verify_socks_proxy(silent=True)

    def ensure_socks_proxy(self):
        try:
            host = os.environ.get("OPENWRT_SSH_HOST","dev-openwrt")
            user = os.environ.get("OPENWRT_SSH_USER","root")
            target = f"{user}@{host}"
            port = os.environ.get("NOJS_SOCKS_PORT") or "10800"
            rc, out, _ = run_shell_cmd(["bash","-lc",f"ss -lnt | awk '{{print $4}}' | grep -q ':{port}$' && echo ok || echo fail"], timeout=5)
            active = ((out or "").strip() == "ok")
            if not active:
                run_shell_cmd(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=no","-f","-N","-D",f"127.0.0.1:{port}",target], timeout=10)
                time.sleep(1)
            run_shell_cmd(["bash","-lc",f"export ALL_PROXY=socks5h://127.0.0.1:{port}; export HTTPS_PROXY=$ALL_PROXY; export HTTP_PROXY=$ALL_PROXY; true"], timeout=2)
        except Exception:
            pass

    def setup_browser(self):
        if self.browser and self.context and self.page:
            return True
        self.logger.info("Настройка Playwright Chromium...")
        pw = sync_playwright().start()
        port = os.environ.get("NOJS_SOCKS_PORT") or "10800"
        browser = pw.chromium.launch(headless=True, proxy={"server": f"socks5://127.0.0.1:{port}"})
        context = browser.new_context()
        page = context.new_page()
        self.pw = pw
        self.browser = browser
        self.context = context
        self.page = page
        try:
            self.page.set_default_timeout(self.nav_timeout_ms)
            self.page.set_default_navigation_timeout(self.nav_timeout_ms)
        except Exception:
            pass
        def _route_handler(route, request):
            try:
                u = urlparse(request.url)
                host = (u.netloc or '').lower()
            except Exception:
                host = ''
            if ('msn.com' in host) or host.endswith('msn.com') or ('assets.msn.com' in host) or ('srtb.msn.com' in host) or ('go.microsoft.com' in host) or host.endswith('microsoft.com'):
                try:
                    self.logger.info(f"[ABORT MSN] {request.method} {request.url}")
                except Exception:
                    pass
                try:
                    self.msn_detected = True
                    if not self.msn_stop_done:
                        try:
                            self.page.evaluate("try{ window.stop(); }catch(e){}")
                        except Exception:
                            pass
                        self.msn_stop_done = True
                except Exception:
                    pass
                try:
                    route.abort()
                except Exception:
                    pass
                return
            try:
                route.continue_()
            except Exception:
                try:
                    route.fallback()
                except Exception:
                    pass
        try:
            self.context.route('**/*', _route_handler)
        except Exception:
            pass
        def _on_req(r):
            try:
                self.logger.info(f"[REQUEST] {r.method} {r.url}")
            except Exception:
                pass
            try:
                self.captured_requests.append({"url": r.url, "method": r.method})
            except Exception:
                pass
        self.page.on("request", _on_req)
        self.logger.info("Chromium готов")
        return True

    def dump_cookies_and_storage(self, label=""):
        try:
            cookies = self.context.cookies()
            self.logger.debug(f"[COOKIES{(' ' + label) if label else ''}] всего: {len(cookies)}")
            try:
                doc_cookie = self.page.evaluate("document.cookie || ''")
            except Exception:
                doc_cookie = ""
            self.logger.debug(f"[document.cookie{(' ' + label) if label else ''}] {doc_cookie}")
            try:
                ls = self.page.evaluate("(function(){var r=[]; if(window.localStorage){ for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i); r.push([k,localStorage.getItem(k)]);} } return r;})()")
                self.logger.debug(f"[localStorage{(' ' + label) if label else ''}] length={len(ls or [])}")
            except Exception:
                pass
            try:
                ss = self.page.evaluate("(function(){var r=[]; if(window.sessionStorage){ for(var i=0;i<sessionStorage.length;i++){var k=sessionStorage.key(i); r.push([k,sessionStorage.getItem(k)]);} } return r;})()")
                self.logger.debug(f"[sessionStorage{(' ' + label) if label else ''}] length={len(ss or [])}")
            except Exception:
                pass
        except Exception as e:
            self.logger.debug(f"Ошибка дампа cookies/storage: {e}")

    def _green(self, s):
        try:
            return f"\x1b[32m{s}\x1b[0m"
        except Exception:
            return s

    def _red(self, s):
        try:
            return f"\x1b[31m{s}\x1b[0m"
        except Exception:
            return s

    def _collect_tokens(self):
        html = ""
        try:
            html = self.page.content() or ""
        except Exception:
            html = ""
        tokens = {}
        try:
            tokens = extract_tokens_from_html(html) or {}
        except Exception:
            tokens = {}
        try:
            st = self.page.evaluate("(function(){var r={}; if(window.sessionStorage){ for(var i=0;i<sessionStorage.length;i++){var k=sessionStorage.key(i); var v=sessionStorage.getItem(k); r[k]=v;} } if(window.localStorage){ for(var j=0;j<localStorage.length;j++){var k2=localStorage.key(j); var v2=localStorage.getItem(k2); r[k2]=v2;} } return r;})()")
            for k,v in (st or {}).items():
                kl = (k or "").lower()
                if v is None:
                    continue
                if "apisessionid" in kl:
                    tokens["apiSessionId"] = v
                    tokens["api_session_id"] = v
                elif "paymentreturnproxyurl" in kl:
                    tokens["paymentReturnProxyUrl"] = v
                elif (kl.endswith("siteid") or kl.endswith("site_id")) and v:
                    tokens["siteId"] = v
        except Exception:
            pass
        return tokens

    def _nojs_build_consent_body(self, tokens):
        try:
            try:
                u = urlparse(self.page.url or "")
                qs = parse_qs(u.query or "")
                flat_qs = {k:(v[0] if isinstance(v,list) and v else v) for k,v in qs.items()}
            except Exception:
                flat_qs = {}
            phpsessid = None
            try:
                for c in (self.context.cookies() or []):
                    if (c.get("name") or "") == "PHPSESSID":
                        phpsessid = c.get("value")
                        break
            except Exception:
                phpsessid = None
            try:
                tariff_default = os.environ.get("NOJS_DEFAULT_TARIFF","381")
            except Exception:
                tariff_default = "381"
            return build_consent_body(flat_qs, tokens or {}, tariff_default, phpsessid)
        except Exception:
            return {}

    def _ensure_php_session(self):
        try:
            url = self.page.url or ""
            u = urlparse(url)
            base = f"{u.scheme}://{u.netloc}" if u.netloc else None
        except Exception:
            base = None
        try:
            if base:
                try:
                    self.page.goto(f"{base}/registration-free", wait_until="load", timeout=self.nav_timeout_ms)
                except Exception:
                    pass
                try:
                    self.page.goto(f"{base}/wbs/authenticate-me/", wait_until="load", timeout=self.nav_timeout_ms)
                except Exception:
                    pass
            toks = self._collect_tokens()
            sid = toks.get("siteId") or toks.get("site_id")
            prx = toks.get("paymentReturnProxyUrl") or toks.get("payment_return_proxy_url")
            if not prx and sid:
                prx = f"https://{sid}.rdr.conn4.com/admon-assets/payment-return-proxy.php?PaymentProxyUrl="
            if prx:
                try:
                    self.page.goto(prx, wait_until="load", timeout=self.nav_timeout_ms)
                except Exception:
                    pass
            try:
                for c in (self.context.cookies() or []):
                    if (c.get("name") or "") == "PHPSESSID" and c.get("value"):
                        return c.get("value")
            except Exception:
                pass
        except Exception:
            pass
        return None

    def _authorize_via_login_free(self):
        try:
            toks = self._collect_tokens()
            php_sid = self._ensure_php_session()
            try:
                self.page.goto("http://www.msftconnecttest.com/redirect", wait_until="load", timeout=self.nav_timeout_ms)
            except Exception:
                pass
            toks = self._collect_tokens()
            consent = self._nojs_build_consent_body(toks)
            url = self.page.url or ""
            u = urlparse(url)
            endpoint = f"{u.scheme}://{u.netloc}/wbs/api/v1/login/free/"
            if not php_sid:
                try:
                    cookie_val = None
                    try:
                        for c in (self.context.cookies() or []):
                            if (c.get("name") or "").lower() == "himalaya-site-ident":
                                cookie_val = c.get("value")
                                break
                    except Exception:
                        cookie_val = None
                    site_id = toks.get("siteId") or toks.get("site_id") or ""
                    client_ip = toks.get("clientIp") or toks.get("client_ip") or ""
                    client_mac = toks.get("clientMac") or toks.get("client_mac") or ""
                    wbs = WbsTokenBuilder.generate_wbs_token_from_site_ident(cookie_val, site_id, client_ip, client_mac) if cookie_val else None
                    if wbs and u.netloc:
                        create_ep = f"{u.scheme}://{u.netloc}/wbs/api/v1/create-session/"
                        payload = {
                            "session_id": "",
                            "with-tariffs": "1",
                            "locationId": str(site_id or ""),
                            "locale": toks.get("locale") or toks.get("portalLocale") or "en_US",
                            "authorization": f"token={wbs}"
                        }
                        try:
                            body_cs = self.page.evaluate(
                                """
                                (url, data) => {
                                  const p = new URLSearchParams();
                                  for (const [k,v] of Object.entries(data||{})) { if (v!=null) p.append(k, String(v)); }
                                  return fetch(url, {method:'POST', credentials:'include', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: p.toString()})
                                    .then(r => r.text())
                                    .catch(() => "");
                                }
                                """,
                                create_ep,
                                payload,
                            )
                        except Exception:
                            pass
                        try:
                            import re
                            m = re.search(r"apiSessionId[\"']?\s*[:=]\s*[\"']([A-Za-z0-9_\-]+)[\"']", body_cs or "")
                            if m:
                                toks["apiSessionId"] = m.group(1)
                                toks["api_session_id"] = m.group(1)
                        except Exception:
                            pass
                        try:
                            prx2 = toks.get("paymentReturnProxyUrl") or toks.get("payment_return_proxy_url")
                            if not prx2 and site_id:
                                prx2 = f"https://{site_id}.rdr.conn4.com/admon-assets/payment-return-proxy.php?PaymentProxyUrl="
                            if prx2:
                                from urllib.parse import quote
                                self.page.goto(f"{prx2}{quote('https://www.leonardo-hotels.com/destinations', safe='')}", wait_until="load", timeout=self.nav_timeout_ms)
                        except Exception:
                            pass
                        try:
                            for c in (self.context.cookies() or []):
                                if (c.get("name") or "") == "PHPSESSID" and c.get("value"):
                                    php_sid = c.get("value")
                                    break
                        except Exception:
                            pass
                except Exception:
                    pass
            try:
                res = self.page.evaluate("""
                (url, data) => {
                  const p = new URLSearchParams();
                  for (const [k,v] of Object.entries(data||{})) { if (v!=null) p.append(k, String(v)); }
                  return fetch(url, {method:'POST', credentials:'include', headers:{'Content-Type':'application/x-www-form-urlencoded','X-Requested-With':'XMLHttpRequest','Accept':'application/json, */*'}, body: p.toString()})
                    .then(r => ({ok: r.ok, status: r.status}))
                    .catch(e => ({ok:false, status:0, error: String(e)}));
                }
                """, endpoint, consent)
            except Exception:
                res = {"ok": False, "status": 0}
            try:
                self.logger.info((self._green if res.get("ok") else self._red)(f"POST login/free status={res.get('status')}"))
                if not res.get("ok"):
                    try:
                        err = res.get("error")
                        if err:
                            self.logger.info(self._red(f"POST login/free error={err}"))
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                prx = toks.get("paymentReturnProxyUrl") or toks.get("payment_return_proxy_url") or ""
            except Exception:
                prx = ""
            try:
                target = "https://www.leonardo-hotels.com/destinations"
                if prx:
                    from urllib.parse import quote
                    self.page.goto(f"{prx}{quote(target, safe='')}", wait_until="load", timeout=self.nav_timeout_ms)
            except Exception:
                pass
            if not res.get("ok"):
                try:
                    alt = self.page.evaluate(
                        """
                        (url, data) => {
                          const p = new URLSearchParams();
                          for (const [k,v] of Object.entries(data||{})) { if (v!=null) p.append(k, String(v)); }
                          return fetch(url, {method:'POST', credentials:'include', headers:{'Content-Type':'application/x-www-form-urlencoded','X-Requested-With':'XMLHttpRequest','Accept':'application/json, */*'}, body: p.toString()})
                            .then(r => ({ok: r.ok, status: r.status}))
                            .catch(e => ({ok:false, status:0, error: String(e)}));
                        }
                        """,
                        (self.page.url or ""),
                        consent,
                    )
                    try:
                        self.logger.info((self._green if alt.get("ok") else self._red)(f"POST scene status={alt.get('status')}"))
                        if not alt.get("ok"):
                            try:
                                e2 = alt.get("error")
                                if e2:
                                    self.logger.info(self._red(f"POST scene error={e2}"))
                            except Exception:
                                pass
                    except Exception:
                        pass
                    res = alt
                except Exception:
                    pass
            return bool(res.get("ok"))
        except Exception:
            return False

    def test_conn4_portal(self):
        try:
            try:
                self.logger.info("Открытие портала")
            except Exception:
                pass
            try:
                self.page.goto("http://www.msftconnecttest.com/redirect", wait_until="load", timeout=self.nav_timeout_ms)
                if self.msn_detected:
                    try:
                        self.logger.info(self._red("Редирект на msn.com — останавливаем работу"))
                    except Exception:
                        pass
                    self._save_master(success=False)
                    return False
                try:
                    u = urlparse(self.page.url or '')
                    host = (u.netloc or '').lower()
                    if 'msn.com' in host:
                        self.logger.info(self._red("Редирект на msn.com — останавливаем работу"))
                        self._save_master(success=False)
                        return False
                except Exception:
                    pass
            except Exception as e:
                try:
                    self.logger.info(self._red(f"PORTAL GOTO TIMEOUT/ERR: {e}"))
                except Exception:
                    pass
                for u in [
                    "http://captive.apple.com/hotspot-detect.html",
                    "http://example.com/",
                ]:
                    try:
                        self.page.goto(u, wait_until="load", timeout=self.nav_timeout_ms)
                        break
                    except Exception:
                        continue
            time.sleep(2)
            try:
                self.logger.info(self._green("Портал загружен"))
            except Exception:
                pass
            self.dump_cookies_and_storage(label="pre-click")
            toks = self._collect_tokens()
            try:
                self.logger.debug(f"TOKENS: apiSessionId={toks.get('apiSessionId')} paymentReturnProxyUrl={toks.get('paymentReturnProxyUrl')} siteId={toks.get('siteId')}")
            except Exception:
                pass
            try:
                with open(os.path.join(self.artifact_dir, "conn4_session_storage_trace.json"), "w", encoding="utf-8") as f:
                    json.dump({"tokens": toks}, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            if self.noform:
                self.dump_cookies_and_storage(label="after-noform")
                try:
                    url = self.page.url or ""
                except Exception:
                    url = ""
                try:
                    host = urlparse(url).netloc.lower()
                except Exception:
                    host = ""
                try:
                    cookies = self.context.cookies() or []
                except Exception:
                    cookies = []
                names = set([c.get("name") or "" for c in cookies])
                portal_hit = ("rdr.conn4.com" in (host or "")) or ("conn4.com" in (host or ""))
                internet_redirect = ("leonardo-hotels.com" in (host or ""))
                if not internet_redirect:
                    try:
                        for it in (self.captured_requests or []):
                            uu = urlparse(it.get("url") or "")
                            hh = (uu.netloc or "").lower()
                            if "leonardo-hotels.com" in (hh or ""):
                                internet_redirect = True
                                break
                    except Exception:
                        pass
                try:
                    self.logger.info(f"ДЕТЕКЦИЯ: portal_hit={portal_hit} internet_redirect={internet_redirect} host={host}")
                except Exception:
                    pass
                ok = bool(internet_redirect and not portal_hit)
                try:
                    if ok:
                        self.logger.info("СТАТУС: авторизация уже пройдена (редирект в интернет)")
                    else:
                        self.logger.info("СТАТУС: обнаружен портал/нет редиректа, авторизация не подтверждена")
                except Exception:
                    pass
                self._save_master(success=ok)
                return ok
            btns = []
            try:
                btns.extend(self.page.locator("//button[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free wi-fi')]").all())
                btns.extend(self.page.locator("//button[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'free wi-fi')]").all())
                btns.extend(self.page.locator("//button[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'free wifi')]").all())
                btns.extend(self.page.locator("//button[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]").all())
                btns.extend(self.page.locator("//button[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]").all())
                btns.extend(self.page.locator("//button[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]").all())
                btns.extend(self.page.locator("//button[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]").all())
                btns.extend(self.page.locator("//input[@type='submit']").all())
                btns.extend(self.page.locator("//button[@type='submit']").all())
                btns.extend(self.page.locator("//button[contains(@class,'btn')]").all())
                btns.extend(self.page.locator("//a[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'free wi-fi')]").all())
                btns.extend(self.page.locator("//a[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'free wifi')]").all())
                btns.extend(self.page.locator("//a[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]").all())
                btns.extend(self.page.locator("//a[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]").all())
                btns.extend(self.page.locator("//a[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]").all())
                btns.extend(self.page.locator("//a[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]").all())
            except Exception:
                btns = []
            ch = []
            try:
                ch = self.page.locator("input[type='checkbox']").all()
            except Exception:
                ch = []
            forms = []
            try:
                forms = self.page.locator("form").all()
            except Exception:
                forms = []
            try:
                self.logger.info(f"Проверка портала: чекбоксов={len(ch)} кнопок={len(btns)} форм={len(forms)}")
            except Exception:
                pass
            if not btns:
                try:
                    self.logger.info(self._red("Кнопки отправки не найдены — пропуск шага клика"))
                except Exception:
                    pass
                try:
                    auth_ok = self._authorize_via_login_free()
                    self.logger.info((self._green if auth_ok else self._red)(f"API авторизация login/free: {auth_ok}"))
                except Exception:
                    pass
            for cb in ch:
                try:
                    cb.scroll_into_view_if_needed()
                    cb.check(force=True)
                except Exception:
                    pass
            time.sleep(2)
            clicked = False
            for el in btns:
                try:
                    if el.is_visible():
                        el.scroll_into_view_if_needed()
                        try:
                            el.click()
                        except Exception:
                            try:
                                href = el.get_attribute('href')
                                if href:
                                    self.page.goto(href, wait_until="load", timeout=self.nav_timeout_ms)
                            except Exception:
                                pass
                        try:
                            self.logger.info(self._green("Клик по кнопке отправки"))
                        except Exception:
                            pass
                        clicked = True
                        break
                except Exception:
                    continue
            time.sleep(5)
            try:
                self.logger.info("Проверка результата авторизации")
            except Exception:
                pass
            self.dump_cookies_and_storage(label="after-auth")
            url = ""
            try:
                url = self.page.url or ""
            except Exception:
                url = ""
            host = urlparse(url).netloc.lower()
            if clicked and host and ("conn4.com" not in host):
                try:
                    self.logger.info(self._green(f"AUTH FLOW: clicked={clicked} host={host} → успех, интернет доступен"))
                except Exception:
                    pass
                self._save_master(success=True)
                return True
            ok = self._check_success_alt()
            try:
                self.logger.info((self._green if ok else self._red)(f"AUTH FLOW: clicked={clicked} host={host} → success_alt={ok}"))
            except Exception:
                pass
            self._save_master(success=ok)
            return ok
        except Exception as e:
            self.logger.error(f"Ошибка доступа к порталу: {e}")
            return False

    def _check_success_alt(self):
        try:
            url = self.page.url or ""
            u = urlparse(url)
            host = (u.netloc or "").lower()
            if host and ("leonardo-hotels.com" in host):
                return True
            try:
                for it in (self.captured_requests or []):
                    h = ""
                    try:
                        uu = urlparse(it.get("url") or "")
                        h = (uu.netloc or "").lower()
                    except Exception:
                        h = ""
                    if h and ("leonardo-hotels.com" in h):
                        return True
            except Exception:
                pass
        except Exception:
            pass
        return False

    def _save_master(self, success):
        try:
            dbg = {}
            try:
                dbg["current_url"] = self.page.url
            except Exception:
                dbg["current_url"] = None
            try:
                dbg["page_html"] = self.page.content()
            except Exception:
                dbg["page_html"] = ""
            try:
                dbg["cookies"] = self.context.cookies()
            except Exception:
                dbg["cookies"] = []
            try:
                dbg["capturedRequests"] = self.captured_requests
            except Exception:
                dbg["capturedRequests"] = []
            try:
                tokens = self._collect_tokens()
            except Exception:
                tokens = {}
            try:
                consent = self._nojs_build_consent_body(tokens)
            except Exception:
                consent = {}
            try:
                url = self.page.url or ""
            except Exception:
                url = ""
            try:
                host = urlparse(url).netloc.lower()
            except Exception:
                host = ""
            st = {}
            try:
                cookies = self.context.cookies() or []
            except Exception:
                cookies = []
            try:
                names = set([c.get("name") or "" for c in cookies])
                portal_hit = ("rdr.conn4.com" in (host or "")) or ("conn4.com" in (host or ""))
                stopped_on_msn = ("msn.com" in (host or "")) or ("microsoft.com" in (host or "")) or ("go.microsoft.com" in (host or ""))
                internet_redirect = ("leonardo-hotels.com" in (host or ""))
                if not internet_redirect:
                    try:
                        for it in (self.captured_requests or []):
                            uu = urlparse(it.get("url") or "")
                            hh = (uu.netloc or "").lower()
                            if "leonardo-hotels.com" in (hh or ""):
                                internet_redirect = True
                                break
                    except Exception:
                        pass
                if stopped_on_msn:
                    st = {"authorized": False, "reason": "stopped_on_msn", "url": url, "host": host}
                else:
                    st = {"authorized": bool(internet_redirect or (success is True and not portal_hit)), "reason": ("internet_redirect" if internet_redirect else ("portal_detected" if portal_hit else ("success" if success else "unknown"))), "url": url, "host": host}
                try:
                    if st.get("authorized"):
                        self.logger.info(self._green(f"ИТОГО: авторизовано (reason={st.get('reason')}) {host}"))
                    else:
                        self.logger.info(self._red(f"ИТОГО: не авторизовано (reason={st.get('reason')}) {host}"))
                except Exception:
                    pass
            except Exception:
                st = {"authorized": False, "reason": "unknown", "url": url, "host": host}
            try:
                compare = {"computedTokens": tokens, "computedConsent": consent, "network": self.captured_requests}
            except Exception:
                compare = {}
            obj = {"debug": dbg, "success": success, "status": st, "compare": compare}
            path = os.path.join(self.artifact_dir, "conn4_master.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
            try:
                cmp_path = os.path.join(self.artifact_dir, "conn4_compare.json")
                with open(cmp_path, "w", encoding="utf-8") as f:
                    json.dump(compare, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            idx = os.path.join(self.artifact_dir, "index.json")
            with open(idx, "w", encoding="utf-8") as f:
                json.dump({"artifacts": ["conn4_master.json","conn4_compare.json"], "created_at": time.time(), "run_id": os.path.basename(self.artifact_dir)}, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Сводный отчёт сохранён: {path}")
        except Exception:
            pass

    def cleanup(self):
        try:
            pass
        except Exception:
            pass
        try:
            if self.browser:
                self.browser.close()
        except Exception:
            pass
        try:
            if getattr(self, "pw", None):
                self.pw.stop()
        except Exception:
            pass

    def run_test(self):
        self.logger.info("ТЕСТИРОВАНИЕ CONN4.COM CAPTIVE PORTAL (Playwright)")
        try:
            try:
                self.ensure_socks_proxy()
            except Exception:
                pass
            force_run = (os.environ.get("CPM_FORCE_RUN") or "").strip() == "1"
            if not self.verify_socks_proxy() and not force_run:
                self.logger.error("SOCKS-прокси не готов")
                return False
            if not (self.browser and self.context and self.page):
                if not self.setup_browser():
                    return False
            ok = self.test_conn4_portal()
            return ok
        except Exception as e:
            self.logger.error(f"Критическая ошибка: {e}")
            return False
        finally:
            self.cleanup()
            try:
                self.socks_manager.shutdown_socks_proxy()
            except Exception:
                pass

def main():
    tester = Conn4PortalPlaywrightTester()
    try:
        args = sys.argv[1:]
        url_arg = None
        out_arg = "conn4_tokens.json"
        collect_only = False
        write_compare = False
        if "--noform" in args:
            tester.noform = True
            try:
                tester.logger.info("Режим —noform активирован: форму не отправляем, фиксируем состояние")
            except Exception:
                pass
        if "--url" in args:
            i = args.index("--url")
            if i + 1 < len(args):
                url_arg = args[i + 1]
        if "--out" in args:
            i = args.index("--out")
            if i + 1 < len(args):
                out_arg = args[i + 1]
        if "--collect-tokens" in args:
            collect_only = True
        if "--write-compare" in args:
            write_compare = True
        tester.check_environment()
        if not tester.setup_browser():
            sys.exit(2)
        target_url = url_arg or "http://www.msftconnecttest.com/redirect"
        try:
            tester.page.goto(target_url, wait_until="load", timeout=tester.nav_timeout_ms)
            time.sleep(2)
            tester.dump_cookies_and_storage(label="ready")
            toks = tester._collect_tokens()
            data = {
                "apiSessionId": toks.get("apiSessionId"),
                "paymentReturnProxyUrl": toks.get("paymentReturnProxyUrl"),
                "siteId": toks.get("siteId"),
            }
            with open(out_arg, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            try:
                tester.logger.info(f"READY GOTO TIMEOUT/ERR: {e}")
            except Exception:
                pass
            try:
                with open(out_arg, "w", encoding="utf-8") as f:
                    json.dump({"error": "ready_goto_failed", "details": str(e)}, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        if write_compare:
            try:
                consent = tester._nojs_build_consent_body(toks)
            except Exception:
                consent = {}
            try:
                compare = {"computedTokens": toks, "computedConsent": consent, "network": tester.captured_requests}
                with open("conn4_compare.json", "w", encoding="utf-8") as f:
                    json.dump(compare, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        if not collect_only:
            ok = tester.run_test()
            sys.exit(0 if ok else 1)
        tester.cleanup()
        sys.exit(0)
    except KeyboardInterrupt:
        tester.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
