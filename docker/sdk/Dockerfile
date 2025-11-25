# Multi-stage Dockerfile for OpenWrt SDK
# This image provides a pre-configured OpenWrt SDK environment for building packages

ARG UBUNTU_VERSION=24.04
ARG OPENWRT_VERSION=23.05.5
ARG SDK_TARGET
ARG SDK_SUBTARGET

# Stage 1: Download and extract SDK
FROM ubuntu:${UBUNTU_VERSION} AS sdk-downloader

ARG OPENWRT_VERSION
ARG SDK_TARGET
ARG SDK_SUBTARGET

# Install minimal dependencies for downloading and extracting
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        xz-utils && \
    rm -rf /var/lib/apt/lists/*

# Download and extract OpenWrt SDK
# hadolint ignore=DL3003,DL4006
WORKDIR /tmp
# Download SDK with aggressive retry and error handling
RUN SDK_URL="https://downloads.openwrt.org/releases/${OPENWRT_VERSION}/targets/${SDK_TARGET}/${SDK_SUBTARGET}/openwrt-sdk-${OPENWRT_VERSION}-${SDK_TARGET}-${SDK_SUBTARGET}_gcc-12.3.0_musl.Linux-x86_64.tar.xz" && \
    echo "Downloading SDK from: ${SDK_URL}" && \
    curl -fL --retry 15 --retry-delay 10 --retry-all-errors \
         --max-time 3600 --connect-timeout 60 --speed-limit 1000 --speed-time 30 \
         -o sdk.tar.xz "${SDK_URL}" && \
    ls -lh sdk.tar.xz

# Download and verify checksums
RUN SHA256_URL="https://downloads.openwrt.org/releases/${OPENWRT_VERSION}/targets/${SDK_TARGET}/${SDK_SUBTARGET}/sha256sums" && \
    curl -fL --retry 5 --retry-delay 5 -o sha256sums "${SHA256_URL}" && \
    SDK_FILE="openwrt-sdk-${OPENWRT_VERSION}-${SDK_TARGET}-${SDK_SUBTARGET}_gcc-12.3.0_musl.Linux-x86_64.tar.xz" && \
    grep "${SDK_FILE}" sha256sums | sha256sum -c -

# Extract SDK
RUN mkdir -p /opt/openwrt-sdk && \
    tar -C /opt/openwrt-sdk --strip-components=1 -xf sdk.tar.xz && \
    rm sdk.tar.xz sha256sums

# Stage 2: Build final image with SDK and build dependencies
FROM ubuntu:${UBUNTU_VERSION}

ARG OPENWRT_VERSION
ARG SDK_TARGET
ARG SDK_SUBTARGET

# Add metadata labels (OCI specification)
LABEL org.opencontainers.image.title="OpenWrt SDK ${OPENWRT_VERSION}"
LABEL org.opencontainers.image.description="OpenWrt SDK ${OPENWRT_VERSION} for ${SDK_TARGET}/${SDK_SUBTARGET}"
LABEL org.opencontainers.image.version="${OPENWRT_VERSION}"
LABEL org.opencontainers.image.source="https://github.com/nagual2/openwrt-captive-monitor"
LABEL org.opencontainers.image.vendor="openwrt-captive-monitor"
LABEL openwrt.version="${OPENWRT_VERSION}"
LABEL openwrt.target="${SDK_TARGET}"
LABEL openwrt.subtarget="${SDK_SUBTARGET}"

# Install build dependencies
RUN set -eux && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        file \
        gawk \
        gettext \
        git \
        libncurses5-dev \
        libssl-dev \
        python3 \
        python3-setuptools \
        rsync \
        unzip \
        wget \
        zlib1g-dev && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/* && \
    rm -rf /var/tmp/* && \
    echo "Verifying build tools installation..." && \
    make --version && \
    gcc --version && \
    git --version && \
    python3 --version

# Copy SDK from downloader stage
COPY --from=sdk-downloader /opt/openwrt-sdk /opt/openwrt-sdk

# Set working directory to SDK
WORKDIR /opt/openwrt-sdk

# Set environment variables
ENV PATH="/opt/openwrt-sdk/staging_dir/host/bin:${PATH}"
ENV OPENWRT_VERSION="${OPENWRT_VERSION}"
ENV SDK_TARGET="${SDK_TARGET}"
ENV SDK_SUBTARGET="${SDK_SUBTARGET}"

# Default command
CMD ["/bin/bash"]
