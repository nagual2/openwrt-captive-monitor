#!/bin/sh

# Config
TEST_URL="http://www.msftconnecttest.com/redirect"
PORTAL_TRIGGER_URL="http://www.msftconnecttest.com/redirect"
COOKIE_FILE="/tmp/conn4_cookies.txt"
LOG_TAG="conn4_auth"
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
    logger -t "$LOG_TAG" "$1"
}

# --- DNS Resolution Helpers ---
get_dns_servers() {
    # Try to get DNS from wwan interface via ubus
    if command -v ubus >/dev/null && command -v jsonfilter >/dev/null; then
        # Extract DNS servers array from wwan status
        ubus call network.interface.wwan status 2>/dev/null | jsonfilter -e '@["dns-server"][*]'
    fi
}

# Detect WWAN Device for curl binding
if command -v ubus >/dev/null && command -v jsonfilter >/dev/null; then
    WWAN_DEVICE=$(ubus call network.interface.wwan status 2>/dev/null | jsonfilter -e '@["l3_device"]')
    WWAN_IP=$(ubus call network.interface.wwan status 2>/dev/null | jsonfilter -e '@["ipv4-address"][0].address')
fi

resolve_host() {
    HOST=$1
    DNS_LIST=$(get_dns_servers)
    
    # If no specific DNS from wwan, we cannot enforce the requirement.
    # Return empty to let curl fail or fallback (though requirement is strict).
    if [ -z "$DNS_LIST" ]; then
        return 1
    fi
    
    for DNS in $DNS_LIST; do
        # nslookup on OpenWrt/BusyBox:
        # Server:    10.73.192.2
        # Address 1: 10.73.192.2
        # 
        # Name:      google.com
        # Address 1: 142.250.186.78
        
        # We target the Address in the answer section (skipping the Server section)
        IP=$(nslookup "$HOST" "$DNS" 2>/dev/null | grep "Address" | tail -n +2 | awk '{print $NF}' | head -n 1)
        
        # Clean up 'Address 1: 1.2.3.4' -> '1.2.3.4' handling
        # standard busybox nslookup output format can vary, but usually the last field is the IP
        
        if [ -n "$IP" ]; then
            echo "$IP"
            return 0
        fi
    done
    return 1
}

# --- Curl Wrapper ---
curl_custom() {
    # Wrapper to enforce DNS resolution via specific servers using --resolve
    
    # Extract URL from arguments to find hostname
    URL=""
    for arg in "$@"; do
        case "$arg" in
            http://*|https://*) URL="$arg"; break ;;
        esac
    done
    
    RESOLVE_ARGS=""
    if [ -n "$URL" ]; then
        # Extract Hostname
        HOST=$(echo "$URL" | awk -F/ '{print $3}')
        # Remove port if present
        HOST_CLEAN=$(echo "$HOST" | cut -d: -f1)
        
        # Skip resolving if it's already an IP
        if ! echo "$HOST_CLEAN" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
             IP=$(resolve_host "$HOST_CLEAN")
             if [ -n "$IP" ]; then
                 # Force curl to use this IP for both HTTP and HTTPS
                 RESOLVE_ARGS="--resolve $HOST_CLEAN:80:$IP --resolve $HOST_CLEAN:443:$IP"
                 # log "Resolving $HOST_CLEAN -> $IP (Custom DNS)"
             fi
        fi
    fi
    
    # Run curl with -k (insecure) and passed args
    # Use the specific interface device if detected to ensure correct source IP
    IFACE_ARG=""
    if [ -n "$WWAN_DEVICE" ]; then
        IFACE_ARG="--interface $WWAN_DEVICE"
    fi
    
    /usr/bin/curl -k $IFACE_ARG $RESOLVE_ARGS "$@"
}

urlencode() {
    # Helper to urlencode strings
    echo "$1" | awk 'BEGIN {
        for (i = 0; i <= 255; i++) {
            ord[sprintf("%c", i)] = i
        }
    }
    {
        len = length($0)
        for (i = 1; i <= len; i++) {
            c = substr($0, i, 1)
            if (c ~ /[a-zA-Z0-9.~_-]/) {
                printf "%s", c
            } else {
                printf "%%%02X", ord[c]
            }
        }
        printf "\n"
    }'
}

# --- Main Flow ---

# 1. Check Internet
check_internet() {
    CODE=$(curl_custom -I -s --connect-timeout 5 -w "%{http_code}" -o /dev/null "$TEST_URL")
    if [ "$CODE" = "204" ]; then
        return 0
    else
        return 1
    fi
}

if [ -n "$FORCE" ]; then
    log "FORCE mode. Skipping internet check."
