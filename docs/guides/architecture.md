# Architecture Overview

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


System design and component architecture of **openwrt-captive-monitor**.

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Devices                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Laptop    │  │   Phone     │  │   Tablet    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────┬───────────────────────────────────────┘
                      │ LAN Traffic (HTTP/DNS)
┌─────────────────────┴───────────────────────────────────────┐
│                  OpenWrt Router                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                Captive Monitor                      │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │    │
│  │  │ Connectivity │  │  Detection  │  │ Interception│ │    │
│  │  │   Checker    │  │   Engine    │  │   Manager    │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │    │
│  │  │   Logger    │  │  Config     │  │   Cleanup   │ │    │
│  │  │  Manager    │  │  Manager    │  │  Manager    │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              System Integration                      │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │    │
│  │  │   dnsmasq   │  │  iptables/  │  │ busybox     │ │    │
│  │  │  (DNS)      │  │  nftables   │  │  httpd      │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │    │
│  │  │   procd     │  │     UCI     │  │   syslog    │ │    │
│  │  │  (init)     │  │  (config)   │  │  (logging)  │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────┘
                      │ WAN Traffic
┌─────────────────────┴───────────────────────────────────────┐
│                 External Network                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Internet  │  │   Gateway   │  │   Captive   │        │
│  │   (Direct)  │  │   (Router)  │  │   Portal    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Core Components

### 1. Main Script (`openwrt_captive_monitor.sh`)

The central orchestrator that coordinates all functionality:

```bash
┌─────────────────────────────────────────────────────────────┐
│                Main Script Flow                              │
│                                                             │
│  1. Initialization                                          │
│     ├─ Load configuration (UCI → Environment → CLI)         │
│     ├─ Validate dependencies                                 │
│     ├─ Detect network interfaces                             │
│     └─ Setup logging                                        │
│                                                             │
│  2. Main Loop (Monitor Mode)                               │
│     ├─ Connectivity Checker                                 │
│     ├─ Detection Engine                                     │
│     ├─ Interception Manager (if needed)                     │
│     ├─ Cleanup Manager (if restored)                        │
│     └─ Wait for next interval                              │
│                                                             │
│  3. Single Execution (Oneshot Mode)                         │
│     └─ Execute steps 2a-2e once and exit                   │
└─────────────────────────────────────────────────────────────┘
```

### 2. Connectivity Checker

Monitors network connectivity using multiple methods:

```
Connectivity Checker
├─ Gateway Reachability
│   ├─ Ping gateway IP
│   └─ Check ARP table
├─ Internet Connectivity
│   ├─ Ping external servers
│   ├─ HTTP/HTTPS probes
│   └─ DNS resolution tests
└─ Network Interface Status
    ├─ WiFi interface state
    ├─ IP address assignment
    └─ Route table validation
```

### 3. Detection Engine

Identifies captive portal conditions:

```
Detection Engine
├─ Gateway Check
│   ├─ ICMP ping to gateway
│   ├─ MAC address verification
│   └─ Route validation
├─ Internet Check
│   ├─ Multiple ping servers
│   ├─ HTTP probe responses
│   └─ DNS resolution tests
└─ Captive Portal Detection
    ├─ HTTP redirect detection
    ├─ Response code analysis
    ├─ Location header extraction
    └─ Portal URL validation
```

### 4. Interception Manager

Handles traffic interception when captive portal is detected:

```
Interception Manager
├─ DNS Hijacking
│   ├─ Create dnsmasq drop-in config
│   ├─ Override all domains to router IP
│   ├─ Preserve specific portal domains
│   └─ Reload dnsmasq service
├─ HTTP Redirection
│   ├─ Setup firewall NAT rules
│   ├─ Configure HTTP server
│   ├─ Create redirect HTML page
│   └─ Start busybox httpd
└─ Traffic Monitoring
    ├─ Monitor NAT rule usage
    ├─ Track DNS query patterns
    └─ Log redirection events
```

