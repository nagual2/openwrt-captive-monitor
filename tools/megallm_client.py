#!/usr/bin/env python3
"""
MegaLLM CLI Client - консольный агент для доступа к MegaLLM API
Использование: python megallm_client.py --model gpt-4o-mini --prompt "Your question"
"""

import os
import sys
import json
import argparse
from typing import Optional
import urllib.request
import urllib.error


class MegaLLMClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://ai.megallm.io/v1"):
        self.api_key = api_key or os.getenv("MEGALLM_API_KEY")
        if not self.api_key:
            raise ValueError("MEGALLM_API_KEY not found in environment")
        self.base_url = base_url
    
    def list_models(self) -> list:
        """Получить список доступных моделей"""
        url = f"{self.base_url}/models"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            req = urllib.request.Request(url, headers=headers, method='GET')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('data', [])
        
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"HTTP {e.code}: {error_body}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def chat(self, prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Отправить запрос к MegaLLM API"""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"HTTP {e.code}: {error_body}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="MegaLLM CLI Client")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model ID (default: gpt-4o-mini)")
    parser.add_argument("--prompt", help="Prompt text")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature (default: 0.7)")
    parser.add_argument("--max-tokens", type=int, default=2000, help="Max tokens (default: 2000)")
    parser.add_argument("--stdin", action="store_true", help="Read prompt from stdin")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    
    args = parser.parse_args()
    
    try:
        client = MegaLLMClient()
        
        # Список моделей
        if args.list_models:
            models = client.list_models()
            print(json.dumps(models, indent=2, ensure_ascii=False))
            return
        
        # Получить промпт
        if args.stdin:
            prompt = sys.stdin.read().strip()
        elif args.prompt:
            prompt = args.prompt
        else:
            print("Error: Provide --prompt or --stdin", file=sys.stderr)
            sys.exit(1)
        
        response = client.chat(
            prompt=prompt,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens
        )
        print(response)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
