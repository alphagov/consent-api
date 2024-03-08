FROM node:slim

WORKDIR /app

COPY . .

RUN npm ci
RUN npx -y playwright@1.41.1 install --with-deps