---

## 🔗 System Integration

### OpenWrt Integration Points

```
OpenWrt System Integration
├─ procd (Process Management)
│   ├─ Service definition (/etc/init.d/captive-monitor)
│   ├─ Process monitoring and respawn
│   └─ Signal handling and cleanup
├─ UCI Configuration System
│   ├─ Configuration storage (/etc/config/captive-monitor)
│   ├─ Runtime configuration loading
│   └─ Configuration validation
├─ Network Stack
│   ├─ Interface management (ip command)
│   ├─ Routing table manipulation
│   └─ WiFi interface control (wifi command)
├─ Firewall Integration
│   ├─ iptables backend (legacy)
│   ├─ nftables backend (fw4)
│   └─ Automatic backend detection
└─ Service Integration
    ├─ dnsmasq (DNS/DHCP)
    ├─ syslog (logging)
    └─ hotplug (interface events)
```

### Service Dependencies

```
Dependency Graph
┌─────────────────────────────────────────────────────────────┐
│                captive-monitor                              │
│                                                             │
│  Depends on:                                               │
│  ├─ dnsmasq (DNS resolution, intercept)                    │
│  ├─ iptables/nftables (traffic redirection)                │
│  ├─ busybox (HTTP server, basic utilities)                │
│  ├─ curl (HTTP probes, captive detection)                 │
│  ├─ iproute2 (network interface management)                │
│  └─ wireless tools (WiFi interface control)                 │
│                                                             │
│  Provides:                                                  │
│  ├─ Automatic captive portal detection                      │
│  ├─ Traffic interception for authentication                │
│  ├─ Automatic cleanup after authentication                  │
│  └─ Network connectivity monitoring                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow

### Normal Operation Flow

```
Normal Operation
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│    Router   │───▶│  Internet   │
│   Device    │    │  (Normal)   │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
     ▲                   │                   │
     │                   ▼                   │
     │            ┌─────────────┐           │
     │            │ Captive     │           │
     │            │ Monitor     │           │
     │            │ (Monitoring)│           │
     │            └─────────────┘           │
     │                   │                   │
     └───────────────────┼───────────────────┘
                         │
                Periodic checks
                (no intervention)
```

### Captive Portal Flow

```
Captive Portal Detection
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│    Router   │───▶│ Captive     │
│   Device    │    │ (Intercept) │    │ Portal      │
└─────────────┘    └─────────────┘    └─────────────┘
     │                   ▲                   │
     │                   │                   ▼
     │            ┌─────────────┐    ┌─────────────┐
     │            │ Captive     │    │ User        │
     │            │ Monitor     │    │ Authenticates│
     │            │ (Active)    │    └─────────────┘
     │            └─────────────┘            │
     │                   │                    │
     └───────────────────┼────────────────────┘
                        │
                Detection and
                interception
```

### Authentication and Cleanup Flow

```
Authentication and Cleanup
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│    Router   │───▶│  Internet   │
│   Device    │    │  (Normal)   │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
     │                   │                   │
     │                   ▼                   │
     │            ┌─────────────┐           │
     │            │ Captive     │           │
     │            │ Monitor     │           │
     │            │ (Cleanup)   │           │
     │            └─────────────┘           │
     │                   │                   │
     └───────────────────┼───────────────────┘
                         │
                Automatic cleanup
                (restore normal)
```

---

## 🔄 State Management

### Service States

```
State Machine
┌─────────────────┐
│   INITIALIZING  │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   MONITORING    │◀──────────────────┐
└─────────┬───────┘                   │
          │                           │
          ▼                           │
┌─────────────────┐                   │
│   CHECKING      │                   │
└─────────┬───────┘                   │
          │                           │
          ▼                           │
┌─────────────────┐                   │
│   CONNECTED     │                   │
└─────────┬───────┘                   │
          │                           │
          ▼                           │
