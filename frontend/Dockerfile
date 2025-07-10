# Frontend Dockerfile for FindersKeepers v2
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose port 3000
EXPOSE 3000

# Set environment variables for development
ENV NODE_ENV=development
ENV VITE_API_URL=http://localhost:8000
ENV VITE_WS_URL=ws://localhost:8000

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]