#!/bin/bash
set -e

cleanup() {
    kill $XVFB_PID $QGIS_PID $NGINX_PID
}

waitfor() {
    while ! pidof $1 >/dev/null; do
        sleep 1
    done
    pidof $1
}

trap cleanup SIGINT SIGTERM

rm -f /tmp/.X99-lock
fc-cache

# Generate landing page nginx config if QGIS_SERVER_LANDING_PAGE_PREFIX is set
if [ -n "${QGIS_SERVER_LANDING_PAGE_PREFIX:-}" ]; then
    PREFIX="${QGIS_SERVER_LANDING_PAGE_PREFIX}"
    [[ "$PREFIX" != /* ]] && PREFIX="/${PREFIX}"
    if [[ "$PREFIX" =~ ^/[a-zA-Z0-9/_-]+$ ]]; then
        cat > /etc/nginx/qgis.d/landing-page.conf <<LANDING_CONF
location ${PREFIX} {
    fastcgi_pass  localhost:9993;
    fastcgi_param SCRIPT_FILENAME /usr/lib/cgi-bin/qgis_mapserv.fcgi;
    fastcgi_param QUERY_STRING    \$query_string;
    fastcgi_param HTTPS           \$qgis_ssl;
    fastcgi_param SERVER_NAME     \$qgis_host;
    fastcgi_param SERVER_PORT     \$qgis_port;
    include fastcgi_params;
}
LANDING_CONF
        echo "Landing page nginx config generated for prefix: ${PREFIX}"
    fi
fi

/usr/bin/Xvfb :99 -ac -screen 0 1280x1024x16 +extension GLX +render -noreset >/dev/null &
XVFB_PID=$(waitfor /usr/bin/Xvfb)

nginx
NGINX_PID=$(waitfor /usr/sbin/nginx)

spawn-fcgi -n -u ${QGIS_USER:-www-data} -g ${QGIS_USER:-www-data} -d ${HOME:-/var/lib/qgis} -P /run/qgis.pid -p 9993 -- /usr/lib/cgi-bin/qgis_mapserv.fcgi &
QGIS_PID=$(waitfor qgis_mapserv.fcgi)
wait $QGIS_PID
