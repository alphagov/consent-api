FROM node:slim

WORKDIR /app

COPY . .

RUN npm ci
RUN npx playwright install --with-deps
