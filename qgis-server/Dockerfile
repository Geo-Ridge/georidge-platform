FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV QGIS_VERSION=3.44.12

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    ninja-build \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libsqlite3-dev \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libxml2-dev \
    libxslt1-dev \
    libzip-dev \
    libspatialindex-dev \
    libspatialite-dev \
    libqwt-qt5-dev \
    libqt5svg5-dev \
    libqt5serialport5-dev \
    qtbase5-dev \
    qttools5-dev \
    qttools5-dev-tools \
    libqt5xml5 \
    libqt5webkit5-dev \
    libgsl-dev \
    libpqtypes-dev \
    libldap2-dev \
    libcrypt-dev \
    libfmt-dev \
    libdraco-dev \
    libexiv2-dev \
    libqscintilla2-qt5-dev \
    pkg-config \
    wget \
    ca-certificates \
    nginx \
    spawn-fcgi \
    libfcgi-bin \
    xvfb \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Clone QGIS source
RUN git clone --depth 1 --branch ${QGIS_VERSION} https://github.com/qgis/QGIS.git /tmp/qgis

# Build QGIS
RUN mkdir /tmp/qgis/build && cd /tmp/qgis/build && \
    cmake .. \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DWITH_BINDINGS=ON \
    -DWITH_SERVER=ON \
    -DWITH_3D=OFF \
    -DWITHgłęb=OFF \
    -DWITH_QUICK=OFF \
    -DENABLE_TESTS=OFF \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DQGIS_DATA_SUBDIR=share/qgis \
    -DQGIS_PLUGIN_SUBDIR=lib/qgis/plugins \
    && ninja -j$(nproc) \
    && ninja install

# Clean up build files
RUN rm -rf /tmp/qgis

# Create web user
RUN useradd -m -s /bin/bash qgis

# Set up server directory and nginx config
RUN mkdir -p /var/www/qgis-server/projects /etc/nginx/qgis.d && \
    chown -R qgis:qgis /var/www/qgis-server

COPY nginx.conf /etc/nginx/nginx.conf

# Copy entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["docker-entrypoint.sh"]
