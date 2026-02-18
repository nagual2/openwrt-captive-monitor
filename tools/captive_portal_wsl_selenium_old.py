#!/usr/bin/env python3
"""
Авторизация на captive порталах через WSL (SOCKS Proxy)
=======================================================

Основной скрипт для авторизации на captive порталах (в частности conn4.com)
через SOCKS прокси. Не требует sudo и изменения маршрутизации.

Использование:
    wsl python3 tools/captive_portal_wsl_selenium.py
"""

import sys
import os
import time
import logging
import subprocess
import json
import re
import socket
import base64
import shutil
from urllib.parse import urlparse, parse_qs, unquote, urlencode
sys.path.append(os.path.dirname(__file__))
from conn4_shared import base_origin_from_url, extract_resource_urls_from_html, extract_urls_from_js_text, extract_tokens_from_html, collect_tokens_from_text, build_consent_body
from conn4_utils import setup_logging, run_shell_cmd, SocksProxyManager
from html_form_parser import FormParser
from schema_utils import normalize_perf_logs, build_schema
from conn4_auth_lib import PhpSerializer, WbsTokenBuilder

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("❌ Selenium не установлен!")
    print("Установите: pip3 install selenium webdriver-manager")
    sys.exit(1)

# Проверяем, что мы в WSL
is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
if not is_wsl:
    print("❌ Этот скрипт должен запускаться только в WSL!")
    sys.exit(1)

