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

Backend shared PostgreSQL container ga ulanadi:

- `DB_HOST=shared_postgres`
- `DB_PORT=5432`

Compose `shared_db` external network'ga ulanadi, shuning uchun mavjud `shared_postgres` konteyneri DNS bilan ko'rinadi.

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
