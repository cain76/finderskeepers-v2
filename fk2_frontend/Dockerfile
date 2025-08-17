# New frontend Dockerfile for FindersKeepers v2 (UI/UX overhaul)
#
# This Dockerfile mirrors the development setup used by the original
# frontend. It uses a Node base image to install dependencies and
# runs the Vite development server on port 3000. Environment
# variables are provided as defaults but can be overridden by
# docker‑compose.

FROM node:20-alpine

# Set working directory inside the container
WORKDIR /app

# Copy package manifests first and install dependencies. Doing this
# separately allows Docker to cache npm install steps when only
# application code changes.
COPY package*.json ./
# Use npm ci when a lockfile exists; otherwise fall back to npm install
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
RUN npm install @mui/material @emotion/react @emotion/styled

# Copy the rest of the frontend source code
COPY . .

# Expose port 3000 so the app is accessible outside the container
EXPOSE 3000

# Provide default values for the environment variables used in the app.
ENV NODE_ENV=development
ENV VITE_API_URL=http://fk2_fastapi:8000
ENV VITE_WS_URL=ws://fk2_fastapi:8000

# Start the development server
CMD ["npm", "run", "dev"]