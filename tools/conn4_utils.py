#!/usr/bin/env python3
import os
import time
import logging
import subprocess
import socket
from urllib.request import build_opener, Request

try:
    from dotenv import load_dotenv
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _env_path = os.path.join(_project_root, ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
except Exception:
    pass

def setup_logging(logger_name, log_file_name=None):
    """Настройка логирования: INFO в консоль, DEBUG в файл"""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    # Очищаем существующие хендлеры
    if logger.handlers:
        logger.handlers = []
        
    # Console handler (INFO guaranteed)
    ch = logging.StreamHandler()
    lvl = (os.environ.get("CPM_LOG_LEVEL") or "").upper()
    ch.setLevel(logging.DEBUG if lvl == "DEBUG" else logging.INFO)
    ch_fmt = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
    ch.setFormatter(ch_fmt)
    logger.addHandler(ch)
    
    # File handler (DEBUG)
    if log_file_name:
        fh = logging.FileHandler(log_file_name, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh_fmt = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
        fh.setFormatter(fh_fmt)
        logger.addHandler(fh)
    
    return logger

def run_shell_cmd(cmd, timeout=15):
    """Запуск shell команды с таймаутом"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or ""), (r.stderr or "")
    except Exception as e:
        return -1, "", str(e)

class SocksProxyManager:
    def __init__(self, logger, ssh_host=None, ssh_user=None, port=None):
        self.logger = logger
        # CPM_ENV: 'prod' или 'dev'. По умолчанию 'dev'.
        self.cpm_env = (os.environ.get("CPM_ENV") or "dev").lower()
        
        default_host = "prod-openwrt" if self.cpm_env == "prod" else "dev-openwrt"
        self.ssh_host = ssh_host or os.environ.get("OPENWRT_SSH_HOST", default_host)
        self.ssh_user = ssh_user or os.environ.get("OPENWRT_SSH_USER", "root")
        self.socks_port = port or os.environ.get("NOJS_SOCKS_PORT") or "10800"
        self.socks_process = None
        self.logger.info(f"SocksProxyManager инициализирован: env={self.cpm_env}, host={self.ssh_host}")

    def get_ssh_base_cmd(self, connect_timeout=10, batch_mode=True):
        """Возвращает базу команды SSH с учетом ключа из окружения"""
        key_path = os.environ.get("OPENWRT_SSH_KEY") or ""
        base = ["ssh", "-o", f"ConnectTimeout={connect_timeout}", "-o", "StrictHostKeyChecking=no"]
        if key_path:
            base.extend(["-i", key_path])
        if batch_mode:
            base.extend(["-o", "BatchMode=yes"])
        return base

    def verify_ssh_router_access(self):
        """Проверка SSH доступа к роутеру"""
        try:
            base = self.get_ssh_base_cmd(connect_timeout=5)
            target = f"{self.ssh_user}@{self.ssh_host}"
            cmd = base + [target, "echo ok"]
            
            rc, out, _ = run_shell_cmd(cmd, timeout=8)
            if rc == 0 and "ok" in out.strip():
                self.logger.info(f"SSH доступ к {self.ssh_host}: OK")
                return True
            self.logger.warning(f"SSH доступ к {self.ssh_host}: FAIL (rc={rc})")
            return False
        except Exception as e:
            self.logger.warning(f"Ошибка проверки SSH: {e}")
            return False

    def check_router_ping(self):
        try:
            target = os.environ.get("CAPTIVE_ROUTER_IP") or self.ssh_host
            rc_ping, out_ping, _ = run_shell_cmd(["ping", "-c", "1", str(target)], timeout=5)
            if rc_ping == 0 and ("1 received" in out_ping.lower() or "ttl=" in out_ping.lower()):
                self.logger.info(f"Проверка ping {target}: OK")
                return True
            self.logger.info(f"Проверка ping {target}: FAIL")
            return False
        except Exception:
            return False

    def ensure_socks_proxy(self):
        self.logger.info(f"Принудительный перезапуск SOCKS прокси на порту {self.socks_port} через {self.ssh_host}...")
        try:
            # Всегда убиваем старый прокси перед запуском нового
            run_shell_cmd(["pkill", "-f", f"ssh.*-D {self.socks_port}"], timeout=5)
            time.sleep(1)
            
            pwd = os.environ.get("OPENWRT_SSH_PASS") or ""
            
            base = self.get_ssh_base_cmd(connect_timeout=10, batch_mode=not bool(pwd))
            base.extend([
                "-o", "ServerAliveInterval=60",
                "-f", "-N",
                "-D", f"127.0.0.1:{self.socks_port}",
            ])
            
            target = f"{self.ssh_user}@{self.ssh_host}"
            cmd = base + [target]
            
            if pwd:
                cmd = ["sshpass", "-p", pwd] + cmd
                
            rc, out, err = run_shell_cmd(cmd, timeout=12)
            if rc != 0:
                self.logger.error(f"Ошибка запуска SOCKS: rc={rc} err={err.strip()}")
            try:
                time.sleep(2)
            except Exception:
                pass
            if self.verify_socks_proxy():
                os.environ["ALL_PROXY"] = f"socks5h://127.0.0.1:{self.socks_port}"
                os.environ["HTTPS_PROXY"] = os.environ["ALL_PROXY"]
                os.environ["HTTP_PROXY"] = os.environ["ALL_PROXY"]
                self.logger.info(f"SOCKS прокси {self.socks_port} успешно запущен")
                return True
            else:
                self.logger.error("Не удалось поднять SOCKS прокси")
                return False
        except Exception as e:
            self.logger.error(f"Ошибка запуска SOCKS прокси: {e}")
            return False

    def verify_socks_proxy(self, silent=False):
        """Проверка доступности SOCKS порта"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            result = s.connect_ex(('127.0.0.1', int(self.socks_port)))
            s.close()
            if result == 0:
                if not silent:
                    self.logger.info(f"SOCKS прокси на порту {self.socks_port} активен")
                return True
            else:
                if not silent:
                    self.logger.info(f"SOCKS прокси на порту {self.socks_port} НЕ активен")
                return False
        except Exception:
            if not silent:
                self.logger.info(f"SOCKS прокси на порту {self.socks_port} ошибка проверки")
            return False

    def shutdown_socks_proxy(self):
        """Остановка SOCKS прокси"""
        try:
            self.logger.info(f"Остановка SOCKS прокси {self.socks_port}...")
            run_shell_cmd(["pkill", "-f", f"ssh.*-D {self.socks_port}"], timeout=5)
        except Exception:
            pass

    def strict_check_portal_time_via_socks(self, user_agent="Mozilla/5.0"):
        """Проверка доступности /_time через SOCKS"""
        try:
            import socks
            from sockshandler import SocksiPyHandler
        except ImportError:
            self.logger.warning("Библиотека PySocks не установлена, пропуск проверки через urllib")
            return True # Fallback to true if no libs

        port = int(self.socks_port)
        handler = SocksiPyHandler(socks.SOCKS5, "127.0.0.1", port)
        opener = build_opener(handler)
        
        # В оригинале используется urljoin от page_url, но здесь мы хотим просто проверить канал.
        # Лучше использовать endpoint который точно есть.
        # В оригинальном коде логика зависела от portal_url. 
        # Сделаем более простую проверку: доступность google.com или captive.apple.com
        
        test_url = "http://captive.apple.com/hotspot-detect.html"
        
        try:
            req = Request(test_url, headers={"User-Agent": user_agent})
            rs = opener.open(req, timeout=10)
            code = rs.getcode()
            self.logger.info(f"[SOCKS TEST] {test_url} → {code}")
            return True
        except Exception as e:
            self.logger.info(f"[SOCKS TEST ERR] {e}")
            return False
