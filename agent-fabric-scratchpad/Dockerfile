FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.server.json tsconfig.client.json ./
COPY src src
COPY public public
COPY catalog catalog
RUN npm test

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY --from=build /app/dist dist
COPY --from=build /app/public public
COPY catalog catalog
ENV PORT=3014
ENV AFD_URL=http://agent-front-door:3005
EXPOSE 3014
CMD ["node", "dist/server/main.js"]
