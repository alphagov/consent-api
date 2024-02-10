FROM node:slim

WORKDIR /app

COPY package.json package-lock.json .

RUN npx -y playwright@1.41.1 install --with-deps
RUN npm ci

COPY . .