class Conn4PortalTester:
    """Запускает Chrome через SOCKS, воспроизводит flow conn4.com и сохраняет подробные артефакты."""

    def __init__(self, ssh_host=None, ssh_user=None):
        self.driver = None
        self.portal_frame_index = None
        self.pre_click_url = None
        self.pre_click_tokens = {}

        # Настройка логирования
        self.logger = setup_logging(__name__, "conn4_selenium_debug.log")

        self.socks_manager = SocksProxyManager(self.logger, ssh_host, ssh_user)
        self.ssh_host = self.socks_manager.ssh_host
        self.ssh_user = self.socks_manager.ssh_user
        self.cookie_decoded_ip = None
        self.cookie_decoded_mac = None
        self.cookie_decoded_site_id = None

    def check_environment(self):
        """Быстрая проверка доступности роутера и SOCKS-прокси до запуска браузера."""
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

    def _switch_to_portal_frame(self):
        """Находит iframe с формой/чекбоксами/кнопкой Wi-Fi и запоминает его индекс."""
        try:
            self.driver.switch_to.default_content()
            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            for idx, frame in enumerate(frames):
                try:
                    self.driver.switch_to.frame(frame)
                    candidates = [
                        "//button[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free wi-fi')]",
                        "//*[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free wi-fi')]",
                        "//input[@type='checkbox']",
                        "//*[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'wi-fi access')]",
                    ]
                    for xpath in candidates:
                        found = self.driver.find_elements(By.XPATH, xpath)
                        if found:
                            self.portal_frame_index = idx
                            return True
                except Exception:
                    pass
                finally:
                    self.driver.switch_to.default_content()
            return False
        except Exception:
            return False
    
    def _first_hop(self, dest_ip):
        return None
    
    def _ssh_ping_via_router(self, dest_ip):
        """Пробует пропинговать dest_ip через один или несколько роутеров по SSH."""
        try:
            targets = [f"{self.ssh_user}@{self.ssh_host}"]
            if self.ssh_host != "dev-openwrt":
                targets.append(f"{self.ssh_user}@dev-openwrt")
            ssh_opts = ['-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=5', '-o', 'PreferredAuthentications=publickey,password', '-o', 'BatchMode=yes']
            for target in targets:
                cmd = ['ssh'] + ssh_opts + [target, f'ping -c 1 -W 3 {dest_ip}']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return True
                try:
                    which = subprocess.run(['which', 'sshpass'], capture_output=True, text=True)
                    sshpass_path = which.stdout.strip()
                    ssh_pass = os.environ.get("OPENWRT_SSH_PASS")
                    if sshpass_path and ssh_pass:
                        cmd = [sshpass_path, '-p', ssh_pass, 'ssh'] + ssh_opts + [target, f'ping -c 1 -W 3 {dest_ip}']
                        result2 = subprocess.run(cmd, capture_output=True, text=True)
                        if result2.returncode == 0:
                            return True
                except Exception:
                    pass
            return False
        except Exception:
            return False
    

    def setup_chrome_driver(self):
        """Настройка Chrome WebDriver"""
        self.logger.info("Настройка Chrome WebDriver...")

        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            try:
                lang_pref = os.environ.get("SELENIUM_ACCEPT_LANGUAGE_PREF") or os.environ.get("SELENIUM_ACCEPT_LANGUAGE") or "en-US,en"
                options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2, "intl.accept_languages": lang_pref})
                self.logger.info(f"Отключена загрузка изображений через Chrome prefs")
                self.logger.info(f"Язык браузера: {lang_pref}")
            except Exception:
                pass
            
            # Настройка прокси
            socks_port = os.environ.get("NOJS_SOCKS_PORT") or "10800"
            options.add_argument(f"--proxy-server=socks5://127.0.0.1:{socks_port}")
            self.logger.info(f"Настройка Chrome через SOCKS прокси: 127.0.0.1:{socks_port}")

            # НЕ отключаем JavaScript - он нужен для conn4.com

            # Многоуровневый запуск chromedriver
            def _try_driver(service):
                try:
                    return webdriver.Chrome(service=service, options=options)
                except Exception as e:
                    self.logger.debug(f"Driver start failed: {e}")
                    return None
            drv = None
            # 1) Локальный chromedriver
            try:
                drv_path = os.environ.get("CHROMEDRIVER_PATH") or "/usr/bin/chromedriver"
                if os.path.exists(drv_path):
                    self.logger.info(f"Используем локальный chromedriver: {drv_path}")
                    drv = _try_driver(Service(drv_path))
            except Exception:
                drv = None
            # 2) Selenium Manager
            if drv is None:
                try:
                    self.logger.info("Пробуем запуск через Selenium Manager")
                    drv = _try_driver(Service())
                except Exception:
                    drv = None
            # 3) webdriver-manager
            if drv is None:
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    self.logger.info("Фоллбек на webdriver-manager (может требоваться интернет)")
                    drv = _try_driver(Service(ChromeDriverManager().install()))
                except Exception:
                    drv = None
            if drv is None:
                raise RuntimeError("Не удалось запустить ChromeDriver")
            self.driver = drv
            self.driver.set_page_load_timeout(30)

            self.logger.info("✅ Chrome WebDriver настроен")
            try:
                try:
                    hook_src = """
                    (function(){
                      try {
                        window.__storageEvents = window.__storageEvents || [];
                        const log = window.__storageEvents;
                        const origSetItem = Storage.prototype.setItem;
                        Storage.prototype.setItem = function(k,v){
                          try {
                            var st = (new Error()).stack;
                            var kind = this===window.sessionStorage ? "session" : "local";
                            log.push({type:"setItem", storage:kind, key:k, value:v, stack:st});
                          } catch(e){}
                          return origSetItem.apply(this, arguments);
                        };
                        const origGetItem = Storage.prototype.getItem;
                        Storage.prototype.getItem = function(k){
                          try {
                            var val = origGetItem.apply(this, arguments);
                            var kind = this===window.sessionStorage ? "session" : "local";
                            log.push({type:"getItem", storage:kind, key:k, value:val});
                            return val;
                          } catch(e){}
                          return origGetItem.apply(this, arguments);
                        };
                        const origParse = JSON.parse;
                        JSON.parse = function(s){
                          var obj = origParse.call(JSON, s);
                          try {
                            if (obj) {
                              var apiId = obj.apiSessionId || obj.sessionId || obj.api_session_id || null;
                              var token = obj.wbsApiAuthToken || obj.token || null;
                              if (apiId || token) {
                                log.push({type:"json", hasApiSession:!!apiId, apiSessionId:apiId, hasToken:!!token});
                              }
                            }
                          } catch(e){}
                          return obj;
                        };
                        if (typeof XMLHttpRequest !== "undefined" && XMLHttpRequest.prototype) {
                          const origXHROpen = XMLHttpRequest.prototype.open;
                          const origXHRSend = XMLHttpRequest.prototype.send;
                          XMLHttpRequest.prototype.open = function(method, url){
                            try {
                              this.__cpm_method = method;
                              this.__cpm_url = url;
                            } catch(e){}
                            return origXHROpen.apply(this, arguments);
                          };
                          XMLHttpRequest.prototype.send = function(body){
                            try {
                              var u = this.__cpm_url || "";
                              var m = this.__cpm_method || "";
                              if (u.indexOf("/wbs/api/v1/") !== -1) {
                                var st = (new Error()).stack;
                                var b = body;
                                try {
                                  if (b && typeof b !== "string") {
                                    b = String(b);
                                  }
                                } catch(e){}
                                var parsed = {};
                                try {
                                  if (b && typeof b === "string") {
                                    var parts = b.split("&");
                                    for (var i = 0; i < parts.length; i++) {
                                      var p = parts[i];
                                      if (!p) continue;
                                      var kv = p.split("=");
                                      var key = kv[0] ? decodeURIComponent(kv[0]) : "";
                                      var val = kv.length > 1 ? decodeURIComponent(kv.slice(1).join("=")) : "";
                                      if (key) parsed[key] = val;
                                    }
                                  }
                                } catch(e){}
                                log.push({type:"xhr", url:u, method:m, body:b || null, parsed:parsed, stack:st});
                                try {
                                  if (u.indexOf("/wbs/api/v1/login/free/") !== -1) {
                                    var apiSess = null;
                                    var payerId = null;
                                    var retUrl = null;
                                    try {
                                      apiSess = window.sessionStorage ? window.sessionStorage.getItem("conn4-hotspot-storage-apiSessionId") : null;
                                    } catch(e){}
                                    try {
                                      payerId = window.sessionStorage ? window.sessionStorage.getItem("conn4-hotspot-storage-payerId") : null;
                                    } catch(e){}
                                    try {
                                      retUrl = window.sessionStorage ? window.sessionStorage.getItem("conn4-hotspot-storage-paymentReturnProxyUrl") : null;
                                    } catch(e){}
                                    var cookies = null;
                                    try {
                                      cookies = document.cookie;
                                    } catch(e){}
                                    log.push({
                                      type:"loginFreeSnapshot",
                                      url:u,
                                      method:m,
                                      body:b || null,
                                      parsed:parsed,
                                      apiSessionId:apiSess,
                                      payerId:payerId,
                                      paymentReturnProxyUrl:retUrl,
                                      cookies:cookies,
                                      stack:st
                                    });
                                  }
                                } catch(e){}
                              }
                            } catch(e){}
                            return origXHRSend.apply(this, arguments);
                          };
                        }
                        if (typeof window.fetch === "function") {
                          const origFetch = window.fetch;
                          window.fetch = function(resource, init){
                            var url = "";
                            try {
                              if (typeof resource === "string") {
                                url = resource;
                              } else if (resource && resource.url) {
                                url = resource.url;
                              }
                            } catch(e){}
                            var method = init && init.method ? init.method : "GET";
                            var body = init && init.body ? init.body : null;
                            try {
                              if (url.indexOf("/wbs/api/v1/") !== -1) {
                                var st = (new Error()).stack;
                                var b = body;
                                try {
                                  if (b && typeof b !== "string") {
                                    b = String(b);
                                  }
                                } catch(e){}
                                log.push({type:"fetch", url:url, method:method, body:b, stack:st});
                              }
                            } catch(e){}
                            return origFetch.apply(this, arguments);
                          };
                        }
                        window.__getStorageEvents = function(){
                          try {
                            return JSON.stringify(log);
                          } catch(e){
                            return "[]";
                          }
                        };
                      } catch(e){}
                    })();"""
                    self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': hook_src})
                except Exception:
                    pass
                self.driver.execute_cdp_cmd('Network.enable', {'maxTotalBufferSize': 10485760, 'maxResourceBufferSize': 10485760})
                try:
                    al = os.environ.get("SELENIUM_ACCEPT_LANGUAGE") or "en-US,en;q=0.9"
                    self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'Accept-Language': al}})
                    self.logger.info(f"Accept-Language: {al}")
                    # blocked = [
                    #     "*.png","*.jpg","*.jpeg","*.webp","*.svg","*.gif","*.ico","*.bmp","*.css",
                    #     "*.woff","*.woff2","*.ttf","*.otf","*.eot",
                    #     "data:image/*"
                    # ]
                    # self.driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': blocked})
                    # self.logger.info(f"Блокируем статические ресурсы: {len(blocked)} шаблонов")
                    self.logger.info("Загрузка всех ресурсов разрешена (включая файлы с хешами в именах)")
                except Exception:
                    pass
            except Exception:
                pass
            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка настройки Chrome: {e}")
            return False
        
    def _apply_block_redirect_policy(self, portal_url=None):
        """Блокирует внешние редиректы (по умолчанию leonardo-hotels.com), чтобы остаться на портале."""
        try:
            hosts_env = os.environ.get("CPM_BLOCK_REDIRECT_HOSTS") or ""
            if hosts_env.strip():
                items = [s.strip() for s in hosts_env.split(",") if s.strip()]
            else:
                items = ["leonardo-hotels.com", "www.leonardo-hotels.com"]
            if items:
                try:
                    self.driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': items})
                    self.logger.info(f"Блокируем редиректы: {len(items)} хостов")
                except Exception:
                    pass
        except Exception:
            pass
    
    def test_conn4_portal(self):
        """Тестирование conn4.com портала"""
        portal_url = None

        self.logger.info(f"Переход на conn4.com портал...")
        self.logger.info(f"URL: {portal_url or '(auto-detect via msftconnecttest)'}")

        try:
            try:
                target_url = "http://www.msftconnecttest.com/redirect"
                self.logger.info(f"Эмуляция входа: переход на {target_url} ...")
                self.driver.get(target_url)
                time.sleep(5)
                current = self.driver.current_url
                try:
                    dom_lang = self.driver.execute_script("return document.documentElement.getAttribute('lang') || ''")
                except Exception:
                    dom_lang = ""
                try:
                    dom_locale = self.driver.execute_script("return (document.body && document.body.getAttribute('data-locale')) || ''")
                except Exception:
                    dom_locale = ""
                self.logger.info(f"DOM lang={dom_lang} data-locale={dom_locale}")
                self.logger.info(f"URL после {target_url}: {current}")
                if "conn4.com" in (current or "").lower():
                    portal_url = current
            except Exception:
                pass
            
            if not portal_url:
                cu = (current or "").lower()
                if cu and ("conn4.com" not in cu) and (cu.startswith("http")):
                    self.logger.info("Авторизация уже пройдена: редирект не ведёт на портал")
                    try:
                        self.driver.save_screenshot("already_authorized.png")
                    except Exception:
                        pass
                    return True
                self.logger.warning("Не удалось автоматически обнаружить портал через редирект")
                return False
            
            try:
                do_block = (os.environ.get("CPM_BLOCK_EXTERNAL") or "1").strip() == "1"
            except Exception:
                do_block = True
            if do_block:
                try:
                    self._apply_block_redirect_policy(portal_url)
                except Exception:
                    pass

            # Динамическая готовность без фиксированных пауз
            self.logger.info("Ожидание готовности страницы (динамически)...")
            try:
                WebDriverWait(self.driver, 1).until(
                    lambda d: (
                        len(d.find_elements(By.XPATH, "//*[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free wi-fi')]")) > 0
                        or len(d.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")) > 0
                        or (d.execute_script("return (window.performance && window.performance.getEntriesByType) ? window.performance.getEntriesByType('resource').filter(e => e.initiatorType==='script').length : 0") or 0) > 10
                        or (d.execute_script("return (window.__capturedRequests || []).length") or 0) > 3
                    )
                )
            except TimeoutException:
                self.logger.info("Таймаут ожидания динамической готовности, продолжаем с текущим состоянием")
            # Логируем список скриптов, загруженных ресурсами
            try:
                perfScripts = self.driver.execute_script("return (window.performance && window.performance.getEntriesByType) ? window.performance.getEntriesByType('resource') : []")
                try:
                    perfScripts = sorted(perfScripts or [], key=lambda e: e.get('startTime') or 0)
                except Exception:
                    pass
                names = []
                for e in perfScripts or []:
                    if e.get('initiatorType') == 'script':
                        names.append(e.get('name'))
                if names:
                    self.logger.info(f"Загружено скриптов: {len(names)}")
                    for n in names[:25]:
                        self.logger.info(f"  script: {n}")
            except Exception:
                pass
            try:
                self.debug_checkpoint("ready")
            except Exception:
                pass

            try:
                pass
            except Exception:
                pass

            # Принудительно выполняем JavaScript для инициализации страницы
            try:
                self.driver.execute_script("if (typeof initPage === 'function') { initPage(); }")
                self.driver.execute_script("if (typeof loadContent === 'function') { loadContent(); }")
                self.driver.execute_script("document.dispatchEvent(new Event('DOMContentLoaded'));")
            except Exception as e:
                self.logger.debug(f"Ошибка выполнения JavaScript: {e}")

            try:
                self._switch_to_portal_frame()
                if self.portal_frame_index is not None:
                    self.logger.info(f"Переключение в iframe индекса {self.portal_frame_index}")
                    frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                    if self.portal_frame_index < len(frames):
                        self.driver.switch_to.frame(frames[self.portal_frame_index])
            except Exception:
                pass

            current_url = self.driver.current_url
            page_title = self.driver.title

            self.logger.info(f"Текущий URL: {current_url}")
            self.logger.info(f"Заголовок: {page_title}")

            # Сохраняем скриншот
            self.driver.save_screenshot("conn4_portal_page.png")
            self.logger.info("Скриншот сохранен: conn4_portal_page.png")

            # Анализируем страницу
            self.analyze_page()
            try:
                ev = self.driver.execute_script("try { return window.__getStorageEvents ? window.__getStorageEvents() : '[]'; } catch(e) { return '[]'; }") or "[]"
                try:
                    with open("conn4_session_storage_trace.json","w",encoding="utf-8") as f:
                        f.write(ev)
                    self.logger.info("Трасса sessionStorage сохранена: conn4_session_storage_trace.json")
                except Exception:
                    pass
            except Exception:
                pass
            try:
                cb = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            except Exception:
                cb = []
            try:
                btns = self.driver.find_elements(By.TAG_NAME, "button")
            except Exception:
                btns = []
            try:
                subm = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
            except Exception:
                subm = []
            try:
                binp = self.driver.find_elements(By.CSS_SELECTOR, "input[type='button']")
            except Exception:
                binp = []
            all_buttons = btns + subm + binp
            try:
                forms = self.driver.find_elements(By.TAG_NAME, "form")
            except Exception:
                forms = []
            self.logger.info(f"Проверка портала: чекбоксов={len(cb)} кнопок={len(all_buttons)} форм={len(forms)}")
            if len(cb) == 0 or len(all_buttons) == 0 or len(forms) == 0:
                self.logger.error("❌ Портал не открыт: нет формы с галкой и кнопкой")
                return False
            self.dump_cookies_and_storage(label="before-auth")
            try:
                self.save_debug_artifact("conn4_debug_before_auth.json")
            except Exception:
                pass
            try:
                self.driver.execute_script("""
                window.__capturedRequests = [];
                window.__traceLog = [];
                window.__formSubmits = [];
                function __tracePush(type, detail){
                  try {
                    window.__traceLog.push({type:type, detail:detail, ts: Date.now()});
                  } catch(e){}
                }
                __tracePush('inject', 'start');
                document.addEventListener('DOMContentLoaded', function(){ __tracePush('dom', 'DOMContentLoaded'); });
                window.addEventListener('load', function(){ __tracePush('dom', 'load'); });
                (function(){
                  try {
                    var origFetch = window.fetch;
                    if (origFetch) {
                      window.fetch = function(){
                        try { 
                          var u = arguments[0];
                          var st = null; try { st = (new Error()).stack; } catch(e){}
                          window.__capturedRequests.push({kind:'fetch', url:u, stack: st}); 
                        } catch(e){}
                        __tracePush('fetch', arguments[0]);
                        return origFetch.apply(this, arguments);
                      };
                    }
                  } catch(e){}
                  try {
                    var origOpen = XMLHttpRequest.prototype.open;
                    XMLHttpRequest.prototype.open = function(method, url){
                      try { 
                        var st = null; try { st = (new Error()).stack; } catch(e){}
                        window.__capturedRequests.push({kind:'xhr', url:url, stack: st}); 
                      } catch(e){}
                      __tracePush('xhr', method+':'+url);
                      return origOpen.apply(this, arguments);
                    };
                  } catch(e){}
                  try {
                    var origSubmit = HTMLFormElement.prototype.submit;
                    HTMLFormElement.prototype.submit = function(){
                      try {
                        var fd = new FormData(this);
                        var o = {action: (this.action || ''), method: ((this.method || 'GET')+'').toUpperCase(), fields: []};
                        fd.forEach(function(v,k){ try { o.fields.push({name:k, value: v}); } catch(e){} });
                        try { window.__formSubmits.push(o); } catch(e){}
                        __tracePush('form.submit', o.action || '');
                      } catch(e){}
                      return origSubmit.apply(this, arguments);
                    };
                    try {
                      var forms = document.getElementsByTagName('form');
                      for (var i=0;i<forms.length;i++){
                        try {
                          forms[i].addEventListener('submit', function(ev){
                            try {
                              var fd = new FormData(this);
                              var o = {action: (this.action || ''), method: ((this.method || 'GET')+'').toUpperCase(), fields: []};
                              fd.forEach(function(v,k){ try { o.fields.push({name:k, value: v}); } catch(e){} });
                              try { window.__formSubmits.push(o); } catch(e){}
                              __tracePush('form.event', o.action || '');
                            } catch(e){}
                          }, true);
                        } catch(e){}
                      }
                    } catch(e){}
                  } catch(e){}
                  try {
                    var origNow = Date.now;
                    Date.now = function(){
                      var v = origNow.call(Date);
                      __tracePush('date.now', v);
                      return v;
                    };
                  } catch(e){}
                  try {
                    var pnow = (window.performance && window.performance.now) ? window.performance.now.bind(window.performance) : null;
                    if (pnow) {
                      window.performance.now = function(){
                        var v = pnow();
                        __tracePush('perf.now', v);
                        return v;
                      }
                    }
                  } catch(e){}
                  try {
                    if (typeof initPage === 'function') {
                      var origInit = initPage;
                      initPage = function(){
                        __tracePush('func', 'initPage');
                        return origInit.apply(this, arguments);
                      }
                    }
                  } catch(e){}
                  try {
                    if (typeof loadContent === 'function') {
                      var origLoad = loadContent;
                      loadContent = function(){
                        __tracePush('func', 'loadContent');
                        return origLoad.apply(this, arguments);
                      }
                    }
                  } catch(e){}
                })();
                """)
                self.logger.info("Инжект перехвата fetch/XHR выполнен")
            except Exception:
                pass
            try:
                self.save_debug_artifact("conn4_debug_after_inject.json")
            except Exception:
                pass
            try:
                self._nojs_compute_and_compare()
            except Exception:
                pass
            # Инжект в каждый iframe
            try:
                self.driver.switch_to.default_content()
                frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                for fr in frames:
                    try:
                        self.driver.switch_to.frame(fr)
                        self.driver.execute_script("""
                        try {
                          window.__capturedRequests = window.__capturedRequests || [];
                          window.__traceLog = window.__traceLog || [];
                          window.__formSubmits = window.__formSubmits || [];
                          function __tracePush(type, detail){
                            try { window.__traceLog.push({type:type, detail:detail, ts: Date.now()}); } catch(e){}
                          }
                          (function(){
                            try {
                              var origFetch = window.fetch;
                              if (origFetch) {
                                window.fetch = function(){
                                  try { window.__capturedRequests.push(arguments[0]); } catch(e){}
                                  __tracePush('fetch', arguments[0]);
                                  return origFetch.apply(this, arguments);
                                };
                              }
                            } catch(e){}
                            try {
                              var origOpen = XMLHttpRequest.prototype.open;
                              XMLHttpRequest.prototype.open = function(method, url){
                                try { window.__capturedRequests.push(url); } catch(e){}
                                __tracePush('xhr', method+':'+url);
                                return origOpen.apply(this, arguments);
                              };
                            } catch(e){}
                            try {
                              var origSubmit = HTMLFormElement.prototype.submit;
                              HTMLFormElement.prototype.submit = function(){
                                try {
                                  var fd = new FormData(this);
                                  var o = {action: (this.action || ''), method: ((this.method || 'GET')+'').toUpperCase(), fields: []};
                                  fd.forEach(function(v,k){ try { o.fields.push({name:k, value: v}); } catch(e){} });
                                  try { window.__formSubmits.push(o); } catch(e){}
                                  __tracePush('form.submit', o.action || '');
                                } catch(e){}
                                return origSubmit.apply(this, arguments);
                              };
                              try {
                                var forms = document.getElementsByTagName('form');
                                for (var i=0;i<forms.length;i++){
                                  try {
                                    forms[i].addEventListener('submit', function(ev){
                                      try {
                                        var fd = new FormData(this);
                                        var o = {action: (this.action || ''), method: ((this.method || 'GET')+'').toUpperCase(), fields: []};
                                        fd.forEach(function(v,k){ try { o.fields.push({name:k, value: v}); } catch(e){} });
                                        try { window.__formSubmits.push(o); } catch(e){}
                                        __tracePush('form.event', o.action || '');
                                      } catch(e){}
                                    }, true);
                                  } catch(e){}
                                }
                              } catch(e){}
                            } catch(e){}
                          })();
                        """)
                    except Exception:
                        pass
                    finally:
                        self.driver.switch_to.default_content()
                self.logger.info("Инжект перехвата в iframe выполнен")
            except Exception:
                pass
            def _log_conn4_requests(urls, label=""):
                try:
                    items = [u for u in (urls or []) if isinstance(u, str) and ("conn4.com" in u)]
                    if items:
                        self.logger.info(f"[conn4.com requests{(' ' + label) if label else ''}] {len(items)}")
                        for u in items:
                            self.logger.info(f"  {u}")
                            try:
                                p = urlparse(u)
                                qs = parse_qs(p.query)
                                keys = ["client_ip","client_mac","site_id","signature","loggedin","remembered_mac"]
                                vals = {k:(qs.get(k,[None])[0]) for k in keys}
                                self.logger.info(f"    params: {json.dumps(vals, ensure_ascii=False)}")
                            except Exception:
                                pass
                except Exception:
                    pass
            try:
                pass
            except Exception:
                pass

            # Пробуем авторизацию
            return self.try_authentication()

        except Exception as e:
            self.logger.error(f"❌ Ошибка доступа к порталу: {e}")
            return False

    def analyze_page(self):
        """Анализ страницы портала"""
        self.logger.info("=== АНАЛИЗ СТРАНИЦЫ ПОРТАЛА ===")

        try:
            # Ждем дополнительно для загрузки динамического контента
            time.sleep(5)

            # Ищем ВСЕ элементы input
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            self.logger.info(f"Найдено всех input элементов: {len(all_inputs)}")

            for i, inp in enumerate(all_inputs):
                inp_type = inp.get_attribute("type") or "text"
                inp_name = inp.get_attribute("name") or ""
                inp_value = inp.get_attribute("value") or ""
                inp_id = inp.get_attribute("id") or ""
                inp_class = inp.get_attribute("class") or ""
                is_visible = inp.is_displayed()
                self.logger.info(f"  Input {i+1}: type='{inp_type}' name='{inp_name}' id='{inp_id}' class='{inp_class}' value='{inp_value}' visible={is_visible}")

            # Ищем ВСЕ кнопки
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            submit_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
            button_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='button']")

            all_buttons = buttons + submit_inputs + button_inputs
            self.logger.info(f"Найдено всех кнопок: {len(all_buttons)}")

            for i, btn in enumerate(all_buttons):
                text = btn.text.strip() or btn.get_attribute("value") or ""
                btn_type = btn.get_attribute("type") or ""
                btn_id = btn.get_attribute("id") or ""
                btn_class = btn.get_attribute("class") or ""
                onclick = btn.get_attribute("onclick") or ""
                is_visible = btn.is_displayed()
                is_enabled = btn.is_enabled()
                self.logger.info(f"  Кнопка {i+1}: text='{text}' type='{btn_type}' id='{btn_id}' class='{btn_class}' visible={is_visible} enabled={is_enabled}")
                if onclick:
                    self.logger.info(f"    onclick: {onclick}")

            # Ищем чекбоксы отдельно
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            self.logger.info(f"Найдено чекбоксов: {len(checkboxes)}")

            for i, checkbox in enumerate(checkboxes):
                name = checkbox.get_attribute("name") or ""
                checkbox_id = checkbox.get_attribute("id") or ""
                is_checked = checkbox.is_selected()
                is_visible = checkbox.is_displayed()
                self.logger.info(f"  Чекбокс {i+1}: name='{name}' id='{checkbox_id}' checked={is_checked} visible={is_visible}")

            # Ищем элементы с текстом "Get Free WiFi"
            wifi_elements = []
            try:
                wifi_elements = self.driver.find_elements(By.XPATH, "//*[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free wi-fi')]")
            except Exception:
                pass
            self.logger.info(f"Найдено элементов с 'Get Free WiFi': {len(wifi_elements)}")

            for i, elem in enumerate(wifi_elements):
                tag = elem.tag_name
                text = elem.text.strip()
                elem_id = elem.get_attribute("id") or ""
                elem_class = elem.get_attribute("class") or ""
                is_visible = elem.is_displayed()
                is_enabled = elem.is_enabled() if hasattr(elem, 'is_enabled') else True
                self.logger.info(f"  WiFi элемент {i+1}: <{tag}> text='{text}' id='{elem_id}' class='{elem_class}' visible={is_visible} enabled={is_enabled}")

            # Ищем формы
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            self.logger.info(f"Найдено форм: {len(forms)}")

            for i, form in enumerate(forms):
                action = form.get_attribute("action") or ""
                method = form.get_attribute("method") or "GET"
                form_id = form.get_attribute("id") or ""
                self.logger.info(f"  Форма {i+1}: {method} {action} id='{form_id}'")

            # Выводим часть HTML для отладки
            page_source = self.driver.page_source
            self.logger.info(f"Размер HTML: {len(page_source)} символов")

            # Ищем ключевые слова в HTML
            keywords = ['get free wifi', 'get free wi-fi', 'checkbox', 'connect', 'continue', 'accept', 'agree', 'submit', 'button', 'input', 'wi-fi access', 'free wi-fi']
            for keyword in keywords:
                count = page_source.lower().count(keyword)
                if count > 0:
                    self.logger.info(f"  Найдено '{keyword}': {count} раз в HTML")
            
            try:
                self._log_external_lib_refs(page_source or "")
            except Exception:
                pass
            try:
                scripts = self.driver.find_elements(By.TAG_NAME, "script")
            except Exception:
                scripts = []
            self.logger.info(f"Найдено script тегов: {len(scripts)}")
            for i, sc in enumerate(scripts):
                try:
                    src = sc.get_attribute("src") or ""
                    if src:
                        self.logger.info(f"  script {i+1} src: {src}")
                        try:
                            self._log_external_lib_refs(src)
                        except Exception:
                            pass
                    else:
                        try:
                            txt = sc.get_attribute("innerHTML") or ""
                        except Exception:
                            txt = ""
                        if txt and len(txt) > 10:
                            self.logger.info(f"  script {i+1} inline length: {len(txt)}")
                            try:
                                self._log_external_lib_refs(txt)
                            except Exception:
                                pass
                except Exception:
                    pass
            try:
                self._enumerate_assets_and_large_js_scan()
            except Exception:
                pass
            try:
                captured = self.driver.execute_script("return window.__capturedRequests || []")
            except Exception:
                captured = []
            if captured:
                self.logger.info(f"[Captured requests] {len(captured)}")
                for u in captured:
                    self.logger.info(f"  {u}")
                    try:
                        self._log_external_lib_refs(str(u))
                    except Exception:
                        pass

        except Exception as e:
            self.logger.error(f"Ошибка анализа страницы: {e}")
    
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
    
    def dump_cookies_and_storage(self, label=""):
        try:
            cookies = self.driver.get_cookies()
            self.logger.info(f"[COOKIES{(' ' + label) if label else ''}] всего: {len(cookies)}")
            for c in cookies:
                try:
                    self.logger.info(f"  cookie: {json.dumps(c, ensure_ascii=False)}")
                except Exception:
                    self.logger.info(f"  cookie: {c}")
            try:
                doc_cookie = self.driver.execute_script("return document.cookie || ''")
            except Exception:
                doc_cookie = ""
            self.logger.info(f"[document.cookie{(' ' + label) if label else ''}] {doc_cookie}")
            # localStorage
            try:
                ls_len = self.driver.execute_script("return window.localStorage ? window.localStorage.length : 0")
                self.logger.info(f"[localStorage{(' ' + label) if label else ''}] length={ls_len}")
                for i in range(int(ls_len or 0)):
                    try:
                        key = self.driver.execute_script("return window.localStorage.key(arguments[0])", i)
                        val = self.driver.execute_script("return window.localStorage.getItem(arguments[0])", key)
                        self.logger.info(f"  ls[{i}]: {key}={val}")
                    except Exception:
                        pass
            except Exception:
                pass
            # sessionStorage
            try:
                ss_len = self.driver.execute_script("return window.sessionStorage ? window.sessionStorage.length : 0")
                self.logger.info(f"[sessionStorage{(' ' + label) if label else ''}] length={ss_len}")
                for i in range(int(ss_len or 0)):
                    try:
                        key = self.driver.execute_script("return window.sessionStorage.key(arguments[0])", i)
                        val = self.driver.execute_script("return window.sessionStorage.getItem(arguments[0])", key)
                        self.logger.info(f"  ss[{i}]: {key}={val}")
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception as e:
            self.logger.info(f"Ошибка дампа cookies/storage: {e}")

    def debug_checkpoint(self, label=""):
        try:
            data = {}
            try:
                data["label"] = label
            except Exception:
                pass
            try:
                data["current_url"] = self.driver.current_url
            except Exception:
                data["current_url"] = None
            try:
                data["cookies"] = self.driver.get_cookies() or []
            except Exception:
                data["cookies"] = []
            try:
                html = self.driver.page_source or ""
            except Exception:
                html = ""
            try:
                toks = self._nojs_collect_tokens(html) or {}
            except Exception:
                toks = {}
            try:
                data["computedTokens"] = toks
            except Exception:
                pass
            try:
                if self.pre_click_tokens:
                    data["pre_click_tokens"] = self.pre_click_tokens
            except Exception:
                pass
            try:
                with open(f"conn4_debug_checkpoint_{label}.json","w",encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Отладочный чекпоинт сохранён: conn4_debug_checkpoint_{label}.json")
            except Exception:
                pass
            try:
                self.dump_js_bodies(label=label)
            except Exception:
                pass
        except Exception:
            pass

    def try_authentication(self):
        """Попытка авторизации"""
        self.logger.info("=== ПОПЫТКА АВТОРИЗАЦИИ ===")

        try:
            # Сначала ищем и отмечаем чекбоксы (галки)
            try:
                self._switch_to_portal_frame()
                if self.portal_frame_index is not None:
                    frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                    if self.portal_frame_index < len(frames):
                        self.driver.switch_to.frame(frames[self.portal_frame_index])
            except Exception:
                pass

            container = None
            try:
                container = self.driver.find_element(By.ID, "wbs-tpl-registration-free-container")
            except Exception:
                try:
                    container = self.driver.find_element(By.CSS_SELECTOR, ".free-login.js-site-box")
                except Exception:
                    pass

            checkboxes = []
            if container:
                try:
                    checkboxes = container.find_elements(By.CSS_SELECTOR, "input[type='checkbox'], input[type='CHECKBOX']")
                except Exception:
                    pass

            if not checkboxes:
                labels_xpath = "//label[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'terms and conditions') or contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'terms')]"
                labels = []
                try:
                    labels = (container.find_elements(By.XPATH, labels_xpath) if container
                              else self.driver.find_elements(By.XPATH, labels_xpath))
                except Exception:
                    labels = []
                for label in labels:
                    for_attr = label.get_attribute("for")
                    if for_attr:
                        linked = self.driver.find_elements(By.ID, for_attr)
                        checkboxes.extend(linked)
                    else:
                        try:
                            nested = label.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                            checkboxes.extend(nested)
                        except Exception:
                            pass

            for i, checkbox in enumerate(checkboxes):
                try:
                    if not checkbox.is_selected():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                        try:
                            checkbox.click()
                            self.logger.info(f"✅ Чекбокс {i+1} отмечен")
                        except Exception:
                            try:
                                self.driver.execute_script("arguments[0].click();", checkbox)
                                self.logger.info(f"✅ Чекбокс {i+1} отмечен через JavaScript")
                            except Exception:
                                try:
                                    self.driver.execute_script("arguments[0].checked = true; arguments[0].dispatchEvent(new Event('change'));", checkbox)
                                    self.logger.info(f"✅ Чекбокс {i+1} установлен программно")
                                except Exception:
                                    pass
                except Exception:
                    pass

            checked_any = any(cb.is_selected() for cb in checkboxes) if checkboxes else False
            if not checked_any:
                try:
                    label_to_click = None
                    labels_xpath2 = "//label[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'terms and conditions')]"
                    label_to_click = (container.find_element(By.XPATH, labels_xpath2) if container
                                      else self.driver.find_element(By.XPATH, labels_xpath2))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label_to_click)
                    label_to_click.click()
                except Exception:
                    pass

            # Небольшая пауза после отметки чекбоксов
            time.sleep(2)

            # Теперь ищем кнопки для подключения
            connect_selectors = [
                # Поиск по конкретному тексту "Get Free WiFi"
                "//button[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free wi-fi')]",
                "//input[@value][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free wi-fi')]",
                "//*[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free wi-fi')]",

                # Поиск по тексту кнопки (общие варианты)
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free wifi')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",

                # Поиск по типу
                "//input[@type='submit']",
                "//button[@type='submit']",
                "//button[@type='button']",

                # Поиск по классам (часто используемые в conn4)
                "//button[contains(@class, 'btn')]",
                "//button[contains(@class, 'button')]",
                "//input[contains(@class, 'btn')]",

                # Поиск любых кликабельных элементов
                "//*[@onclick]",

                # Поиск по ID (если есть стандартные)
                "//button[@id]",
                "//input[@id and @type='submit']"
            ]

            for selector in connect_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            text = element.text.strip() or element.get_attribute("value") or element.get_attribute("id") or "Безымянная кнопка"
                            self.logger.info(f"Найдена кнопка: '{text}' ({selector})")

                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                try:
                                    self.pre_click_url = self.driver.current_url
                                except Exception:
                                    self.pre_click_url = None
                                
                                # Собираем токены перед кликом, пока доступны sessionStorage и cookies текущего домена
                                try:
                                    self.logger.info("Сбор токенов перед кликом...")
                                    self.dump_cookies_and_storage(label="pre-click")
                                    self.pre_click_tokens = self._nojs_collect_tokens(self.driver.page_source)
                                    self.logger.info(f"Собрано токенов: {len(self.pre_click_tokens)}")
                                    if self.pre_click_tokens.get("apiSessionId"):
                                        self.logger.info(f"  apiSessionId: {self.pre_click_tokens.get('apiSessionId')}")
                                    try:
                                        self.debug_checkpoint("preclick")
                                    except Exception:
                                        pass
                                except Exception as e:
                                    self.logger.error(f"Ошибка сбора токенов перед кликом: {e}")

                                try:
                                    WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable(element))
                                except Exception:
                                    pass
                                try:
                                    element.click()
                                except Exception:
                                    try:
                                        self.driver.execute_script("arguments[0].click();", element)
                                    except Exception as e:
                                        self.logger.warning(f"Ошибка клика по кнопке '{text}': {e}")
                                        try:
                                            self.driver.execute_script("arguments[0].classList.remove('disabled'); arguments[0].removeAttribute('disabled'); arguments[0].click();", element)
                                        except Exception:
                                            pass
                                self.logger.info(f"✅ Кнопка '{text}' нажата")

                                # Короткий опрос перехваченных запросов до редиректа
                                try:
                                    time.sleep(2)
                                    captured_mid = self.driver.execute_script("return window.__capturedRequests || []")
                                    if captured_mid:
                                        self.logger.info(f"[Captured requests mid] {len(captured_mid)}")
                                        for u in captured_mid:
                                            self.logger.info(f"  {u}")
                                        try:
                                            _log_conn4_requests(captured_mid, label=" mid")
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                time.sleep(8)

                                # Проверяем результат
                                new_url = self.driver.current_url
                                self.logger.info(f"Новый URL после клика: {new_url}")

                                # Сохраняем скриншот результата
                                self.driver.save_screenshot("conn4_after_click.png")
                                self.logger.info("Скриншот после клика: conn4_after_click.png")

                                # Проверяем успех
                                try:
                                    nu = urlparse(new_url or "")
                                    if nu.netloc and ("conn4.com" not in nu.netloc.lower()):
                                        try:
                                            self.driver.execute_cdp_cmd('Page.stopLoading', {})
                                        except Exception:
                                            pass
                                        try:
                                            self.driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': ['*']})
                                        except Exception:
                                            pass
                                        try:
                                            self.driver.execute_script("try { window.stop(); } catch(e){}")
                                        except Exception:
                                            pass
                                        try:
                                            self.dump_cookies_and_storage(label="after-auth")
                                        except Exception:
                                            pass
                                        return True
                                except Exception:
                                    pass
                                if self.check_success():
                                    # Немедленно останавливаем дальнейшие загрузки после подтверждения редиректа
                                    try:
                                        self.driver.execute_cdp_cmd('Page.stopLoading', {})
                                    except Exception:
                                        pass
                                    try:
                                        self.driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': ['*']})
                                    except Exception:
                                        pass
                                    try:
                                        self.driver.execute_script("try { window.stop(); } catch(e){}")
                                    except Exception:
                                        pass
                                    try:
                                        self.dump_cookies_and_storage(label="after-auth")
                                        try:
                                            captured = self.driver.execute_script("return window.__capturedRequests || []")
                                            if captured:
                                                self.logger.info(f"[Captured requests] {len(captured)}")
                                                for u in captured:
                                                    self.logger.info(f"  {u}")
                                                try:
                                                    _log_conn4_requests(captured, label=" end")
                                                except Exception:
                                                    pass
                                                try:
                                                    c_time = [u for u in captured if '/_time' in (u or '')]
                                                    if c_time:
                                                        self.logger.info(f"[Captured _time] {len(c_time)}")
                                                        for u in c_time:
                                                            self.logger.info(f"  {u}")
                                                except Exception:
                                                    pass
                                            trace = self.driver.execute_script("return window.__traceLog || []")
                                            if trace:
                                                self.logger.info(f"[Trace sequence] {len(trace)} events")
                                                for t in trace:
                                                    self.logger.info(f"  {t}")
                                            try:
                                                perfScripts = self.driver.execute_script("return (window.performance && window.performance.getEntriesByType) ? window.performance.getEntriesByType('resource') : []")
                                                count = 0
                                                try:
                                                    perfScripts = sorted(perfScripts or [], key=lambda e: e.get('startTime') or 0)
                                                except Exception:
                                                    pass
                                                for e in perfScripts or []:
                                                    if e.get('initiatorType') in ('script','xmlhttprequest','fetch'):
                                                        self.logger.info(f"[Perf] {e.get('initiatorType')} {e.get('name')} start={e.get('startTime')}")
                                                        count += 1
                                                if count:
                                                    self.logger.info(f"[Perf] total traced: {count}")
                                            except Exception:
                                                pass
                                            try:
                                                logs = []
                                                try:
                                                    logs = self.driver.get_log('performance') or []
                                                except Exception:
                                                    logs = []
                                                net = []
                                                for ent in logs:
                                                    try:
                                                        m = json.loads(ent.get('message') or '{}').get('message') or {}
                                                        if m.get('method') in ('Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished'):
                                                            net.append(m)
                                                    except Exception:
                                                        pass
                                                if net:
                                                    try:
                                                        detailed = []
                                                        for mm in net:
                                                            p = mm.get('params') or {}
                                                            rid = p.get('requestId')
                                                            item = {'event': mm.get('method')}
                                                            if rid is not None:
                                                                item['id'] = rid
                                                            ts = p.get('timestamp')
                                                            if ts is not None:
                                                                item['ts'] = ts
                                                            t = p.get('type')
                                                            if t is not None:
                                                                item['type'] = t
                                                            doc_url = p.get('documentURL')
                                                            if doc_url:
                                                                item['documentURL'] = doc_url
                                                            initiator = p.get('initiator')
                                                            if initiator:
                                                                item['initiator'] = initiator
                                                            req = p.get('request') or {}
                                                            if req:
                                                                item['request'] = {
                                                                    'url': req.get('url'),
                                                                    'method': req.get('method'),
                                                                    'headers': req.get('headers'),
                                                                    'postData': req.get('postData')
                                                                }
                                                            resp = p.get('response') or {}
                                                            if resp:
                                                                item['response'] = {
                                                                    'url': resp.get('url') or resp.get('urlFragment'),
                                                                    'status': resp.get('status'),
                                                                    'mimeType': resp.get('mimeType'),
                                                                    'headers': resp.get('headers'),
                                                                    'remoteIPAddress': resp.get('remoteIPAddress'),
                                                                    'remotePort': resp.get('remotePort'),
                                                                    'timing': resp.get('timing')
                                                                }
                                                            if mm.get('method') == 'Network.requestWillBeSentExtraInfo':
                                                                extra = {}
                                                                if p.get('headers') is not None:
                                                                    extra['requestHeaders'] = p.get('headers')
                                                                if p.get('associatedCookies') is not None:
                                                                    extra['associatedCookies'] = p.get('associatedCookies')
                                                                if p.get('headersText') is not None:
                                                                    extra['headersText'] = p.get('headersText')
                                                                if extra:
                                                                    item['extra'] = extra
                                                            if mm.get('method') == 'Network.responseReceivedExtraInfo':
                                                                extra = {}
                                                                if p.get('headers') is not None:
                                                                    extra['responseHeaders'] = p.get('headers')
                                                                if p.get('headersText') is not None:
                                                                    extra['headersText'] = p.get('headersText')
                                                                if p.get('blockedCookies') is not None:
                                                                    extra['blockedCookies'] = p.get('blockedCookies')
                                                                if p.get('cookies') is not None:
                                                                    extra['cookies'] = p.get('cookies')
                                                                if extra:
                                                                    item['extra'] = extra
                                                            if mm.get('method') == 'Network.loadingFinished':
                                                                edl = p.get('encodedDataLength')
                                                                if edl is not None:
                                                                    item['encodedDataLength'] = edl
                                                            detailed.append(item)
                                                        with open("conn4_network.json","w",encoding="utf-8") as f:
                                                            json.dump({'events': detailed}, f, ensure_ascii=False, indent=2)
                                                        self.logger.info("Артефакт сети сохранен: conn4_network.json")
                                                    except Exception:
                                                        pass
                                            except Exception:
                                                pass
                                        except Exception:
                                            pass
                                    except Exception:
                                        pass
                                    
                                    # Double check with SOCKS (with retry)
                                    for _ in range(3):
                                        if self.strict_check_portal_time_via_socks():
                                            return True
                                        self.logger.info("Waiting for internet access...")
                                        time.sleep(2)
                                    self.logger.warning("Авторизация вроде успешна (tokens), но SOCKS недоступен после повторов")
                                    return False

                            except Exception as e:
                                self.logger.warning(f"Ошибка клика по кнопке '{text}': {e}")
                                try:
                                    self.driver.execute_script("arguments[0].click();", element)
                                    time.sleep(5)
                                    if self.check_success():
                                        try:
                                            self.dump_cookies_and_storage(label="after-auth-js")
                                        except Exception:
                                            pass
                                        
                                        if self.strict_check_portal_time_via_socks():
                                            return True
                                        
                                        # Retry logic for JS fallback
                                        for _ in range(3):
                                            self.logger.info("Waiting for internet access (JS fallback)...")
                                            time.sleep(2)
                                            if self.strict_check_portal_time_via_socks():
                                                return True

                                        self.logger.warning("Авторизация (JS) вроде успешна, но SOCKS недоступен")
                                        return False
                                except Exception:
                                    pass
                                continue

                except Exception as e:
                    self.logger.debug(f"Ошибка с селектором {selector}: {e}")
                    continue

            self.logger.warning("Не найдены кнопки для авторизации")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка авторизации: {e}")
            return False
        
    def _enumerate_assets_and_large_js_scan(self):
        """Сканирует DOM и performance для поиска ассетов и самого большого JS-бандла портала."""
        try:
            scripts = []
            links = []
            imgs = []
            iframes = []
            assets_result = {"scripts": [], "links": [], "imgs": [], "iframes": [], "perf_scripts": [], "sizes": [], "big_js": None, "github_links": []}
            try:
                scripts = [e.get_attribute("src") or "" for e in self.driver.find_elements(By.CSS_SELECTOR, "script[src]")]
            except Exception:
                scripts = []
            try:
                links = [e.get_attribute("href") or "" for e in self.driver.find_elements(By.CSS_SELECTOR, "link[href]")]
            except Exception:
                links = []
            try:
                imgs = [e.get_attribute("src") or "" for e in self.driver.find_elements(By.CSS_SELECTOR, "img[src]")]
            except Exception:
                imgs = []
            try:
                iframes = [e.get_attribute("src") or "" for e in self.driver.find_elements(By.CSS_SELECTOR, "iframe[src]")]
            except Exception:
                iframes = []
            self.logger.info(f"[Assets] scripts={len([u for u in scripts if u])} links={len([u for u in links if u])} imgs={len([u for u in imgs if u])} iframes={len([u for u in iframes if u])}")
            assets_result["scripts"] = [u for u in scripts if u]
            assets_result["links"] = [u for u in links if u]
            assets_result["imgs"] = [u for u in imgs if u]
            assets_result["iframes"] = [u for u in iframes if u]
            perf_entries = []
            try:
                perf_entries = self.driver.execute_script("return (window.performance && window.performance.getEntriesByType) ? window.performance.getEntriesByType('resource') : []")
            except Exception:
                perf_entries = []
            perf_scripts = []
            try:
                for e in perf_entries or []:
                    n = e.get('name')
                    it = e.get('initiatorType')
                    if n:
                        if it == 'script' or n.lower().endswith('.js'):
                            perf_scripts.append(n)
                if perf_scripts:
                    self.logger.debug(f"[Perf scripts] {len(perf_scripts)}")
                    for n in perf_scripts[:50]:
                        self.logger.debug(f"  perf: {n}")
                assets_result["perf_scripts"] = perf_scripts
            except Exception:
                pass
            urls = set()
            for u in scripts + perf_scripts:
                if u:
                    urls.add(u)
            urls = list(urls)
            if not urls:
                try:
                    self._save_assets_artifact(assets_result)
                except Exception:
                    pass
                return assets_result
            socks_port = os.environ.get("NOJS_SOCKS_PORT")
            def curl_size(u):
                try:
                    if socks_port:
                        cmd = ["bash","-lc",f"curl -x socks5h://127.0.0.1:{socks_port} -L -s -w '%{{size_download}}' -o /dev/null '{u}'"]
                    else:
                        cmd = ["bash","-lc",f"curl -L -s -w '%{{size_download}}' -o /dev/null '{u}'"]
                    rc, out, _ = self._sh(cmd, timeout=30)
                    if rc == 0:
                        return int(out.strip() or "0")
                except Exception:
                    pass
                return 0
            sizes = []
            for u in urls[:100]:
                s = curl_size(u)
                sizes.append((u, s))
                self.logger.debug(f"[JS size] {u} → {s} bytes")
            try:
                assets_result["sizes"] = [{"url": u, "bytes": s} for (u, s) in sizes]
            except Exception:
                pass
            big = [t for t in sizes if t[1] >= 512000]
            if not big:
                try:
                    self._save_assets_artifact(assets_result)
                except Exception:
                    pass
                return assets_result
            target = sorted(big, key=lambda x: x[1], reverse=True)[0][0]
            self.logger.debug(f"[Big JS] {target}")
            assets_result["big_js"] = target
            try:
                if socks_port:
                    cmd = ["bash","-lc",f"curl -x socks5h://127.0.0.1:{socks_port} -L -s '{target}'"]
                else:
                    cmd = ["bash","-lc",f"curl -L -s '{target}'"]
                rc, out, _ = self._sh(cmd, timeout=60)
                if rc == 0 and out:
                    gh = []
                    for mm in re.finditer(r"https?://[^\\s'\"<>]+", out):
                        u = mm.group(0)
                        low = u.lower()
                        if ("github.com" in low) or ("raw.githubusercontent.com" in low) or ("gist.github.com" in low):
                            gh.append(u)
                    if gh:
                        uniq = []
                        seen = set()
                        for u in gh:
                            if u not in seen:
                                seen.add(u)
                                uniq.append(u)
                        self.logger.debug(f"[GitHub links in big JS] {len(uniq)}")
                        for u in uniq:
                            self.logger.debug(f"  {u}")
                        assets_result["github_links"] = uniq
            except Exception:
                pass
            try:
                self._save_assets_artifact(assets_result)
            except Exception:
                pass
            return assets_result
        except Exception:
            pass
        return assets_result
    
    def _save_assets_artifact(self, data):
        try:
            path = "conn4_assets.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"[Assets artifact] сохранён: {path}")
        except Exception:
            pass

    def check_success(self):
        """Проверка успешности авторизации"""
        try:
            url = (self.driver.current_url or "").lower()
            if ('msn.com' in url) or ('leonardo-hotels.com' in url):
                return True
            cookies = []
            try:
                cookies = self.driver.get_cookies() or []
            except Exception:
                cookies = []
            has_cookie = False
            try:
                has_cookie = any((c.get("name") or "") == "himalaya-site-ident" for c in cookies)
            except Exception:
                has_cookie = False
            api = None
            prx = None
            try:
                api = self.driver.execute_script("try { return window.sessionStorage.getItem('conn4-hotspot-storage-apiSessionId'); } catch(e) { return null; }")
            except Exception:
                api = None
            try:
                prx = self.driver.execute_script("try { return window.sessionStorage.getItem('conn4-hotspot-storage-paymentReturnProxyUrl'); } catch(e) { return null; }")
            except Exception:
                prx = None
            # Strict validation: Tokens alone are not enough if network confirmation is missing.
            # However, for legacy compatibility, we treat tokens as a "Candidate Success".
            # The caller MUST verify internet connectivity.
            if has_cookie or api or prx:
                # We found tokens. Let's see if we can find a 200 OK to confirm.
                try:
                    logs = self.driver.get_log('performance') or []
                    for entry in logs:
                        try:
                            msg = json.loads(entry.get('message') or '{}').get('message') or {}
                            if msg.get('method') == 'Network.responseReceived':
                                p = msg.get('params') or {}
                                resp = p.get('response') or {}
                                u = (resp.get('url') or (p.get('request') or {}).get('url') or '').lower()
                                st = resp.get('status')
                                if st == 200 and ('/wbs/api/v1/login/free/' in u):
                                    self.logger.info("Success confirmed via Network Log (200 OK from Auth API).")
                                    return True
                        except Exception:
                            pass
                except Exception:
                    pass
                
                # If we didn't find the 200 OK, we still return True because tokens are present,
                # BUT the caller (try_authentication) has a mandatory SOCKS check now.
                return True
            try:
                if ('conn4.com' in url) and (('loggedin=' in url) or ('remembered_mac=' in url) or ('cookie-challenge=' in url)):
                    return True
            except Exception:
                pass
            return False
        except Exception as e:
            self.logger.error(f"Ошибка проверки успеха: {e}")
            return False

    def cleanup(self):
        """Очистка ресурсов"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Chrome WebDriver закрыт")
            except:
                pass
    
    def _current_url_sanitized(self):
        try:
            url = self.driver.current_url or ""
        except Exception:
            url = ""
        try:
            u = urlparse(url)
            host = (u.netloc or "").lower()
            allowed = ("conn4.com" in host) or ("rdr.conn4.com" in host) or ("msftconnecttest.com" in host) or ("captive.apple.com" in host) or ("connectivitycheck.gstatic.com" in host)
            if allowed:
                return url
        except Exception:
            pass
        try:
            base_host = self._resolve_portal_host() or ""
            if base_host:
                return f"https://{base_host}"
        except Exception:
            pass
        return "http://www.msftconnecttest.com/redirect"
    
    def save_debug_artifact(self, path="conn4_debug.json"):
        try:
            data = {}
            try:
                data["current_url"] = self._current_url_sanitized()
            except Exception:
                data["current_url"] = None
            try:
                data["pre_click_url"] = self.pre_click_url
            except Exception:
                data["pre_click_url"] = None
            try:
                data["title"] = self.driver.title
            except Exception:
                data["title"] = None
            try:
                data["capturedRequests"] = self.driver.execute_script("return window.__capturedRequests || []")
            except Exception:
                data["capturedRequests"] = []
            try:
                data["traceLog"] = self.driver.execute_script("return window.__traceLog || []")
            except Exception:
                data["traceLog"] = []
            try:
                cs = self.driver.get_cookies() or []
                filt = []
                for c in cs:
                    try:
                        d = (c.get("domain") or "").lower()
                        if ("conn4.com" in d) or ("rdr.conn4.com" in d):
                            filt.append(c)
                    except Exception:
                        pass
                data["cookies"] = filt
            except Exception:
                data["cookies"] = []
            try:
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                submit_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
                button_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='button']")
                checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                scripts = self.driver.find_elements(By.TAG_NAME, "script")
                data["domCounts"] = {
                    "inputs": len(inputs),
                    "buttons": len(buttons),
                    "submit_inputs": len(submit_inputs),
                    "button_inputs": len(button_inputs),
                    "checkboxes": len(checkboxes),
                    "scripts": len(scripts)
                }
            except Exception:
                data["domCounts"] = {}
            try:
                frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                srcs = []
                for fr in frames:
                    try:
                        s = fr.get_attribute("src") or ""
                        sl = s.lower()
                        if ("conn4.com" in sl) or ("rdr.conn4.com" in sl) or ("msftconnecttest.com" in sl) or ("captive.apple.com" in sl) or ("connectivitycheck.gstatic.com" in sl):
                            srcs.append(s)
                    except Exception:
                        pass
                data["iframes"] = srcs
            except Exception:
                data["iframes"] = []
            try:
                data["page_html"] = self.driver.page_source
            except Exception:
                data["page_html"] = ""
            data["portal_frame_index"] = self.portal_frame_index
            try:
                data["formSubmits"] = self.driver.execute_script("return window.__formSubmits || []")
            except Exception:
                data["formSubmits"] = []
            try:
                data["networkSummary"] = self._collect_network_events()
            except Exception:
                data["networkSummary"] = []
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Отладочный артефакт сохранен: {path}")
            except Exception as e:
                self.logger.info(f"Ошибка сохранения артефакта: {e}")
        except Exception as e:
            try:
                self.logger.info(f"Ошибка подготовки артефакта: {e}")
            except Exception:
                pass
    
    def _nojs_collect_tokens(self, html):
        tokens = extract_tokens_from_html(html or "")
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
        except Exception:
            pass
        try:
            bodies = []
            try:
                bodies = self._collect_js_bodies()
            except Exception:
                bodies = []
            for _, b in bodies or []:
                try:
                    t2 = collect_tokens_from_text(b or "")
                    for k, v in (t2 or {}).items():
                        if v is not None and k not in tokens:
                            tokens[k] = v
                except Exception:
                    pass
        except Exception:
            pass
        try:
            api = self.driver.execute_script("try { return window.sessionStorage.getItem('conn4-hotspot-storage-apiSessionId'); } catch(e) { return null; }")
            if api:
                tokens["apiSessionId"] = api
        except Exception:
            pass
        try:
            prx = self.driver.execute_script("try { return window.sessionStorage.getItem('conn4-hotspot-storage-paymentReturnProxyUrl'); } catch(e) { return null; }")
            if prx:
                tokens["paymentReturnProxyUrl"] = prx
        except Exception:
            pass
        try:
            u = urlparse(self.driver.current_url or "")
            qs = parse_qs(u.query or "")
            for k in ("client_ip","client_mac","site_id","signature","loggedin","remembered_mac","cookie-challenge"):
                v = (qs.get(k, [None])[0])
                if v is not None:
                    tokens[k] = v
            if "client_ip" in tokens and "clientIp" not in tokens:
                tokens["clientIp"] = tokens.get("client_ip")
            if "client_mac" in tokens and "clientMac" not in tokens:
                tokens["clientMac"] = tokens.get("client_mac")
            if "site_id" in tokens and "siteId" not in tokens:
                tokens["siteId"] = tokens.get("site_id")
        except Exception:
            pass
        try:
            cookies = self.driver.get_cookies() or []
            for c in cookies:
                try:
                    if (c.get("name") or "") == "himalaya-site-ident":
                        import base64
                        raw = c.get("value") or ""
                        s = unquote(raw)
                        pad = "=" * ((4 - len(s) % 4) % 4)
                        dec = base64.b64decode(s + pad)
                        txt = ""
                        try:
                            txt = dec.decode("utf-8","replace")
                        except Exception:
                            txt = str(dec)
                        if txt:
                            ipm = re.search(r's:12:"\\*IPAddress";s:\\d+:"((?:\\d{1,3}\\.){3}\\d{1,3})"', txt) or re.search(r"\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b", txt)
                            macm = re.search(r's:13:"\\*MACAddress";s:\\d+:"([0-9A-F]{12})"', txt) or re.search(r"\\b[0-9A-F]{12}\\b", txt)
                            sidm = re.search(r's:9:".*siteId";i:(\\d+)', txt) or re.search(r'siteId";i:(\\d+)', txt)
                            ip = ipm.group(1) if ipm and ipm.lastindex and ipm.lastindex >= 1 else (ipm.group(0) if ipm else None)
                            mac = macm.group(1) if macm and macm.lastindex and macm.lastindex >= 1 else (macm.group(0) if macm else None)
                            sid = sidm.group(1) if sidm and sidm.lastindex and sidm.lastindex >= 1 else (sidm.group(0) if sidm else None)
                            if ip and "client_ip" not in tokens:
                                tokens["client_ip"] = ip
                            if mac and "client_mac" not in tokens:
                                tokens["client_mac"] = mac
                            if sid and "site_id" not in tokens:
                                tokens["site_id"] = sid
                            if "clientIp" not in tokens and tokens.get("client_ip"):
                                tokens["clientIp"] = tokens.get("client_ip")
                            if "clientMac" not in tokens and tokens.get("client_mac"):
                                tokens["clientMac"] = tokens.get("client_mac")
                            if "siteId" not in tokens and tokens.get("site_id"):
                                tokens["siteId"] = tokens.get("site_id")
                except Exception:
                    continue
        except Exception:
            pass
        return tokens
    
    def _cookie_names_from_header(self, header_value):
        try:
            s = header_value or ""
            parts = [p.strip() for p in s.split(";") if p.strip()]
            names = []
            for p in parts:
                if "=" in p:
                    names.append(p.split("=",1)[0])
            uniq = []
            seen = set()
            for n in names:
                if n not in seen:
                    seen.add(n)
                    uniq.append(n)
            return uniq
        except Exception:
            return []
    
    def _sanitize_headers(self, headers, for_response=False):
        try:
            if not isinstance(headers, dict):
                return headers
            clean = {}
            cookie_names_key = "setCookieNames" if for_response else "cookieNames"
            for k, v in headers.items():
                kl = (k or "").lower()
                if kl == "cookie":
                    try:
                        clean[cookie_names_key] = self._cookie_names_from_header(v)
                    except Exception:
                        clean[cookie_names_key] = []
                    clean[k] = "<redacted>"
                else:
                    clean[k] = v
            return clean
        except Exception:
            return headers
    
    def _nojs_build_consent_body(self, tokens):
        try:
            u = urlparse(self.driver.current_url or "")
            qs = parse_qs(u.query or "")
            flat_qs = {k:(v[0] if isinstance(v,list) and v else v) for k,v in qs.items()}
        except Exception:
            flat_qs = {}
        phpsessid = None
        try:
            for c in (self.driver.get_cookies() or []):
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
    
    def _get_cookie_value(self, name):
        try:
            for c in (self.driver.get_cookies() or []):
                if (c.get("name") or "") == name:
                    return c.get("value")
        except Exception:
            return None
        return None
    
    def _extract_authorization_token_from_cookie(self):
        try:
            raw = self._get_cookie_value("himalaya-site-ident") or ""
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
                    ipm = re.search(r's:12:"\\*IPAddress";s:\\d+:"((?:\\d{1,3}\\.){3}\\d{1,3})"', txt) or re.search(r"\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b", txt)
                    macm = re.search(r's:13:"\\*MACAddress";s:\\d+:"([0-9A-F]{12})"', txt) or re.search(r"\\b[0-9A-F]{12}\\b", txt)
                    sidm = re.search(r's:9:".*siteId";i:(\\d+)', txt) or re.search(r'siteId";i:(\\d+)', txt)
                    self.cookie_decoded_ip = ipm.group(1) if ipm and ipm.lastindex and ipm.lastindex >= 1 else (ipm.group(0) if ipm else self.cookie_decoded_ip)
                    self.cookie_decoded_mac = macm.group(1) if macm and macm.lastindex and macm.lastindex >= 1 else (macm.group(0) if macm else self.cookie_decoded_mac)
                    self.cookie_decoded_site_id = sidm.group(1) if sidm and sidm.lastindex and sidm.lastindex >= 1 else (sidm.group(0) if sidm else self.cookie_decoded_site_id)
                except Exception:
                    pass
            return txt
        except Exception:
            return None
    
    def _create_wbs_api_auth_token(self, site_id, client_ip, client_mac):
        try:
            cookie_token = self._extract_authorization_token_from_cookie() or ""
            existing_hash = ""
            if cookie_token and "|" in cookie_token:
                existing_hash = cookie_token.split("|")[-1]
            if not existing_hash:
                return None
            token_obj = WbsTokenBuilder.build_token_object(int(site_id or 0), client_ip or "127.0.0.1", client_mac or "")
            serialized = PhpSerializer.serialize(token_obj)
            full_str = f"HWA*{serialized}|{existing_hash}"
            return base64.b64encode(full_str.encode("utf-8")).decode("ascii")
        except Exception:
            return None
    
    def _stepwise_compare(self, report_obj):
        diffs = []
        try:
            cmp = (report_obj.get("compare") or {})
            tokens = cmp.get("computedTokens") or {}
            site_id = tokens.get("siteId") or tokens.get("site_id") or "1096"
            client_ip = tokens.get("clientIp") or tokens.get("client_ip")
            client_mac = tokens.get("clientMac") or tokens.get("client_mac")
            local_wbs = self._create_wbs_api_auth_token(site_id, client_ip, client_mac) or ""
            net = report_obj.get("network") or []
            def _find_post(substr):
                for e in net:
                    rq = e.get("request") or {}
                    u = (rq.get("url") or e.get("url") or "") or ""
                    if substr in (u or ""):
                        pd = rq.get("postData")
                        if isinstance(pd, str) and pd:
                            return pd
                return None
            def _find_get_qs(substr):
                for e in net:
                    rq = e.get("request") or {}
                    u = (rq.get("url") or e.get("url") or "") or ""
                    m = e.get("method") or rq.get("method")
                    if substr in (u or "") and (m or "").upper() == "GET":
                        try:
                            pu = urlparse(u)
                            return pu.query or ""
                        except Exception:
                            return ""
                return ""
            post_create = _find_post("/wbs/api/v1/create-session/")
            post_login = _find_post("/wbs/api/v1/login/free/")
            post_auth = _find_post("/wbs/authenticate-me/")
            post_reg = _find_post("/registration-free")
            get_ident_qs = _find_get_qs("/ident")
            if isinstance(post_create, str) and post_create:
                try:
                    s = unquote(post_create)
                    qs = parse_qs(s)
                    auth = (qs.get("authorization",[None])[0] or "")
                    real_tok = ""
                    if auth.startswith("token="):
                        real_tok = auth[6:]
                    if local_wbs and real_tok and local_wbs != real_tok:
                        diffs.append({"step":"create-session","field":"wbsApiAuthToken","selenium":real_tok,"nojs":local_wbs})
                except Exception:
                    pass
            consent = self._nojs_build_consent_body(tokens) or {}
            if isinstance(post_login, str) and post_login:
                try:
                    s = unquote(post_login)
                    qs = parse_qs(s)
                    exp = {"authorization": consent.get("authorization"), "tariff": str(consent.get("tariff"))}
                    act = {"authorization": (qs.get("authorization",[None])[0]), "tariff": (qs.get("tariff",[None])[0])}
                    if exp != act:
                        diffs.append({"step":"login-free","field":"payload","selenium":act,"nojs":exp})
                except Exception:
                    pass
            if isinstance(post_auth, str) and post_auth:
                try:
                    s = unquote(post_auth)
                    qs = parse_qs(s)
                    exp = {"api_session_id": consent.get("api_session_id"), "payment_return_proxy_url": consent.get("payment_return_proxy_url"), "signature": tokens.get("signature")}
                    act = {"api_session_id": (qs.get("api_session_id",[None])[0]), "payment_return_proxy_url": (qs.get("payment_return_proxy_url",[None])[0]), "signature": (qs.get("signature",[None])[0])}
                    if exp != act:
                        diffs.append({"step":"authenticate-me","field":"payload","selenium":act,"nojs":exp})
                except Exception:
                    pass
            if isinstance(post_reg, str) and post_reg:
                try:
                    s = unquote(post_reg)
                    qs = parse_qs(s)
                    exp = {"authorization": consent.get("authorization"), "tariff": str(consent.get("tariff"))}
                    act = {"authorization": (qs.get("authorization",[None])[0]), "tariff": (qs.get("tariff",[None])[0])}
                    if exp != act:
                        diffs.append({"step":"registration-free","field":"payload","selenium":act,"nojs":exp})
                except Exception:
                    pass
            if isinstance(get_ident_qs, str) and get_ident_qs:
                try:
                    qs = parse_qs(get_ident_qs)
                    exp = {"client_ip": tokens.get("client_ip") or tokens.get("clientIp"), "client_mac": tokens.get("client_mac") or tokens.get("clientMac"), "site_id": tokens.get("site_id") or tokens.get("siteId"), "signature": tokens.get("signature")}
                    act = {"client_ip": (qs.get("client_ip",[None])[0] or qs.get("ip",[None])[0]), "client_mac": (qs.get("client_mac",[None])[0] or qs.get("mac",[None])[0]), "site_id": (qs.get("site_id",[None])[0]), "signature": (qs.get("signature",[None])[0])}
                    if exp != act:
                        diffs.append({"step":"ident","field":"query","selenium":act,"nojs":exp})
                except Exception:
                    pass
        except Exception:
            pass
        return diffs
    
    def _collect_network_events(self):
        events = []
        try:
            logs = self.driver.get_log('performance') or []
        except Exception:
            logs = []
        for ent in logs:
            try:
                msg = json.loads(ent.get('message') or '{}')
                m = msg.get('message') or {}
                method = m.get('method')
                p = m.get('params') or {}
                rid = p.get('requestId')
                item = {'event': method}
                if rid is not None:
                    item['id'] = rid
                ts = p.get('timestamp')
                if ts is not None:
                    item['ts'] = ts
                t = p.get('type')
                if t is not None:
                    item['type'] = t
                doc_url = p.get('documentURL')
                if doc_url:
                    item['documentURL'] = doc_url
                initiator = p.get('initiator')
                if initiator:
                    item['initiator'] = initiator
                req = p.get('request') or {}
                if req:
                    rq = {
                        'url': req.get('url'),
                        'method': req.get('method'),
                        'headers': self._sanitize_headers(req.get('headers') or {}),
                        'postData': req.get('postData')
                    }
                    try:
                        if isinstance(rq.get('headers'), dict):
                            ref = rq['headers'].get('Referer') or rq['headers'].get('referer')
                            if ref:
                                rq['referer'] = ref
                    except Exception:
                        pass
                    try:
                        u = rq.get('url') or ''
                        if u:
                            pu = urlparse(u)
                            item['url'] = u
                            if rq.get('method') is not None:
                                item['method'] = rq.get('method')
                            if pu.scheme:
                                item['scheme'] = pu.scheme
                            if pu.netloc:
                                item['host'] = pu.netloc
                            if pu.path:
                                item['path'] = pu.path
                            if pu.query:
                                item['query'] = pu.query
                        if rq.get('referer') is not None:
                            item['referer'] = rq.get('referer')
                        if isinstance(rq.get('headers'), dict):
                            item['requestHeaders'] = rq.get('headers')
                            cn = rq['headers'].get('cookieNames')
                            if cn is not None:
                                item['cookieNames'] = cn
                    except Exception:
                        pass
                    item['request'] = rq
                resp = p.get('response') or {}
                if resp:
                    rp = {
                        'url': resp.get('url') or resp.get('urlFragment'),
                        'status': resp.get('status'),
                        'mimeType': resp.get('mimeType'),
                        'headers': self._sanitize_headers(resp.get('headers') or {}, for_response=True),
                        'remoteIPAddress': resp.get('remoteIPAddress'),
                        'remotePort': resp.get('remotePort'),
                        'timing': resp.get('timing'),
                        'fromDiskCache': resp.get('fromDiskCache'),
                        'fromServiceWorker': resp.get('fromServiceWorker'),
                        'protocol': resp.get('protocol')
                    }
                    item['response'] = rp
                    try:
                        if rp.get('url'):
                            item['responseUrl'] = rp.get('url')
                        if rp.get('status') is not None:
                            item['status'] = rp.get('status')
                        if rp.get('mimeType') is not None:
                            item['mimeType'] = rp.get('mimeType')
                        if isinstance(rp.get('headers'), dict):
                            item['responseHeaders'] = rp.get('headers')
                            scn = rp['headers'].get('setCookieNames')
                            if scn is not None:
                                item['setCookieNames'] = scn
                        if rp.get('remoteIPAddress') is not None:
                            item['remoteIPAddress'] = rp.get('remoteIPAddress')
                        if rp.get('remotePort') is not None:
                            item['remotePort'] = rp.get('remotePort')
                        if rp.get('protocol') is not None:
                            item['protocol'] = rp.get('protocol')
                    except Exception:
                        pass
                if method == 'Network.requestWillBeSentExtraInfo':
                    extra = {}
                    if p.get('headers') is not None:
                        extra['requestHeaders'] = self._sanitize_headers(p.get('headers') or {})
                    if p.get('associatedCookies') is not None:
                        try:
                            ecs = []
                            for c in p.get('associatedCookies') or []:
                                try:
                                    nm = ((c.get('cookie') or {}).get('name') or '')
                                    dm = ((c.get('cookie') or {}).get('domain') or '')
                                    pt = ((c.get('cookie') or {}).get('path') or '')
                                    ecs.append({'name': nm, 'domain': dm, 'path': pt})
                                except Exception:
                                    pass
                            extra['associatedCookies'] = ecs
                        except Exception:
                            extra['associatedCookies'] = []
                    if p.get('headersText') is not None:
                        extra['headersText'] = p.get('headersText')
                    if extra:
                        item['extra'] = extra
                if method == 'Network.responseReceivedExtraInfo':
                    extra = {}
                    if p.get('headers') is not None:
                        extra['responseHeaders'] = self._sanitize_headers(p.get('headers') or {}, for_response=True)
                    if p.get('headersText') is not None:
                        extra['headersText'] = p.get('headersText')
                    if p.get('blockedCookies') is not None:
                        extra['blockedCookies'] = p.get('blockedCookies')
                    if p.get('cookies') is not None:
                        try:
                            ecs = []
                            for c in p.get('cookies') or []:
                                try:
                                    nm = (c.get('name') or '')
                                    dm = (c.get('domain') or '')
                                    pt = (c.get('path') or '')
                                    ecs.append({'name': nm, 'domain': dm, 'path': pt})
                                except Exception:
                                    pass
                            extra['cookies'] = ecs
                        except Exception:
                            extra['cookies'] = []
                    if extra:
                        item['extra'] = extra
                if method == 'Network.dataReceived':
                    dr = {}
                    if p.get('dataLength') is not None:
                        dr['dataLength'] = p.get('dataLength')
                    if p.get('encodedDataLength') is not None:
                        dr['encodedDataLength'] = p.get('encodedDataLength')
                    item['data'] = dr
                if method == 'Network.loadingFinished':
                    edl = p.get('encodedDataLength')
                    if edl is not None:
                        item['encodedDataLength'] = edl
                    try:
                        if (p.get('requestId') is not None) and (p.get('type') in ('Script','XHR')):
                            body_obj = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': p.get('requestId')})
                            b = body_obj.get('body') or ''
                            if body_obj.get('base64Encoded'):
                                try:
                                    b = base64.b64decode(b).decode('utf-8', 'replace')
                                except Exception:
                                    b = ''
                            if b:
                                try:
                                    snip = b[:1024]
                                    item['responseBodySnippet'] = snip
                                    item['responseBodyLength'] = len(b)
                                except Exception:
                                    pass
                    except Exception:
                        pass
                if method == 'Network.loadingFailed':
                    lf = {}
                    if p.get('errorText'):
                        lf['errorText'] = p.get('errorText')
                    if p.get('canceled') is not None:
                        lf['canceled'] = p.get('canceled')
                    if p.get('type'):
                        lf['type'] = p.get('type')
                    item['failure'] = lf
                events.append(item)
            except Exception:
                pass
        return events
    
    def _build_redirect_ident_url(self, tokens):
        try:
            u = urlparse(self.driver.current_url or "")
            base = f"{u.scheme}://{u.netloc}" if (u.scheme and u.netloc) else None
            if not base:
                return None
            dest = f"{base}/admon-assets/ident.php"
            mac = tokens.get("client_mac") or tokens.get("clientMac")
            ip = tokens.get("client_ip") or tokens.get("clientIp")
            site = tokens.get("site_id") or tokens.get("siteId")
            sig = tokens.get("signature")
            q = {}
            if mac: q["client_mac"] = mac
            if ip: q["client_ip"] = ip
            if site: q["site_id"] = site
            if sig: q["signature"] = sig
            qs = urlencode(q)
            return f"{dest}?{qs}" if qs else dest
        except Exception:
            return None
    
    def _build_ident_url(self, tokens):
        try:
            u = urlparse(self.driver.current_url or "")
            base = f"{u.scheme}://{u.netloc}" if (u.scheme and u.netloc) else None
            if not base:
                return None
            dest = f"{base}/ident"
            mac = tokens.get("client_mac") or tokens.get("clientMac")
            ip = tokens.get("client_ip") or tokens.get("clientIp")
            site = tokens.get("site_id") or tokens.get("siteId")
            sig = tokens.get("signature")
            q = {}
            if mac: q["client_mac"] = mac
            if ip: q["client_ip"] = ip
            if site: q["site_id"] = site
            if sig: q["signature"] = sig
            if not q:
                return dest
            qs = urlencode(q)
            return f"{dest}?{qs}"
        except Exception:
            return None
    
    def _nojs_compute_and_compare(self):
        html = ""
        try:
            html = self.driver.page_source or ""
        except Exception:
            html = ""
        try:
            tokens = self._nojs_collect_tokens(html)
        except Exception:
            tokens = {}
        
        # Если есть токены, собранные перед кликом (пока мы были на conn4.com), используем их
        if self.pre_click_tokens:
            self.logger.info(f"Используем pre_click_tokens: {len(self.pre_click_tokens)} шт.")
            for k, v in self.pre_click_tokens.items():
                if v is not None and (k not in tokens or not tokens[k]):
                    tokens[k] = v
        
        try:
            body = self._nojs_build_consent_body(tokens)
        except Exception:
            body = {}
        try:
            net = self._collect_network_events()
        except Exception:
            net = []
        summary = {"computedTokens": tokens, "computedConsent": body, "network": net}
        try:
            with open("conn4_compare.json","w",encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            self.logger.info("Сравнение вычислений сохранено: conn4_compare.json")
        except Exception as e:
            try:
                self.logger.info(f"Ошибка сохранения сравнения: {e}")
            except Exception:
                pass

    def run_test(self):
        """Запуск полного теста"""
        self.logger.info("=" * 60)
        self.logger.info("ТЕСТИРОВАНИЕ CONN4.COM CAPTIVE PORTAL")
        self.logger.info("=" * 60)

        try:
            try:
                self.ensure_socks_proxy()
            except Exception:
                pass
            force_run = (os.environ.get("CPM_FORCE_RUN") or "").strip() == "1"
            if not self.verify_socks_proxy() and not force_run:
                self.logger.error("❌ SOCKS-прокси не готов")
                return False
            if not self.verify_ssh_router_access() and not force_run:
                self.logger.warning("⚠️ SSH доступ к роутеру недоступен, продолжаем при активном SOCKS")
            if not self.strict_check_portal_time_via_socks() and not force_run:
                self.logger.warning("⚠️ Проверка /_time через SOCKS не пройдена, продолжаем")
            if (os.environ.get("CPM_PRECHECK_ONLY") or "").strip() == "1":
                self.logger.info("Пред-проверка среды завершена, браузер не запускается")
                return True
            if not self.setup_chrome_driver():
                return False

            success = False
            try:
                success = self.test_conn4_portal()
            except Exception:
                success = False
            if success:
                final_url = ""
                try:
                    final_url = (self.driver.current_url or "").lower()
                except Exception:
                    final_url = ""
                override = ('msn.com' in final_url) or ('leonardo-hotels.com' in final_url)
                if not override:
                    try:
                        if not self.strict_check_portal_time_via_socks():
                            self.logger.warning("⚠️ Интернет через SOCKS после авторизации недоступен, продолжаем как успешную авторизацию по редиректу")
                    except Exception:
                        self.logger.warning("⚠️ Не удалось выполнить проверку интернета после авторизации")
            try:
                self.save_debug_artifact("conn4_debug_success.json" if success else "conn4_debug_fail.json")
            except Exception:
                pass
            try:
                self.debug_checkpoint("postlogin")
            except Exception:
                pass
            try:
                self._nojs_compute_and_compare()
            except Exception:
                pass
            try:
                self._save_js_time_sources()
            except Exception:
                pass
            try:
                self._save_time_initiators()
            except Exception:
                pass
            try:
                self._save_conn4_schema()
            except Exception:
                pass
            try:
                _save_master_report(self)
            except Exception as e:
                self.logger.error(f"CRITICAL: Failed to save master report: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
            if success:
                self.logger.info("🎉 АВТОРИЗАЦИЯ НА CONN4.COM УСПЕШНА!")
            else:
                self.logger.warning("❌ Авторизация не удалась")
            return success

        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка: {e}")
            return False
        finally:
            self.cleanup()
            try:
                self.shutdown_socks_proxy()
            except Exception:
                pass

    def verify_socks_proxy(self):
        try:
            if self.socks_manager.verify_socks_proxy(silent=True):
                self.logger.info(f"[SOCKS CHECK] порт {self.socks_manager.socks_port} активен")
                return True
            port = os.environ.get("NOJS_SOCKS_PORT") or "10800"
            rci1, ip1, _ = self._sh(["bash","-lc","which curl >/dev/null 2>&1 && curl -s --max-time 8 https://api.ipify.org || echo NA"], timeout=12)
            rci2, ip2, _ = self._sh(["bash","-lc",f"which curl >/dev/null 2>&1 && curl -x socks5h://127.0.0.1:{port} -s --max-time 8 https://api.ipify.org || echo NA"], timeout=12)
            ip1 = (ip1 or "").strip()
            ip2 = (ip2 or "").strip()
            self.logger.info(f"[SOCKS CHECK] ip direct={ip1 or 'NA'} ip socks={ip2 or 'NA'}")
            if ip2 and ip2 != "NA":
                return True
            # Fallback: если curl недоступен, но порт открыт — считаем готовым
            return self.socks_manager.verify_socks_proxy(silent=True)
        except Exception:
            return self.socks_manager.verify_socks_proxy(silent=True)
    
    def ensure_socks_proxy(self):
        try:
            host = os.environ.get("OPENWRT_SSH_HOST","dev-openwrt")
            user = os.environ.get("OPENWRT_SSH_USER","root")
            target = f"{user}@{host}"
            port = os.environ.get("NOJS_SOCKS_PORT") or "10800"
            rc, out, _ = self._sh(["bash","-lc",f"ss -lnt | awk '{{print $4}}' | grep -q ':{port}$' && echo ok || echo fail"], timeout=5)
            active = ((out or "").strip() == "ok")
            if not active:
                self._sh(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=no","-f","-N","-D",f"127.0.0.1:{port}",target], timeout=10)
                try:
                    time.sleep(1)
                except Exception:
                    pass
            self._sh(["bash","-lc",f"export ALL_PROXY=socks5h://127.0.0.1:{port}; export HTTPS_PROXY=$ALL_PROXY; export HTTP_PROXY=$ALL_PROXY; true"], timeout=2)
        except Exception:
            pass
    
    def shutdown_socks_proxy(self):
        try:
            port = os.environ.get("NOJS_SOCKS_PORT") or "10800"
            script = "set -e; pids=$(ss -lntp 2>/dev/null | awk -v port=':{p}$' '$4 ~ port { match($NF, /pid=([0-9]+)/, m); if (m[1]) print m[1]; }' | tr '\\n' ' '); [ -n \"$pids\" ] && kill $pids >/dev/null 2>&1 || true".replace("{p}", port)
            self._sh(["bash","-lc", script], timeout=10)
        except Exception:
            pass
    
    def _resolve_portal_host(self):
        try:
            env_url = os.environ.get("PORTAL_URL") or ""
            env_host = os.environ.get("PORTAL_HOST") or ""
            site = os.environ.get("CONN4_SITE_ID") or ""
            if env_host:
                return env_host
            if env_url:
                try:
                    u = urlparse(env_url)
                    h = u.netloc or u.path
                    if h:
                        return h
                except Exception:
                    pass
            if site:
                return f"{site}.rdr.conn4.com"
        except Exception:
            pass
        return None
    
    def verify_ssh_router_access(self):
        try:
            host = os.environ.get("OPENWRT_SSH_HOST","dev-openwrt")
            user = os.environ.get("OPENWRT_SSH_USER","root")
            target = f"{user}@{host}"
            rc, out, err = self._sh(["bash","-lc",f"ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=6 {target} ip addr show br-lan"], timeout=12)
            ok = (rc == 0) and ("br-lan" in (out or ""))
            self.logger.info(f"[SSH br-lan] {'OK' if ok else 'FAIL'} rc={rc}")
            return ok
        except Exception:
            return False
    
    def strict_check_portal_time_via_socks(self):
        try:
            host = self._resolve_portal_host()
            if not host:
                port = os.environ.get("NOJS_SOCKS_PORT") or "10800"
                proxy = f"socks5h://127.0.0.1:{port}"
                def curl_code_and_url(url):
                    rc, out, err = self._sh(["bash","-lc",f"curl -x {proxy} -s -L -o /dev/null -w '%{{http_code}} %{{url_effective}}' --max-time 10 '{url}'"], timeout=15)
                    if rc == 0:
                        return (out or "").strip()
                    return ""
                
                # Check multiple URLs to avoid false positives/negatives
                test_urls = [
                    "http://detectportal.firefox.com/canonical.html",
                    "http://connectivitycheck.gstatic.com/generate_204",
                    "http://www.msftconnecttest.com/connecttest.txt"
                ]
                
                for test_url in test_urls:
                    result = curl_code_and_url(test_url)
                    if result:
                        parts = result.split(maxsplit=1)
                        code = parts[0]
                        effective_url = parts[1] if len(parts) > 1 else ""
                        host = urlparse(effective_url).netloc.lower()
                        
                        if "conn4.com" in host:
                            self.logger.warning(f"Портал conn4.com обнаружен через {test_url}")
                            return False
                            
                        if code.startswith(("2","3")):
                            self.logger.info(f"[SOCKS FALLBACK] {test_url} OK {code} (final: {host})")
                            return True
                            
                self.logger.warning("Портал неизвестен и fallback через тестовые URL не пройден")
                return False

            port = os.environ.get("NOJS_SOCKS_PORT") or "10800"
            proxy = f"socks5h://127.0.0.1:{port}"
            def curl_code_and_url(url):
                rc, out, err = self._sh(["bash","-lc",f"curl -x {proxy} -s -L -o /dev/null -w '%{{http_code}} %{{url_effective}}' --max-time 10 '{url}'"], timeout=15)
                if rc == 0:
                    return (out or "").strip()
                return ""
            for test_url in ["http://detectportal.firefox.com/canonical.html","http://connectivitycheck.gstatic.com/generate_204","http://www.msftconnecttest.com/connecttest.txt"]:
                result = curl_code_and_url(test_url)
                if result:
                    parts = result.split(maxsplit=1)
                    code = parts[0]
                    effective_url = parts[1] if len(parts) > 1 else ""
                    eff_host = urlparse(effective_url).netloc.lower()
                    if "conn4.com" in eff_host:
                        continue
                    if code.startswith(("2","3")):
                        self.logger.info(f"[SOCKS] {test_url} OK {code} (final: {eff_host})")
                        return True
            def curl_code(url):
                rc, out, err = self._sh(["bash","-lc",f"curl -sS -x {proxy} --max-time 10 -w '%{{http_code}}' -o /dev/null '{url}'"], timeout=15)
                if rc == 0:
                    return (out or "").strip()
                return ""
            code_https = curl_code(f"https://{host}/_time")
            if code_https.startswith(("2","3")):
                self.logger.info(f"[/_time HTTPS] OK {code_https}")
                return True
            code_http = curl_code(f"http://{host}/_time")
            if code_http.startswith(("2","3")):
                self.logger.info(f"[/_time HTTP] OK {code_http}")
                return True
            self.logger.error(f"[/_time] недоступен через SOCKS: https={code_https or 'NA'} http={code_http or 'NA'}")
            return False
        except Exception:
            return False
    


def main():
    tester = Conn4PortalTester()

    try:
        url_arg = None
        out_arg = "conn4_tokens.json"
        collect_only = False
        write_compare = False
        args = sys.argv[1:] if len(sys.argv) > 1 else []
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
        if collect_only:
            try:
                ok = tester.setup_chrome_driver()
            except Exception:
                ok = False
            if not ok:
                sys.exit(2)
            try:
                tester.driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': []})
                tester.logger.info("Временно отключена блокировка ресурсов для сборки токенов")
            except Exception:
                pass
            try:
                target_url = url_arg or "http://www.msftconnecttest.com/redirect"
                tester.driver.get(target_url)
                try:
                    time.sleep(3)
                except Exception:
                    pass
                try:
                    tester.driver.execute_script("if (typeof initPage === 'function') { try { initPage(); } catch(e){} }")
                    tester.driver.execute_script("if (typeof loadContent === 'function') { try { loadContent(); } catch(e){} }")
                except Exception:
                    pass
                try:
                    found_storage = False
                    for _ in range(20):
                        api = tester.driver.execute_script("try { return window.sessionStorage.getItem('conn4-hotspot-storage-apiSessionId'); } catch(e) { return null; }")
                        prx = tester.driver.execute_script("try { return window.sessionStorage.getItem('conn4-hotspot-storage-paymentReturnProxyUrl'); } catch(e) { return null; }")
                        if api or prx:
                            found_storage = True
                            break
                        time.sleep(0.5)
                except Exception:
                    pass
                try:
                    found_cookie = False
                    for _ in range(12):
                        cs = tester.driver.get_cookies() or []
                        if any((c.get("name") or "") == "himalaya-site-ident" for c in cs):
                            found_cookie = True
                            break
                        time.sleep(0.5)
                    if not found_cookie:
                        cu = urlparse(tester.driver.current_url or "")
                        if cu.scheme and cu.netloc:
                            tester.driver.get(f"{cu.scheme}://{cu.netloc}/admon-assets/cookie-challenge.php")
                            try:
                                time.sleep(2)
                            except Exception:
                                pass
                    cu = urlparse(tester.driver.current_url or "")
                    if cu.scheme and cu.netloc:
                        try:
                            tester.driver.get(f"{cu.scheme}://{cu.netloc}/")
                            try:
                                time.sleep(2)
                            except Exception:
                                pass
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    html = tester.driver.page_source or ""
                except Exception:
                    html = ""
                toks = tester._nojs_collect_tokens(html)
                try:
                    ident_url = tester._build_redirect_ident_url(toks)
                except Exception:
                    ident_url = None
                if ident_url:
                    try:
                        tester.driver.get(ident_url)
                        try:
                            time.sleep(2)
                        except Exception:
                            pass
                        try:
                            html = tester.driver.page_source or ""
                        except Exception:
                            html = ""
                        toks = tester._nojs_collect_tokens(html)
                    except Exception:
                        pass
                try:
                    ident2 = tester._build_ident_url(toks)
                except Exception:
                    ident2 = None
                if ident2:
                    try:
                        tester.driver.get(ident2)
                        try:
                            time.sleep(2)
                        except Exception:
                            pass
                        try:
                            html = tester.driver.page_source or ""
                        except Exception:
                            html = ""
                        toks = tester._nojs_collect_tokens(html)
                    except Exception:
                        pass
                data = {
                    "apiSessionId": toks.get("apiSessionId"),
                    "paymentReturnProxyUrl": toks.get("paymentReturnProxyUrl"),
                    "siteId": toks.get("siteId"),
                    "clientIp": toks.get("clientIp"),
                    "clientMac": toks.get("clientMac"),
                    "signature": toks.get("signature"),
                    "client_ip": toks.get("client_ip"),
                    "client_mac": toks.get("client_mac"),
                    "site_id": toks.get("site_id"),
                    "loggedin": toks.get("loggedin"),
                    "remembered_mac": toks.get("remembered_mac"),
                    "cookie-challenge": toks.get("cookie-challenge"),
                }
                try:
                    with open(out_arg, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                if write_compare:
                    try:
                        consent = tester._nojs_build_consent_body(toks)
                    except Exception:
                        consent = {}
                    try:
                        net = tester._collect_network_events()
                    except Exception:
                        net = []
                    cmp_obj = {
                        "computedTokens": toks,
                        "computedConsent": consent,
                        "network": net
                    }
                    try:
                        with open("conn4_compare_selenium.json", "w", encoding="utf-8") as f:
                            json.dump(cmp_obj, f, ensure_ascii=False, indent=2)
                    except Exception:
                        pass
                try:
                    tester.driver.quit()
                except Exception:
                    pass
                sys.exit(0)
            except Exception:
                try:
                    tester.driver.quit()
                except Exception:
                    pass
                sys.exit(1)
        success = tester.run_test()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
        tester.cleanup()
        sys.exit(1)
        

def _save_mcp_artifacts(self, ordered):
        try:
            try:
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            except Exception:
                project_root = os.getcwd()
            base_dir = os.environ.get("MCP_ARTIFACTS_DIR") or os.path.join(project_root, "mcp_artifacts", "conn4_selenium")
            try:
                meta = ordered.get("meta") or {}
            except Exception:
                meta = {}
            ts = None
            try:
                ts = meta.get("timestamp")
            except Exception:
                ts = None
            if isinstance(ts, (int, float)):
                label = time.strftime("%Y%m%d_%H%M%S", time.localtime(ts))
            else:
                label = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            run_id = f"{label}_{os.getpid()}"
            run_dir = os.path.join(base_dir, run_id)
            os.makedirs(run_dir, exist_ok=True)
            artifacts = [
                "conn4_master.json",
                "conn4_portal_page.png",
                "conn4_session_storage_trace.json",
                "conn4_debug_before_auth.json",
                "conn4_debug_after_inject.json",
                "conn4_debug_success.json",
                "conn4_debug_fail.json",
                "conn4_assets.json",
                "conn4_schema.json",
                "conn4_compare.json",
                "conn4_compare_selenium.json",
                "conn4_network.json",
                "conn4_selenium_debug.log",
            ]
            saved = []
            for name in artifacts:
                try:
                    if os.path.exists(name):
                        dst = os.path.join(run_dir, name)
                        shutil.copy2(name, dst)
                        saved.append(name)
                except Exception:
                    pass
            index = {
                "created_at": time.time(),
                "run_id": run_id,
                "artifacts": saved,
                "meta": meta,
                "request": ordered.get("Request"),
            }
            try:
                idx_path = os.path.join(run_dir, "index.json")
                with open(idx_path, "w", encoding="utf-8") as f:
                    json.dump(index, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            try:
                self.logger.info(f"MCP артефакты сохранены: {run_dir}")
            except Exception:
                pass
        except Exception:
            pass


def _save_master_report(self):
        """Собирает мастер-отчёт: nojs_plan, сеть, токены, ассеты, время и метаданные окружения."""
        report = {"plan_md": "", "nojs_plan": [], "meta": {}, "debug": {}, "network": [], "schema": {}, "compare": {}, "assets": {}, "time_sources": [], "time_initiators": []}
        try:
            report["meta"] = {
                "timestamp": time.time(),
                "env": {"NOJS_SOCKS_PORT": os.environ.get("NOJS_SOCKS_PORT"), "OPENWRT_SSH_HOST": os.environ.get("OPENWRT_SSH_HOST"), "OPENWRT_SSH_USER": os.environ.get("OPENWRT_SSH_USER")}
            }
        except Exception:
            pass
        # debug
        try:
            dbg = {}
            try:
                dbg["current_url"] = self._current_url_sanitized()
            except Exception:
                dbg["current_url"] = None
            try:
                dbg["pre_click_url"] = self.pre_click_url
            except Exception:
                dbg["pre_click_url"] = None
            try:
                dbg["title"] = self.driver.title
            except Exception:
                dbg["title"] = None
            try:
                dbg["capturedRequests"] = self.driver.execute_script("return window.__capturedRequests || []")
            except Exception:
                dbg["capturedRequests"] = []
            try:
                dbg["traceLog"] = self.driver.execute_script("return window.__traceLog || []")
            except Exception:
                dbg["traceLog"] = []
            try:
                cs = self.driver.get_cookies() or []
                filt = []
                for c in cs:
                    try:
                        d = (c.get("domain") or "").lower()
                        if ("conn4.com" in d) or ("rdr.conn4.com" in d):
                            filt.append(c)
                    except Exception:
                        pass
                dbg["cookies"] = filt
            except Exception:
                dbg["cookies"] = []
            try:
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                submit_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
                button_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='button']")
                checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                scripts = self.driver.find_elements(By.TAG_NAME, "script")
                dbg["domCounts"] = {
                    "inputs": len(inputs),
                    "buttons": len(buttons),
                    "submit_inputs": len(submit_inputs),
                    "button_inputs": len(button_inputs),
                    "checkboxes": len(checkboxes),
                    "scripts": len(scripts)
                }
            except Exception:
                dbg["domCounts"] = {}
            try:
                frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                srcs = []
                for fr in frames:
                    try:
                        s = fr.get_attribute("src") or ""
                        sl = s.lower()
                        if ("conn4.com" in sl) or ("rdr.conn4.com" in sl) or ("msftconnecttest.com" in sl) or ("captive.apple.com" in sl) or ("connectivitycheck.gstatic.com" in sl):
                            srcs.append(s)
                    except Exception:
                        pass
                dbg["iframes"] = srcs
            except Exception:
                dbg["iframes"] = []
            try:
                dbg["page_html"] = self.driver.page_source or ""
            except Exception:
                dbg["page_html"] = ""
            dbg["portal_frame_index"] = self.portal_frame_index
            try:
                dbg["formSubmits"] = self.driver.execute_script("return window.__formSubmits || []")
            except Exception:
                dbg["formSubmits"] = []
            report["debug"] = dbg
        except Exception:
            pass
        # network (raw)
        try:
            net_events = self._collect_network_events()
            def _evt_url(e):
                try:
                    if isinstance(e.get("url"), str):
                        return e.get("url")
                except Exception:
                    pass
                try:
                    rq = e.get("request") or {}
                    if isinstance(rq.get("url"), str):
                        return rq.get("url")
                except Exception:
                    pass
                try:
                    rp = e.get("response") or {}
                    if isinstance(rp.get("url"), str):
                        return rp.get("url")
                except Exception:
                    pass
                return None
            if net_events:
                filt = []
                for e in net_events:
                    u = (_evt_url(e) or "").lower()
                    if ("conn4.com" in u) or ("rdr.conn4.com" in u) or ("msftconnecttest.com" in u) or ("captive.apple.com" in u) or ("connectivitycheck.gstatic.com" in u):
                        filt.append(e)
                report["network"] = filt
            else:
                try:
                    with open("conn4_network.json","r",encoding="utf-8") as f:
                        obj = json.load(f)
                        ev = obj.get("events") or []
                        filt = []
                        for e in ev:
                            u = ((_evt_url(e) or "")).lower()
                            if ("conn4.com" in u) or ("rdr.conn4.com" in u) or ("msftconnecttest.com" in u) or ("captive.apple.com" in u) or ("connectivitycheck.gstatic.com" in u):
                                filt.append(e)
                        report["network"] = filt
                except Exception:
                    report["network"] = []
        except Exception:
            report["network"] = []
        # assets
        try:
            report["assets"] = self._enumerate_assets_and_large_js_scan() or {}
        except Exception:
            report["assets"] = {}
        # schema
        try:
            perf_logs = self.driver.get_log('performance') or []
            events = normalize_perf_logs(perf_logs)
        except Exception:
            events = []
        try:
            bodies = self._collect_js_bodies()
        except Exception:
            bodies = []
        try:
            cookies = self.driver.get_cookies() or []
        except Exception:
            cookies = []
        try:
            schema = build_schema(report["debug"].get("page_html") or "", report["debug"].get("current_url") or "", events, bodies, cookies)
            report["schema"] = schema or {}
        except Exception:
            report["schema"] = {}
        # compare and plan
        try:
            with open("conn4_compare.json", "r", encoding="utf-8") as f:
                compare_data = json.load(f)
        except Exception:
            compare_data = {}

        if compare_data:
            report["compare"] = compare_data
            tokens = compare_data.get("computedTokens") or {}
            consent = compare_data.get("computedConsent") or {}
        else:
            try:
                tokens = self._nojs_collect_tokens(report["debug"].get("page_html") or "")
                # Если fallback, попробуем pre_click_tokens
                if self.pre_click_tokens:
                    for k, v in self.pre_click_tokens.items():
                        if v is not None and (k not in tokens or not tokens[k]):
                            tokens[k] = v
            except Exception:
                tokens = {}
            try:
                consent = self._nojs_build_consent_body(tokens)
            except Exception:
                consent = {}
            try:
                report["compare"] = {"computedTokens": tokens, "computedConsent": consent, "network": report["network"]}
            except Exception:
                report["compare"] = {}
        try:
            cur = urlparse(report["debug"].get("current_url") or "")
            base_scheme = cur.scheme or "https"
            base_host = cur.netloc or (self._resolve_portal_host() or "")
            base = f"{base_scheme}://{base_host}" if base_host else None
        except Exception:
            base = None
        create_body = None
        try:
            if base:
                site_id = tokens.get("siteId") or tokens.get("site_id") or "1096"
                client_ip = tokens.get("clientIp") or tokens.get("client_ip")
                client_mac = tokens.get("clientMac") or tokens.get("client_mac")
                wbs = self._create_wbs_api_auth_token(site_id, client_ip, client_mac)
                if wbs:
                    create_body = {
                        "session_id": "",
                        "with-tariffs": "1",
                        "locationId": str(site_id),
                        "locale": tokens.get("locale") or tokens.get("portalLocale") or "en_US",
                        "authorization": f"token={wbs}"
                    }
        except Exception:
            create_body = None
        plan = []
        try:
            plan.append({"name": "msftconnecttest redirect", "method": "GET", "url": "http://www.msftconnecttest.com/redirect"})
        except Exception:
            pass
        if base:
            plan.append({"name": "portal base", "method": "GET", "url": base})
            plan.append({"name": "portal time check", "method": "GET", "url": f"{base}/_time"})
            try:
                if create_body:
                    plan.append({"name": "create-session", "method": "POST", "url": f"{base}/wbs/api/v1/create-session/", "body": create_body})
            except Exception:
                pass
        try:
            ident_url = self._build_ident_url(tokens)
            if ident_url:
                plan.append({"name": "ident", "method": "GET", "url": ident_url})
        except Exception:
            pass
        try:
            rid_url = self._build_redirect_ident_url(tokens)
            if rid_url:
                plan.append({"name": "ident.php", "method": "GET", "url": rid_url})
        except Exception:
            pass
        try:
            extra_time = set()
            for src in report.get("time_sources") or []:
                for u in src.get("refs") or []:
                    if isinstance(u, str) and ("/_time" in u or "/time/" in u):
                        extra_time.add(u)
            base_time = f"{base}/_time" if base else None
            for u in sorted(extra_time):
                if not base_time or u != base_time:
                    plan.append({"name": "time endpoint", "method": "GET", "url": u})
        except Exception:
            pass
        try:
            big_js = (report.get("assets") or {}).get("big_js")
            if big_js:
                plan.append({"name": "portal big js", "method": "GET", "url": big_js})
        except Exception:
            pass
        try:
            cc_seen = set()
            for e in report.get("network") or []:
                u = (_evt_url(e) or "") or ""
                if "cookie-challenge" not in u.lower():
                    continue
                if u in cc_seen:
                    continue
                cc_seen.add(u)
                plan.append({"name": "cookie-challenge", "method": "GET", "url": u})
        except Exception:
            pass
        try:
            if base:
                body = consent or {}
                plan.append({"name": "login free", "method": "POST", "url": f"{base}/wbs/api/v1/login/free/", "body": body})
        except Exception:
            pass
        try:
            prx = tokens.get("paymentReturnProxyUrl")
            if prx:
                plan.append({"name": "paymentReturnProxyUrl", "method": "GET", "url": prx})
        except Exception:
            pass
        try:
            report["nojs_plan"] = plan
            lines = []
            for i, step in enumerate(plan, 1):
                method = step.get("method") or "GET"
                url = step.get("url") or ""
                lines.append(f"{i}. [{method}] {url}")
            report["plan_md"] = "# NoJS План запроса\n" + "\n".join(lines)
        except Exception:
            pass
        # time sources and initiators
        try:
            report["time_sources"] = self._collect_time_sources() or []
        except Exception:
            report["time_sources"] = []
        try:
            report["time_initiators"] = self._collect_time_initiators() or []
        except Exception:
            report["time_initiators"] = []
        # write with explicit ordering: Request first, then plan
        try:
            try:
                from collections import OrderedDict
            except Exception:
                OrderedDict = dict
            req_num = 0
            try:
                net = report.get("network") or []
                if net:
                    # номер по списку запросов: первый релевантный Network.requestWillBeSent
                    idx = 0
                    for i, e in enumerate(net):
                        if (e.get("event") or "") == "Network.requestWillBeSent":
                            idx = i
                            break
                    req_num = idx + 1
            except Exception:
                req_num = 0
            def _evt_url(e):
                try:
                    if isinstance(e.get("url"), str):
                        return e.get("url")
                except Exception:
                    pass
                try:
                    rq = e.get("request") or {}
                    if isinstance(rq.get("url"), str):
                        return rq.get("url")
                except Exception:
                    pass
                try:
                    rp = e.get("response") or {}
                    if isinstance(rp.get("url"), str):
                        return rp.get("url")
                except Exception:
                    pass
                return None
            allowed_hosts = ("conn4.com","rdr.conn4.com","msftconnecttest.com","captive.apple.com","connectivitycheck.gstatic.com")
            filtered_net = []
            for e in (report.get("network") or []):
                u = (_evt_url(e) or "").lower()
                if any(h in u for h in allowed_hosts):
                    filtered_net.append(e)
            # пере-счёт Request по отфильтрованной сети
            req_num = 0
            for i, e in enumerate(filtered_net):
                if (e.get("event") or "") == "Network.requestWillBeSent":
                    req_num = i + 1
                    break
            # санитизация current_url
            dbg = report.get("debug") or {}
            try:
                dbg["current_url"] = self._current_url_sanitized()
            except Exception:
                pass
            ordered = OrderedDict()
            ordered["Request"] = req_num
            ordered["plan_md"] = report.get("plan_md")
            ordered["nojs_plan"] = report.get("nojs_plan")
            ordered["debug"] = dbg
            ordered["network"] = filtered_net
            ordered["compare"] = report.get("compare")
            ordered["schema"] = report.get("schema")
            ordered["assets"] = report.get("assets")
            ordered["time_sources"] = report.get("time_sources")
            ordered["time_initiators"] = report.get("time_initiators")
            ordered["meta"] = report.get("meta")
            try:
                ordered["step_diffs"] = self._stepwise_compare(ordered)
                try:
                    self.logger.info(f"Расхождения по шагам: {len(ordered['step_diffs'] or [])}")
                    for d in (ordered["step_diffs"] or [])[:10]:
                        self.logger.info(json.dumps(d, ensure_ascii=False))
                except Exception:
                    pass
            except Exception:
                ordered["step_diffs"] = []
            with open("conn4_master.json","w",encoding="utf-8") as f:
                json.dump(ordered, f, ensure_ascii=False, indent=2)
            self.logger.info("Сводный отчёт сохранён: conn4_master.json")
            try:
                _save_mcp_artifacts(self, ordered)
            except Exception:
                pass
        except Exception:
            pass


if __name__ == "__main__":
    main()

    def _collect_js_bodies(self):
        bodies = []
        try:
            logs = []
            try:
                logs = self.driver.get_log('performance') or []
            except Exception:
                logs = []
            for entry in logs:
                try:
                    msg = json.loads(entry.get('message') or '{}')
                    m = msg.get('message') or {}
                    if m.get('method') == 'Network.responseReceived':
                        p = m.get('params') or {}
                        t = (p.get('type') or '').lower()
                        mime = ((p.get('response') or {}).get('mimeType') or '').lower()
                        if t in ('script', 'xhr') or ('javascript' in mime):
                            rid = p.get('requestId')
                            url = (p.get('response') or {}).get('url') or (p.get('response') or {}).get('urlFragment') or ''
                            if rid:
                                try:
                                    body_obj = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': rid})
                                    b = body_obj.get('body') or ''
                                    if body_obj.get('base64Encoded'):
                                        try:
                                            b = base64.b64decode(b).decode('utf-8', 'replace')
                                        except Exception:
                                            b = ''
                                    if b:
                                        bodies.append((url, b))
                                except Exception:
                                    pass
                except Exception:
                    pass
        except Exception:
            pass
        return bodies
    
    def dump_js_bodies(self, label=""):
        try:
            out_dir = os.path.join(os.getcwd(), "conn4_js")
            os.makedirs(out_dir, exist_ok=True)
            bodies = self._collect_js_bodies()
            for i, (url, body) in enumerate(bodies or []):
                try:
                    fn = f"{label}_{i}.js" if label else f"script_{i}.js"
                    if url:
                        try:
                            p = urlparse(url)
                            base = (p.netloc or "conn4") + (p.path or "")
                            base = re.sub(r"[\\/]+", "_", base)
                            if base.lower().endswith(".js"):
                                fn = base
                        except Exception:
                            pass
                    with open(os.path.join(out_dir, fn), "w", encoding="utf-8") as wf:
                        wf.write(body or "")
                except Exception:
                    pass
            return True
        except Exception:
            return False

    def collect_static_resource_urls_without_js(self):
        urls = set()
        try:
            html = self.driver.page_source or ""
            base = base_origin_from_url(self.driver.current_url or "")
            for u in extract_resource_urls_from_html(html, base):
                urls.add(u)
        except Exception:
            pass
        try:
            base = base_origin_from_url(self.driver.current_url or "")
            for _, body in self._collect_js_bodies():
                for u in extract_urls_from_js_text(body, base):
                    urls.add(u)
        except Exception:
            pass
        result = sorted(list(urls))
        try:
            self.logger.info(f"[static parse] urls={len(result)}")
            for u in result[:50]:
                self.logger.info(f"[static] {u}")
        except Exception:
            pass
        return result

    def _save_js_time_sources(self):
        idx = self._collect_time_sources()
        try:
            with open("conn4_js_time_sources.json","w",encoding="utf-8") as f:
                json.dump({"items": idx}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _save_time_initiators(self):
        items = self._collect_time_initiators()
        try:
            with open("conn4_time_initiators.json","w",encoding="utf-8") as f:
                json.dump({'items': items}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _collect_time_sources(self):
        idx = []
        try:
            base = base_origin_from_url(self.driver.current_url or "")
        except Exception:
            base = ""
        try:
            bodies = self._collect_js_bodies()
        except Exception:
            bodies = []
        try:
            for url, body in bodies or []:
                refs = []
                try:
                    for m in re.finditer(r"(/_time(?:\\?[^'\"\\s]*)?)", body or "", flags=re.IGNORECASE):
                        u = m.group(1)
                        p = urlparse(u)
                        refs.append(f"{base}{u}" if not p.scheme else u)
                    for m in re.finditer(r"(/time/[^'\"\\s]+)", body or "", flags=re.IGNORECASE):
                        u = m.group(1)
                        p = urlparse(u)
                        refs.append(f"{base}{u}" if not p.scheme else u)
                except Exception:
                    refs = []
                if refs:
                    idx.append({"script": url, "refs": list(dict.fromkeys(refs))})
        except Exception:
            pass
        return idx
    
    def _collect_time_initiators(self):
        items = []
        try:
            logs = self.driver.get_log('performance') or []
        except Exception:
            logs = []
        try:
            for entry in logs:
                try:
                    msg = json.loads(entry.get('message') or '{}')
                    m = msg.get('message') or {}
                    if m.get('method') == 'Network.requestWillBeSent':
                        p = m.get('params') or {}
                        url = (p.get('request') or {}).get('url') or p.get('documentURL') or ''
                        if '/_time' in (url or ''):
                            init = p.get('initiator') or {}
                            stack = (init.get('stack') or {}).get('callFrames') or init.get('stackTrace') or []
                            frames = []
                            try:
                                for fr in stack or []:
                                    u = (fr.get('url') if isinstance(fr, dict) else None) or ''
                                    if u:
                                        frames.append(u)
                            except Exception:
                                frames = []
                            items.append({'url': url, 'initiators': list(dict.fromkeys(frames))})
                except Exception:
                    pass
        except Exception:
            pass
        return items

    def _save_conn4_schema(self):
        try:
            html = self.driver.page_source or ""
        except Exception:
            html = ""
        try:
            current = self.driver.current_url or ""
        except Exception:
            current = ""
        try:
            perf_logs = self.driver.get_log('performance') or []
        except Exception:
            perf_logs = []
        try:
            events = normalize_perf_logs(perf_logs)
        except Exception:
            events = []
        try:
            bodies = self._collect_js_bodies()
        except Exception:
            bodies = []
        try:
            cookies = self.driver.get_cookies() or []
        except Exception:
            cookies = []
        try:
            schema = build_schema(html, current, events, bodies, cookies)
        except Exception:
            schema = {}
        try:
            with open("conn4_schema.json","w",encoding="utf-8") as f:
                json.dump(schema, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