┌─────────────────┐                   │
│   CAPTIVE       │                   │
│   DETECTED      │                   │
└─────────┬───────┘                   │
          │                           │
          ▼                           │
┌─────────────────┐                   │
│   INTERCEPTING   │                   │
└─────────┬───────┘                   │
          │                           │
          ▼                           │
┌─────────────────┐                   │
│   RESTORED      │───────────────────┘
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   MONITORING    │
└─────────────────┘
```

### Configuration Layers

```
Configuration Precedence
┌─────────────────────────────────────────────────────────────┐
│                Configuration Layers                         │
│                                                             │
│  1. Command Line Flags (Highest Priority)                  │
│     └─ Runtime overrides for testing/automation           │
│                                                             │
│  2. Environment Variables                                  │
│     └─ Container/deployment specific settings             │
│                                                             │
│  3. UCI Configuration (Default)                            │
│     └─ Persistent configuration storage                    │
│                                                             │
│  4. Built-in Defaults (Lowest Priority)                   │
│     └─ Fallback values for all settings                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Security Architecture

### Isolation and Privileges

```
Security Model
┌─────────────────────────────────────────────────────────────┐
│                Security Boundaries                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              User Space                             │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │    │
│  │  │ Captive     │  │   dnsmasq   │  │  httpd      │ │    │
│  │  │ Monitor     │  │  (DNS)      │  │  server     │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │    │
│  │  │   curl      │  │  iptables/  │  │  syslog     │ │    │
│  │  │  client     │  │  nftables   │  │  daemon     │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │               Kernel Space                           │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │    │
│  │  │  Network    │  │  Firewall   │  │   Process   │ │    │
│  │  │   Stack     │  │   Rules     │  │  Manager    │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  Privilege Requirements:                                     │
│  ├─ Root access (required for firewall/DNS modifications)   │
│  ├─ Network interface control                               │
│  ├─ Service management (start/stop/restart)                │
│  └─ Configuration file access                               │
└─────────────────────────────────────────────────────────────┘
```

### Traffic Flow Security

```
Traffic Isolation
┌─────────────────────────────────────────────────────────────┐
│                Traffic Security                             │
│                                                             │
│  Normal Mode:                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Client    │───▶│    Router   │───▶│  Internet   │     │
│  │   Traffic   │    │  (Forward)  │    │             │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                             │
│  Captive Mode:                                              │
│  ┌─────────────┐    ┌─────────────┐                        │
│  │   Client    │───▶│    Router   │                        │
│  │   HTTP      │    │  (Redirect) │                        │
│  │   Traffic   │    │  to Portal  │                        │
│  └─────────────┘    └─────────────┘                        │
│                            │                                │
│                            ▼                                │
│                   ┌─────────────┐                           │
│                   │   Captive   │                           │
│                   │   Portal    │                           │
│                   └─────────────┘                           │
│                                                             │
│  Security Considerations:                                    │
│  ├─ HTTPS traffic NOT intercepted (preserves security)      │
│  ├─ DNS queries redirected to router (temporary)           │
│  ├─ HTTP only interception (HSTS compliant)                │
│  ├─ No packet inspection or modification                   │
│  └─ Automatic cleanup prevents permanent interception        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Performance Architecture

### Resource Management

```
Resource Usage
┌─────────────────────────────────────────────────────────────┐
│                Resource Profile                            │
│                                                             │
│  CPU Usage:                                                 │
│  ├─ Monitoring mode: < 1% average                          │
│  ├─ Oneshot mode: Burst during checks                      │
│  ├─ Captive mode: Slight increase (HTTP server, logging)   │
│  └─ Cleanup: Minimal impact                                 │
│                                                             │
│  Memory Usage:                                              │
│  ├─ Base process: ~2-4 MB                                   │
│  ├─ HTTP server: +1-2 MB (when active)                     │
│  ├─ DNS intercept: Negligible                              │
│  └─ Firewall rules: Kernel memory (minimal)                │
│                                                             │
│  Network Impact:                                            │
│  ├─ Monitoring: Periodic pings/probes (minimal)             │
│  ├─ Captive mode: DNS queries to router, HTTP redirects    │
│  ├─ Cleanup: Brief rule removal                             │
│  └─ No impact on non-intercepted traffic                    │
└─────────────────────────────────────────────────────────────┘
```

### Scalability Considerations

```
Scalability Design
┌─────────────────────────────────────────────────────────────┐
│                Scalability Factors                         │
│                                                             │
│  Client Scaling:                                            │
│  ├─ DNS hijacking: Scales to hundreds of clients           │
│  ├─ HTTP redirection: Limited by httpd capacity             │
│  ├─ Firewall rules: Per-interface, not per-client          │
│  └─ Memory usage: Constant regardless of client count       │
│                                                             │
│  Network Scaling:                                           │
│  ├─ Multiple interfaces: Supported (per-interface config)    │
│  ├─ VLAN support: Works with tagged interfaces             │
│  └─ Multiple gateways: Primary interface focus              │
│                                                             │
│  Performance Tuning:                                        │
│  ├─ Monitor interval: Adjustable (30-300 seconds)           │
│  ├─ Check timeouts: Configurable per environment           │
│  ├─ Parallel checks: Sequential for reliability             │
│  └─ Resource limits: Built-in safeguards                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Extension Points