elif check_internet; then
    log "Internet is available."
    exit 0
else
    # Internet is missing. Reset interface and cookies to ensure a clean state.
    log "Internet not available. Resetting interface and clearing cookies..."
    
    # Clear cookies
    rm -f "$COOKIE_FILE"
    log "Cookies cleared."
    
    # Restart Interface (requires root/sudo privileges usually available on OpenWrt)
    ifdown wwan && ifup wwan
    log "Interface wwan restarted. Waiting for network to stabilize..."
    
    # Wait for IP acquisition
    sleep 10
    
    # Re-check internet just in case (optional, but good practice)
    if check_internet; then
        log "Internet restored after restart."
        exit 0
    fi
fi

log "Starting authentication..."

# 2. Detect Portal URL
# Use msftconnecttest as primary, similar to Selenium
PORTAL_URL=$(curl_custom -A "$USER_AGENT" -s -I "$PORTAL_TRIGGER_URL" | grep -i "^Location:" | awk '{print $2}' | tr -d '\r')

if [ -z "$PORTAL_URL" ]; then
    # Fallback to neverssl
    PORTAL_URL=$(curl_custom -A "$USER_AGENT" -s -I "http://neverssl.com" | grep -i "^Location:" | awk '{print $2}' | tr -d '\r')
fi

# If still empty, try effective URL
if [ -z "$PORTAL_URL" ]; then
     PORTAL_URL=$(curl_custom -A "$USER_AGENT" -s -L -w "%{url_effective}" -o /dev/null "$PORTAL_TRIGGER_URL")
fi

# Extract base
PORTAL_BASE=$(echo "$PORTAL_URL" | awk -F/ '{print $1 "//" $3}' | tr -d '\r')

if [ -z "$PORTAL_BASE" ]; then
    log "Failed to detect portal. Exiting."
    exit 1
fi

log "Portal: $PORTAL_BASE"

# 3. Fetch Landing Page
# Get the page to set initial cookies (PHPSESSID) and extract params
curl_custom -A "$USER_AGENT" -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" -L "$PORTAL_URL" -o /tmp/landing_page.html

LANDING_HTML=$(cat /tmp/landing_page.html)

# Extract Tokens
# 1. Site ID
SITE_ID=$(echo "$PORTAL_BASE" | sed -n 's/.*https:\/\/\([0-9]\+\)\..*/\1/p')
if [ -z "$SITE_ID" ]; then
    SITE_ID=$(echo "$LANDING_HTML" | sed -n 's/.*"siteId":\([0-9]\+\).*/\1/p')
fi

# 2. Params from URL (signature, client_ip, etc.)
# We extract params from the URL because they are signed.
SIGNATURE=$(echo "$PORTAL_URL" | sed -n 's/.*signature=\([^&]*\).*/\1/p')
CLIENT_IP=$(echo "$PORTAL_URL" | sed -n 's/.*client_ip=\([^&]*\).*/\1/p')
CLIENT_MAC=$(echo "$PORTAL_URL" | sed -n 's/.*client_mac=\([^&]*\).*/\1/p')

log "Auth Params from URL: IP=$CLIENT_IP, MAC=$CLIENT_MAC"

if [ -n "$WWAN_IP" ] && [ "$WWAN_IP" != "$CLIENT_IP" ]; then
    log "WARNING: Mismatch detected! System IP ($WWAN_IP) != URL IP ($CLIENT_IP)."
    log "The portal might be authorizing a stale IP. Internet access may fail."
    # We proceed anyway because using the wrong IP breaks the signature (1004 error).
    # Ideally, we should force a refresh of the redirect URL here.
fi

# 3. wbsApiAuthToken (if needed for create-session, though we prefer skipping it)
TOKEN=$(echo "$LANDING_HTML" | sed -n 's/.*conn4\.hotspot\.wbsToken.*"token"\s*:\s*"\([^\"]\+\)".*/\1/p')

# 4. Check for existing PHPSESSID
PHPSESSID=$(grep "PHPSESSID" "$COOKIE_FILE" | tail -n 1 | awk '{print $7}')

if [ -n "$PHPSESSID" ]; then
    log "Session found ($PHPSESSID). Skipping create-session."
    SESSION_ID="$PHPSESSID"
