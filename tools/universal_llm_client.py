#!/usr/bin/env python3
"""
Universal LLM CLI Client - поддержка MegaLLM и Z.AI
Использование: python universal_llm_client.py --provider zai --model glm-4.7-flash --prompt "Your question"
"""

import os
import sys
import json
import argparse
from typing import Optional
import urllib.request
import urllib.error


class UniversalLLMClient:
    PROVIDERS = {
        "megallm": {
            "base_url": "https://ai.megallm.io/v1",
            "env_key": "MEGALLM_API_KEY",
            "default_model": "mistralai/mistral-nemotron"
        },
        "zai": {
            "base_url": "https://api.z.ai/api/paas/v4",
            "env_key": "ZAI_API_KEY",
            "default_model": "glm-4.7-flash"
        }
    }
    
    def __init__(self, provider: str = "zai", api_key: Optional[str] = None):
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}. Available: {list(self.PROVIDERS.keys())}")
        
        self.provider = provider
        self.config = self.PROVIDERS[provider]
        self.api_key = api_key or os.getenv(self.config["env_key"])
        
        if not self.api_key:
            raise ValueError(f"{self.config['env_key']} not found in environment")
    
    def list_models(self) -> list:
        """Получить список доступных моделей"""
        url = f"{self.config['base_url']}/models"
        
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
    
    def chat(self, prompt: str, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Отправить запрос к LLM API"""
        model = model or self.config["default_model"]
        url = f"{self.config['base_url']}/chat/completions"
        
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
    parser = argparse.ArgumentParser(description="Universal LLM CLI Client")
    parser.add_argument("--provider", default="zai", choices=["megallm", "zai"], 
                       help="LLM provider (default: zai)")
    parser.add_argument("--model", help="Model ID (default: provider-specific)")
    parser.add_argument("--prompt", help="Prompt text")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature (default: 0.7)")
    parser.add_argument("--max-tokens", type=int, default=2000, help="Max tokens (default: 2000)")
    parser.add_argument("--stdin", action="store_true", help="Read prompt from stdin")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    
    args = parser.parse_args()
    
    try:
        client = UniversalLLMClient(provider=args.provider)
        
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
