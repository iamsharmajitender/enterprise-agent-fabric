FROM node:22-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY tsconfig.json ./
COPY src src
COPY public public
RUN npm test

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY package.json ./
RUN npm install --omit=dev
COPY --from=build /app/dist dist
COPY public public
ENV PORT=3013
EXPOSE 3013
CMD ["node", "dist/main.js"]