else
    # Create Session
    SESSION_URL="${PORTAL_BASE}/wbs/api/v1/create-session/"
    ENCODED_TOKEN=$(urlencode "$TOKEN")
    
    PAYLOAD="session_id=&with-tariffs=1&locationId=${SITE_ID}&locale=en_US&authorization=token%3D${ENCODED_TOKEN}&signature=${SIGNATURE}&client_ip=${CLIENT_IP}&client_mac=${CLIENT_MAC}"

    # log "Creating session..."
    curl_custom -A "$USER_AGENT" -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" \
        -X POST "$SESSION_URL" \
        -H "X-Requested-With: XMLHttpRequest" \
        -H "Content-Type: application/x-www-form-urlencoded; charset=UTF-8" \
        -H "Origin: ${PORTAL_BASE}" \
        -H "Referer: ${PORTAL_URL}" \
        -d "$PAYLOAD" > /tmp/resp_create.json
        
    SESSION_ID=$(cat /tmp/resp_create.json | sed -n 's/.*"session":"\([^"]\+\)".*/\1/p')
    log "Create-session response: $(cat /tmp/resp_create.json)"
    log "Extracted Session ID: $SESSION_ID"
    
    # Ensure PHPSESSID is in the cookie jar if not already
    if ! grep -q "PHPSESSID" "$COOKIE_FILE"; then
        log "Injecting PHPSESSID into cookie jar from session response"
        DOMAIN=$(echo "$PORTAL_BASE" | awk -F/ '{print $3}')
        echo "$DOMAIN	FALSE	/	FALSE	0	PHPSESSID	$SESSION_ID" >> "$COOKIE_FILE"
    fi
fi

# 5. Login / Register
REG_ENDPOINT="/wbs/api/v1/login/free/"
REG_URL="${PORTAL_BASE}${REG_ENDPOINT}"

# Define Success URL (User indicated this is the expected destination)
SUCCESS_URL="https://www.leonardo-hotels.com/destinations"
ENCODED_SUCCESS_URL=$(urlencode "$SUCCESS_URL")

# Prepare Params
AUTH_VAL="session%3D${SESSION_ID}"
API_SESSION_ID="$SESSION_ID"
PAYMENT_PROXY_URL="${PORTAL_BASE}/admon-assets/payment-return-proxy.php?PaymentProxyUrl=${ENCODED_SUCCESS_URL}"
ENCODED_PAYMENT_URL=$(urlencode "$PAYMENT_PROXY_URL")

REG_PAYLOAD="agree=1&accept=1&terms=1&policy=1&consent=1&tariff=381&locationId=${SITE_ID}&authorization=${AUTH_VAL}&apiSessionId=${API_SESSION_ID}&paymentReturnProxyUrl=${ENCODED_PAYMENT_URL}&loggedin=0&remembered_mac=0&loggedIn=0&rememberedMac=0&signature=${SIGNATURE}&client_ip=${CLIENT_IP}&client_mac=${CLIENT_MAC}"

# log "Registering..."
curl_custom -A "$USER_AGENT" -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" \
    -X POST "$REG_URL" \
    -H "Origin: $PORTAL_BASE" \
    -H "Referer: $PORTAL_URL" \
    -H "X-Requested-With: XMLHttpRequest" \
    -H "Content-Type: application/x-www-form-urlencoded;charset=UTF-8" \
    -d "$REG_PAYLOAD" > /tmp/resp_reg.json

REG_RESPONSE=$(cat /tmp/resp_reg.json)

if echo "$REG_RESPONSE" | grep -q '"ok":true'; then
    log "Registration OK. Finalizing..."
    
    # Hit Payment Proxy to activate session (Follow redirects)
    # Success criterion: Redirect to specific destination URL
    # We add Referer to ensure the server knows where we came from.
    # We capture headers to inspect Location if needed.
    
    PROXY_URL_EFFECTIVE=$(curl_custom -L -v -A "$USER_AGENT" -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" \
        -H "Referer: $PORTAL_URL" \
        -w "%{url_effective}" -o /tmp/proxy_body.txt "$PAYMENT_PROXY_URL" 2> /tmp/proxy_headers.txt)
    
    # Extract Location from the *first* 302 (if any)
    REDIRECT_LOC=$(grep -i "< Location:" /tmp/proxy_headers.txt | head -n 1 | awk '{$1=""; print $0}' | tr -d '\r')
    
    log "Payment Proxy Request complete."
    log "Redirect Location (Header): $REDIRECT_LOC"
    log "Final Effective URL: $PROXY_URL_EFFECTIVE"
    
    if echo "$PROXY_URL_EFFECTIVE" | grep -q "leonardo-hotels.com"; then
        log "Redirect to success page detected."
    fi
    
    # ALWAYS verify internet access. Redirect is not enough if firewall is closed.
    if check_internet; then
        log "Success! Internet available (204 check passed)."
        exit 0
    else
        log "FAILURE: Redirected but internet check failed. Firewall is likely still closed."
        exit 1
    fi
else
    log "Registration failed: $REG_RESPONSE"
    exit 1
fi
