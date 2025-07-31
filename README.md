# WiFi Troubleshooting App

An intelligent WiFi troubleshooting chatbot that helps users diagnose and resolve WiFi connectivity issues. The app features automatic network testing, interactive chat support, and personalized troubleshooting recommendations.

## Live Demo

**Access the deployed app:** [http://147.182.156.161](http://147.182.156.161)

## Features

- **Intelligent Chat Support**: AI-powered troubleshooting assistant
- **Automatic Network Testing**: Real-time connectivity and speed tests
- **Interactive UI**: Modern, responsive design with real-time feedback
- **Personalized Solutions**: Tailored recommendations based on device and network conditions

## Architecture

- **Frontend**: React + Vite with modern UI components
- **Backend**: FastAPI with OpenAI integration
- **Deployment**: Docker containers with nginx proxy
- **Infrastructure**: DigitalOcean Droplet

## Local Development

### Prerequisites

- Node.js (v18 or higher)
- Python 3.11+
- Docker and Docker Compose
- OpenAI API Key

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/thao-1/WiFi-troubleshooting-app.git
   cd WiFi-troubleshooting-app
   ```

2. **Set up environment variables:**
   ```bash
   # Create backend environment file
   cp backend/.env.example backend/.env
   # Add your OpenAI API key to backend/.env
   echo "OPENAI_API_KEY=your_openai_api_key_here" >> backend/.env
   ```

3. **Run with Docker (Recommended):**
   ```bash
   docker-compose up -d
   ```
   - Frontend: http://localhost
   - Backend API: http://localhost:8000

4. **Run locally for development:**
   ```bash
   # Install dependencies and start both services
   npm run dev
   ```
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000

### Development Commands

```bash
# Start both frontend and backend in development mode
npm run dev

# Start only frontend
npm run dev:frontend

# Start only backend
npm run dev:backend

# Build for production
npm run build

# Run with Docker
docker-compose up -d

# View logs
docker-compose logs -f
```

## Deployment

The app is deployed using Docker containers on a DigitalOcean Droplet with:

- **Frontend**: Nginx serving React build with API proxy
- **Backend**: FastAPI with Uvicorn server
- **Networking**: Docker Compose with custom network
- **SSL**: Ready for SSL certificate setup

### Deployment Architecture

```
User → Nginx (Port 80) → React App
                      ↓
                   /api/* → FastAPI Backend (Port 8000)
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Required for AI chat functionality
- `PYTHONPATH`: Set to `/app` for backend
- `PYTHONUNBUFFERED`: Set to `1` for proper logging

### Nginx Configuration

- Serves React build from `/usr/share/nginx/html`
- Proxies `/api/v1/*` requests to backend
- Handles client-side routing
- Includes security headers and gzip compression

## Testing

```bash
# Test backend health
curl http://localhost:8000/health

# Test chat API
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "My WiFi is slow", "session_id": "test"}'
```

## API Documentation

- **Health Check**: `GET /health`
- **Chat Endpoint**: `POST /api/v1/chat`
- **Interactive Docs**: http://localhost:8000/docs (when running locally)

