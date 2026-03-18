#!/usr/bin/env python3
import hashlib
import base64
from urllib.parse import unquote
from datetime import datetime

class PhpSerializer:
    @staticmethod
    def serialize(data):
        """Простая реализация PHP сериализации"""
        if data is None:
            return "N;"
        elif isinstance(data, bool):
            return f"b:{1 if data else 0};"
        elif isinstance(data, int):
            return f"i:{data};"
        elif isinstance(data, float):
            return f"d:{data};"
        elif isinstance(data, str):
            # Handle null bytes explicitly if they are passed in the string
            # In python source code, \0 is a null byte.
            return f's:{len(data)}:"{data}";'
        elif isinstance(data, dict):
            # Проверяем, является ли это представлением объекта
            if "__classname__" in data:
                classname = data["__classname__"]
                props = data.get("__props__", {})
                out = f'O:{len(classname)}:"{classname}":{len(props)}:{{'
                for k, v in props.items():
                    out += PhpSerializer.serialize(k) + PhpSerializer.serialize(v)
                out += "}"
                return out
            else:
                out = f"a:{len(data)}:{{"
                for k, v in data.items():
                    out += PhpSerializer.serialize(k) + PhpSerializer.serialize(v)
                out += "}}"
                return out
        return "N;"

class WbsTokenBuilder:
    @staticmethod
    def build_token_object(site_id, client_ip, client_mac, created_datetime=None, classname="M3\\Himalaya\\Shared\\WBSApiAuth\\Token"):
        """
        Создает структуру словаря, которая при сериализации превратится 
        в объект M3\\Himalaya\\Shared\\WBSApiAuth\\Token (или другой указанный)
        """
        if not created_datetime:
            created_datetime = datetime.utcnow()
            
        date_str = created_datetime.strftime("%Y-%m-%d %H:%M:%S.000000")
        
        # Структура DateTime объекта PHP
        date_obj = {
            "__classname__": "DateTime",
            "__props__": {
                "date": date_str,
                "timezone_type": 3,
                "timezone": "UTC"
            }
        }
        
        # Структура Token объекта
        # Свойства protected, поэтому ключи должны начинаться с \0*\0
        # Note: SiteIdent token uses "MACAddress" (PascalCase) while WBSApiAuth might use "macAddress" (camelCase)
        # We might need to adjust property names based on classname?
        # For now, keeping as is.
        token_props = {
            "\0*\0siteId": int(site_id) if site_id else 0,
            "\0*\0remoteAddress": client_ip or "127.0.0.1",
            "\0*\0macAddress": client_mac or "",
            "\0*\0deviceId": None,
            "\0*\0created": date_obj,
            "\0*\0origin": f"https://{site_id}.rdr.conn4.com" if site_id else "https://rdr.conn4.com"
        }
        
        return {
            "__classname__": classname,
            "__props__": token_props
        }

    @staticmethod
    def generate_token_string(site_id, client_ip, client_mac, secret_key=""):
        """
        Генерирует полную строку токена (Base64 от serialized|signature)
        Примечание: secret_key нам неизвестен, поэтому подпись будет невалидной 
        для сервера, если он проверяет её. Но мы эмулируем структуру.
        """
        token_obj = WbsTokenBuilder.build_token_object(site_id, client_ip, client_mac)
        serialized_data = PhpSerializer.serialize(token_obj)
        
        # Подпись (эмуляция)
        # В реальности подпись = hash_hmac('sha256', serialized_data, secret)
        # Если секрет пустой, просто хешируем данные или используем placeholder
        if secret_key:
            signature = hashlib.sha256((serialized_data + secret_key).encode('utf-8')).hexdigest()
        else:
            # Placeholder, похожий на настоящий (64 chars hex)
            signature = hashlib.sha256(serialized_data.encode('utf-8')).hexdigest()
            
        raw_payload = f"{serialized_data}|{signature}"
        return base64.b64encode(raw_payload.encode('utf-8')).decode('utf-8')

    @staticmethod
    def generate_wbs_token_from_site_ident(site_ident_cookie, site_id, client_ip, client_mac):
        """
        Генерирует wbsApiAuthToken, используя подпись (хеш) из cookie himalaya-site-ident.
        Формат токена: HWA*<serialized_object>|<hash_from_cookie>
        """
        if not site_ident_cookie:
            return None
            
        try:
            # 1. Decode cookie to get the hash
            # Cookie format: HSI*<serialized>|<hash> (Base64 encoded)
            s = unquote(site_ident_cookie)
            pad = "=" * ((4 - len(s) % 4) % 4)
            decoded_cookie = base64.b64decode(s + pad).decode('utf-8', 'replace')
            
            if "|" not in decoded_cookie:
                return None
                
            existing_hash = decoded_cookie.split("|")[-1]
            if not existing_hash:
                return None

            # 2. Build new token object
            token_obj = WbsTokenBuilder.build_token_object(int(site_id or 0), client_ip or "127.0.0.1", client_mac or "")
            serialized = PhpSerializer.serialize(token_obj)
            
            # 3. Construct new payload with HWA* prefix and existing hash
            full_str = f"HWA*{serialized}|{existing_hash}"
            
            # 4. Encode back to Base64
            return base64.b64encode(full_str.encode("utf-8")).decode("ascii")
            
        except Exception as e:
            print(f"Error generating token from cookie: {e}")
            return None
