# ---------- Backend: FastAPI + uvicorn ----------
FROM python:3.11-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/

# Run as a non-root user
RUN useradd --create-home --uid 10001 orca && chown -R orca:orca /srv
USER orca

EXPOSE 8000

# main.py imports `backend.services...`, so the package must stay importable
# from the working directory. Do not flatten backend/ into /srv.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]


# ---------- Frontend build ----------
FROM node:20-alpine AS frontend-build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install

COPY frontend/ .
RUN npm run build


# ---------- Frontend runtime: nginx serving the built SPA ----------
FROM nginx:alpine AS web

COPY --from=frontend-build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
