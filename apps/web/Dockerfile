FROM node:22-alpine AS base

WORKDIR /app

COPY package.json package-lock.json* ./
COPY apps/web/package.json apps/web/
COPY libs/ui/package.json libs/ui/
COPY libs/shared-types/package.json libs/shared-types/

RUN npm install

COPY apps/web/ apps/web/
COPY libs/ui/ libs/ui/
COPY libs/shared-types/ libs/shared-types/
COPY tsconfig.base.json ./

EXPOSE 5173

CMD ["npx", "vite", "--host", "0.0.0.0", "--config", "apps/web/vite.config.ts"]

FROM base AS build
RUN npx vite build --config apps/web/vite.config.ts

FROM nginx:alpine AS production
COPY --from=build /app/apps/web/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
