FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

# For development, use dev mode
CMD ["npm", "run", "dev"]

