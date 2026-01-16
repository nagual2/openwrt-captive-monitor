#!/bin/sh

# Config
TEST_URL="http://clients3.google.com/generate_204"
# A generic HTTP URL that is likely to trigger captive portal redirect
PORTAL_TRIGGER_URL="http://neverssl.com"
COOKIE_FILE="/tmp/conn4_cookies.txt"
LOG_TAG="conn4_auth"
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    logger -t "$LOG_TAG" "$1"
}

# 1. Check Internet
check_internet() {
    # Check for specific 204 response from Google
    CODE=$(/usr/bin/curl -I -s --connect-timeout 5 -w "%{http_code}" -o /dev/null "$TEST_URL")
    if [ "$CODE" = "204" ]; then
        return 0
    else
        return 1
    fi
}

urlencode() {
    # Basic urlencoding using awk
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

if [ -n "$FORCE" ]; then
    log "FORCE mode enabled. Skipping internet check."
elif check_internet; then
    log "Internet is available."
    
    # Attempt to send heartbeat/keepalive if we have session info
    if [ -f "$COOKIE_FILE" ]; then
        # Extract saved session ID and site ID
        SAVED_SESSION=$(grep "conn4_session_id" "$COOKIE_FILE" | awk '{print $7}')
        SAVED_SITE=$(grep "conn4_site_id" "$COOKIE_FILE" | awk '{print $7}')
        SAVED_DOMAIN=$(grep "conn4_site_id" "$COOKIE_FILE" | awk '{print $1}')
        
        if [ -n "$SAVED_SESSION" ] && [ -n "$SAVED_SITE" ]; then
            log "Sending heartbeat for session $(echo "$SAVED_SESSION" | cut -c1-7)..."
            
            # Use POST /wbs/api/v1/login/status with proper auth header
            HEARTBEAT_URL="https://${SAVED_DOMAIN}/wbs/api/v1/login/status"
            
            # We use the cookies we have
            HB_RESPONSE=$(/usr/bin/curl -A "$USER_AGENT" -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" \
                -X POST "$HEARTBEAT_URL" \
                -H "X-Requested-With: XMLHttpRequest" \
                -H "Content-Type: application/x-www-form-urlencoded" \
                -H "Authorization: session=${SAVED_SESSION}" \
                -d "session=${SAVED_SESSION}&authorization=session=${SAVED_SESSION}")
            
            if [ -n "$HB_RESPONSE" ]; then
                # Check for loggedIn:true OR if response is a valid HTML/JSON without explicit error
                # The portal returns a meta-refresh HTML on success or JSON {"loggedIn":true}
                if echo "$HB_RESPONSE" | grep -qE "loggedIn\":true|<meta http-equiv=\"refresh\""; then
                     log "Heartbeat response OK"
                else
                     log "Heartbeat response unexpected: $(echo "$HB_RESPONSE" | head -c 50)..."
                fi
            else
                log "Heartbeat sent (no response body)."
            fi
        fi
    fi
    
    exit 0
fi

log "Internet not available. Starting authentication flow..."

# 2. Detect Portal URL
# We want the FIRST redirect location from the trigger URL, which usually contains the ident/session info
# curl -I (HEAD) doesn't follow redirects by default
# Note: neverssl.com sometimes returns 200 OK directly if not intercepted.
# We should try a known HTTP endpoint that definitely redirects in a captive portal.
# If PORTAL_TRIGGER_URL fails to redirect (returns 200), we might need another target or assume we are already online (but check_internet failed?).
PORTAL_URL=$(/usr/bin/curl -A "$USER_AGENT" -s -I "$PORTAL_TRIGGER_URL" | grep -i "^Location:" | awk '{print $2}' | tr -d '\r')

if [ -z "$PORTAL_URL" ]; then
    # Fallback: try following one redirect if it's just a local redirect (rare)
    # Or maybe the portal returns 200 OK directly?
    log "Failed to detect portal URL via Location header. Trying effective URL."
    # If we got 200 OK from neverssl, it means NO PORTAL or PORTAL IS BROKEN/TRANSPARENT?
    # Let's try http://www.msftconnecttest.com/redirect which is standard
    PORTAL_URL=$(/usr/bin/curl -A "$USER_AGENT" -s -I "http://www.msftconnecttest.com/redirect" | grep -i "^Location:" | awk '{print $2}' | tr -d '\r')
    
    if [ -z "$PORTAL_URL" ]; then
         log "Failed to detect portal URL via msftconnecttest too. Trying effective URL of neverssl."
         PORTAL_URL=$(/usr/bin/curl -A "$USER_AGENT" -s -L -w "%{url_effective}" -o /dev/null "$PORTAL_TRIGGER_URL")
    fi
fi

# Extract base domain (scheme + host)
# e.g. https://1096.rdr.conn4.com/foo/bar -> https://1096.rdr.conn4.com
PORTAL_BASE=$(echo "$PORTAL_URL" | awk -F/ '{print $1 "//" $3}')

if [ -z "$PORTAL_BASE" ]; then
    log "Failed to detect portal URL. Exiting."
    exit 1
fi

log "Detected portal base: $PORTAL_BASE"
log "Initial Portal URL: $PORTAL_URL"

# 3. Fetch Landing Page & Extract Token
# Use a temporary file for headers/output to capture effective URL and content
/usr/bin/curl -A "$USER_AGENT" -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" -L -w "%{url_effective}" "$PORTAL_URL" -o /tmp/landing_page.html > /tmp/effective_url.txt
LANDING_HTML=$(cat /tmp/landing_page.html)
EFFECTIVE_URL=$(cat /tmp/effective_url.txt)

log "Effective URL: $EFFECTIVE_URL"

# Check for "Cookies are required"
if echo "$LANDING_HTML" | grep -q "Cookies are required"; then
    log "Hit 'Cookies are required' page. Attempting to fix cookies..."
    
    # Extract cookie-challenge from URL
    # URL format: .../?cookie-challenge=VALUE
    CHALLENGE=$(echo "$EFFECTIVE_URL" | sed -n 's/.*cookie-challenge=\([^&]*\).*/\1/p')
    
    if [ -n "$CHALLENGE" ]; then
        log "Found cookie-challenge: $CHALLENGE"
        
        # Add to cookie file manually
        # Format: domain flag path secure expiration name value
        # We assume 1096.rdr.conn4.com (extracted from PORTAL_BASE)
        DOMAIN=$(echo "$PORTAL_BASE" | awk -F/ '{print $3}')
        EXPIRATION=$(date +%s | awk '{print $1 + 7200}')
        
        echo "$DOMAIN	FALSE	/	FALSE	$EXPIRATION	cookie-challenge	$CHALLENGE" >> "$COOKIE_FILE"
        
        log "Added cookie-challenge to cookie jar. Retrying..."
        
        # Retry fetch - go back to initial PORTAL_URL which contains ident info
        /usr/bin/curl -A "$USER_AGENT" -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" -L "$PORTAL_URL" -o /tmp/landing_page.html
        LANDING_HTML=$(cat /tmp/landing_page.html)
    else
        log "Could not extract cookie-challenge from URL."
        
        # Check for "reconnect" link in HTML as fallback
        # href="/wbs/authenticate-me/?redirectUrl=..."
        RECONNECT_LINK=$(echo "$LANDING_HTML" | sed -n 's/.*href="\([^"]*authenticate-me[^"]*\)".*/\1/p')
        if [ -n "$RECONNECT_LINK" ]; then
            log "Found reconnect link: $RECONNECT_LINK"
            # Construct full URL
            # If link starts with /, append to base
            if echo "$RECONNECT_LINK" | grep -q "^/"; then
                RECONNECT_URL="${PORTAL_BASE}${RECONNECT_LINK}"
            else
                RECONNECT_URL="$RECONNECT_LINK"
            fi
             # Retry fetch
            /usr/bin/curl -A "$USER_AGENT" -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" -L "$RECONNECT_URL" -o /tmp/landing_page.html
            LANDING_HTML=$(cat /tmp/landing_page.html)
        fi
    fi
fi

# Extract wbsApiAuthToken
# Pattern: conn4.hotspot.wbsToken = {..."token":"VALUE"...}
# We look for "token":"..." and extract the value inside quotes
TOKEN=$(echo "$LANDING_HTML" | sed -n 's/.*conn4\.hotspot\.wbsToken.*"token"\s*:\s*"\([^"]\+\)".*/\1/p')

if [ -z "$TOKEN" ]; then
    log "Failed to extract wbsApiAuthToken from landing page."
    
    # SPECIAL CASE: Pre-authorized but cookie file missing or internet check flaky?
    # If we are already online, the portal might not intercept, so we get no token.
    # Check internet one more time to be sure.
    log "Re-checking internet connectivity..."
    if check_internet; then
        log "Internet is actually available! Assuming session is valid."
        exit 0
    fi
    
    # Debug: dump HTML snippet
    # echo "$LANDING_HTML" > /tmp/landing_debug.html
    # log "Dumped HTML to /tmp/landing_debug.html"
    exit 1
fi

log "Extracted wbsApiAuthToken (len=$(echo "$TOKEN" | awk '{print length($0)}'))"

    # Extract Location ID (Site ID) if possible, default to something if not found (or parse from URL?)
# Usually in URL: https://1096.rdr.conn4.com -> 1096
SITE_ID=$(echo "$PORTAL_BASE" | sed -n 's/.*https:\/\/\([0-9]\+\)\..*/\1/p')

if [ -z "$SITE_ID" ]; then
    # Try extracting from HTML
    SITE_ID=$(echo "$LANDING_HTML" | sed -n 's/.*"siteId":\([0-9]\+\).*/\1/p')
fi

log "Detected Site ID: ${SITE_ID:-unknown}"

# 4. Create Session
# Endpoint: /wbs/api/v1/create-session/
SESSION_URL="${PORTAL_BASE}/wbs/api/v1/create-session/"
ENCODED_TOKEN=$(urlencode "$TOKEN")
PAYLOAD="session_id=&with-tariffs=1&locationId=${SITE_ID}&locale=en_US&authorization=token%3D${ENCODED_TOKEN}"

log "Sending create-session request..."

RESPONSE=$(/usr/bin/curl -A "$USER_AGENT" -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" \
    -X POST "$SESSION_URL" \
    -H "X-Requested-With: XMLHttpRequest" \
    -H "Content-Type: application/x-www-form-urlencoded; charset=UTF-8" \
    -H "Origin: ${PORTAL_BASE}" \
    -H "Referer: ${PORTAL_URL}" \
    -d "$PAYLOAD")

# Extract session ID from response globally
SESSION_ID=$(echo "$RESPONSE" | sed -n 's/.*"session":"\([^"]\+\)".*/\1/p')

# Check result
# We expect {"session":"...","loggedIn":true,...} or similar
IS_LOGGED_IN=$(echo "$RESPONSE" | grep -o '"loggedIn":true')

if [ -n "$IS_LOGGED_IN" ]; then
    log "Session created successfully (loggedIn: true)."
    # Verify internet immediately. If we have internet, we are done.
    # If not, the session might be stale or requires re-registration/activation.
    if check_internet; then
        log "Internet access verified."
        
        # Save Session ID and Site ID as cookies so they persist for potential reuse
        if [ -n "$SESSION_ID" ] && [ -n "$SITE_ID" ]; then
            DOMAIN=$(echo "$PORTAL_BASE" | awk -F/ '{print $3}')
            EXP=$(date +%s | awk '{print $1 + 86400}')
            # Use tabs for cookie file format
            printf "%s\tFALSE\t/\tFALSE\t%s\tconn4_session_id\t%s\n" "$DOMAIN" "$EXP" "$SESSION_ID" >> "$COOKIE_FILE"
            printf "%s\tFALSE\t/\tFALSE\t%s\tconn4_site_id\t%s\n" "$DOMAIN" "$EXP" "$SITE_ID" >> "$COOKIE_FILE"
            log "Saved Session ID and Site ID to cookie file."
        fi

        exit 0
    else
        log "Internet still not accessible despite loggedIn:true. Proceeding to force registration..."
        IS_LOGGED_IN="" # Force fall-through
    fi
else
    log "Session created but loggedIn: false. Attempting registration..."
fi

if [ -z "$IS_LOGGED_IN" ]; then
    # 5. Register (Free)
    # Extract free tariff ID from response
    # We want the FIRST free tariff.
    # Split by objects, find price:0, extract ID.
    # Note: BusyBox sed/grep might be limited, but s/},{/\n/g usually works if we handle quotes right.
    # The JSON is strictly formatted, so "},{" is a good separator.
    TARIFF_ID=$(echo "$RESPONSE" | sed 's/},{/\n/g' | grep '"price":0' | head -n 1 | sed -n 's/.*"id":\([0-9]\+\).*/\1/p')
    
    if [ -z "$TARIFF_ID" ]; then
        # Fallback to default 381 if extraction fails
        TARIFF_ID="381"
    fi
    log "Selected Tariff ID: $TARIFF_ID"
    
    # Find registration endpoint
    # Usually /registration-free or /wbs/authenticate-me/
    # We check the landing page for hints or default to /registration-free
    if echo "$LANDING_HTML" | grep -q "registration-free"; then
        REG_ENDPOINT="/registration-free"
    else
        REG_ENDPOINT="/wbs/api/v1/login/free/"
    fi
    
    REG_URL="${PORTAL_BASE}${REG_ENDPOINT}"
    
    # Build payload
    # Note: authorization=session=... is required?
    # The session ID is in the create-session response: "session":"..."
    # SESSION_ID is already extracted above
    
    # Try to find PHPSESSID in cookies first (preferred for login/free)
    PHPSESSID=$(grep "PHPSESSID" "$COOKIE_FILE" | tail -n 1 | awk '{print $7}')
    
    if [ -n "$PHPSESSID" ]; then
        AUTH_VAL="session%3D${PHPSESSID}"
        log "Using PHPSESSID for authorization: $PHPSESSID"
    else
        AUTH_VAL="session%3D${SESSION_ID}"
        log "Using API Session ID for authorization: $SESSION_ID"
    fi

    REG_PAYLOAD="agree=1&accept=1&terms=1&policy=1&consent=1&tariff=${TARIFF_ID}&locationId=${SITE_ID}&authorization=${AUTH_VAL}"
    
    log "Sending registration request to $REG_ENDPOINT..."
    
    REG_RESPONSE=$(/usr/bin/curl -A "$USER_AGENT" -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" \
        -X POST "$REG_URL" \
        -H "X-Requested-With: XMLHttpRequest" \
        -H "Content-Type: application/x-www-form-urlencoded; charset=UTF-8" \
        -H "Origin: ${PORTAL_BASE}" \
        -H "Referer: ${PORTAL_URL}" \
        -d "$REG_PAYLOAD")
        
    log "Registration response: $(echo "$REG_RESPONSE" | head -c 100)..."
fi

# 6. Verify Internet
sleep 2
if check_internet; then
    log "Authentication successful! Internet is available."
    
    # Save Session ID and Site ID as cookies so they persist for potential reuse
    if [ -n "$SESSION_ID" ] && [ -n "$SITE_ID" ]; then
        DOMAIN=$(echo "$PORTAL_BASE" | awk -F/ '{print $3}')
        EXP=$(date +%s | awk '{print $1 + 86400}')
        # Use tabs for cookie file format
        printf "%s\tFALSE\t/\tFALSE\t%s\tconn4_session_id\t%s\n" "$DOMAIN" "$EXP" "$SESSION_ID" >> "$COOKIE_FILE"
        printf "%s\tFALSE\t/\tFALSE\t%s\tconn4_site_id\t%s\n" "$DOMAIN" "$EXP" "$SITE_ID" >> "$COOKIE_FILE"
        log "Saved Session ID and Site ID to cookie file."
    fi

    exit 0
else
    log "Authentication failed. Still no internet access."
    exit 1
fi