### Customization Options

```
Extension Architecture
┌─────────────────────────────────────────────────────────────┐
│                Extension Points                            │
│                                                             │
│  Detection Customization:                                   │
│  ├─ Custom captive portal URLs                             │
│  ├─ Additional detection methods                           │
│  ├─ Configurable response analysis                         │
│  └─ Plugin architecture (future)                           │
│                                                             │
│  Interception Customization:                                │
│  ├─ Custom HTTP server content                              │
│  ├─ Alternative redirect methods                           │
│  ├─ Custom DNS override rules                              │
│  └─ Third-party authentication integration                 │
│                                                             │
│  Integration Hooks:                                         │
│  ├─ Pre/post check callbacks                               │
│  ├─ Detection event handlers                               │
│  ├─ Cleanup completion notifications                        │
│  └─ External monitoring integration                        │
│                                                             │
│  Configuration Extensions:                                   │
│  ├─ Custom UCI options                                      │
│  ├─ Environment variable overrides                         │
│  ├─ Runtime configuration reloading                        │
│  └─ Profile-based configurations                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Component Interactions

### Service Lifecycle

```
Service Lifecycle
┌─────────────────────────────────────────────────────────────┐
│                Lifecycle Management                          │
│                                                             │
│  Startup:                                                   │
│  ├─ procd starts service                                   │
│  ├─ Load UCI configuration                                 │
│  ├─ Validate dependencies                                 │
│  ├─ Detect network environment                              │
│  └─ Begin monitoring loop                                  │
│                                                             │
│  Runtime:                                                   │
│  ├─ Periodic connectivity checks                            │
│  ├─ Dynamic configuration reloading                        │
│  ├─ Signal handling (SIGTERM, SIGHUP)                      │
│  └─ Error recovery and retry logic                          │
│                                                             │
│  Shutdown:                                                  │
│  ├─ Signal reception from procd                            │
│  ├─ Graceful cleanup of active rules                       │
│  ├─ Service de-registration                                │
│  └─ Process termination                                    │
│                                                             │
│  Error Handling:                                            │
│  ├─ Configuration validation failures                      │
│  ├─ Network interface errors                               │
│  ├─ Service dependency failures                            │
│  └─ Automatic recovery mechanisms                          │
└─────────────────────────────────────────────────────────────┘
```

This architecture provides a robust, scalable foundation for captive portal detection and handling while maintaining security and performance standards expected in OpenWrt environments.
