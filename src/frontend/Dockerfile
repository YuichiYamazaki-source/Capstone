FROM node:20-alpine

WORKDIR /app

COPY src/frontend/package.json ./
RUN npm install

COPY src/frontend/ .

EXPOSE 5173

CMD ["npx", "vite", "--host", "0.0.0.0"]
