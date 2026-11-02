# syntax=docker/dockerfile:1.7
FROM node:24.19.0-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
# tsc -b type-checks tests too; /app/tests/setup/../../../../tests resolves to /tests
COPY --from=contract_fixtures . /tests/contract_fixtures
RUN npm run build

FROM nginx:1.30.6-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
