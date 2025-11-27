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

# Install minimal dependencies, download, extract, and cleanup in single layer
WORKDIR /tmp
COPY docker/sdk/download-sdk.sh /tmp/download-sdk.sh

RUN set -eux && \
apt-get update && \
apt-get install -y --no-install-recommends \
axel \
ca-certificates \
curl \
xz-utils && \
rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* && \
chmod +x /tmp/download-sdk.sh && \
/tmp/download-sdk.sh && \
mkdir -p /opt/openwrt-sdk && \
tar -C /opt/openwrt-sdk --strip-components=1 -xf openwrt-sdk-*.tar.xz && \
rm -rf /tmp/* /var/tmp/* && \
find /opt/openwrt-sdk -type f -name "*.o" -delete && \
find /opt/openwrt-sdk -type f -name "*.a" -delete && \
rm -rf /opt/openwrt-sdk/build_dir/target-*/linux-* && \
rm -rf /opt/openwrt-sdk/build_dir/target-*/root-* && \
rm -rf /opt/openwrt-sdk/dl/* && \
rm -rf /opt/openwrt-sdk/docs && \
rm -rf /opt/openwrt-sdk/examples && \
rm -rf /opt/openwrt-sdk/.git* && \
find /opt/openwrt-sdk -type f -name "*.md" -delete && \
find /opt/openwrt-sdk -type f -name "README*" -delete && \
find /opt/openwrt-sdk/staging_dir -type f -name "*.la" -delete

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

# Create non-root user first (before copying SDK to avoid chown layer duplication)
RUN useradd -m -s /bin/bash builder

# Install build dependencies and clean up in single layer
RUN set -eux && \
apt-get update && \
apt-get install -y --no-install-recommends \
build-essential \
bzip2 \
ca-certificates \
file \
findutils \
gawk \
gettext \
git \
libncurses5-dev \
libssl-dev \
patch \
python3 \
python3-setuptools \
rsync \
unzip \
wget \
zlib1g-dev && \
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archives/* && \
apt-get clean && \
echo "Verifying build tools installation..." && \
make --version && gcc --version && git --version && python3 --version && \
xargs --version && patch --version && bzip2 --version

# Copy SDK from downloader stage with correct ownership
COPY --from=sdk-downloader --chown=builder:builder /opt/openwrt-sdk /opt/openwrt-sdk

# Set working directory to SDK
WORKDIR /opt/openwrt-sdk

# Switch to non-root user
USER builder

# Set environment variables
# Note: System binaries come first to ensure prereq checks work correctly
ENV PATH="${PATH}:/opt/openwrt-sdk/staging_dir/host/bin"
ENV OPENWRT_VERSION="${OPENWRT_VERSION}"
ENV SDK_TARGET="${SDK_TARGET}"
ENV SDK_SUBTARGET="${SDK_SUBTARGET}"

# Default command
CMD ["/bin/bash"]
