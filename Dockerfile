    FROM node:latest

    WORKDIR /app

    COPY package.json package-lock.json ./

    RUN npm install

    COPY . .

    RUN npm install -g mint

    CMD ["mint", "dev"]