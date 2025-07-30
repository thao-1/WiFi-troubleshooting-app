# Multi-stage build for React/Vite app
FROM node:18-alpine as build

# Set working directory
WORKDIR /app

# Copy only package.json first (not package-lock.json to avoid architecture issues)
COPY package.json ./

# Install dependencies (including dev dependencies for build)
# This will create a new package-lock.json for the container architecture
RUN npm install

# Copy source code (excluding node_modules via .dockerignore)
COPY . .

# Build the app
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy built app from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
