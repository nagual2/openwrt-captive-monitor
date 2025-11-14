#!/usr/bin/env python3

import base64
import json
import os
import sys

def main():
    # Read token from environment variable
    token = os.environ.get("OIDC_TOKEN")
    if not token:
        print("Error: OIDC_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Split the token and decode the payload
        segments = token.split('.')
        if len(segments) < 2:
            print("Error: Invalid token structure", file=sys.stderr)
            sys.exit(1)
            
        payload_segment = segments[1]
        # Add padding if needed
        padding = '=' * (-len(payload_segment) % 4)
        payload = base64.urlsafe_b64decode((payload_segment + padding).encode()).decode()
        claims = json.loads(payload)
        
        # Print the claims we're interested in
        print(f"OIDC issuer: {claims.get('iss')}")
        print(f"OIDC subject: {claims.get('sub')}")
        print(f"OIDC audience: {claims.get('aud')}")
        
    except Exception as e:
        print(f"Error processing token: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
