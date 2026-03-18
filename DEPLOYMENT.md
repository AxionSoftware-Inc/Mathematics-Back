# Deployment

## Layout

Serverda repo'lar sibling bo'lishi kerak:

```text
/opt/math-platform/Math-back
/opt/math-platform/Math-Front
```

## Production fayllar

- `backend/deploy/docker-compose.prod.yml`
- `backend/deploy/.env.production`
- `backend/deploy/pull-and-restart.sh`

`.env.production` yaratish uchun `backend/.env.production.example` dan nusxa olinadi.

## Portlar

Default production portlar:

- Frontend: `3100`
- Backend: `8100`

Band bo'lsa `.env.production` ichida almashtiriladi.

## Database

Backend host'dagi PostgreSQL ga ulanadi:

- `DB_HOST=host.docker.internal`
- `DB_PORT=5432`

Container host PostgreSQL ni ko'rishi uchun compose `host-gateway` ishlatadi.

## Bir martalik deploy

```bash
cd /opt/math-platform
git clone https://github.com/AxionSoftware-Inc/Math-back.git
git clone https://github.com/AxionSoftware-Inc/Math-Front.git
cp Math-back/.env.production.example Math-back/deploy/.env.production
nano Math-back/deploy/.env.production
docker compose --env-file Math-back/deploy/.env.production -f Math-back/deploy/docker-compose.prod.yml up -d --build
```

## Keyingi yangilanish

```bash
cd /opt/math-platform/Math-back/deploy
./pull-and-restart.sh
```
