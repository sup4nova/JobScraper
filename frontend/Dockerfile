FROM nginx:alpine

# Static files as-is - no build step, Vue is loaded from CDN (see index.html)
COPY index.html styles.css /usr/share/nginx/html/
COPY public/ /usr/share/nginx/html/

# nginx config (gzip, cache, security headers, SPA routing, API reverse-proxy)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Listens on 8080 (not the privileged port 80) so it can run as the
# unprivileged `nginx` user the base image already ships with. nginx still
# needs to create its cache/pid files at runtime, so those directories have
# to be writable by that user ahead of time.
RUN mkdir -p /var/cache/nginx/client_temp /var/cache/nginx/proxy_temp \
             /var/cache/nginx/fastcgi_temp /var/cache/nginx/uwsgi_temp /var/cache/nginx/scgi_temp \
    && chown -R nginx:nginx /var/cache/nginx /var/run \
    && touch /var/run/nginx.pid \
    && chown nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
