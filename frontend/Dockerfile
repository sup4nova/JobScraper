FROM nginx:alpine

# Copie des fichiers statiques (l'app principale n'utilise pas Vite)
COPY index.html app.js data.js mascot.js styles.css /usr/share/nginx/html/
COPY public/ /usr/share/nginx/html/public/

# Config nginx (gzip, cache, security headers, SPA routing)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
