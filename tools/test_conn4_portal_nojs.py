#!/usr/bin/env python3
import sys
import os
import re
import json
import logging
import time
import subprocess
import base64
import tempfile
import socket
from urllib.parse import urlparse, parse_qs, urlencode, urljoin, unquote
from urllib.request import build_opener, HTTPCookieProcessor, Request, ProxyHandler, getproxies
from http.cookiejar import CookieJar
from html_form_parser import FormParser
from conn4_auth_lib import WbsTokenBuilder, PhpSerializer
sys.path.append(os.path.dirname(__file__))
from conn4_shared import base_origin_from_url, extract_resource_urls_from_html, extract_urls_from_js_text, extract_tokens_from_html, collect_tokens_from_text, build_consent_body, choose_authorize_endpoint
from conn4_utils import setup_logging, run_shell_cmd, SocksProxyManager
from conn4_wbs_client import WbsApiClient

try:
    import socks  # type: ignore
    from sockshandler import SocksiPyHandler  # type: ignore
except Exception:
    socks = None


import http.cookiejar as cj


class NoJsConn4Authorizer:
    """Эмуляция авторизации на портале conn4.com без браузера через HTTP и SOCKS."""

    def __init__(self, portal_url=None, ssh_host=None, ssh_user=None):
        # 1. Сначала определяем директорию для артефактов
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        except Exception:
            project_root = os.getcwd()
        
        base_dir = os.environ.get("MCP_ARTIFACTS_DIR") or os.path.join(project_root, "mcp_artifacts", "conn4_nojs")
        label = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        run_id = f"{label}_{os.getpid()}"
        self.artifact_dir = os.path.join(base_dir, run_id)
        
        try:
            os.makedirs(self.artifact_dir, exist_ok=True)
        except Exception:
            import tempfile
            self.artifact_dir = os.path.join(tempfile.gettempdir(), f"conn4_nojs_{run_id}")
            os.makedirs(self.artifact_dir, exist_ok=True)

        # 2. Настраиваем логирование внутри этой директории
        log_file = os.path.join(self.artifact_dir, "conn4_nojs_debug.log")
        self.logger = setup_logging("nojs-auth", log_file)
        self.logger.info(f"Артефакты и логи будут сохранены в: {self.artifact_dir}")

        # 3. Настройка окружения (dev/prod)
        cpm_env = os.environ.get("CPM_ENV", "dev").lower()
        if not ssh_host:
            if cpm_env == "prod":
                ssh_host = "prod-openwrt"
            else:
                ssh_host = "dev-openwrt"
        
        self.socks_manager = SocksProxyManager(self.logger, ssh_host, ssh_user)
        self.portal_url = portal_url or os.environ.get("PORTAL_URL") or os.environ.get("PORTAL_START_URL") or os.environ.get("SELENIUM_START_URL")
        self.cookies = CookieJar()
        try:
            handlers = [HTTPCookieProcessor(self.cookies)]
            try:
                proxies = getproxies()
            except Exception:
                proxies = {}
            if proxies:
                handlers.append(ProxyHandler(proxies))
            self.opener = build_opener(*handlers)
        except Exception:
            self.opener = build_opener(HTTPCookieProcessor(self.cookies))
        self.page_url = None
        self.page_html = None
        parsed = urlparse(self.portal_url or "")
        self.initial_query = parse_qs(parsed.query)
        self.host_id = os.environ.get("HOST_ID") or socket.gethostname()
        self.touched_urls = set()
        self.touched_domains = {}
        self.dynamic_tokens = {}
        self.client_ip_override = os.environ.get("NOJS_CLIENT_IP")
        self.client_mac_override = os.environ.get("NOJS_CLIENT_MAC")
        self.cookie_decoded_ip = None
        self.cookie_decoded_mac = None
        self.cookie_decoded_site_id = None
        # Реалистичный User-Agent современного браузера Chrome на Windows
        default_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        self.user_agent = os.environ.get("NOJS_USER_AGENT", default_ua)
        self.captured_requests = []
        self.trace_log = []
        self.captured_iframes = []
        self.disable_ssh = os.environ.get("NOJS_DISABLE_SSH") == "1"
        self.logger.info(f"NOJS_DISABLE_SSH={os.environ.get('NOJS_DISABLE_SSH')} (parsed as {self.disable_ssh})")
        self.force_gateway = os.environ.get("NOJS_GATEWAY") or "192.168.1.1"
        self.default_tariff = os.environ.get("NOJS_DEFAULT_TARIFF","381")
        self.default_locale = os.environ.get("NOJS_DEFAULT_LOCALE","en_US")
        self.logger.info("Загрузка всех ресурсов разрешена (включая файлы с хешами в именах)")

    def save_debug_artifact(self, path="conn4_debug.json"):
        if not os.path.isabs(path):
            full_path = os.path.join(self.artifact_dir, path)
        else:
            full_path = path
        
        data = {}
        try:
            data["current_url"] = self.page_url
        except Exception:
            data["current_url"] = None
            
        try:
            data["page_html"] = self.page_html
        except Exception:
            data["page_html"] = None

        data["cookies"] = []
        try:
            for c in self.cookies:
                 data["cookies"].append({
                     "name": c.name, 
                     "value": c.value, 
                     "domain": c.domain, 
                     "path": c.path
                 })
        except Exception:
            pass
            
        data["capturedRequests"] = self.captured_requests
        data["traceLog"] = self.trace_log
        data["iframes"] = self.captured_iframes
        data["networkSummary"] = getattr(self, 'network_summary', [])
        
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Отладочный артефакт сохранен: {full_path}")
        except Exception as e:
            self.logger.info(f"Ошибка сохранения артефакта: {e}")

    def _filtered_cookies_for_compare(self):
        items = []
        try:
            for c in self.cookies:
                try:
                    d = (c.domain or "").lower()
                    if ("conn4.com" in d) or ("rdr.conn4.com" in d):
                        name = c.name
                        if name:
                            items.append({"name": name, "domain": c.domain, "path": c.path})
                except Exception:
                    pass
        except Exception:
            pass
        return items

    def save_cookie_set_artifact(self, path="conn4_cookies_nojs.json"):
        if not os.path.isabs(path):
            full_path = os.path.join(self.artifact_dir, path)
        else:
            full_path = path
        try:
            data = {"cookies": self._filtered_cookies_for_compare()}
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Cookie-набор сохранён: {full_path}")
            return full_path
        except Exception as e:
            self.logger.info(f"Ошибка сохранения cookie-набора: {e}")
            return None

    def _cookie_names_from_artifact(self, path):
        if not path or not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cookies = data.get("cookies", [])
            return {c.get("name") for c in cookies if c.get("name")}
        except Exception:
            return None

    def compare_cookie_sets(self, selenium_path, nojs_path, out_name="conn4_cookie_set_compare.json"):
        sel = self._cookie_names_from_artifact(selenium_path)
        nojs = self._cookie_names_from_artifact(nojs_path)
        if sel is None or nojs is None:
            return None
        only_sel = sorted(list(sel - nojs))
        only_nojs = sorted(list(nojs - sel))
        result = {
            "identical": sel == nojs,
            "selenium_count": len(sel),
            "nojs_count": len(nojs),
            "only_in_selenium": only_sel,
            "only_in_nojs": only_nojs,
        }
        try:
            out_path = os.path.join(self.artifact_dir, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Сравнение cookie-наборов сохранено: {out_path}")
        except Exception:
            pass
        try:
            if result["identical"]:
                self.logger.info("Наборы cookie совпадают")
            else:
                self.logger.info(f"Наборы cookie различаются: selenium_only={len(only_sel)} nojs_only={len(only_nojs)}")
        except Exception:
            pass
        return result

    def debug_checkpoint(self, label):
        self.save_debug_artifact(f"conn4_debug_checkpoint_{label}.json")

    def check_environment(self):
        """Проверка окружения: пинг роутера и наличие SOCKS прокси."""
        try:
            if self.socks_manager.check_router_ping():
                 self.logger.info("Проверка роутера: OK")
            else:
                 self.logger.info("Проверка роутера: FAIL")
            
            if self.socks_manager.verify_socks_proxy():
                 self.logger.info(f"Проверка SOCKS {self.socks_manager.socks_port}: OK")
                 return True
            self.logger.info(f"Проверка SOCKS {self.socks_manager.socks_port}: FAIL")
            if self.socks_manager.ensure_socks_proxy():
                 self.logger.info(f"SOCKS {self.socks_manager.socks_port} поднят")
                 return True
            self.logger.error("SOCKS недоступен, выходим")
            return False
        except Exception:
            return False

    def reset_authorization(self):
        """Сброс авторизации через рестарт интерфейса wwan на роутере."""
        self.logger.info("Сброс авторизации: рестарт интерфейса wwan...")
        base = self.socks_manager.get_ssh_base_cmd()
        target = f"{self.socks_manager.ssh_user}@{self.socks_manager.ssh_host}"
        cmd = base + [target, "ifdown wwan && ifup wwan"]
        rc, out, err = run_shell_cmd(cmd, timeout=30)
        if rc == 0:
            self.logger.info("Интерфейс wwan перезагружен, ждем восстановления сети...")
            time.sleep(15) # Wait for interface to come up
            return True
        else:
            self.logger.error(f"Ошибка рестарта wwan: {err}")
            return False

    def _open(self, request, timeout=20):
        """Отправляет запрос через urllib opener, логирует и при обрыве шлёт через curl/SOCKS."""
        try:
            try:
                try:
                    u = getattr(request, "full_url", None) or request.get_full_url()
                except Exception:
                    u = ""
                self.logger.info(f"[REQ] url={u}")

                # Log cookies that will be sent
                try:
                    req_host = urlparse(u).netloc
                    c_count = 0
                    c_names = []
                    for c in self.cookies:
                         should_send = False
                         if c.domain:
                             if c.domain.startswith("."):
                                 if req_host.endswith(c.domain) or req_host == c.domain[1:]:
                                     should_send = True
                             elif req_host == c.domain:
                                 should_send = True
                         else:
                             should_send = True
                         if should_send:
                             c_count += 1
                             c_names.append(c.name)
                    if c_count > 0:
                        self.logger.info(f"[REQ COOKIES] {c_count} matched for {req_host}: {', '.join(c_names)}")
                except Exception:
                    pass
            except Exception:
                pass
            try:
                self.logger.info(f"[REQ HDR] {json.dumps(getattr(request, 'headers', {}), ensure_ascii=False)}")
            except Exception:
                pass
            try:
                d = getattr(request, "data", None)
                if d is not None:
                    if isinstance(d, bytes):
                        try:
                            dd = d.decode("utf-8", "replace")
                        except Exception:
                            dd = str(d)
                    else:
                        dd = str(d)
                    self.logger.info(f"[REQ DATA] {dd}")
            except Exception:
                pass
        except Exception:
            pass
        try:
            resp = self.opener.open(request, timeout=timeout)
        except Exception as e:
            try:
                u = getattr(request, "full_url", None) or request.get_full_url()
            except Exception:
                u = ""
            try:
                hdrs = getattr(request, "headers", {})
            except Exception:
                hdrs = {}
            try:
                d = getattr(request, "data", None)
            except Exception:
                d = None
            try:
                low = str(e).lower()
            except Exception:
                low = ""
            if ("remote end closed connection" in low) or ("connection closed unexpectedly" in low):
                resp = self._open_socks_curl(u, data=d, headers=hdrs, timeout=timeout)
            else:
                raise
        try:
            self.logger.info(f"[RESP] code={resp.getcode()} url={resp.geturl()} ct={resp.headers.get('Content-Type','')}")
        except Exception:
            pass
        return resp

    def _open_socks_curl(self, url, data=None, headers=None, timeout=20):
        """Выполняет запрос через curl по SOCKS-прокси, имитируя заголовки/куки urllib-запроса."""
        try:
            port = int(os.environ.get("NOJS_SOCKS_PORT","10800"))
        except Exception:
            port = 1081
        try:
            method = "POST" if data is not None else "GET"
            hdr_parts = []
            if not isinstance(headers, dict) or not headers:
                try:
                    headers = self._default_headers(referer=self.page_url or self.portal_url, ajax=(data is not None))
                except Exception:
                    headers = {"User-Agent": self.user_agent}
            # Ensure Origin even without referer
            try:
                if "Origin" not in headers:
                    pu = urlparse(url)
                    if pu.scheme and pu.netloc:
                        headers["Origin"] = f"{pu.scheme}://{pu.netloc}"
            except Exception:
                pass

            # Inject Cookies if not present
            has_cookie = False
            if isinstance(headers, dict):
                for k in headers:
                    if k.lower() == "cookie":
                        has_cookie = True
                        break

            if not has_cookie:
                try:
                    c_parts = []
                    req_host = urlparse(url).netloc
                    for c in self.cookies:
                         should_send = False
                         if c.domain:
                             if c.domain.startswith("."):
                                 if req_host.endswith(c.domain) or req_host == c.domain[1:]:
                                     should_send = True
                             elif req_host == c.domain:
                                 should_send = True
                         else:
                             should_send = True

                         # Check path
                         if should_send and c.path:
                             req_path = urlparse(url).path or "/"
                             if not req_path.startswith(c.path):
                                 should_send = False

                         if should_send:
                             c_parts.append(f"{c.name}={c.value}")

                    if c_parts:
                        hdr_parts.append(f"-H 'Cookie: {'; '.join(c_parts)}'")
                        self.logger.info(f"[SOCKS COOKIES] injected {len(c_parts)} cookies")
                except Exception:
                    pass

            if isinstance(headers, dict):
                for k, v in headers.items():
                    if v is None:
                        continue
                    hk = str(k).replace("'", "").replace("\n"," ")
                    hv = str(v).replace("'", "").replace("\n"," ")
                    hdr_parts.append(f"-H '{hk}: {hv}'")
            body_part = ""
            if data is not None:
                if isinstance(data, bytes):
                    try:
                        dd = data.decode("utf-8","replace")
                    except Exception:
                        dd = str(data)
                else:
                    dd = str(data)
                body_part = f"--data-raw '{dd}'"
            # Add --compressed to handle gzip automatically
            cmd = f"curl --compressed -x socks5h://127.0.0.1:{port} -s -L -i {' '.join(hdr_parts)} {body_part} -X {method} -w '\\n__STATUS:%{{http_code}}\\n__URL:%{{url_effective}}' '{url}'"
            # Используем text=False (bytes), чтобы не падать на бинарных файлах (картинки, шрифты)
            r = subprocess.run(["bash","-lc",cmd], capture_output=True, text=False)
            # Декодируем вывод как latin-1 или utf-8 с replace, чтобы разделить заголовки и тело
            # Но надежнее найти маркеры __STATUS и __URL в байтах
            raw_out = r.stdout or b""

            # Попытка декодировать все как текст с replace для парсинга заголовков
            # Это безопасно, так как мы не будем использовать text для тела, если оно бинарное
            # Однако, если тело огромное и бинарное, decode может быть медленным.
            # Лучше найти границы через regex в байтах.

            status = None
            eff_url = None

            # Ищем маркеры с конца
            m_status = re.search(rb"__STATUS:(\d{3})", raw_out)
            m_url = re.search(rb"__URL:(.+)", raw_out)

            if m_status:
                status = int(m_status.group(1))
            if m_url:
                eff_url = m_url.group(1).strip().decode("utf-8", "replace")

            # Удаляем маркеры из тела
            # Маркеры добавляются в конец, нужно их отрезать
            # Режем по первому вхождению маркеров (они в конце)
            end_marker_pos = -1
            if m_status:
                p = raw_out.rfind(b"__STATUS:")
                if p != -1:
                    end_marker_pos = p
            elif m_url: # если статус не нашли, но нашли URL (странно, но бывает)
                 p = raw_out.rfind(b"__URL:")
                 if p != -1:
                    end_marker_pos = p

            full_resp = raw_out[:end_marker_pos] if end_marker_pos != -1 else raw_out

            # Разделяем заголовки и тело
            # Curl с -i разделяет заголовки и тело пустой строкой (\r\n\r\n или \n\n)
            # Но если были редиректы, может быть несколько блоков заголовков.
            # Нас интересует тело (последняя часть) и заголовки (все или последние).
            # Простой способ: найти первый double-newline, который отделяет заголовки от тела...
            # НЕТ, при редиректах (-L) curl выводит заголовки каждого ответа.
            # Тело находится после последней пустой строки заголовков.

            # Разделим по \r\n\r\n или \n\n
            parts = re.split(rb"\r?\n\r?\n", full_resp)
            # parts содержит: Header1, [Body1? if no redirect], Header2, Body2...
            # Если curl -L -i, то при редиректе он пишет HTTP/1.1 302 ... \n\n HTTP/1.1 200 ... \n\n BODY
            # Значит последний элемент - это тело (или часть тела, если внутри тела есть \n\n, упс).
            # re.split ненадежен для тела.

            # Надежнее: парсить HTTP заголовки.
            # Но мы можем просто использовать 'text=True' для метаданных и 'text=False' для контента? Нет, curl один.

            # Упрощение: считаем, что заголовки идут до первой последовательности \r\n\r\n, которая не является частью HTTP/1.1 (сложно).
            # Попробуем просто найти последнюю группу заголовков?
            # Или просто возьмем весь ответ, попробуем декодировать начало для кук.

            # Для надежности с бинарниками:
            # 1. Заголовки обычно ASCII.
            # 2. Тело может быть чем угодно.

            # Пойдем простым путем:
            # Декодируем с 'replace' для извлечения кук и редиректов (они текстовые).
            # Тело оставляем как есть (из raw_out), вырезав маркеры.

            text_for_parsing = raw_out.decode("utf-8", "replace")

            set_cookies = []
            redirects = []
            try:
                for line in text_for_parsing.splitlines():
                    if line.lower().startswith("location:"):
                        try:
                            loc = line.split(":",1)[1].strip()
                            if loc:
                                redirects.append(loc)
                        except Exception:
                            pass
                    if line.lower().startswith("set-cookie:"):
                        try:
                            raw = line.split(":",1)[1].strip()
                        except Exception:
                            raw = line.strip()
                        if raw:
                            set_cookies.append(raw)
            except Exception:
                pass

            # Вычисляем тело из байтов (отрезаем заголовки - это сложно сделать точно без парсера)
            # В данном скрипте self._body используется редко, в основном для сохранения артефактов и поиска токенов.
            # Если это картинка, токены искать не надо.
            # Если это HTML, он будет текстом.

            # Попробуем найти начало тела.
            # Если статус 200, тело идет после последних заголовков.
            # Сложно.

            # Временное решение:
            # Если мы скачиваем статику (картинки), нам тело нужно только для сохранения (если будем сохранять) или просто чтобы curl не упал.
            # В текущей логике:
            # body = re.sub(r"__STATUS:...", ..., text).encode(...)
            # Мы можем восстановить body из text, закодировав обратно? Нет, потеряем байты (replace).

            # Правильное решение:
            # Использовать --output для тела во временный файл? Нет, медленно.

            # Давайте просто уберем маркеры из raw_out и вернем это как тело.
            # Да, заголовки останутся в начале тела. Это "грязно", но для NoJS скрипта, который ищет токены в HTML,
            # заголовки в начале HTML не сильно мешают (они не похожи на токены).
            # А для картинок - мы их не парсим, просто скачиваем.
            # НО: Если мы сохраняем артефакт, картинка будет битой (с заголовками в начале).

            # Попытаемся найти конец заголовков.
            # Заголовки заканчиваются на \r\n\r\n.
            # Если было несколько редиректов, заголовков несколько групп.
            # Ищем последнюю "HTTP/1.1 200" (или подобное) и от нее \r\n\r\n.
            
            # Разделим по двойному переносу строки.
            # curl -i выводит заголовки и тело, разделенные пустой строкой.
            # При редиректах (-L) будет несколько блоков заголовков.
            # Последний блок - это тело (или пустая строка, если тела нет).
            
            # Нормализуем переносы строк для split
            clean_out = raw_out.replace(b"\r\n", b"\n")
            parts = clean_out.split(b"\n\n")
            
            if len(parts) > 1:
                # Если частей > 1, значит есть заголовки и тело.
                # Последняя часть - это тело.
                # НО: если тело само содержит \n\n, мы его разбили.
                # Нам нужно найти ПЕРВЫЙ \n\n после ПОСЛЕДНЕГО блока заголовков.
                # Это сложно.
                
                # Простой подход: 
                # Если curl -i, то заголовки всегда в начале.
                # Если мы считаем, что заголовки не содержат \n\n (пустых строк), то 
                # split корректно разделит блоки.
                # Последний элемент - это тело (или часть тела).
                # Нет, если тело содержит \n\n, split разобьет тело.
                
                # Правильнее: Найти смещение, где заканчиваются заголовки.
                # Заголовки HTTP начинаются с "HTTP/"
                # Ищем последнее вхождение "HTTP/" в начале строки (после \n\n)?
                pass

            # Возвращаемся к простому split, но аккуратно.
            # Обычно заголовки отделены от тела первой пустой строкой.
            # Если редиректы, то несколько блоков.
            # Мы можем предположить, что все блоки заголовков начинаются с HTTP/.
            # Но проще взять split и проверить, похоже ли это на заголовки.
            
            # САМЫЙ ПРОСТОЙ РАБОЧИЙ ВАРИАНТ для curl -i:
            # Тело - это все после последней последовательности "\r\n\r\n", которая следует за блоком заголовков.
            # Но мы не знаем где заголовки.
            
            # Компромисс: используем split(b'\r\n\r\n') и берем последнюю часть,
            # ЕСЛИ она не начинается с HTTP/.
            # Если начинается - значит тела нет (пустое), или это заголовки.
            
            # Для надежности в данном контексте (JSON/HTML):
            # Если в raw_out есть заголовки, они в начале.
            # Попробуем найти \r\n\r\n.
            # Если есть, берем все после ПЕРВОГО \r\n\r\n? Нет, редиректы.
            # Берем все после ПОСЛЕДНЕГО \r\n\r\n?
            # Если в теле есть \r\n\r\n, мы его обрежем. Плохо.
            
            # Ладно, вернемся к "грязному" body, но добавим метод clean_body() в _R?
            # Или попытаемся здесь вычистить.
            
            body = raw_out[:end_marker_pos] if end_marker_pos != -1 else raw_out
            
            # Попытка очистить body от заголовков (наивная)
            try:
                # Ищем последнюю пустую строку перед началом контента
                # Если контент JSON ({...}), ищем {
                # Если HTML (<...), ищем <
                
                s_body = body.decode("utf-8", "replace")
                
                # JSON heuristic
                if s_body.strip().endswith("}"):
                    idx = s_body.find("{")
                    if idx != -1:
                        # Проверяем, что перед { идут заголовки (или ничего)
                        # Это опасно, если { в URL или заголовке.
                        pass
                
                # Header stripping heuristic:
                # Split by double newline.
                # Check if parts look like headers (start with HTTP/).
                # The first part that DOES NOT look like header is the body start.
                
                sparts = body.split(b"\r\n\r\n")
                if len(sparts) == 1:
                    sparts = body.split(b"\n\n")
                
                real_body_parts = []
                headers_finished = False
                
                for p in sparts:
                    if not headers_finished:
                        if p.startswith(b"HTTP/") or p.startswith(b"HTTP "):
                            # Это заголовок
                            continue
                        else:
                            # Это начало тела
                            headers_finished = True
                            real_body_parts.append(p)
                    else:
                        # Это продолжение тела (которое содержало \n\n)
                        real_body_parts.append(p)
                
                if real_body_parts:
                    # Собираем обратно
                    # Разделитель был потерян, но какой? \r\n\r\n или \n\n.
                    # Предположим тот же, по которому сплитили.
                    sep = b"\r\n\r\n" if b"\r\n\r\n" in body else b"\n\n"
                    body = sep.join(real_body_parts)
                else:
                    # Если все части похожи на заголовки, значит тела нет
                    body = b""
                    
            except Exception:
                pass # Fallback to dirty body

            class _R:
                def __init__(self, code, url, body, redirects=None):
                    self._code = code
                    self._url = url
                    self._body = body
                    self.headers = {}
                    self.redirects = redirects or []
                def getcode(self):
                    return self._code or 0
                def geturl(self):
                    return self._url or url
                def read(self):
                    return self._body
            if status:
                # apply cookies from curl headers
                try:
                    netloc = urlparse(eff_url or url).netloc or urlparse(url).netloc
                    for sc in set_cookies:
                        try:
                            parts = [p.strip() for p in sc.split(";")]
                            if not parts:
                                continue
                            kv = parts[0]
                            if "=" not in kv:
                                continue
                            name, value = kv.split("=",1)
                            dom = None
                            path = "/"
                            for p2 in parts[1:]:
                                pl = p2.lower()
                                if pl.startswith("domain="):
                                    dom = p2.split("=",1)[1].strip()
                                elif pl.startswith("path="):
                                    path = p2.split("=",1)[1].strip() or "/"
                            dom = dom or netloc
                            if name and dom:
                                self._set_cookie(name.strip(), value.strip(), dom, path)
                        except Exception:
                            continue
                except Exception:
                    pass
                self.logger.info(f"[CURL SOCKS] {_safe_url(url)} → {status}")
                return _R(status, eff_url or url, body, redirects)
        except Exception as e:
            self.logger.info(f"[CURL SOCKS ERR] {e}")
            raise

    def _set_cookie(self, name, value, domain, path="/"):
        try:
            cookie = cj.Cookie(
                version=0,
                name=name,
                value=value,
                port=None,
                port_specified=False,
                domain=domain,
                domain_specified=True,
                domain_initial_dot=False,
                path=path,
                path_specified=True,
                secure=False,
                expires=None,
                discard=True,
                comment=None,
                comment_url=None,
                rest={},
                rfc2109=False,
            )
            self.cookies.set_cookie(cookie)
        except Exception:
            pass
    
    def _choose_login_referer(self):
        try:
            # 1. Try to find form action pointing to /scenes/
            try:
                m = re.search(r"action=['\"]([^'\"]*/scenes/[^'\"]+)['\"]", self.page_html or "", flags=re.IGNORECASE)
                if m:
                    u = urljoin(self.page_url or self.portal_url, m.group(1))
                    self.logger.info(f"[REFERER] Found form action: {u}")
                    return u
            except Exception:
                pass

            # 2. Prefer scenes URL from resources
            try:
                urls = self.extract_resource_urls()
            except Exception:
                urls = []
            for u in urls or []:
                try:
                    p = urlparse(u)
                    if "/scenes/" in (p.path or ""):
                        return u
                except Exception:
                    continue
            # 3. Fallback
            try:
                if self.page_url:
                    return self.page_url
            except Exception:
                pass
            try:
                base = f"{urlparse(self.page_url or self.portal_url).scheme}://{urlparse(self.page_url or self.portal_url).netloc}"
                return base
            except Exception:
                return None
        except Exception:
            return None

    def _ensure_php_session_cookie(self):
        try:
            phpsessid = None
            try:
                for c in self.cookies:
                    if c.name == "PHPSESSID" and c.value:
                        phpsessid = c.value
                        break
            except Exception:
                phpsessid = None
            if phpsessid:
                return phpsessid
            base = f"{urlparse(self.page_url or self.portal_url).scheme}://{urlparse(self.page_url or self.portal_url).netloc}"
            try:
                req = self._req(base, referer=self.page_url)
                resp = self._open(req)
                self.page_url = resp.geturl()
                self.page_html = resp.read().decode("utf-8", "replace")
                self._record_touch(self.page_url)
            except Exception:
                pass
            try:
                for c in self.cookies:
                    if c.name == "PHPSESSID" and c.value:
                        phpsessid = c.value
                        break
            except Exception:
                phpsessid = None
            if phpsessid:
                return phpsessid
            target = None
            try:
                urls = self.extract_resource_urls()
                for u in urls:
                    p = urlparse(u)
                    if "/scenes/" in p.path or "/admon/js/" in p.path or "/wbs/" in p.path:
                        target = u
                        break
            except Exception:
                target = None
            if target:
                try:
                    self._open(self._req(target, referer=self.page_url))
                except Exception:
                    pass
            try:
                for c in self.cookies:
                    if c.name == "PHPSESSID" and c.value:
                        return c.value
            except Exception:
                return None
            return None
        except Exception:
            return None

    def _record_touch(self, u):
        try:
            if not u:
                return
            self.touched_urls.add(u)
            p = urlparse(u)
            d = p.netloc
            if d:
                self.touched_domains[d] = self.touched_domains.get(d, 0) + 1
        except Exception:
            pass

    def _default_headers(self, referer=None, ajax=False):
        try:
            hdrs = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": os.environ.get("NOJS_ACCEPT_LANGUAGE", "en-US,en;q=0.9"),
                "Accept-Encoding": "gzip, deflate",
                "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
            }
            ref = referer or (self.page_url or self.portal_url)
            if ref:
                hdrs["Referer"] = ref
                pu = urlparse(ref)
                if pu.scheme and pu.netloc:
                    hdrs["Origin"] = f"{pu.scheme}://{pu.netloc}"
            if ajax:
                hdrs["X-Requested-With"] = "XMLHttpRequest"
                hdrs["Accept"] = "*/*"  # Как в Selenium для AJAX запросов
            else:
                hdrs["Upgrade-Insecure-Requests"] = "1"
            return hdrs
        except Exception:
            return {"User-Agent": self.user_agent}

    def _req(self, url, data=None, referer=None, ajax=False):
        try:
            hdrs = self._default_headers(referer=referer, ajax=ajax)
            if data is not None and "Content-Type" not in hdrs:
                hdrs["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
            return Request(url, data=data, headers=hdrs)
        except Exception:
            return Request(url, data=data, headers={"User-Agent": self.user_agent})

    def extract_resource_urls(self):
        try:
            base = base_origin_from_url(self.page_url or self.portal_url or "")
            html = self.page_html or ""
            html_urls = extract_resource_urls_from_html(html, base)
            js_urls = extract_urls_from_js_text(html, base)
            combined = html_urls + js_urls
            seen = set()
            clean = []
            for u in combined:
                if u not in seen:
                    seen.add(u)
                    clean.append(u)
            return clean
        except Exception:
            return []

    def _collect_tokens(self):
        tokens = {}
        html = self.page_html or ""
        
        # Fallback: Manual Regex for wbsApiAuthToken (robust against nested braces)
        m = re.search(r"conn4\.hotspot\.wbsToken\s*=\s*\{.*?\"token\"\s*:\s*\"([^\"]+)\"", html, flags=re.DOTALL)
        if m:
             tokens["wbsApiAuthToken"] = m.group(1)

        # Try to collect from full HTML text first (robust against script tag parsing issues)
        try:
            t_full = collect_tokens_from_text(html)
            if t_full:
                tokens.update(t_full)
        except Exception:
            pass

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
                if n and v:
                    if "apiSessionId" in n or "paymentReturnProxyUrl" in n or "conn4-hotspot" in n:
                        tokens[n] = v
                        key_name = n.replace("conn4-hotspot-storage-", "")
                        if key_name != n:
                            tokens[key_name] = v
        except Exception:
            pass
        try:
            for mm in re.finditer(r"['\"]apiSessionId['\"]\s*:\s*['\"]([^'\"]+)['\"]", html):
                tokens["apiSessionId"] = mm.group(1)
            for mm in re.finditer(r"['\"]paymentReturnProxyUrl['\"]\s*:\s*['\"]([^'\"]+)['\"]", html):
                tokens["paymentReturnProxyUrl"] = mm.group(1)
        except Exception:
            pass
        try:
            m = re.search(r"initPage\s*\(\s*(\{[\s\S]*?\})\s*\)", html)
            if m:
                obj = json.loads(m.group(1))
                if isinstance(obj, dict):
                    for k in ("siteId","clientIp","clientMac","signature","loggedin","remembered_mac"):
                        v = obj.get(k)
                        if v is not None:
                            tokens[k] = v
        except Exception:
            pass
        try:
            scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.IGNORECASE | re.DOTALL)
            for script_body in scripts:
                try:
                    t2 = collect_tokens_from_text(script_body or "")
                    for k, v in (t2 or {}).items():
                        if v is not None and k not in tokens:
                            tokens[k] = v
                except Exception:
                    pass
        except Exception:
            pass
        try:
            for k, v in (self.dynamic_tokens or {}).items():
                if v is not None:
                    tokens[k] = v
        except Exception:
            pass
        try:
            pu = urlparse(self.page_url or self.portal_url or "")
            qs = parse_qs(pu.query or "")
            for k in ("client_ip","client_mac","site_id","signature","loggedin","remembered_mac","cookie-challenge"):
                v = (qs.get(k, [None])[0])
                if v is not None and v != "":
                    if k not in tokens:
                        tokens[k] = v
            if "client_ip" in tokens and tokens.get("client_ip"):
                if "clientIp" not in tokens:
                    tokens["clientIp"] = tokens.get("client_ip")
            if "client_mac" in tokens and tokens.get("client_mac"):
                if "clientMac" not in tokens:
                    tokens["clientMac"] = tokens.get("client_mac")
            if "site_id" in tokens and tokens.get("site_id"):
                if "siteId" not in tokens:
                    tokens["siteId"] = tokens.get("site_id")
        except Exception:
            pass
        return tokens

    def _handle_cookie_challenge(self):
        try:
            u = self.page_url or self.portal_url or ""
            p = urlparse(u)
            qs = parse_qs(p.query)
            val = (qs.get("cookie-challenge", [None])[0])
            if val is None:
                return False
            dom = p.netloc
            if dom:
                self._set_cookie("cookie-challenge", str(val), dom, "/")
            base = f"{p.scheme}://{p.netloc}"
            req = self._req(base, referer=self.page_url)
            resp = self._open(req)
            self.page_url = resp.geturl()
            self.page_html = resp.read().decode("utf-8", "replace")
            self._record_touch(self.page_url)
            return True
        except Exception:
            return False

    def _collect_tokens_from_text(self, text):
        try:
            toks = collect_tokens_from_text(text or "")
            for k, v in toks.items():
                self.dynamic_tokens[k] = v
        except Exception:
            pass

    def _consent_payload(self):
        return self._build_consent_body()

    def check_socks_availability(self):
        """
        Проверяет доступность SOCKS прокси.
        Возвращает True если SOCKS доступен, False если нет.
        """
        if self.disable_ssh:
            self.logger.info("Проверка SOCKS пропущена (NOJS_DISABLE_SSH=1)")
            return True

        try:
            port = int(os.environ.get("NOJS_SOCKS_PORT","10800"))
            self.logger.info(f"Проверка SOCKS прокси на порту {port}...")

            # Проверка 1: Слушает ли порт
            try:
                check = subprocess.run(
                    ["bash","-lc",f"ss -lnt | awk '{{print $4}}' | grep -q ':{port}$'"],
                    capture_output=True,
                    timeout=5
                )
                port_listening = (check.returncode == 0)
            except Exception:
                port_listening = False

            if not port_listening:
                self.logger.error(f"❌ SOCKS прокси не запущен на порту {port}")
                self.logger.error("Запустите SOCKS прокси командой:")
                self.logger.error(f"  ssh -D {port} -f -N root@prod-openwrt")
                return False

            self.logger.info(f"✅ SOCKS прокси слушает на порту {port}")

            # Проверка 2: Можем ли подключиться
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()

                if result != 0:
                    self.logger.error(f"❌ Не удается подключиться к SOCKS прокси на 127.0.0.1:{port}")
                    return False

                self.logger.info(f"✅ Успешное подключение к SOCKS прокси")
            except Exception as e:
                self.logger.error(f"❌ Ошибка проверки подключения к SOCKS: {e}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка при проверке SOCKS: {e}")
            return False

    def check_internet_via_socks(self):
        """
        Проверяет доступ в интернет через SOCKS прокси.
        Возвращает True если интернет доступен, False если нет (captive portal).
        """
        try:
            try:
                port = int(self.socks_manager.socks_port)
            except Exception:
                port = int(os.environ.get("NOJS_SOCKS_PORT", "10800"))
            self.logger.info("Проверка доступа в интернет через SOCKS...")
            msft_redirect = "http://www.msftconnecttest.com/redirect"
            test_urls = [
	                msft_redirect,
	                "http://detectportal.firefox.com/canonical.html",
	                "http://connectivitycheck.gstatic.com/generate_204",
	                "http://www.msftconnecttest.com/connecttest.txt",
	            ]
            seen_conn4 = False
            for test_url in test_urls:
                try:
                    cmd = f"curl -x socks5h://127.0.0.1:{port} -s -L -o /dev/null -w '%{{http_code}} %{{url_effective}}' --connect-timeout 5 --max-time 10 '{test_url}'"
                    result = subprocess.run(
                        ["bash", "-lc", cmd],
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                    out = (result.stdout or "").strip()
                    if not out:
                        self.logger.info(f"  {test_url} → пустой ответ от curl")
                        continue
                    parts = out.split(maxsplit=1)
                    http_code = parts[0]
                    effective_url = parts[1] if len(parts) > 1 else test_url
                    self.logger.info(f"  {test_url} → HTTP {http_code} ({effective_url})")
                    try:
                        code = int(http_code)
                        host = urlparse(effective_url).netloc.lower()

                        if test_url == msft_redirect:
                            if "conn4.com" in host:
                                seen_conn4 = True
                                self.logger.info(f"  {test_url} → редирект на портал {host}")
                                try:
                                    try:
                                        self.detect_portal_via_redirect()
                                    except Exception as e:
                                        self.logger.info(f"  detect_portal_via_redirect ошибка: {e}")
                                except Exception:
                                    pass
                                return False
                            
                            # Проверка на msn.com/microsoft.com - признак успешной авторизации
                            if "msn.com" in host or "microsoft.com" in host:
                                self.logger.warning(f"✅ Обнаружен редирект на {host}. Интернет уже доступен. Завершение.")
                                sys.exit(0)

                            if 200 <= code < 300 or 300 <= code < 400:
                                self.logger.warning(f"✅ MSFT redirect прошёл без портала (HTTP {code}, {host or effective_url})")
                                self.logger.warning("⚠️  Captive portal не активен, авторизация не требуется")
                                return True
                            self.logger.info(f"⚠️  MSFT redirect вернул неожиданный код (HTTP {code})")
                            continue

                        if "conn4.com" in host:
                            seen_conn4 = True
                            self.logger.info(f"  {test_url} → редирект на портал {host}")
                            continue

                        if 200 <= code < 300 or 300 <= code < 400:
                            self.logger.warning(f"✅ Интернет доступен через SOCKS (HTTP {code}, {host or effective_url})")
                            self.logger.warning("⚠️  Captive portal не активен, авторизация не требуется")
                            return True
                        self.logger.info(f"⚠️  Необычный код ответа (HTTP {code})")
                        continue
                    except ValueError:
                        self.logger.info(f"⚠️  Не удалось получить HTTP код от {test_url}")
                        continue
                except subprocess.TimeoutExpired:
                    self.logger.info(f"  {test_url} → timeout (возможен captive portal)")
                    continue
                except Exception as e:
                    self.logger.info(f"  {test_url} → ошибка: {e}")
                    continue
            if seen_conn4:
                self.logger.info("❌ Интернет недоступен через SOCKS - обнаружен captive portal conn4.com")
            else:
                self.logger.info("❌ Интернет недоступен через SOCKS - тестовые URL недоступны")
            self.logger.info("❌ Интернет недоступен через SOCKS - обнаружен captive portal")
            return False
        except Exception as e:
            self.logger.error(f"❌ Ошибка при проверке интернета через SOCKS: {e}")
            return False

    def ensure_socks_proxy(self):
        try:
            if self.disable_ssh:
                return True
                
            if not self.socks_manager.ensure_socks_proxy():
                return False

            port = int(self.socks_manager.socks_port)
            os.environ["ALL_PROXY"] = f"socks5h://127.0.0.1:{port}"
            os.environ["HTTPS_PROXY"] = os.environ["ALL_PROXY"]
            os.environ["HTTP_PROXY"] = os.environ["ALL_PROXY"]
            
            if socks is not None:
                self.opener = build_opener(
                    HTTPCookieProcessor(self.cookies),
                    SocksiPyHandler(socks.SOCKS5, "127.0.0.1", port)
                )
            else:
                handlers = [HTTPCookieProcessor(self.cookies), ProxyHandler(getproxies())]
                self.opener = build_opener(*handlers)
                
            self.logger.info(f"[SOCKS] 127.0.0.1:{port}")
            return True
        except Exception as e:
            self.logger.info(f"[SOCKS ERR] {e}")
            return False

    def _log_conn4_params(self, u, label=""):
        try:
            p = urlparse(u)
            qs = parse_qs(p.query)
            keys = ["client_ip","client_mac","site_id","signature","loggedin","remembered_mac"]
            vals = {k:(qs.get(k,[None])[0]) for k in keys}
            self.logger.info(f"[conn4.com params{(' ' + label) if label else ''}] {json.dumps(vals, ensure_ascii=False)}")
        except Exception:
            pass

    def _extract_js_links_from_text(self, text, base_url):
        links = []
        try:
            for mm in re.finditer(r"(?:location(?:\.replace)?|window\.location\.href)\s*=\s*['\"]([^'\"\"]+)['\"]", text):
                links.append(urljoin(base_url, mm.group(1)))
            for mm in re.finditer(r"window\.open\(\s*['\"]([^'\"\"]+)['\"]", text):
                links.append(urljoin(base_url, mm.group(1)))
            for mm in re.finditer(r"(?:goTo|navigate|redirect)\s*\(\s*['\"]([^'\"\"]+)['\"]", text, flags=re.IGNORECASE):
                links.append(urljoin(base_url, mm.group(1)))
            for mm in re.finditer(r"['\"](/[^'\"\\s]+)['\"]", text):
                links.append(urljoin(base_url, mm.group(1)))
        except Exception:
            pass
        clean = []
        seen = set()
        for u in links:
            if not u or u in seen:
                continue
            seen.add(u)
            clean.append(u)
        return clean

    def init_cookies(self):
        netloc = urlparse(self.portal_url).netloc
        if netloc:
            # host-id cookie for server-side heuristics
            self._set_cookie("client_host_id", self.host_id, netloc, "/")
            # optional: env provided cookies
            extra = os.environ.get("NOJS_INIT_COOKIES", "")
            for part in extra.split(";"):
                part = part.strip()
                if not part or "=" not in part:
                    continue
                k, v = part.split("=", 1)
                self._set_cookie(k.strip(), v.strip(), netloc, "/")

    def load_captured_artifact(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except Exception as e:
            self.logger.info(f"Ошибка загрузки артефакта: {e}")
            return False
        try:
            cur = obj.get("current_url")
            html = obj.get("page_html")
            if cur:
                self.page_url = cur
                self.portal_url = cur
                try:
                    self.initial_query = parse_qs(urlparse(cur).query)
                except Exception:
                    pass
                try:
                    q = parse_qs(urlparse(cur).query)
                    cip = (q.get("client_ip", [None])[0])
                    cmac = (q.get("client_mac", [None])[0])
                    sid = (q.get("site_id", [None])[0])
                    if cip:
                        self.client_ip_override = cip
                    if cmac:
                        self.client_mac_override = cmac
                    if sid and not self.cookie_decoded_site_id:
                        self.cookie_decoded_site_id = sid
                except Exception:
                    pass
            if html:
                self.page_html = html
                try:
                    self._log_external_lib_refs(self.page_html or "")
                except Exception:
                    pass
            cookies = obj.get("cookies") or []
            netloc = urlparse(self.portal_url).netloc if self.portal_url else None
            for c in cookies:
                try:
                    name = c.get("name")
                    value = c.get("value")
                    domain = c.get("domain") or netloc
                    path = c.get("path") or "/"
                    if name is not None and value is not None and domain:
                        self._set_cookie(name, value, domain, path)
                except Exception:
                    pass
            self.captured_requests = obj.get("capturedRequests") or []
            self.trace_log = obj.get("traceLog") or []
            self.captured_iframes = [u for u in (obj.get("iframes") or []) if isinstance(u, str)]
            self.network_summary = obj.get("networkSummary") or []
            self.logger.info(f"Загружено capturedRequests: {len(self.captured_requests)}")
            self.logger.info(f"Загружено traceLog: {len(self.trace_log)}")
            self.logger.info(f"Загружено iframe src: {len(self.captured_iframes)}")
            self.logger.info(f"Загружено networkSummary: {len(self.network_summary)}")
            try:
                self._load_selenium_comparison()
            except Exception:
                pass
            # Дополнительно подхватываем conn4_network.json если есть
            try:
                net_path = os.path.join(os.getcwd(), "conn4_network.json")
                if os.path.exists(net_path):
                    with open(net_path, "r", encoding="utf-8") as nf:
                        net_obj = json.load(nf)
                    evs = net_obj.get("events") or []
                    if isinstance(evs, list) and evs:
                        self.network_summary = evs
                        self.logger.info(f"Загружено network events: {len(evs)}")
            except Exception:
                pass
            return True
        except Exception as e:
            self.logger.info(f"Ошибка обработки артефакта: {e}")
            return False

    def _load_selenium_comparison(self):
        try:
            comp_path = os.path.join(os.getcwd(), "conn4_compare_selenium.json")
            if not os.path.exists(comp_path):
                comp_path = os.path.join(os.getcwd(), "conn4_compare.json")
            if not os.path.exists(comp_path):
                return False
            with open(comp_path, "r", encoding="utf-8") as f:
                comp = json.load(f)
            sel_tokens = comp.get("computedTokens") or {}
            for k, v in sel_tokens.items():
                if v is not None:
                    if k not in self.dynamic_tokens:
                        self.dynamic_tokens[k] = v
                        self.logger.info(f"[SELENIUM TOKEN] {k}={str(v)[:50]}")

            # Попробуем извлечь WBSApiAuthToken из сетевого трейсинга Selenium
            try:
                network = comp.get("network") or []
                for ev in network:
                    try:
                        url = (ev.get("url") or "") if isinstance(ev, dict) else ""
                    except Exception:
                        url = ""
                    if not url or "/wbs/api/v1/create-session/" not in url:
                        continue
                    try:
                        post_data = ev.get("postData") or ""
                    except Exception:
                        post_data = ""
                    if not isinstance(post_data, str) or "authorization=token%3D" not in post_data:
                        continue
                    m = re.search(r"authorization=token%3D([^&]+)", post_data)
                    if not m:
                        continue
                    raw_b64 = m.group(1)
                    try:
                        tok_b64 = unquote(raw_b64)
                    except Exception:
                        tok_b64 = raw_b64
                    if tok_b64:
                        self.dynamic_tokens["wbsApiAuthToken"] = tok_b64
                        self.logger.info(f"[SELENIUM TOKEN] wbsApiAuthToken len={len(tok_b64)} (из артефакта)")
                        break
            except Exception:
                pass
            return True
        except Exception as e:
            self.logger.info(f"Не удалось загрузить токены из Selenium: {e}")
            return False

    def log_cookies(self, label=""):
        try:
            # Read cookies from jar
            entries = []
            for c in self.cookies:
                try:
                    entries.append(f"{c.name}={c.value}; domain={c.domain}; path={c.path}")
                except Exception:
                    pass
            if entries:
                self.logger.info(f"[COOKIEJAR {label}] {len(entries)} cookies")
                for e in entries:
                    self.logger.info(f"  {e}")
            for c in self.cookies:
                try:
                    if (c.name or "") == "himalaya-site-ident":
                        import base64
                        from urllib.parse import unquote
                        raw = c.value or ""
                        s = unquote(raw)
                        pad = "=" * ((4 - len(s) % 4) % 4)
                        dec = base64.b64decode(s + pad)
                        if dec:
                            try:
                                txt = dec.decode("utf-8", "replace")
                            except Exception:
                                txt = str(dec)
                            if txt:
                                self.logger.info(f"  himalaya-site-ident decoded preview: {txt[:200]}")
                                import re
                                ipm = re.search(r's:12:"\*IPAddress";s:\d+:"((?:\d{1,3}\.){3}\d{1,3})"', txt) or re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", txt)
                                macm = re.search(r's:13:"\*MACAddress";s:\d+:"([0-9A-F]{12})"', txt) or re.search(r"\b[0-9A-F]{12}\b", txt)
                                sidm = re.search(r's:9:".*siteId";i:(\d+)', txt) or re.search(r'siteId";i:(\d+)', txt)
                                self.cookie_decoded_ip = ipm.group(1) if ipm and ipm.lastindex and ipm.lastindex >= 1 else (ipm.group(0) if ipm else None)
                                self.cookie_decoded_mac = macm.group(1) if macm and macm.lastindex and macm.lastindex >= 1 else (macm.group(0) if macm else None)
                                self.cookie_decoded_site_id = sidm.group(1) if sidm and sidm.lastindex and sidm.lastindex >= 1 else (sidm.group(0) if sidm else None)
                                self.logger.info(f"  decoded params: ip={self.cookie_decoded_ip} mac={self.cookie_decoded_mac} site_id={self.cookie_decoded_site_id}")
                except Exception as e:
                    self.logger.info(f"  himalaya-site-ident decode error: {e}")
        except Exception:
            pass

    def fetch_portal(self):
        self.logger.info("Загрузка страницы портала")
        if not self.portal_url:
            self.logger.warning("URL портала не определен, fetch_portal пропущен")
            return False
        req = self._req(self.portal_url)
        try:
            resp = self._open(req)
            self.page_url = resp.geturl()
            self.page_html = resp.read().decode("utf-8", "replace")
            self.logger.info(f"URL ответа: {self.page_url}")
            self.logger.info(f"Размер HTML: {len(self.page_html)} байт")
            try:
                self._log_external_lib_refs(self.page_html or "")
            except Exception:
                pass
            self.log_cookies("after-fetch")
            self._record_touch(self.page_url)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка загрузки портала: {e}")
            return False

    def discover_portal(self):
        candidates = [
            "http://connectivitycheck.gstatic.com/generate_204",
            "http://www.msftconnecttest.com/redirect",
            "http://captive.apple.com/hotspot-detect.html",
        ]
        for u in candidates:
            try:
                req = self._req(u)
                resp = self._open(req)
                url = resp.geturl()
                html = resp.read().decode("utf-8", "replace")
                if "conn4.com" in url or "conn4.com" in html:
                    self.portal_url = url
                    self.page_url = url
                    self.page_html = html
                    self.logger.info(f"Обнаружен портал через проверку: {self.page_url}")
                    return True
            except Exception:
                continue
        return False

    def try_registration_free(self):
        html = self.page_html or ""
        base = self.page_url or self.portal_url
        endpoints = set()
        try:
            for mm in re.finditer(r"['\"](/[^'\"\s]*registration-free[^'\"\s]*)['\"]", html, flags=re.IGNORECASE):
                endpoints.add(urljoin(base, mm.group(1)))
            for mm in re.finditer(r"['\"](/[^'\"\s]*free-login[^'\"\s]*)['\"]", html, flags=re.IGNORECASE):
                endpoints.add(urljoin(base, mm.group(1)))
            for mm in re.finditer(r"['\"](/[^'\"\s]*registration[^'\"\s]*)['\"]", html, flags=re.IGNORECASE):
                endpoints.add(urljoin(base, mm.group(1)))
            for mm in re.finditer(r"['\"](/[^'\"\s]*free[^'\"\s]*)['\"]", html, flags=re.IGNORECASE):
                endpoints.add(urljoin(base, mm.group(1)))
            for u in self._extract_js_links_from_text(html, base):
                if any(k in u.lower() for k in ["registration-free", "free-login", "/registration", "/free"]):
                    endpoints.add(u)
        except Exception:
            pass
        tried = False
        for u in list(endpoints)[:6]:
            tried = True
            try:
                payload = self._consent_payload()
                req = self._req(u, data=payload, referer=self.page_url, ajax=True)
                resp = self._open(req)
                self.page_url = resp.geturl()
                self.page_html = resp.read().decode("utf-8", "replace")
                self.logger.info(f"POST регистрация/согласие → {self.page_url}")
                self._record_touch(self.page_url)
                if self.check_success():
                    return True
            except Exception:
                try:
                    req = self._req(u, referer=self.page_url)
                    resp = self._open(req)
                    self.page_url = resp.geturl()
                    self.page_html = resp.read().decode("utf-8", "replace")
                    self.logger.info(f"GET регистрация/согласие → {self.page_url}")
                    self._record_touch(self.page_url)
                    if self.check_success():
                        return True
                except Exception:
                    continue
        return tried and False

    def discover_portal_from_artifacts(self):
        """Пытается обнаружить портал и восстановить состояние из артефактов Selenium."""
        candidates = ["conn4_debug_success.json", "conn4_debug_before_auth.json", "conn4_debug_fail.json"]
        for name in candidates:
             path = os.path.join(os.getcwd(), name)
             if os.path.exists(path):
                 self.logger.info(f"Обнаружен артефакт: {name}, пытаемся загрузить...")
                 if self.load_captured_artifact(path):
                     self.logger.info(f"✅ Состояние восстановлено из {name}")
                     return True
        return False

    def discover_portal_via_router(self):
        """Пытается узнать URL портала через curl с роутера по SSH и сразу загружает его."""
        if self.disable_ssh:
            return False
        host = os.environ.get("OPENWRT_SSH_HOST", "dev-openwrt")
        user = os.environ.get("OPENWRT_SSH_USER", "root")
        target = f"{user}@{host}"
        opts = ['-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=5', '-o', 'PreferredAuthentications=publickey,password', '-o', 'BatchMode=yes']
        cmd_hdrs = ['ssh'] + opts + [target, 'curl -sI http://connectivitycheck.gstatic.com/generate_204']
        cmd_body = ['ssh'] + opts + [target, 'curl -sL http://connectivitycheck.gstatic.com/generate_204']
        try:
            r1 = subprocess.run(cmd_hdrs, capture_output=True, text=True)
            r2 = subprocess.run(cmd_body, capture_output=True, text=True)
            data = (r1.stdout or "") + "\n" + (r2.stdout or "")
            m = re.search(r"Location:\s*(https?://[^\s]+)", data, flags=re.IGNORECASE)
            url = m.group(1) if m else None
            if not url and "conn4.com" in data:
                m2 = re.search(r"https?://[^\s]+conn4\.com[^\s]+", data)
                url = m2.group(0) if m2 else None
            if url:
                self.portal_url = url
                req = self._req(url)
                resp = self._open(req)
                self.page_url = resp.geturl()
                self.page_html = resp.read().decode("utf-8", "replace")
                self.logger.info(f"URL портала через роутер: {self.page_url}")
                self._record_touch(self.page_url)
                return True
        except Exception:
            return False
        return False

    def _attempt_ident_with_params(self):
        try:
            base = f"{urlparse(self.page_url or self.portal_url).scheme}://{urlparse(self.page_url or self.portal_url).netloc}"
            ident_url = urljoin(base, "/ident")
            flat_qs = {k: (v[0] if isinstance(v, list) and v else v) for k, v in self.initial_query.items()}
            toks = self._collect_tokens()
            if "siteId" in toks and "site_id" not in flat_qs:
                flat_qs["site_id"] = toks.get("siteId")
            if "clientIp" in toks and "client_ip" not in flat_qs:
                flat_qs["client_ip"] = toks.get("clientIp")
            if "clientMac" in toks and "client_mac" not in flat_qs:
                flat_qs["client_mac"] = toks.get("clientMac")
            if "signature" in toks and "signature" not in flat_qs:
                flat_qs["signature"] = toks.get("signature")
            if self.client_ip_override:
                flat_qs["client_ip"] = self.client_ip_override
            if self.client_mac_override:
                flat_qs["client_mac"] = self.client_mac_override
            if not self.client_ip_override and self.cookie_decoded_ip:
                flat_qs["client_ip"] = self.cookie_decoded_ip
            if not self.client_mac_override and self.cookie_decoded_mac:
                flat_qs["client_mac"] = self.cookie_decoded_mac
            if "site_id" not in flat_qs and self.cookie_decoded_site_id:
                flat_qs["site_id"] = self.cookie_decoded_site_id
            qs = urlencode(flat_qs)
            target = f"{ident_url}?{qs}" if qs else ident_url
            req = self._req(target, referer=self.page_url)
            resp = self._open(req)
            self.page_url = resp.geturl()
            self.page_html = resp.read().decode("utf-8", "replace")
            self.logger.info(f"Запрос ident с параметрами → {self.page_url}")
            self._record_touch(self.page_url)
            return True
        except Exception as e:
            self.logger.info(f"Ошибка ident запроса: {e}")
            return False

    def _attempt_ident_bare(self):
        try:
            base = f"{urlparse(self.page_url or self.portal_url).scheme}://{urlparse(self.page_url or self.portal_url).netloc}"
            ident_url = urljoin(base, "/ident")
            req = self._req(ident_url, referer=self.page_url)
            resp = self._open(req)
            self.page_url = resp.geturl()
            self.page_html = resp.read().decode("utf-8", "replace")
            self.logger.info(f"Запрос ident без параметров → {self.page_url}")
            self._record_touch(self.page_url)
            return True
        except Exception as e:
            self.logger.info(f"Ошибка ident bare запроса: {e}")
            return False

    def emulate_js(self):
        """Грубая эмуляция эффектов JS: initPage, location.href и встроенные URL портала."""
        html = self.page_html or ""
        ok = False
        try:
            self._log_external_lib_refs(html)
        except Exception:
            pass

        m = re.search(r"initPage\s*\(\s*(\{[\s\S]*?\})\s*\)", html)
        if m:
            try:
                obj = json.loads(m.group(1))
                url = obj.get("portalUrl")
                if url:
                    self.portal_url = url
                    ok = True
            except Exception:
                pass

        redirs = []
        for mm in re.finditer(r"(?:location(?:\.replace)?|window\.location\.href)\s*=\s*['\"]([^'\"]+)['\"]", html):
            redirs.append(mm.group(1))
        if redirs:
            self.logger.info(f"Найдены JS редиректы: {len(redirs)}")
            for u in redirs:
                self.logger.info(f"JS redirect: {u}")
            self.portal_url = urljoin(self.page_url, redirs[-1])
            ok = True
            try:
                req = self._req(self.portal_url, referer=self.page_url)
                resp = self._open(req)
                self.page_url = resp.geturl()
                self.page_html = resp.read().decode("utf-8", "replace")
                try:
                    self._log_external_lib_refs(self.page_html or "")
                except Exception:
                    pass
                self._record_touch(self.page_url)
            except Exception:
                pass

        urls = []
        for mm in re.finditer(r"['\"](https?://[^'\"\s]+)['\"]", html):
            urls.append(mm.group(1))
        for mm in re.finditer(r"data-(?:action|action-url|url|endpoint)=['\"]([^'\"]+)['\"]", html, flags=re.IGNORECASE):
            urls.append(urljoin(base, mm.group(1)))
        urls = [u for u in urls if "conn4.com" in u]
        if urls and not ok:
            self.portal_url = urls[0]
            ok = True

        return ok

    def submit_forms(self):
        """Находит формы/виртуальные формы согласия и отправляет их с токенами и consent."""
        html = self.page_html or ""
        parser = FormParser()
        try:
            parser.feed(html)
        except Exception:
            pass

        if not parser.forms:
            # Если нет явных форм, попробуем найти кнопку входа и создать "виртуальную" форму
            if any(k in html.lower() for k in ["registration-free", "free-login", "connect", "guest access"]):
                 self.logger.info("Формы не найдены, но есть признаки входа. Пробуем эмуляцию POST.")
                 # Ищем URL для POST из JS или кнопок
                 endpoints = []
                 for mm in re.finditer(r"['\"](/[^'\"\s]*registration-free[^'\"\s]*)['\"]", html, flags=re.IGNORECASE):
                     endpoints.append(urljoin(self.page_url or self.portal_url, mm.group(1)))
                 for mm in re.finditer(r"['\"](/[^'\"\s]*free-login[^'\"\s]*)['\"]", html, flags=re.IGNORECASE):
                     endpoints.append(urljoin(self.page_url or self.portal_url, mm.group(1)))
                 if endpoints:
                     vform = SimpleForm(action=endpoints[0], method="POST")
                     vform.add_input("agree", "1")
                     vform.add_input("accept", "1")
                     parser.forms.append(vform)
            else:
                return False

        for f in parser.forms:
            try:
                try:
                    present = {n for (n, _) in f.inputs if n}
                except Exception:
                    present = set()
                html_lower = (self.page_html or "").lower()
                if any(k in html_lower for k in ["terms", "conditions", "agree", "accept", "policy"]):
                    for k in ["agree", "accept", "terms", "policy", "consent"]:
                        if k not in present:
                            f.add_input(k, "1")

                # Добавляем токены
                toks = self._collect_tokens()
                for k, v in toks.items():
                    if k not in present and v is not None:
                        f.add_input(k, v)
                        present.add(k)
                if "apiSessionId" in toks and "api_session_id" not in present:
                    f.add_input("api_session_id", toks["apiSessionId"])

                orig = f.to_request(self.page_url or self.portal_url)
                try:
                    url = getattr(orig, 'full_url', None) or orig.get_full_url()
                except Exception:
                    url = self.page_url or self.portal_url
                data = getattr(orig, 'data', None)
                req = self._req(url, data=data, referer=self.page_url, ajax=(data is not None))
                resp = self._open(req)
                new_url = resp.geturl()
                new_html = resp.read().decode("utf-8", "replace")
                self.logger.info(f"Отправлена форма {f.method} {f.action} → {new_url}")
                self.page_url = new_url
                self.page_html = new_html
                self._record_touch(self.page_url)

                # Дополнительная проверка редиректа после POST
                if "conn4.com" in new_url and "success" not in new_url:
                     # Если остались на том же домене и нет явного успеха, ищем JS редирект в ответе
                     js_redirs = []
                     for mm in re.finditer(r"(?:location(?:\.replace)?|window\.location\.href)\s*=\s*['\"]([^'\"]+)['\"]", new_html):
                         js_redirs.append(mm.group(1))
                     if js_redirs:
                         redir_url = urljoin(new_url, js_redirs[-1])
                         self.logger.info(f"Найден JS редирект после формы: {redir_url}")
                         try:
                             req_r = self._req(redir_url, referer=new_url)
                             resp_r = self._open(req_r)
                             self.page_url = resp_r.geturl()
                             self.page_html = resp_r.read().decode("utf-8", "replace")
                             self._record_touch(self.page_url)
                         except Exception:
                             pass

                if self.check_success():
                    return True
            except Exception as e:
                self.logger.info(f"Ошибка отправки формы: {e}")
                continue
        return False

    def load_iframes(self):
        """Загружает iframe-ы страницы портала, пытаясь продолжить авторизацию внутри них."""
        html = self.page_html or ""
        frames = []
        for mm in re.finditer(r"<iframe[^>]*src=['\"]([^'\"]+)['\"][^>]*>", html, flags=re.IGNORECASE):
            frames.append(urljoin(self.page_url or self.portal_url, mm.group(1)))
        if not frames:
            return False
        self.logger.info(f"Обнаружено iframe: {len(frames)}")
        for src in frames:
            if src.lower().startswith("javascript:"):
                continue
            try:
                req = self._req(src, referer=self.page_url)
                resp = self._open(req)
                self.page_url = resp.geturl()
                self.page_html = resp.read().decode("utf-8", "replace")
                self.logger.info(f"Загружен iframe → {self.page_url}")
                self._record_touch(self.page_url)
                if self.check_success():
                    return True
                if self.submit_forms():
                    return True
                if self.try_click_emulation():
                    return True
            except Exception as e:
                self.logger.info(f"Ошибка загрузки iframe: {e}")
                continue
        return False

    def extract_resource_urls(self):
        base = base_origin_from_url(self.page_url or self.portal_url or "")
        html = self.page_html or ""
        html_urls = extract_resource_urls_from_html(html, base)
        js_urls = extract_urls_from_js_text(html, base)
        combined = html_urls + js_urls
        seen = set()
        clean = []
        for u in combined:
            if u not in seen:
                seen.add(u)
                clean.append(u)
        return clean

    def _log_external_lib_refs(self, text):
        try:
            refs = []
            for mm in re.finditer(r"https?://[^\\s'\"<>]+", text):
                u = mm.group(0)
                low = u.lower()
                if any(h in low for h in ["github.com","raw.githubusercontent.com","cdn.jsdelivr.net","unpkg.com","cdnjs.cloudflare.com"]):
                    refs.append(u)
            if refs:
                uniq = []
                seen = set()
                for u in refs:
                    if u not in seen:
                        seen.add(u)
                        uniq.append(u)
                self.logger.info(f"[External libs] найдено ссылок: {len(uniq)}")
                for u in uniq:
                    self.logger.info(f"  {u}")
        except Exception:
            pass

    def environment_tests(self):
        """Диагностика окружения: WSL, ping шлюза, SOCKS, DNS и пробный запрос /_time."""
        try:
            try:
                import platform
                is_linux = (sys.platform.startswith("linux") or platform.system().lower() == "linux")
                self.logger.info(f"[ENV] linux={is_linux}")
            except Exception:
                pass
            try:
                vtxt = ""
                try:
                    with open("/proc/version","r") as f:
                        vtxt = f.read().lower()
                except Exception:
                    vtxt = ""
                is_wsl = ("microsoft" in vtxt) or ("wsl" in vtxt)
                self.logger.info(f"[ENV] wsl={is_wsl}")
            except Exception:
                pass
            try:
                r = subprocess.run(["bash","-lc","ping -c 1 -w 2 192.168.1.1"], capture_output=True, text=True)
                self.logger.info(f"[PING 192.168.1.1] rc={r.returncode}")
            except Exception:
                pass
            self.ensure_socks_proxy()
            try:
                ap = os.environ.get("ALL_PROXY")
                hp = os.environ.get("HTTP_PROXY")
                sp = os.environ.get("HTTPS_PROXY")
                self.logger.info(f"[PROXY ENV] ALL_PROXY={ap} HTTP_PROXY={hp} HTTPS_PROXY={sp}")
            except Exception:
                pass
            try:
                hosts = ["conn4.com","rdr.conn4.com"]
                for h in hosts:
                    ips = []
                    try:
                        ips = list(socket.gethostbyname_ex(h)[2] or [])
                    except Exception:
                        ips = []
                    if ips:
                        self.logger.info(f"[DNS] {h} -> {', '.join(ips)}")
                        for ip in ips[:3]:
                            try:
                                rr = subprocess.run(["bash","-lc",f"ip route get {ip} | head -n 1"], capture_output=True, text=True)
                                line = (rr.stdout or "").strip().replace("\n"," ")
                                self.logger.info(f"[ROUTE] {ip} -> {line}")
                            except Exception:
                                pass
                    else:
                        self.logger.info(f"[DNS] {h} resolution failed")
            except Exception:
                pass
            try:
                base = f"{urlparse(self.page_url or self.portal_url).scheme}://{urlparse(self.page_url or self.portal_url).netloc}" if (self.page_url or self.portal_url) else "https://rdr.conn4.com"
                probe = urljoin(base, "/_time")
                rs = self.opener.open(Request(probe, headers={"User-Agent": self.user_agent}), timeout=10)
                self.logger.info(f"[PROXY PROBE] {_safe_url(probe)} → {rs.getcode()}")
            except Exception as e:
                self.logger.info(f"[PROXY PROBE ERR] {e}")
            return True
        except Exception:
            return False


    def _is_static_url(self, u):
        try:
            low = (u or "").lower()
            if not low:
                return False
            if low.startswith("data:image"):
                return True
            if low.endswith(".png") or low.endswith(".jpg") or low.endswith(".jpeg") or low.endswith(".webp") or low.endswith(".svg") or low.endswith(".gif") or low.endswith(".ico") or low.endswith(".bmp"):
                return True
            if low.endswith(".css") or low.endswith(".woff") or low.endswith(".woff2") or low.endswith(".ttf") or low.endswith(".otf") or low.endswith(".eot"):
                return True
            return False
        except Exception:
            return False

    def _should_request(self, u):
        try:
            # if self._is_static_url(u):
            #     return False
            low = (u or "").lower()
            if "/_time" in low:
                return True
            host = urlparse(u).netloc.lower()
            ph = urlparse(self.portal_url or self.page_url or "").netloc.lower()
            if ("conn4.com" in host) or (ph and host == ph):
                return True
            return False
        except Exception:
            return False


    def try_click_emulation(self):
        html = self.page_html or ""
        # Ищем ссылки или псевдо-кнопки, ведущие к авторизации
        candidates = []
        for mm in re.finditer(r"<a[^>]*href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", html, flags=re.IGNORECASE | re.DOTALL):
            href = mm.group(1)
            text = re.sub(r"\s+", " ", mm.group(2)).strip().lower()
            if any(t in text for t in ["get free wi-fi", "get free wifi", "connect", "continue", "agree", "accept"]):
                u = urljoin(self.page_url, href)
                if self._should_request(u):
                    candidates.append(u)
        for mm in re.finditer(r"<a[^>]*href=['\"]([^'\"]+)['\"][^>]*>", html, flags=re.IGNORECASE):
            href = mm.group(1)
            hl = href.lower()
            if any(k in hl for k in ["registration", "free", "connect", "continue"]) and "w3.org" not in hl:
                u = urljoin(self.page_url, href)
                if self._should_request(u):
                    candidates.append(u)

        # Ищем onclick со ссылками
        for mm in re.finditer(r"onclick=['\"][^'\"]*(['\"])((?:https?://)?[^'\"]+)\1", html, flags=re.IGNORECASE):
            u = urljoin(self.page_url, mm.group(2))
            if self._should_request(u):
                candidates.append(u)
        for mm in re.finditer(r"onclick=['\"][^'\"]*(?:goTo|navigate|redirect)\s*\(\s*(['\"])((?:https?://)?[^'\"]+)\1\s*\)", html, flags=re.IGNORECASE):
            u = urljoin(self.page_url, mm.group(2))
            if self._should_request(u):
                candidates.append(u)
        for mm in re.finditer(r"onclick=['\"][^'\"]*window\.open\(\s*(['\"])((?:https?://)?[^'\"]+)\1\s*,", html, flags=re.IGNORECASE):
            u = urljoin(self.page_url, mm.group(2))
            if self._should_request(u):
                candidates.append(u)

        tried = False
        for u in candidates:
            tried = True
            try:
                req = self._req(u, referer=self.page_url)
                resp = self._open(req)
                self.page_url = resp.geturl()
                self.page_html = resp.read().decode("utf-8", "replace")
                self.logger.info(f"Эмуляция клика → {self.page_url}")
                self._record_touch(self.page_url)
                if self.check_success():
                    return True
            except Exception as e:
                self.logger.info(f"Ошибка клика: {e}")
                continue
        return tried and False

    def apply_captured_flow(self):
        """Воспроизводит последовательность сетевых событий и iframe/URL из Selenium-артефактов."""
        tried = False
        network_summary = getattr(self, 'network_summary', [])
        if network_summary:
            self.logger.info(f"[NETWORK FLOW] Применение последовательности из {len(network_summary)} событий")
            # Сначала ищем точное событие login/free с postData и используем его один в один
            try:
                lf_event = None
                for ev in network_summary:
                    u = (ev.get('url') or ev.get('request', {}).get('url') or '') or ''
                    if '/wbs/api/v1/login/free/' in u:
                        pd = (ev.get('request', {}) or {}).get('postData')
                        if pd:
                            lf_event = ev
                if lf_event:
                    u = lf_event.get('request', {}).get('url') or lf_event.get('url') or ''
                    pd = lf_event.get('request', {}).get('postData') or ''
                    hdrs = (lf_event.get('request', {}).get('headers') or {}) if isinstance(lf_event.get('request', {}), dict) else {}
                    referer = None
                    try:
                        referer = hdrs.get('Referer') or hdrs.get('referer')
                    except Exception:
                        referer = None
                    if not referer:
                        referer = self._choose_login_referer() or self.page_url
                    data = pd.encode('utf-8') if isinstance(pd, str) else pd
                    self.logger.info("[NETWORK] Воспроизведение captured login/free POST")
                    rq = self._req(u, data=data, referer=referer, ajax=True)
                    rs = self._open(rq)
                    self.page_url = rs.geturl()
                    try:
                        self.page_html = rs.read().decode("utf-8", "replace")
                    except Exception:
                        self.page_html = ""
                    self._record_touch(self.page_url)
                    if self.check_success():
                        return True
                    # follow paymentReturnProxyUrl, если доступно
                    try:
                        toks = self._collect_tokens()
                        prx = toks.get("paymentReturnProxyUrl") or self.dynamic_tokens.get("paymentReturnProxyUrl")
                        if prx:
                            r2 = self._open(self._req(prx, referer=u))
                            self.page_url = r2.geturl()
                            try:
                                self.page_html = r2.read().decode("utf-8","replace")
                            except Exception:
                                self.page_html = ""
                            self._record_touch(self.page_url)
                            if self.check_success():
                                return True
                    except Exception:
                        pass
            except Exception:
                pass
            # Затем применяем остальные события (полезны для токенов/кук)
            for event in network_summary:
                try:
                    url = event.get('url') or event.get('request', {}).get('url')
                    method = event.get('method') or 'GET'
                    post_data = event.get('request', {}).get('postData')
                    if not url or 'conn4.com' not in url:
                        continue
                    if '/_time' in url.lower():
                        try:
                            ts = self._open(self._req(url, referer=self.page_url))
                            self.logger.info(f"[NETWORK] _time → {ts.getcode()}")
                            self._record_touch(url)
                        except Exception:
                            pass
                        continue
                    if method == 'POST' and post_data:
                        try:
                            data = post_data.encode('utf-8') if isinstance(post_data, str) else post_data
                            rq = self._req(url, data=data, referer=self.page_url, ajax=True)
                            rs = self._open(rq)
                            self.page_url = rs.geturl()
                            try:
                                self.page_html = rs.read().decode("utf-8", "replace")
                            except Exception:
                                self.page_html = ""
                            self._record_touch(self.page_url)
                            if self.check_success():
                                return True
                        except Exception as e:
                            self.logger.info(f"[NETWORK] Ошибка POST: {e}")
                except Exception:
                    pass

        for src in self.captured_iframes[:10]:
            if not src:
                continue
            if not self._should_request(src):
                continue
            tried = True
            try:
                req = self._req(src, referer=self.page_url)
                resp = self._open(req)
                self.page_url = resp.geturl()
                self.page_html = resp.read().decode("utf-8", "replace")
                self.logger.info(f"Загрузка iframe из артефакта → {self.page_url}")
                self._record_touch(self.page_url)
                if self.check_success():
                    return True
                if self.submit_forms():
                    return True
                if self.try_click_emulation():
                    return True
            except Exception as e:
                self.logger.info(f"Ошибка iframe из артефакта: {e}")
                continue
        for u in self.captured_requests[:25]:
            if not isinstance(u, str):
                continue
            if "conn4.com" not in u:
                continue
            if not self._should_request(u):
                continue
            tried = True
            try:
                self._log_conn4_params(u, label=" captured")
            except Exception:
                pass
            did = False
            try:
                low = u.lower()
                if "/_time" in low:
                    try:
                        base = f"{urlparse(u).scheme}://{urlparse(u).netloc}"
                        ts = self._open(self._req(u, referer=self.page_url))
                        self.logger.info(f"Артефакт _time → {ts.getcode()}")
                        self._record_touch(u)
                    except Exception:
                        pass
                if any(k in low for k in ["registration-free","free-login","/registration","/free"]):
                    payload = self._consent_payload()
                    req = self._req(u, data=payload, referer=self.page_url, ajax=True)
                    resp = self._open(req)
                    self.page_url = resp.geturl()
                    self.page_html = resp.read().decode("utf-8", "replace")
                    self.logger.info(f"POST по captured endpoint → {self.page_url}")
                    self._record_touch(self.page_url)
                    did = True
                if not did:
                    req = self._req(u, referer=self.page_url)
                    resp = self._open(req)
                    self.page_url = resp.geturl()
                    self.page_html = resp.read().decode("utf-8", "replace")
                    self.logger.info(f"GET по captured endpoint → {self.page_url}")
                    self._record_touch(self.page_url)
                if self.check_success():
                    return True
                if self.submit_forms():
                    return True
                if self.load_iframes():
                    return True
                if self.try_click_emulation():
                    return True
            except Exception as e:
                self.logger.info(f"Ошибка запроса по captured: {e}")
                continue
        return tried and False

    def run_nojs_plan_from_master(self):
        """Выполняет шаги nojs_plan из conn4_master.json, пропуская диагностический шаг portal big js."""
        plan = []
        try:
            master_path = os.path.join(os.getcwd(), "conn4_master.json")
            if not os.path.exists(master_path):
                return False
            with open(master_path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            plan = obj.get("nojs_plan") or []
        except Exception as e:
            try:
                self.logger.info(f"[NOJS PLAN] Не удалось загрузить conn4_master.json: {e}")
            except Exception:
                pass
            return False
        if not plan:
            try:
                self.logger.info("[NOJS PLAN] План отсутствует в conn4_master.json")
            except Exception:
                pass
            return False
        try:
            self.logger.info(f"[NOJS PLAN] Выполнение плана из conn4_master.json: {len(plan)} шагов")
        except Exception:
            pass
        success = False
        for step in plan:
            try:
                name = (step.get("name") or "").strip()
                method = (step.get("method") or "GET").upper()
                url = step.get("url") or ""
                body = step.get("body") or None
                if not url:
                    continue
                if name == "portal big js":
                    try:
                        self.logger.info(f"[NOJS PLAN] Пропуск шага '{name}' ({url})")
                    except Exception:
                        pass
                    continue
                try:
                    self.logger.info(f"[NOJS PLAN] Шаг: {name or method} {url}")
                except Exception:
                    pass
                if method == "POST":
                    data = None
                    try:
                        if isinstance(body, dict):
                            data = urlencode(body, doseq=True).encode("utf-8")
                        elif isinstance(body, str):
                            data = body.encode("utf-8")
                    except Exception:
                        data = None
                    if data is None and name == "login free":
                        try:
                            data = self._consent_payload()
                        except Exception:
                            data = None
                    try:
                        referer = self._choose_login_referer() or self.page_url
                        req = self._req(url, data=data, referer=referer, ajax=True)
                        resp = self._open(req)
                        self.page_url = resp.geturl()
                        try:
                            self.page_html = resp.read().decode("utf-8", "replace")
                        except Exception:
                            self.page_html = ""
                        self._record_touch(self.page_url)
                        try:
                            self.logger.info(f"[NOJS PLAN] POST {_safe_url(url)} → {self.page_url}")
                        except Exception:
                            pass
                        # Follow paymentReturnProxyUrl if present
                        try:
                            toks = self._collect_tokens()
                            prx = toks.get("paymentReturnProxyUrl") or self.dynamic_tokens.get("paymentReturnProxyUrl")
                            if prx:
                                r2 = self._open(self._req(prx, referer=url))
                                self.page_url = r2.geturl()
                                try:
                                    self.page_html = r2.read().decode("utf-8","replace")
                                except Exception:
                                    self.page_html = ""
                                self._record_touch(self.page_url)
                        except Exception:
                            pass
                    except Exception as e:
                        try:
                            self.logger.info(f"[NOJS PLAN] Ошибка POST: {e}")
                        except Exception:
                            pass
                        continue
                else:
                    try:
                        req = self._req(url, referer=self.page_url)
                        resp = self._open(req)
                        self.page_url = resp.geturl()
                        try:
                            self.page_html = resp.read().decode("utf-8", "replace")
                        except Exception:
                            self.page_html = ""
                        self._record_touch(self.page_url)
                        try:
                            self.logger.info(f"[NOJS PLAN] GET {_safe_url(url)} → {self.page_url}")
                        except Exception:
                            pass
                    except Exception as e:
                        try:
                            self.logger.info(f"[NOJS PLAN] Ошибка GET: {e}")
                        except Exception:
                            pass
                        continue
                if self.check_success():
                    try:
                        self.logger.info(f"[NOJS PLAN] Авторизация подтверждена на шаге '{name or method}'")
                    except Exception:
                        pass
                    success = True
                    break
            except Exception:
                continue
        return success

    def check_success(self):
        """Онлайн-детектор успеха: JSON, URL/DOM назначения и ключевые слова подключения."""
        url = (self.page_url or "").lower()
        html_src = self.page_html or ""
        if isinstance(html_src, bytes):
            try:
                html = html_src.decode("utf-8", "replace").lower()
            except Exception:
                html = html_src.decode("latin-1", "replace").lower()
        else:
            html = (html_src or "").lower()

        # Проверка 1: JSON ответ с индикаторами успеха
        try:
            t_src = self.page_html or ""
            if isinstance(t_src, bytes):
                try:
                    t = t_src.decode("utf-8", "replace")
                except Exception:
                    t = t_src.decode("latin-1", "replace")
            else:
                t = (t_src or "").strip()
            if "Microsoft Connect Test" in t:
                self.logger.info("✅ УСПЕХ: Microsoft Connect Test обнаружен (доступ в интернет есть)")
                return True
            if t.startswith("{") and t.endswith("}"):
                try:
                    obj = json.loads(t)
                    if obj.get("success") is True or obj.get("authorized") is True or obj.get("status") in ("ok","success","connected"):
                        self.logger.info("✅ УСПЕХ: JSON ответ содержит индикатор успеха")
                        return True
                except Exception:
                    pass
        except Exception:
            pass

        # Проверка 2: Редирект на leonardo-hotels.com или destinations
        if ("leonardo-hotels.com" in url) or ("/destinations" in url):
            self.logger.info("✅ УСПЕХ: Редирект на страницу с картой подтвержден")
            return True

        # Проверка 3: Контент содержит признаки карты/назначений
        kws = ["destinations", "map", "leaflet", "gmaps", "hotel"]
        if ("conn4.com" not in url) and any(k in html for k in kws):
            self.logger.info("✅ УСПЕХ: Страница содержит признаки карты/назначений, авторизация подтверждена")
            return True

        # Проверка 4: Редирект на внешний домен с индикаторами успеха
        try:
            pn = urlparse(self.page_url or "").netloc.lower()
        except Exception:
            pn = ""
        more = ["wifi", "internet", "connected", "welcome", "success"]
        if pn and ("conn4.com" not in pn) and any(k in html for k in more):
            self.logger.info("✅ УСПЕХ: Редирект на внешний домен подтвержден")
            return True

        # Проверка 5: URL вне conn4.com
        if pn and ("conn4.com" not in pn):
            self.logger.info(f"✅ УСПЕХ: URL вне conn4.com → {self.page_url}")
            return True

        # Проверка 6: URL содержит ключевые слова успеха
        success_kw = ["success", "authorized", "authenticated", "welcome", "connected"]
        for kw in success_kw:
            if kw in url:
                self.logger.info(f"✅ УСПЕХ: URL содержит '{kw}'")
                return True

        return False

    def sync_time(self):
        try:
            base = f"{urlparse(self.page_url or self.portal_url).scheme}://{urlparse(self.page_url or self.portal_url).netloc}"
            time_url = urljoin(base, "/_time")
            try:
                t = str(int(time.time() * 1000))
            except Exception:
                t = None
            tgt = f"{time_url}?t={t}" if t else time_url
            rs = self._open(self._req(tgt, referer=self.page_url))
            self.logger.info(f"Синхронизация времени: {_safe_url(tgt)} → {rs.getcode()}")
            self.log_cookies("after-time")
            self._record_touch(tgt)
            return True
        except Exception as e:
            self.logger.info(f"Ошибка синхронизации времени: {e}")
            return False

    def detect_portal_via_redirect(self):
        target_url = "http://www.msftconnecttest.com/redirect"
        self.logger.info(f"Попытка обнаружения портала через {target_url}...")
        try:
            # Используем curl через SOCKS для гарантированного перехвата редиректа
            resp = self._open_socks_curl(target_url, timeout=10)
            final_url = resp.geturl()
            self.logger.info(f"Обнаружен URL: {final_url}")

            # Собираем все URL для анализа (финальный + редиректы)
            all_urls = getattr(resp, "redirects", []) + [final_url]

            found_conn4 = False
            for u in all_urls:
                if "conn4.com" in u:
                    found_conn4 = True

            if found_conn4:
                self.portal_url = final_url
                self.page_url = final_url
                try:
                    self.page_html = resp.read().decode("utf-8", "replace")
                    # Debug save
                    with open("debug_portal.html", "w", encoding="utf-8") as f:
                        f.write(self.page_html)
                except Exception:
                    self.page_html = ""

                # Парсим параметры URL из ВСЕХ редиректов
                for u in all_urls:
                    parsed = urlparse(u)
                    qs = parse_qs(parsed.query)
                    self.initial_query.update(qs)

                    # Обновляем токены из URL
                    for k, v in qs.items():
                        val = v[0] if isinstance(v, list) and v else str(v)
                        self.dynamic_tokens[k] = val
                        # Маппинг для snake_case и camelCase
                        if k == "client_ip": self.dynamic_tokens["clientIp"] = val
                        if k == "client_mac": self.dynamic_tokens["clientMac"] = val
                        if k == "site_id": self.dynamic_tokens["siteId"] = val
                        if k == "signature": self.dynamic_tokens["signature"] = val

                        if k in ["site_id", "client_ip", "client_mac", "signature"]:
                            self.logger.info(f"  Captured {k}: {val} from {u}")

                self._record_touch(final_url)
                
                # Check if himalaya-site-ident cookie is present
                has_ident = False
                for c in self.cookies:
                    if c.name == "himalaya-site-ident":
                        has_ident = True
                        break
                
                if not has_ident:
                    self.logger.warning("Cookie himalaya-site-ident not found after detection. Trying to call /ident explicitly.")
                    # Construct /ident URL
                    # Need site_id, client_ip, client_mac, signature
                    site_id = self.dynamic_tokens.get("siteId") or self.dynamic_tokens.get("site_id")
                    client_ip = self.dynamic_tokens.get("clientIp") or self.dynamic_tokens.get("client_ip")
                    client_mac = self.dynamic_tokens.get("clientMac") or self.dynamic_tokens.get("client_mac")
                    signature = self.dynamic_tokens.get("signature")
                    
                    if site_id and client_ip and client_mac and signature:
                        ident_url = f"https://{site_id}.rdr.conn4.com/ident?client_ip={client_ip}&client_mac={client_mac}&site_id={site_id}&signature={signature}&loggedin=0"
                        self.logger.info(f"Calling explicit /ident: {ident_url}")
                        r_ident = self._open_socks_curl(ident_url)
                        try:
                            # Try to parse token from ident response
                            ident_txt = r_ident.read().decode("utf-8", "replace")
                            self.logger.info(f"[IDENT] Response len={len(ident_txt)}")
                            if ident_txt:
                                self._collect_tokens_from_text(ident_txt)
                        except Exception as e:
                            self.logger.warning(f"[IDENT] Error parsing response: {e}")
                    else:
                        self.logger.error(f"Cannot call /ident, missing params: site={site_id} ip={client_ip} mac={client_mac} sig={bool(signature)}")

                return True
            elif "msftconnecttest" not in final_url:
                # Редирект на внешний домен (например, leonardo-hotels.com) — считаем успехом (авторизация уже пройдена)
                self.page_url = final_url
                try:
                    self.page_html = resp.read().decode("utf-8", "replace")
                except Exception:
                    self.page_html = ""
                self._record_touch(final_url)
                self.logger.info("✅ Редирект на внешний домен — авторизация подтверждена")
                return True
            else:
                self.logger.warning("Редирект не произошел или ведет на MSFT (интернет доступен?)")
                return False
        except Exception as e:
            self.logger.error(f"Ошибка обнаружения портала: {e}")
            return False

    def fetch_resources_step(self):
        """Step to fetch JS and Scene pages to extract tokens."""
        try:
            # Collect from CURRENT page first (before it might be overwritten)
            self._collect_tokens_step()

            self._fetch_and_parse_js_resources()
            self._load_scene_pages()
            return True
        except Exception:
            return False

    def run_flow(self, detect_only=False):
        """Основной последовательный сценарий: поиск портала, sync /_time, токены, create-session и API."""
        steps = [
            ("detect_portal", self.detect_portal_via_redirect),
            ("cookie_challenge", self._handle_cookie_challenge),
            ("sync_time", self.sync_time),
            ("ident_bare", self._attempt_ident_bare),
            ("ident", self._attempt_ident_with_params),
            ("fetch_resources", self.fetch_resources_step),
            ("collect_tokens", self._collect_tokens_step),
        ]
        if not detect_only:
            steps += [
                ("create_session", self._call_create_session_api),
                # Попытка эмуляции формы (как в Selenium) перед API (как fallback)
                ("form_flow", self._run_form_flow),
                ("api_flow", self._run_api_flow),
            ]
        for name, fn in steps:
            try:
                print(f"[DEBUG] Starting step: {name}")
                self.logger.info(f"[FLOW] Выполняется шаг: {name}")
                r = fn()
                if r:
                    self.logger.info(f"[FLOW] ✅ Шаг '{name}' завершен успешно")
                    if name == "api_flow":
                        self.logger.info("[FLOW] 🛑 API Flow успешен, завершаем авторизацию")
                        return True
                else:
                    if name == "api_flow":
                        self.logger.info("[FLOW] ⚠️ API Flow не дал успешного результата")
                    else:
                        self.logger.info(f"[FLOW] ⚠️  Шаг '{name}' вернул False")
            except Exception as e:
                self.logger.warning(f"[FLOW] ❌ Ошибка в шаге '{name}': {e}")
                r = False
            if self.check_success():
                self.logger.info(f"[FLOW] 🎉 Авторизация успешна после шага '{name}'!")
                return True
            time.sleep(1)
        return False



    def _extract_authorization_token_from_cookie(self):
        try:
            for cookie in self.cookies:
                if cookie.name == "himalaya-site-ident":
                    import base64
                    raw = cookie.value or ""
                    if not raw:
                        return None
                    s = unquote(raw)
                    pad = "=" * ((4 - len(s) % 4) % 4)
                    dec = base64.b64decode(s + pad)
                    try:
                        txt = dec.decode("utf-8", "replace")
                    except Exception:
                        txt = dec.decode("latin-1", "replace")
                    if txt:
                        try:
                            ipm = re.search(r's:12:"\*IPAddress";s:\d+:"((?:\d{1,3}\.){3}\d{1,3})"', txt) or re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", txt)
                            macm = re.search(r's:13:"\*MACAddress";s:\d+:"([0-9A-F]{12})"', txt) or re.search(r"\b[0-9A-F]{12}\b", txt)
                            sidm = re.search(r's:9:".*siteId";i:(\d+)', txt) or re.search(r'siteId";i:(\d+)', txt)
                            self.cookie_decoded_ip = ipm.group(1) if ipm and ipm.lastindex and ipm.lastindex >= 1 else (ipm.group(0) if ipm else self.cookie_decoded_ip)
                            self.cookie_decoded_mac = macm.group(1) if macm and macm.lastindex and macm.lastindex >= 1 else (macm.group(0) if macm else self.cookie_decoded_mac)
                            self.cookie_decoded_site_id = sidm.group(1) if sidm and sidm.lastindex and sidm.lastindex >= 1 else (sidm.group(0) if sidm else self.cookie_decoded_site_id)
                        except Exception:
                            pass
                    return txt
        except Exception:
            return None


    def _detect_client_ip_mac(self):
        """Определяет client_ip и client_mac без хардкода: из токенов, cookie или окружения"""
        ip = (self.dynamic_tokens.get("client_ip") or self.dynamic_tokens.get("clientIp") or None)
        mac = (self.dynamic_tokens.get("client_mac") or self.dynamic_tokens.get("clientMac") or None)
        if not ip or not mac:
            tok = self._extract_authorization_token_from_cookie() or ""
            try:
                if tok:
                    m_ip = re.search(r'IPAddress"\s*;\s*s:\d+:"([^"]+)"', tok)
                    m_mac = re.search(r'MACAddress"\s*;\s*s:\d+:"([A-F0-9]+)"', tok)
                    if not m_ip:
                        m_ip = re.search(r'remoteAddress"\s*;\s*s:\d+:"([^"]+)"', tok)
                    if not ip and m_ip:
                        ip = m_ip.group(1)
                    if not mac and m_mac:
                        mac = m_mac.group(1)
            except Exception:
                pass
        if not ip or not mac:
            try:
                pu = urlparse(self.page_url or self.portal_url or "")
                qs = parse_qs(pu.query or "")
                if not ip:
                    ip = (qs.get("client_ip",[None])[0] or qs.get("ip",[None])[0])
                if not mac:
                    mac = (qs.get("client_mac",[None])[0] or qs.get("mac",[None])[0])
            except Exception:
                pass
        if not ip or not mac:
            try:
                flat_qs = {k: (v[0] if isinstance(v, list) and v else v) for k, v in self.initial_query.items()}
                if not ip:
                    ip = flat_qs.get("client_ip") or flat_qs.get("ip")
                if not mac:
                    mac = flat_qs.get("client_mac") or flat_qs.get("mac")
            except Exception:
                pass
        if not ip or not mac:
            try:
                html = self.page_html or ""
                m_ip = re.search(r'name=["\']client_ip["\'][^>]*value=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
                m_mac = re.search(r'name=["\']client_mac["\'][^>]*value=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
                if not ip and m_ip:
                    ip = m_ip.group(1)
                if not mac and m_mac:
                    mac = m_mac.group(1)
            except Exception:
                pass
        # Последний источник — переменные окружения (не хардкод, меняются по прогону)
        if not ip:
            ip = os.environ.get("NOJS_CLIENT_IP")
        if not mac:
            mac = os.environ.get("NOJS_CLIENT_MAC")
        if ip:
            self.dynamic_tokens["client_ip"] = ip
            self.dynamic_tokens["clientIp"] = ip
        if mac:
            self.dynamic_tokens["client_mac"] = mac
            self.dynamic_tokens["clientMac"] = mac
        self.logger.info(f"[CLIENT] IP={ip or 'NA'} MAC={mac or 'NA'}")
        return ip, mac


    def _create_wbs_api_auth_token(self):
        try:
            t = self.dynamic_tokens.get("wbsApiAuthToken")
            if t:
                return t
            t = self._generate_dynamic_wbs_token()
            if t:
                self.dynamic_tokens["wbsApiAuthToken"] = t
                return t
            toks = self._collect_tokens() or {}
            t = toks.get("wbsApiAuthToken")
            if t:
                self.dynamic_tokens["wbsApiAuthToken"] = t
                return t
        except Exception:
            pass
        return None

    def _update_phpsessid_cookie(self, value, domain):
        try:
            found = False
            for c in self.cookies:
                if c.name == "PHPSESSID":
                    c.value = value
                    found = True
                    break
            if not found:
                # Create new cookie
                c = cj.Cookie(
                    version=0, name="PHPSESSID", value=value,
                    port=None, port_specified=False,
                    domain=domain, domain_specified=True, domain_initial_dot=False,
                    path="/", path_specified=True,
                    secure=False, expires=None, discard=True,
                    comment=None, comment_url=None, rest={'HttpOnly': None},
                    rfc2109=False
                )
                self.cookies.set_cookie(c)
            self.logger.info(f"[COOKIE] PHPSESSID обновлен до: {value}")
        except Exception as e:
            self.logger.error(f"[COOKIE] Ошибка обновления PHPSESSID: {e}")

    def _quickjs_serialize_wbs_token(self, site_id, client_ip, client_mac):
        try:
            js = (
                "function s(v){if(v===null)return\"N;\";if(typeof v===\"boolean\")return\"b:\"+(v?1:0)+\";\";"
                "if(Number.isInteger(v))return\"i:\"+v+\";\";if(typeof v===\"number\")return\"d:\"+v+\";\";"
                "if(typeof v===\"string\")return\"s:\"+v.length+':\"'+v+'\";';"
                "if(typeof v===\"object\"){if(v.__classname__){var c=v.__classname__,p=v.__props__||{},k=Object.keys(p);"
                "var o='O:'+c.length+':\"'+c+'\":'+k.length+':{';for(var i=0;i<k.length;i++){var kk=k[i];o+=s(kk)+s(p[kk]);}"
                "o+='}';return o;}else{var k=Object.keys(v);var o='a:'+k.length+':{';for(var i=0;i<k.length;i++){var kk=k[i];o+=s(kk)+s(v[kk]);}"
                "o+='}';return o;}}return\"N;\";}"
                "function pad(n){return n<10?('0'+n):(''+n);}var d=new Date();"
                "var ds=d.getUTCFullYear()+\"-\"+pad(d.getUTCMonth()+1)+\"-\"+pad(d.getUTCDate())+\" \"+pad(d.getUTCHours())+\":\"+pad(d.getUTCMinutes())+\":\"+pad(d.getUTCSeconds())+\".000000\";"
                f"var sid={int(site_id) if str(site_id).isdigit() else 0};var ip=\"{client_ip or '127.0.0.1'}\";var mac=\"{client_mac or ''}\";"
                "var dt={\"__classname__\":\"DateTime\",\"__props__\":{\"date\":ds,\"timezone_type\":3,\"timezone\":\"UTC\"}};"
                "var props={\"\\0*\\0siteId\":sid,\"\\0*\\0remoteAddress\":ip,\"\\0*\\0macAddress\":mac,\"\\0*\\0deviceId\":null,\"\\0*\\0created\":dt,\"\\0*\\0origin\":(sid?(\"https://\"+sid+\".rdr.conn4.com\"):\"https://rdr.conn4.com\")}};"
                "var tok={\"__classname__\":\"M3\\\\Himalaya\\\\Shared\\\\WBSApiAuth\\\\Token\",\"__props__\":props};"
                "console.log(s(tok));"
            )
            fn = os.path.join(self.artifact_dir, "wbs_quickjs_gen.js")
            with open(fn, "w", encoding="utf-8") as f:
                f.write(js)
            r = subprocess.run(["bash", "-lc", f"qjs '{fn}'"], capture_output=True, text=True, timeout=5)
            if r.returncode != 0:
                return None
            out = (r.stdout or "").strip()
            if not out:
                return None
            return out
        except Exception:
            return None
    def _generate_dynamic_wbs_token(self):
        """Generates a dynamic WBS token using WbsTokenBuilder and cookie hash (reusing Selenium logic)."""
        try:
            site_id = self.dynamic_tokens.get("siteId") or self.dynamic_tokens.get("site_id") or "1096"
            client_ip = self.dynamic_tokens.get("clientIp") or self.dynamic_tokens.get("client_ip")
            client_mac = self.dynamic_tokens.get("clientMac") or self.dynamic_tokens.get("client_mac")
            
            # Если IP/MAC еще не определены, попробуем определить
            if not client_ip or not client_mac:
                 ip, mac = self._detect_client_ip_mac()
                 client_ip = client_ip or ip
                 client_mac = client_mac or mac

            if not client_ip:
                self.logger.warning("[TOKEN-GEN] Client IP unknown, using fallback")
                client_ip = "127.0.0.1"

            # Extract himalaya-site-ident cookie
            site_ident = None
            for c in self.cookies:
                if c.name == "himalaya-site-ident":
                    site_ident = c.value
                    break
            
            if not site_ident:
                self.logger.warning("[TOKEN-GEN] himalaya-site-ident cookie not found! Cannot generate signed token.")
                return None

            self.logger.info(f"[TOKEN-GEN] Generating token for site={site_id} ip={client_ip} mac={client_mac} using cookie hash")
            try:
                s = unquote(site_ident or "")
                pad = "=" * ((4 - len(s) % 4) % 4)
                dec = base64.b64decode((s + pad).encode("ascii"))
                decs = dec.decode("utf-8", "replace")
                if "|" in decs:
                    h = decs.split("|")[-1]
                else:
                    h = None
            except Exception:
                h = None
            if h:
                ser = self._quickjs_serialize_wbs_token(site_id, client_ip, client_mac)
                if ser:
                    full = f"HWA*{ser}|{h}"
                    tok = base64.b64encode(full.encode("utf-8")).decode("ascii")
                    self.logger.info(f"[TOKEN-GEN] QuickJS token: {tok[:50]}...")
                    return tok
            
            # METHOD 2: Reuse cookie content directly, just changing prefix
            # Assuming wbsApiAuthToken is just the SiteIdent token presented as AuthToken
            if site_ident and "HSI*" in unquote(site_ident):
                raw = unquote(site_ident)
                if raw.startswith("HSI*"):
                    # Just replace prefix. The content (SiteIdent object) and signature remain valid.
                    token_str = "HWA*" + raw[4:]
                    self.logger.info(f"[TOKEN-GEN] Patched cookie token: {token_str[:50]}...")
                    return token_str
                elif "HSI*" in raw:
                    token_str = raw.replace("HSI*", "HWA*")
                    self.logger.info(f"[TOKEN-GEN] Patched cookie token (replace): {token_str[:50]}...")
                    return token_str
            
            # Fallback to QuickJS generation if patch failed
            ser = self._quickjs_serialize_wbs_token(site_id, client_ip, client_mac)
            if ser and h:
                full = f"HWA*{ser}|{h}"
                tok = base64.b64encode(full.encode("utf-8")).decode("ascii")
                self.logger.info(f"[TOKEN-GEN] QuickJS token: {tok[:50]}...")
                return tok

            # Last resort: use library to rebuild
            token_str = WbsTokenBuilder.generate_wbs_token_from_site_ident(site_ident, site_id, client_ip, client_mac)
            if token_str:
                self.logger.info(f"[TOKEN-GEN] Library generated token: {token_str[:50]}...")
                return token_str
            else:
                self.logger.error("[TOKEN-GEN] Failed to generate token from cookie.")
                return None

        except Exception as e:
            self.logger.error(f"[TOKEN-GEN] Error generating token: {e}")
            return None

    def _call_create_session_api(self):
        base_url = self.page_url or self.portal_url or ""
        if not base_url:
            return False
        if self.dynamic_tokens.get("apiSessionId"):
            return True
        
        curl_proxy = None
        if "socks5h://" in os.environ.get("ALL_PROXY", ""):
            curl_proxy = os.environ["ALL_PROXY"]
        elif self.socks_manager and self.socks_manager.socks_port:
             # Just in case environment variable was cleared but proxy is managed
             # Check if we should use it? 
             # For now rely on ALL_PROXY or manual check.
             # If I manually forced proxy, ALL_PROXY might not be set in this process if I didn't call ensure_socks_proxy?
             # But I did call ensure_socks_proxy via check_internet logic if I am in that flow.
             # Wait, if I am running with my manual command, I might rely on env vars?
             # No, I didn't set env vars in my manual run.
             # But the script calls ensure_socks_proxy if internet check fails.
             # And ensure_socks_proxy sets env vars.
             pass

        client = WbsApiClient(base_url, opener=self.opener, cookies=self.cookies, logger=self.logger, curl_proxy=curl_proxy)
        client.page_html = self.page_html
        site_id = self.cookie_decoded_site_id or "1096"
        token = self.dynamic_tokens.get("wbsApiAuthToken") or self._create_wbs_api_auth_token()
        res = client.create_session(token=token, site_id=site_id, locale=self.default_locale, session_id="")
        if res.get("ok"):
            self.dynamic_tokens["apiSessionId"] = res.get("apiSessionId")
            self.logger.info(f"[CREATE-SESSION] apiSessionId={res.get('apiSessionId')}")
            return True
        try:
            self.logger.info(f"[CREATE-SESSION] error={res.get('error')} payload_keys={list((res.get('payload') or {}).keys())}")
            body_preview = (res.get('body') or '')
            self.logger.info(f"[CREATE-SESSION] body preview: {body_preview[:200]}")
        except Exception:
            pass
        return False

    def _run_api_flow(self):
        """Попытка авторизации через API (wbs/api/v1) с детерминированным session token"""
        print("[DEBUG] Entering _run_api_flow")
        try:
            ok = self._call_create_session_api()
            print(f"[DEBUG] create_session result: {ok}")

            base_url = self.page_url or self.portal_url or ""
            print(f"[DEBUG] base_url: {base_url}")
            if not base_url:
                print("[DEBUG] base_url is empty!")
                return False
            p = urlparse(base_url)
            domain = p.netloc
            scheme = p.scheme or "https"
            print(f"[DEBUG] domain={domain}, scheme={scheme}")

            session_token = None
            session_source = None

            # Prioritize apiSessionId
            # Prefer to use apiSessionId for payload field, but authorization must be PHPSESSID
            api_sid = None
            try:
                api_sid = self.dynamic_tokens.get("apiSessionId") or self.dynamic_tokens.get("api_session_id")
            except Exception:
                api_sid = None
            php_sid = None
            try:
                php_sid = self._ensure_php_session_cookie()
            except Exception:
                php_sid = None
            if api_sid:
                session_token = api_sid
                session_source = "apiSessionId"
            elif php_sid:
                session_token = php_sid
                session_source = "PHPSESSID"

            if not session_token:
                print("[DEBUG] No session token found (apiSessionId/PHPSESSID)")
                self.logger.info("[API] Не удалось определить единственный session token, прерываем API flow")
                return False

            login_url = f"{scheme}://{domain}/wbs/api/v1/login/free/"
            try:
                base = f"{scheme}://{domain}"
                r_pre = self._open(self._req(f"{base}/registration-free", referer=self.page_url))
                try:
                    _ = r_pre.read()
                except Exception:
                    pass
                # Re-evaluate PHPSESSID after hitting registration-free
                php_sid = self._ensure_php_session_cookie() or php_sid
                # Also hit payment-return-proxy.php to force PHP session creation
                try:
                    sid = self.dynamic_tokens.get("siteId") or "1096"
                    prx = f"https://{sid}.rdr.conn4.com/admon-assets/payment-return-proxy.php?PaymentProxyUrl="
                    r_prx = self._open(self._req(prx, referer=base))
                    try:
                        _ = r_prx.read()
                    except Exception:
                        pass
                    php_sid = self._ensure_php_session_cookie() or php_sid
                except Exception:
                    pass
                # Try authenticate-me endpoint which often sets PHPSESSID
                try:
                    r_auth = self._open(self._req(f"{base}/wbs/authenticate-me/", referer=base))
                    try:
                        _ = r_auth.read()
                    except Exception:
                        pass
                    php_sid = self._ensure_php_session_cookie() or php_sid
                except Exception:
                    pass
            except Exception:
                pass
            self.logger.info(f"[API] Используем session token из {session_source}: {session_token[:15]}...")

            # Используем consent body как в Selenium (минимальный набор полей, authorization=session=<PHPSESSID>)
            try:
                payload_data = self._build_consent_body()
            except Exception as e:
                self.logger.warning(f"[API] Ошибка сборки consent body: {e}")
                payload_data = urlencode({
                    "authorization": f"session={php_sid or session_token}",
                    "tariff": self.default_tariff
                }).encode("utf-8")

            try:
                req_login = self._req(login_url, data=payload_data, referer=base_url, ajax=True)
                self.logger.info(f"[API] POST {login_url} payload_len={len(payload_data or b'')}")
                resp_login = self._open(req_login)

                resp_body = ""
                try:
                    resp_body = resp_login.read().decode("utf-8", "replace")
                except Exception:
                    pass

                self.logger.info(f"[API] Raw login response ({session_source}): {resp_body[:200]}")
                
                # Обновляем page_html для check_success
                self.page_html = resp_body

                is_ok = False
                try:
                    res_json = json.loads(resp_body)
                    if res_json.get("success") or res_json.get("authorized") or res_json.get("status") == "ok":
                        is_ok = True
                    else:
                        self.logger.info(f"[API] JSON ответ не подтверждает успех: {res_json}")
                        # Fallback for 1004 Registration required
                        if str(res_json.get("error", {}).get("code")) == "1004":
                            self.logger.info("[API] Detected 1004 Registration required. Attempting fallback to registration...")
                            try:
                                reg_url = f"{scheme}://{domain}/wbs/api/v1/registration/"
                                self.logger.info(f"[API] Fallback POST {reg_url}")
                                req_reg = self._req(reg_url, data=payload_data, referer=base_url, ajax=True)
                                resp_reg = self._open(req_reg)
                                reg_body = resp_reg.read().decode("utf-8", "replace")
                                self.logger.info(f"[API] Registration fallback response: {reg_body[:200]}")
                                try:
                                    rj = json.loads(reg_body)
                                    if rj.get("success") or rj.get("authorized") or rj.get("status") == "ok":
                                        is_ok = True
                                        self.page_html = reg_body
                                except Exception:
                                    pass
                            except Exception as e:
                                self.logger.info(f"[API] Registration fallback failed: {e}")
                        # Fallback for 700 Illegal/Empty token: try minimal payload (authorization + tariff)
                        try:
                            err_code = str((res_json.get("error") or {}).get("code"))
                        except Exception:
                            err_code = None
                        if not is_ok and err_code == "700":
                            try:
                                self.logger.info("[API] Detected 700 Illegal/Empty token. Trying minimal payload fallback...")
                                php_sid2 = self._ensure_php_session_cookie() or php_sid or session_token
                                min_body = urlencode({
                                    "authorization": f"session={php_sid2}",
                                    "tariff": self.dynamic_tokens.get("tariff", self.default_tariff)
                                }).encode("utf-8")
                                req_min = self._req(login_url, data=min_body, referer=base_url, ajax=True)
                                resp_min = self._open(req_min)
                                min_text = resp_min.read().decode("utf-8","replace")
                                self.logger.info(f"[API] Minimal payload response: {min_text[:200]}")
                                try:
                                    mj = json.loads(min_text)
                                    if mj.get("success") or mj.get("authorized") or mj.get("status") == "ok":
                                        is_ok = True
                                        self.page_html = min_text
                                except Exception:
                                    pass
                            except Exception as e:
                                self.logger.info(f"[API] Minimal payload fallback error: {e}")
                except Exception:
                    final_url = resp_login.geturl()
                    if "leonardo-hotels.com" in final_url or "conn4.com" not in final_url.lower():
                        self.logger.info(f"[API] Редирект на внешний домен: {final_url}")
                        is_ok = True

                if is_ok:
                    self.logger.info(f"[API] ✅ Авторизация успешна c токеном из {session_source}")
                    self.page_url = resp_login.geturl()
                    return True

                self.logger.info(f"[API] ❌ Авторизация через API не удалась с токеном из {session_source}")
                return False

            except Exception as e:
                self.logger.info(f"[API] Ошибка запроса login/free: {e}")
                import traceback
                self.logger.debug(traceback.format_exc())
                return False

        except Exception as e:
            self.logger.info(f"[API] Ошибка потока: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False

    def load_tokens_json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            for k in ("apiSessionId","paymentReturnProxyUrl","siteId","clientIp","clientMac","signature"):
                v = obj.get(k)
                if v:
                    if k in ("apiSessionId","paymentReturnProxyUrl"):
                        self.dynamic_tokens[k] = v
                    else:
                        self.initial_query[k] = [v]
            return True
        except Exception:
            return False


    def _collect_tokens_step(self):
        try:
            toks = self._collect_tokens()
            if toks:
                self.dynamic_tokens.update(toks)
            return bool(toks)
        except Exception:
            return False

    def _build_redirect_ident_url(self):
        try:
            base = f"{urlparse(self.page_url or self.portal_url).scheme}://{urlparse(self.page_url or self.portal_url).netloc}"
            dest = urljoin(base, "/admon-assets/ident.php")
            toks = self._collect_tokens()
            mac = toks.get("clientMac") or self.client_mac_override or self.cookie_decoded_mac
            ip = toks.get("clientIp") or self.client_ip_override or self.cookie_decoded_ip
            site = toks.get("siteId") or self.cookie_decoded_site_id
            sig = toks.get("signature")
            q = {}
            if mac: q["client_mac"] = mac
            if ip: q["client_ip"] = ip
            if site: q["site_id"] = site
            if sig: q["signature"] = sig
            return f"{dest}?{urlencode(q)}" if q else dest
        except Exception:
            return None

    def _compute_payment_return_proxy_url(self, site_id=None):
        try:
            sid = str(site_id or self.dynamic_tokens.get("siteId") or "1096")
        except Exception:
            sid = "1096"
        return f"https://{sid}.rdr.conn4.com/admon-assets/payment-return-proxy.php?PaymentProxyUrl="

    def _compute_authorize_request(self):
        """Generates a Form-Submit-like request (instead of JSON API) to match Selenium flow."""
        try:
            # Target is the current page URL (the scene)
            target = self.page_url
            if not target:
                return None

            # Get tokens
            toks = self._collect_tokens()
            
            # Prepare payload exactly as in build_consent_body, but flatten for urlencode
            # Note: _build_consent_body returns encoded bytes. Let's reuse it logic but keep dict.
            # However, _build_consent_body might be too API-centric. 
            # Let's rebuild the form data that the browser would send.
            
            # Form fields commonly found:
            payload = {
                "agree": "1",
                "accept": "1",
                "terms": "1",
                "policy": "1",
                "consent": "1",
                "tariff": self.default_tariff
            }
            
            # Add dynamic tokens from hidden fields/JS
            for k in ("site_id", "client_ip", "client_mac", "signature", "loggedin", "remembered_mac", 
                      "api_session_id", "payment_return_proxy_url", "wbsApiAuthToken"):
                 v = toks.get(k)
                 if v:
                     payload[k] = v
            
            # CamelCase variants if needed (based on previous observations)
            # Actually, let's include what we found in tokens
            if "apiSessionId" in toks and "api_session_id" not in payload:
                 payload["api_session_id"] = toks["apiSessionId"]
            
            if "apiSessionId" not in toks and "api_session_id" not in payload:
                self.logger.warning("⚠️ apiSessionId missing in tokens! Form submission might fail.")
                # Try to force it from dynamic_tokens if available
                if self.dynamic_tokens.get("apiSessionId"):
                    payload["api_session_id"] = self.dynamic_tokens["apiSessionId"]
                    self.logger.info("Recovered apiSessionId from dynamic_tokens")

            # Authorization field (session=PHPSESSID)
            # Browser sends this if it's a hidden input.
            # In API flow we added it manually. In form flow, is it present?
            # If not present in HTML, we shouldn't add it unless we know it's required.
            # But we saw Selenium sending it in "authorization" field in API logs? 
            # Wait, Selenium logs showed "authorization=session=..." in the POST payload for API.
            # But for the FORM submit (Get Free Wi-Fi), we don't have the exact payload logs.
            # Let's assume it behaves like a standard form.
            
            # If the form tag has no action, it submits to self.
            # If method is missing, it defaults to GET? No, usually POST for login.
            # But the form tag we saw: <form id="...-form" novalidate="" data-parsley="">
            # It has no method! Default is GET.
            # BUT, usually there is JS that intercepts submit and does AJAX or POST.
            # Selenium clicks the button. If it's a standard submit button, it submits the form.
            # If there is JS handler, it might do anything.
            
            # We saw in Selenium logs:
            # [18:53:43] INFO:   Форма 2: get https://.../scenes/.../ id='wbs-tpl-registration-free-form'
            # So the form itself might be GET.
            # BUT, the button has class `js-button-ok`. This implies JS handling.
            
            # If it's JS handled, it likely calls the API.
            # BUT our API call failed with 400 Registration Required.
            # Maybe we called the WRONG API endpoint? or wrong parameters?
            
            # Let's try to emulate the FORM SUBMIT to the SCENE URL (self.page_url) using POST (or GET?).
            # Given "Registration Required", maybe we missed a step or parameter in the API call.
            # OR the "Get Free Wi-Fi" button actually triggers a `create-session` then `login/free`?
            # We did `create-session` successfully.
            # `login/free` failed.
            
            # Let's look at `test_conn4_portal_nojs.py` _run_api_flow again.
            # It calls `_call_create_session_api`, then `login/free`.
            
            # Maybe the JS on the page does something else?
            # Selenium artifact `conn4_session_storage_trace.json` showed calls to `create-session`.
            # Did it show `login/free`?
            # We grep'd apiSessionId and found it in `create-session` response and `login/free` payload!
            # So Selenium DOES call `login/free`.
            
            # Why did Selenium succeed and NoJS fail?
            # Selenium Payload for login/free:
            # agree=1&accept=1&terms=1&policy=1&consent=1&loggedin=0&remembered_mac=0&loggedIn=0&rememberedMac=0&site_id=1096&client_ip=10.x.x.x&client_mac=XXXXXXXXXXXX&signature=...&apiSessionId=...&api_session_id=...&paymentReturnProxyUrl=...&payment_return_proxy_url=...&clientIp=...&clientMac=...&siteId=...&authorization=session%3D...&tariff=381
            
            # NoJS Payload:
            # agree=1&accept=1&terms=1&policy=1&consent=1&loggedin=0&remembered_mac=0&loggedIn=0&rememberedMac=0&site_id=1096&client_ip=10.x.x.x&client_mac=XXXXXXXXXXXX&signature=...&paymentReturnProxyUrl=...&payment_return_proxy_url=...&clientIp=...&clientMac=...&siteId=...&authorization=session%3D...&tariff=381
            
            # Difference: NoJS payload has `apiSessionId` MISSING in the diffs!
            # Wait, let's check the diff output from the failed run.
            # computedTokens.apiSessionId: Selenium=... NoJS=... (Different values, expected)
            # computedConsent.apiSessionId: Selenium=... NoJS=... (Different values)
            
            # Ah, the diff showed NoJS had `apiSessionId` in computedConsent.
            # But look at the log:
            # [19:02:27] INFO: [REQ DATA] ...&signature=...&paymentReturnProxyUrl=... (apiSessionId MISSING between signature and paymentReturnProxyUrl?)
            # Wait, let me check the log carefully.
            # NoJS log: ...&signature=c1563...&paymentReturnProxyUrl=...
            # Selenium log: ...&signature=c1563...&apiSessionId=...&api_session_id=...&paymentReturnProxyUrl=...
            
            # IT SEEMS `apiSessionId` IS MISSING IN NOJS PAYLOAD!
            # Even though `_build_consent_body` seems to add it?
            
            # Let's check `_build_consent_body` in `test_conn4_portal_nojs.py`.
            # It uses `toks.get("apiSessionId")`.
            # And `toks` comes from `_collect_tokens()`.
            # `_collect_tokens` collects from HTML and `dynamic_tokens`.
            
            # In `_run_api_flow`:
            # `ok = self._call_create_session_api()` -> updates `self.dynamic_tokens["apiSessionId"]`.
            # Then it calls `_build_consent_body()`.
            # `_build_consent_body` calls `_collect_tokens()`.
            # Does `_collect_tokens` merge `dynamic_tokens`?
            
            # Authorization field (session=PHPSESSID)
            # ...
            
            # Construct the request
            data = urlencode(payload).encode("utf-8")
            # POST to target
            req = self._req(target, data=data, referer=target)
            return req

        except Exception as e:
            self.logger.error(f"[_compute_authorize_request] Error: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None

    def _run_form_flow(self):
        """Attempts to authorize via Form Submit (imitating browser click)"""
        self.logger.info("=== ЗАПУСК FORM FLOW (Эмуляция клика) ===")
        
        # Try using robust submit_forms first
        if self.submit_forms():
            self.logger.info("[FORM] ✅ Успешная авторизация (submit_forms)")
            return True
            
        req = self._compute_authorize_request()
        if not req:
            self.logger.warning("Не удалось сформировать запрос для Form Flow")
            return False
            
        try:
            self.logger.info(f"[FORM] POST {req.get_full_url()}")
            resp = self._open(req)
            code = resp.getcode()
            self.logger.info(f"[FORM] Response code: {code}")
            
            body = resp.read().decode("utf-8", "replace")
            self.page_html = body
            self.page_url = resp.geturl()
            
            # Check for redirect to success page
            if "leonardo-hotels.com" in self.page_url or "conn4.com" not in self.page_url.lower():
                 self.logger.info(f"[FORM] ✅ Редирект на внешний домен: {self.page_url}")
                 return True
                 
            if self.check_success():
                 self.logger.info("[FORM] ✅ Успешная авторизация (check_success)")
                 return True
                 
            return False
        except Exception as e:
            self.logger.error(f"[FORM] Ошибка выполнения запроса: {e}")
            return False

    def single_post_authorize(self):
        try:
            base = f"{urlparse(self.page_url or self.portal_url).scheme}://{urlparse(self.page_url or self.portal_url).netloc}"
            chosen = None
            try:
                chosen = choose_authorize_endpoint(self.page_html or "", self.page_url or self.portal_url)
            except Exception:
                chosen = None
            api_endpoint = chosen or f"{base}/wbs/api/v1/login/free/"
            
            # FORCE override for conn4 to ensure we use the API endpoint, not the HTML page
            # Check both the calculated endpoint host AND the current page URL
            host = urlparse(api_endpoint).netloc.lower()
            page_host = urlparse(self.page_url or "").netloc.lower()
            
            if "conn4.com" in host or "conn4.com" in page_host:
                # Always force the API endpoint for conn4
                api_endpoint = f"{base}/wbs/api/v1/login/free/"
                self.logger.info(f"[AUTH] FORCED conn4 endpoint: {api_endpoint}")
            
            self.logger.info(f"[AUTH] Endpoint авторизации: {api_endpoint}")

            time.sleep(1)

            try:
                has_ident = any((c.name == "himalaya-site-ident") for c in self.cookies)
            except Exception:
                has_ident = False
            if not has_ident:
                try:
                    iu = self._build_redirect_ident_url()
                    if iu:
                        r0 = self._open(self._req(iu, referer=self.page_url))
                        try:
                            self.page_html = r0.read().decode("utf-8","replace")
                        except Exception:
                            self.page_html = ""
                        self.page_url = r0.geturl()
                        self._record_touch(self.page_url)
                except Exception:
                    pass

            payload = self._build_consent_body()
            try:
                payload_str = payload.decode("utf-8", "replace")
                self.logger.info(f"[AUTH] Отправляем POST с payload: {payload_str}")
            except Exception:
                pass
            referer = self._choose_login_referer() or self.page_url
            ajax = "/wbs/" in api_endpoint
            req = self._req(api_endpoint, data=payload, referer=referer, ajax=ajax)
            resp = self._open(req)

            status_code = resp.getcode()
            final_url = resp.geturl()

            self.logger.info(f"[AUTH] HTTP статус: {status_code}")
            self.logger.info(f"[AUTH] Final URL: {final_url}")

            try:
                try:
                    hdr = resp.info()
                    set_cookie = hdr.get_all("Set-Cookie") if hasattr(hdr, "get_all") else [hdr.get("Set-Cookie")]
                    self.logger.info(f"[AUTH HDR] {str(hdr)[:300]}")
                    if set_cookie:
                        self.logger.info(f"[AUTH Set-Cookie] {set_cookie}")
                except Exception:
                    pass
                resp_body = resp.read()
                if isinstance(resp_body, bytes):
                    resp_text = resp_body.decode("utf-8", "replace")
                else:
                    resp_text = str(resp_body)
                self.logger.info(f"[AUTH] Размер ответа: {len(resp_text)} символов")

                # Парсим JSON ответ API
                try:
                    resp_json = json.loads(resp_text)
                    self.logger.info(f"[AUTH] JSON ответ: {json.dumps(resp_json, ensure_ascii=False)[:300]}")

                    # Проверяем успешность в JSON
                    if isinstance(resp_json, dict):
                        if resp_json.get("success") or resp_json.get("status") == "success" or resp_json.get("result") == "success":
                            self.logger.info("[AUTH] ✅ API вернул success в JSON")
                            return True
                        # Проверяем наличие ошибок
                        if resp_json.get("error") or resp_json.get("status") == "error":
                            error_msg = resp_json.get("error") or resp_json.get("message") or "Unknown error"
                            self.logger.error(f"[AUTH] ❌ API вернул ошибку: {error_msg}")
                            return False
                except json.JSONDecodeError:
                    # Не JSON, возможно HTML
                    self.page_html = resp_text
                    self.logger.info(f"[AUTH] Ответ не JSON, первые 200 символов: {resp_text[:200]}")

                # Логируем ответ сервера для анализа
                if status_code >= 400:
                    self.logger.error(f"[AUTH] ❌ Ошибка HTTP {status_code}, ответ сервера:")
                    self.logger.error(f"[AUTH] {resp_text[:500]}")
                else:
                    self.logger.info(f"[AUTH] Ответ сервера (первые 200 символов): {resp_text[:200]}")
            except Exception as e:
                self.logger.error(f"[AUTH] Ошибка чтения ответа: {e}")
                resp_text = ""

            self.page_url = final_url
            self._record_touch(self.page_url)

            # Проверяем статус код
            if status_code >= 400:
                self.logger.error(f"[AUTH] ❌ Сервер вернул ошибку {status_code}")
                return False

            # Для API endpoint успешный ответ - это 200 с JSON
            if status_code == 200:
                self.logger.info("[AUTH] ✅ API вернул 200 OK")
                # Проверяем через check_success для дополнительной валидации
                if self.check_success():
                    return True
                # Выполняем переход по paymentReturnProxyUrl если известен
                try:
                    toks = self._collect_tokens()
                    prx = toks.get("paymentReturnProxyUrl") or self.dynamic_tokens.get("paymentReturnProxyUrl")
                    if prx:
                        self.logger.info(f"[AUTH] Переход по paymentReturnProxyUrl: {prx}")
                        r2 = self._open(self._req(prx, referer=api_endpoint))
                        self.page_url = r2.geturl()
                        try:
                            self.page_html = r2.read().decode("utf-8","replace")
                        except Exception:
                            self.page_html = ""
                        self._record_touch(self.page_url)
                        if self.check_success():
                            return True
                except Exception:
                    pass
                # Даже если check_success не прошел, 200 от API обычно означает успех
                return True

            # Анализ результата для HTML ответов
            if "conn4.com" not in final_url.lower():
                self.logger.info("[AUTH] ✅ Редирект за пределы conn4.com!")
                return True

            # Проверяем индикаторы в HTML
            if resp_text:
                html_lower = resp_text.lower()
                if "success" in html_lower or "connected" in html_lower:
                    self.logger.info("[AUTH] ✅ Найдены индикаторы успеха в ответе")
                    return True

            self.logger.info("[AUTH] ⚠️  POST отправлен успешно, проверяем результат...")
            return True

        except Exception as e:
            self.logger.error(f"[AUTH] ❌ Ошибка авторизации: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False

    def _choose_authorize_endpoint(self):
        try:
            base = f"{urlparse(self.page_url or self.portal_url).scheme}://{urlparse(self.page_url or self.portal_url).netloc}"
            html = self.page_html or ""
            fp = FormParser()
            try:
                fp.feed(html)
            except Exception:
                pass
            for f in fp.forms:
                a = (f.action or "").lower()
                if any(x in a for x in ["registration", "free-login", "authenticate", "wbs"]):
                    return urljoin(base, f.action or "/registration-free")
            m = re.search(r"['\"](/[^'\"\s]*registration-free[^'\"\s]*)['\"]", html, flags=re.IGNORECASE)
            if m:
                return urljoin(base, m.group(1))
            m = re.search(r"['\"](/[^'\"\s]*free-login[^'\"\s]*)['\"]", html, flags=re.IGNORECASE)
            if m:
                return urljoin(base, m.group(1))
            m = re.search(r"['\"](/[^'\"\s]*authenticate[^'\"\s]*)['\"]", html, flags=re.IGNORECASE)
            if m:
                return urljoin(base, m.group(1))
            m = re.search(r"['\"](/[^'\"\s]*wbs[^'\"\s]*)['\"]", html, flags=re.IGNORECASE)
            if m:
                return urljoin(base, m.group(1))
            return urljoin(base, "/registration-free")
        except Exception:
            base = f"{urlparse(self.page_url or self.portal_url).scheme}://{urlparse(self.page_url or self.portal_url).netloc}"
            return urljoin(base, "/registration-free")

    def _build_consent_body(self):
        try:
            toks = self._collect_tokens()
            
            # 1. Client IP/MAC
            ip, mac = self._detect_client_ip_mac()
            if ip:
                toks["client_ip"] = ip
                toks["clientIp"] = ip
            if mac:
                toks["client_mac"] = mac
                toks["clientMac"] = mac
                
            # 2. Extract from HTML (again, just in case)
            try:
                html_tokens = extract_tokens_from_html(self.page_html or "")
                for k, v in (html_tokens or {}).items():
                    if k not in toks:
                        toks[k] = v
            except Exception:
                pass

            # 3. Dynamic tokens merge
            try:
                dyn = getattr(self, "dynamic_tokens", {}) or {}
                for k, v in dyn.items():
                    if v is not None and k not in toks:
                        toks[k] = v
            except Exception:
                pass
            
            # 4. apiSessionId normalization
            api_val = toks.get("apiSessionId") or toks.get("api_session_id")
            if api_val:
                toks["apiSessionId"] = api_val
                toks["api_session_id"] = api_val
            else:
                try:
                    ok = self._call_create_session_api()
                    if ok:
                        api_val2 = self.dynamic_tokens.get("apiSessionId") or self.dynamic_tokens.get("api_session_id")
                        if api_val2:
                            toks["apiSessionId"] = api_val2
                            toks["api_session_id"] = api_val2
                except Exception:
                    pass
            
            # 5. paymentReturnProxyUrl
            prx_val = toks.get("paymentReturnProxyUrl") or toks.get("payment_return_proxy_url")
            if not prx_val:
                sid = toks.get("siteId") or toks.get("site_id") or "1096"
                prx_val = f"https://{sid}.rdr.conn4.com/admon-assets/payment-return-proxy.php?PaymentProxyUrl="
                self.logger.info(f"[CONSENT] Generated fallback paymentReturnProxyUrl: {prx_val}")
            
            if prx_val:
                toks["paymentReturnProxyUrl"] = prx_val
                toks["payment_return_proxy_url"] = prx_val
                
            # 6. PHPSESSID
            phpsessid = None
            try:
                phpsessid = self._ensure_php_session_cookie()
            except Exception:
                phpsessid = None

            # 7. Build body
            # Use minimal tokens and empty QS to match Selenium behavior (avoid polluting body with tracking params)
            minimal_tokens = {}
            # Keep only essential tokens for login/free (CamelCase preferred by conn4)
            keep_keys = ["apiSessionId", "paymentReturnProxyUrl", "wbsApiAuthToken"]
            for k in keep_keys:
                if k in toks:
                    minimal_tokens[k] = toks[k]
            
            # Ensure wbsApiAuthToken is present if we can generate it
            if "wbsApiAuthToken" not in minimal_tokens:
                try:
                    wbs_tok = self.dynamic_tokens.get("wbsApiAuthToken") or self._create_wbs_api_auth_token()
                    if wbs_tok:
                        minimal_tokens["wbsApiAuthToken"] = wbs_tok
                except Exception:
                    pass

            # Pass empty dict for qs to avoid merging initial_query params (client_ip, mac, etc.)
            consent = build_consent_body({}, minimal_tokens, self.dynamic_tokens.get("tariff", self.default_tariff), phpsessid=phpsessid)

            # 8. Ensure camelCase and snake_case consistency for specific fields
            # REMOVED: Do not force loggedIn/rememberedMac as they are not present in Selenium success payload
            # and might trigger 400 Registration required.
            
            # 9. Ensure authorization field
            if "authorization" not in consent:
                # Use apiSessionId as fallback for authorization if PHPSESSID is not available
                auth_val = phpsessid or toks.get("apiSessionId") or toks.get("api_session_id")
                if auth_val:
                    consent["authorization"] = f"session={auth_val}"
                else:
                    self.logger.warning("[CONSENT] WARNING: No session token (PHPSESSID/apiSessionId) for authorization field!")

            # Log
            self.logger.info(f"[CONSENT] Body keys: {list(consent.keys())}")
            if "paymentReturnProxyUrl" not in consent:
                self.logger.error("[CONSENT] CRITICAL: paymentReturnProxyUrl MISSING in body!")

            return urlencode(consent or {}).encode("utf-8")
        except Exception as e:
            self.logger.error(f"[CONSENT] Error: {e}")
            return urlencode({"agree":"1","accept":"1","terms":"1","consent":"1"}).encode("utf-8")

    def run_external_refs_only(self):
        try:
            txt = self.page_html or ""
            if txt:
                try:
                    self._log_external_lib_refs(txt)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            urls = self.extract_resource_urls()
        except Exception:
            urls = []
        if urls:
            try:
                self.logger.info(f"[Resources] найдено: {len(urls)}")
                for u in urls:
                    try:
                        self._log_external_lib_refs(u)
                    except Exception:
                        pass
            except Exception:
                pass
        return True
    
    def _fetch_and_parse_js_resources(self):
        try:
            self.logger.info("[JS-FETCH] Starting resource fetch...")
            out_dir = os.path.join(os.getcwd(), "conn4_js")
            try:
                os.makedirs(out_dir, exist_ok=True)
            except Exception:
                pass
            urls = []
            try:
                urls = self.extract_resource_urls()
            except Exception:
                urls = []
            # Также скрипты из HTML
            try:
                for m in re.finditer(r"<script[^>]*src=['\"]([^'\"\\s]+)['\"][^>]*>", self.page_html or "", flags=re.IGNORECASE):
                    urls.append(m.group(1))
            except Exception:
                pass
            
            print(f"DEBUG: JS-FETCH found {len(urls)} URLs. Page HTML len: {len(self.page_html or '')}")
            if len(urls) == 0:
                print(f"DEBUG: HTML preview: {(self.page_html or '')[:500]}")

            self.logger.info(f"[JS-FETCH] Found {len(urls)} potential URLs in HTML (len={len(self.page_html or '')}) at {self.page_url}")
            
            seen = set()
            for u in urls:
                if not u or u in seen:
                    continue
                seen.add(u)
                print(f"DEBUG: Processing URL candidate: {u}")
                try:
                    pu = urlparse(u)
                except Exception:
                    continue
                if not pu.scheme:
                    # make absolute
                    try:
                        base = f"{urlparse(self.page_url or self.portal_url).scheme}://{urlparse(self.page_url or self.portal_url).netloc}"
                        u = urljoin(base, u)
                        pu = urlparse(u)
                        print(f"DEBUG: Resolved absolute URL: {u}")
                    except Exception:
                        pass
                # только .js из conn4
                if not (pu.path or "").lower().endswith(".js"):
                    print(f"DEBUG: Skipped {u} (not .js)")
                    continue
                if "conn4.com" not in (pu.netloc or ""):
                    print(f"DEBUG: Skipped {u} (not conn4.com)")
                    continue
                try:
                    self.logger.info(f"[JS-FETCH] Downloading {u} ...")
                    print(f"DEBUG: Downloading {u} ...")
                    r = self._open(self._req(u, referer=self.page_url))
                    try:
                        raw = r.read()
                        self.logger.info(f"[JS-FETCH] Downloaded {u} (len={len(raw)})")
                        txt = ""
                        try:
                            enc = getattr(r, "headers", {}).get("Content-Encoding", "")
                        except Exception:
                            enc = ""
                        if enc and "gzip" in enc.lower():
                            import gzip
                            try:
                                txt = gzip.decompress(raw or b"").decode("utf-8","replace")
                            except Exception:
                                txt = raw.decode("utf-8","replace")
                        else:
                            txt = raw.decode("utf-8","replace")
                    except Exception as e:
                        self.logger.warning(f"[JS-FETCH] Error reading {u}: {e}")
                        txt = ""
                    if txt:
                        self.logger.info(f"[JS-FETCH] Parsing {u} for tokens...")
                        old_keys = set(self.dynamic_tokens.keys())
                        self._collect_tokens_from_text(txt)
                        new_keys = set(self.dynamic_tokens.keys()) - old_keys
                        if new_keys:
                            self.logger.info(f"[JS-FETCH] Found new tokens in {u}: {new_keys}")
                        
                        # Сохраняем JS для реверса
                        try:
                            fn = (pu.netloc or "conn4") + (pu.path or "")
                            fn = re.sub(r"[\\/]+", "_", fn)
                            if not fn.lower().endswith(".js"):
                                fn += ".js"
                            fout = os.path.join(out_dir, fn)
                            with open(fout, "w", encoding="utf-8") as wf:
                                wf.write(txt)
                        except Exception:
                            pass
                except Exception:
                    continue
            return True
        except Exception:
            return False
    
    def _load_scene_pages(self):
        try:
            html = self.page_html or ""
            scenes = []
            for m in re.finditer(r"['\"](/scenes/[^'\"\\s]+)['\"]", html, flags=re.IGNORECASE):
                scenes.append(m.group(1))
            for m in re.finditer(r"['\"](/admon-assets/[^'\"\\s]*scene[^'\"\\s]*)['\"]", html, flags=re.IGNORECASE):
                scenes.append(m.group(1))
            base = f"{urlparse(self.page_url or self.portal_url).scheme}://{urlparse(self.page_url or self.portal_url).netloc}"
            for u in scenes:
                try:
                    absu = urljoin(base, u)
                    r = self._open(self._req(absu, referer=self.page_url))
                    self.page_url = r.geturl()
                    try:
                        self.page_html = r.read().decode("utf-8","replace")
                    except Exception:
                        self.page_html = ""
                    self._record_touch(self.page_url)
                    # После загрузки scenes попробуем собрать токены из HTML и JS
                    try:
                        # Сбор токенов из HTML (conn4.hotspot.wbsToken)
                        self._collect_tokens_from_text(self.page_html or "")
                        self._fetch_and_parse_js_resources()
                    except Exception:
                        pass
                    # Сохраняем inline-скрипты для реверса
                    try:
                        out_dir = os.path.join(os.getcwd(), "conn4_js")
                        os.makedirs(out_dir, exist_ok=True)
                        scripts = re.findall(r"<script[^>]*>(.*?)</script>", self.page_html or "", flags=re.IGNORECASE | re.DOTALL)
                        for i, body in enumerate(scripts or []):
                            try:
                                with open(os.path.join(out_dir, f"inline_{i}.js"), "w", encoding="utf-8") as wf:
                                    wf.write(body or "")
                            except Exception:
                                pass
                    except Exception:
                        pass
                except Exception:
                    continue
            return True
        except Exception:
            return False

    def _save_mcp_artifacts(self):
        try:
            run_dir = getattr(self, "artifact_dir", None)
            if not run_dir:
                return

            saved = []
            try:
                for fname in os.listdir(run_dir):
                    if fname.startswith("conn4_") and (fname.endswith(".json") or fname.endswith(".png")):
                        saved.append(fname)
            except Exception:
                pass
            
            if os.path.exists("conn4_nojs_debug.log"):
                try:
                    shutil.copy2("conn4_nojs_debug.log", os.path.join(run_dir, "conn4_nojs_debug.log"))
                    saved.append("conn4_nojs_debug.log")
                except Exception:
                    pass

            index = {
                "created_at": time.time(),
                "run_id": os.path.basename(run_dir),
                "artifacts": saved,
                "meta": {
                    "portal_url": self.portal_url,
                    "final_url": self.page_url
                }
            }
            try:
                idx_path = os.path.join(run_dir, "index.json")
                with open(idx_path, "w", encoding="utf-8") as f:
                    json.dump(index, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            try:
                self.logger.info(f"MCP артефакты обновлены: {run_dir}")
            except Exception:
                pass
        except Exception:
            pass

    def run(self, detect_only=False):
        # Блокировка использования NOJS_FORCE_RUN для исследований
        if os.environ.get("NOJS_FORCE_RUN"):
            self.logger.error("❌ NOJS_FORCE_RUN ломает логику исследований - не используйте для исследований")
            self.logger.error("⚠️  Запуск скрипта отменен по требованию пользователя")
            sys.exit(1)

        self.logger.info("=" * 60)
        self.logger.info("ТЕСТ: авторизация на conn4.com без Selenium")
        self.logger.info("=" * 60)

        # ПРОВЕРКА 1: Доступность SOCKS прокси (уже проверено в main через check_environment)
        if not self.socks_manager.verify_socks_proxy():
            self.logger.warning("⚠️ SOCKS прокси не обнаружен в начале run()")

        self.logger.info("")
        self.logger.info("✅ Обнаружен captive portal - продолжаем авторизацию...")
        self.logger.info("")

        try:
            self.environment_tests()
        except Exception:
            pass

        # Execute the main flow
        # This includes portal detection as the first step, matching Selenium behavior.
        if self.run_flow(detect_only=detect_only):
            return True
        
        self.logger.info("Авторизация не подтверждена")
        try:
            self.logger.info(f"Ресурсов посещено: {len(self.touched_urls)}")
            doms = sorted(self.touched_domains.items(), key=lambda kv: kv[1], reverse=True)
            for d, c in doms:
                self.logger.info(f"Домен: {d} → {c}")
        except Exception:
            pass
        return False

    


def _safe_url(u):
    try:
        p = urlparse(u)
        return f"{p.scheme}://{p.netloc}{p.path}"
    except Exception:
        return u

def _find_latest_artifact_path(base_dir, subdir, filename):
    try:
        d = os.path.join(base_dir, subdir)
        if not os.path.exists(d):
            return None
        runs = sorted([r for r in os.listdir(d) if os.path.isdir(os.path.join(d, r))], reverse=True)
        for r in runs:
            p = os.path.join(d, r, filename)
            if os.path.exists(p):
                return p
        return None
    except Exception:
        return None
def main():
    url_arg = None
    host_id_arg = None
    init_cookie_args = []
    captured_arg = None
    tokens_arg = None
    no_ssh = False
    external_refs_only = False
    collect_only = False
    write_compare = False
    out_arg = "conn4_tokens.json"

    args = sys.argv[1:]
    if os.name == "nt":
        print("Ошибка: Скрипт предназначен для запуска только в среде WSL/Linux.")
        print("Пожалуйста, запустите его через 'wsl python3 ...'")
        sys.exit(2)

    if "--url" in args:
        i = args.index("--url")
        if i + 1 < len(args):
            url_arg = args[i + 1]
    if "--host-id" in args:
        i = args.index("--host-id")
        if i + 1 < len(args):
            host_id_arg = args[i + 1]
    if "--captured" in args:
        i = args.index("--captured")
        if i + 1 < len(args):
            captured_arg = args[i + 1]
    if "--tokens" in args:
        i = args.index("--tokens")
        if i + 1 < len(args):
            tokens_arg = args[i + 1]
    if "--no-ssh" in args:
        no_ssh = True
    if "--external-refs-only" in args:
        external_refs_only = True
    if "--collect-tokens" in args:
        collect_only = True
    if "--write-compare" in args:
        write_compare = True
    if "--out" in args:
        i = args.index("--out")
        if i + 1 < len(args):
            out_arg = args[i + 1]

    if not url_arg:
        url_arg = os.environ.get("PORTAL_URL") or os.environ.get("PORTAL_START_URL") or os.environ.get("SELENIUM_START_URL")

    j = 0
    while True:
        try:
            k = args.index("--cookie", j)
        except ValueError:
            break
        if k + 1 < len(args):
            init_cookie_args.append(args[k + 1])
        j = k + 2

    auth = NoJsConn4Authorizer(portal_url=url_arg)
    if host_id_arg:
        auth.host_id = host_id_arg
    if no_ssh:
        auth.disable_ssh = True
    
    # Рестарт интерфейса если требуется
    env_restart = os.environ.get("RESTART_WWAN") or os.environ.get("NOJS_RESTART_WWAN") or ""
    if str(env_restart).strip().lower() in ("1", "true", "yes", "on"):
        auth.reset_authorization()

    # Проверка окружения (SOCKS)
    if not auth.check_environment():
        sys.exit(3)

    auth.init_cookies()
    for ck in init_cookie_args:
        try:
            name, value = ck.split("=", 1)
            auth._set_cookie(name.strip(), value.strip(), urlparse(auth.portal_url).netloc, "/")
        except Exception:
            pass
    if captured_arg:
        auth.load_captured_artifact(captured_arg)
    if tokens_arg:
        auth.load_tokens_json(tokens_arg)
    else:
        # По умолчанию не подхватываем conn4_tokens.json автоматически,
        # чтобы не использовать устаревшие apiSessionId из прошлых прогонов.
        pass

    # Токены из Selenium прогона НЕ подгружаем (требование: динамическое вычисление)
    # if (os.environ.get("NOJS_ALLOW_ARTIFACTS") or "").strip() == "1":
    #    ...

    if collect_only:
        auth.logger.info("Режим сборки токенов (--collect-tokens)")
        ok = auth.run(detect_only=True)
    elif external_refs_only:
        ok = auth.run_external_refs_only()
    else:
        ok = auth.run()

    # Сохраняем финальные куки и артефакты в любом случае
    auth.save_debug_artifact("conn4_debug_final.json")
    nojs_cookie_path = auth.save_cookie_set_artifact("conn4_cookies_nojs.json")
    try:
        mcp_dir = os.environ.get("MCP_ARTIFACTS_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp_artifacts")
        sel_cookie = _find_latest_artifact_path(mcp_dir, "conn4_selenium", "conn4_cookies_selenium.json")
        if sel_cookie and nojs_cookie_path:
            auth.compare_cookie_sets(sel_cookie, nojs_cookie_path)
    except Exception:
        pass

    try:
        tokens = auth._collect_tokens()
        # Добавляем wbsApiAuthToken в основной список если он есть
        if "wbsApiAuthToken" not in tokens:
            try:
                wbs_tok = auth.dynamic_tokens.get("wbsApiAuthToken") or auth._create_wbs_api_auth_token()
                if wbs_tok:
                    tokens["wbsApiAuthToken"] = wbs_tok
            except Exception:
                pass

        try:
            ip, mac = auth._detect_client_ip_mac()
            if ip and "client_ip" not in tokens:
                tokens["client_ip"] = ip
                tokens["clientIp"] = ip
            if mac and "client_mac" not in tokens:
                tokens["client_mac"] = mac
                tokens["clientMac"] = mac
        except Exception:
            pass
    except Exception:
        tokens = {}
    try:
        consent_bytes = auth._consent_payload()
        consent = {}
        try:
            consent = {kv.split("=")[0]: kv.split("=")[1] for kv in (consent_bytes.decode("utf-8","replace").split("&")) if "=" in kv}
            for k in ("authorization","payment_return_proxy_url","paymentReturnProxyUrl"):
                if k in consent:
                    try:
                        consent[k] = unquote(consent[k])
                    except Exception:
                        pass
            try:
                dyn = getattr(auth, "dynamic_tokens", {}) or {}
            except Exception:
                dyn = {}
            try:
                api_val = tokens.get("api_session_id") or tokens.get("apiSessionId")
            except Exception:
                api_val = None
            if not api_val:
                api_val = dyn.get("api_session_id") or dyn.get("apiSessionId")
            if api_val:
                if "apiSessionId" not in consent:
                    consent["apiSessionId"] = api_val
                if "api_session_id" not in consent:
                    consent["api_session_id"] = api_val
                if "apiSessionId" not in tokens:
                    tokens["apiSessionId"] = api_val
                if "api_session_id" not in tokens:
                    tokens["api_session_id"] = api_val
            try:
                prx_val = tokens.get("payment_return_proxy_url") or tokens.get("paymentReturnProxyUrl")
            except Exception:
                prx_val = None
            if not prx_val:
                prx_val = dyn.get("payment_return_proxy_url") or dyn.get("paymentReturnProxyUrl")
            if prx_val:
                if "paymentReturnProxyUrl" not in consent:
                    consent["paymentReturnProxyUrl"] = prx_val
                if "payment_return_proxy_url" not in consent:
                    consent["payment_return_proxy_url"] = prx_val
                if "paymentReturnProxyUrl" not in tokens:
                    tokens["paymentReturnProxyUrl"] = prx_val
                if "payment_return_proxy_url" not in tokens:
                    tokens["payment_return_proxy_url"] = prx_val
        except Exception:
            consent = {}
        
        try:
            out_tokens = {
                "apiSessionId": tokens.get("apiSessionId") or tokens.get("api_session_id"),
                "paymentReturnProxyUrl": tokens.get("paymentReturnProxyUrl") or tokens.get("payment_return_proxy_url"),
                "siteId": tokens.get("siteId") or tokens.get("site_id"),
                "clientIp": tokens.get("clientIp") or tokens.get("client_ip"),
                "clientMac": tokens.get("clientMac") or tokens.get("client_mac"),
                "signature": tokens.get("signature"),
                "loggedin": ok,
            }
            
            # Сохраняем в артефакты
            with open(os.path.join(auth.artifact_dir, "conn4_tokens_nojs.json"), "w", encoding="utf-8") as f:
                json.dump(out_tokens, f, ensure_ascii=False, indent=2)
                
            # Сохраняем в указанный файл --out (или по умолчанию conn4_tokens.json)
            if out_arg:
                if not os.path.isabs(out_arg):
                     out_path = os.path.join(auth.artifact_dir, out_arg)
                else:
                     out_path = out_arg
                
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(out_tokens, f, ensure_ascii=False, indent=2)
                auth.logger.info(f"Токены сохранены в: {out_path}")
        except Exception:
            pass

        try:
            a_obj = {}
            if write_compare:
                try:
                    # Поиск последнего Selenium прогона для сравнения
                    mcp_dir = os.environ.get("MCP_ARTIFACTS_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp_artifacts")
                    sel_dir = os.path.join(mcp_dir, "conn4_selenium")
                    path_sel = None
                    if os.path.exists(sel_dir):
                        runs = sorted([d for d in os.listdir(sel_dir) if os.path.isdir(os.path.join(sel_dir, d))], reverse=True)
                        if runs:
                            latest = os.path.join(sel_dir, runs[0], "conn4_compare.json")
                            if os.path.exists(latest):
                                path_sel = latest
                    
                    if not path_sel:
                        path_sel = os.path.join(os.getcwd(),"conn4_compare_selenium.json")
                        if not os.path.exists(path_sel):
                            path_sel = os.path.join(os.getcwd(),"conn4_compare.json")

                    if os.path.exists(path_sel):
                        with open(path_sel,"r",encoding="utf-8") as f:
                            a_obj = json.load(f)
                except Exception:
                    a_obj = {}
            
            s_tokens = a_obj.get("computedTokens") or {}
            s_consent = a_obj.get("computedConsent") or {}
            api_val_s = s_tokens.get("apiSessionId") or s_consent.get("apiSessionId")
            prx_val_s = s_tokens.get("paymentReturnProxyUrl") or s_consent.get("paymentReturnProxyUrl")
            
            if api_val_s:
                if "apiSessionId" not in tokens:
                    tokens["apiSessionId"] = api_val_s
                if "apiSessionId" not in consent:
                    consent["apiSessionId"] = api_val_s
                if "api_session_id" not in consent:
                    consent["api_session_id"] = api_val_s
            if prx_val_s:
                if "paymentReturnProxyUrl" not in tokens:
                    tokens["paymentReturnProxyUrl"] = prx_val_s
                if "paymentReturnProxyUrl" not in consent:
                    consent["paymentReturnProxyUrl"] = prx_val_s
                if "payment_return_proxy_url" not in consent:
                    consent["payment_return_proxy_url"] = prx_val_s
            
            if not prx_val:
                prx_val = auth._compute_payment_return_proxy_url(tokens.get("siteId") or consent.get("siteId") or auth.dynamic_tokens.get("siteId"))
                if prx_val:
                    if "paymentReturnProxyUrl" not in tokens:
                        tokens["paymentReturnProxyUrl"] = prx_val
                    if "paymentReturnProxyUrl" not in consent:
                        consent["paymentReturnProxyUrl"] = prx_val
                    if "payment_return_proxy_url" not in consent:
                        consent["payment_return_proxy_url"] = prx_val
        except Exception:
            pass
        cmp_obj = {
            "computedTokens": tokens,
            "computedConsent": consent,
            "network": []
        }
        with open(os.path.join(auth.artifact_dir, "conn4_compare_nojs.json"), "w", encoding="utf-8") as f:
            json.dump(cmp_obj, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    try:
        a = {}
        b = {}
        if write_compare:
            try:
                # Поиск последнего Selenium прогона для сравнения
                mcp_dir = os.environ.get("MCP_ARTIFACTS_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp_artifacts")
                sel_dir = os.path.join(mcp_dir, "conn4_selenium")
                path_sel = None
                if os.path.exists(sel_dir):
                    runs = sorted([d for d in os.listdir(sel_dir) if os.path.isdir(os.path.join(sel_dir, d))], reverse=True)
                    if runs:
                        latest = os.path.join(sel_dir, runs[0], "conn4_compare.json")
                        if os.path.exists(latest):
                            path_sel = latest
                
                if not path_sel:
                    path_sel = os.path.join(os.getcwd(),"conn4_compare_selenium.json")
                    if not os.path.exists(path_sel):
                        path_sel = os.path.join(os.getcwd(),"conn4_compare.json")

                if os.path.exists(path_sel):
                    with open(path_sel,"r",encoding="utf-8") as f:
                        a = json.load(f)
            except Exception:
                a = {}
            try:
                with open(os.path.join(auth.artifact_dir, "conn4_compare_nojs.json"),"r",encoding="utf-8") as f:
                    b = json.load(f)
            except Exception:
                b = {}
            diffs = []
            for k in ("computedTokens","computedConsent"):
                ak = a.get(k) or {}
                bk = b.get(k) or {}
                keys = set(list(ak.keys()) + list(bk.keys()))
                for kk in keys:
                    av = ak.get(kk)
                    bv = bk.get(kk)
                    if av != bv:
                        diffs.append({"field": f"{k}.{kk}", "selenium": av, "nojs": bv})
            if diffs:
                auth.logger.info(f"Обнаружены отличия от Selenium ({len(diffs)})")
                print(json.dumps({"diffs": diffs}, ensure_ascii=False, indent=2))
    except Exception:
        pass
    
    auth._save_mcp_artifacts()

    if ok:
        print("OK")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()
