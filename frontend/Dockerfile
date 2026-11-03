# Frontend EMBICO: React + Vite (dev-сервер)
FROM node:22-alpine

WORKDIR /app

# Сначала зависимости — для кеширования слоя
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# --host 0.0.0.0 — чтобы dev-сервер был доступен снаружи контейнера
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
