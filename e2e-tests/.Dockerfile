FROM node:slim

WORKDIR /app

COPY . .

RUN npm ci
RUN npm install @playwright/test
RUN npx playwright install --with-deps
