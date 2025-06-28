# Bot Detection API

A comprehensive bot detection system with behavioral analysis, survey platform integration, and real-time monitoring capabilities.

## 🚀 Features

- **Advanced Bot Detection**: Rule-based analysis of user behavior patterns
- **Multi-Platform Integration**: Support for Qualtrics and Decipher survey platforms
- **Real-time Analytics**: Live dashboard with session monitoring and detection statistics
- **Scalable Architecture**: FastAPI backend with PostgreSQL and Redis
- **Client SDKs**: Python and JavaScript client libraries for easy integration
- **Webhook Support**: Automated survey response processing
- **Monitoring & Logging**: Comprehensive observability with Prometheus and Grafana

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   Redis Cache   │              │
         │              └─────────────────┘              │
         │                                              │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client SDKs   │    │   Integrations  │    │   Monitoring    │
│   (Python/JS)   │    │   (Webhooks)    │    │   (Prometheus)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
bot_iden_live/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── config.py          # Configuration settings
│   │   ├── database.py        # Database setup
│   │   ├── models/            # SQLAlchemy models
│   │   ├── services/          # Business logic
│   │   ├── controllers/       # API controllers
│   │   ├── utils/             # Utility functions
│   │   └── routes/            # API routes
│   ├── main.py               # Application entry point
│   ├── requirements.txt      # Python dependencies
│   └── .env.example         # Environment variables
├── frontend/                  # React frontend
│   ├── public/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API services
│   │   ├── utils/            # Utility functions
│   │   └── styles/           # CSS styles
│   ├── package.json
│   └── vite.config.js
├── client-sdk/               # Client SDKs
│   ├── python/               # Python client
│   └── javascript/           # JavaScript client
├── docker-compose.yml        # Docker orchestration
└── README.md                # This file
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: Database ORM with async support
- **PostgreSQL**: Primary database
- **Redis**: Caching and session storage
- **Pydantic**: Data validation and settings
- **Uvicorn**: ASGI server

### Frontend
- **React**: UI framework
- **Vite**: Build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd bot_iden_live
```

### 2. Environment Setup
```bash
# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit configuration files with your settings
```

### 3. Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# Start with monitoring
docker-compose --profile monitoring up -d

# Start production stack
docker-compose --profile production up -d
```

### 4. Access Services
- **API Documentation**: http://localhost:8000/docs
- **Frontend Dashboard**: http://localhost:3000
- **Grafana Monitoring**: http://localhost:3001 (if monitoring enabled)

## 📚 API Documentation

### Core Endpoints

#### Sessions
```http
POST /api/v1/detection/sessions
GET /api/v1/detection/sessions/{session_id}/status
```

#### Events
```http
POST /api/v1/detection/sessions/{session_id}/events
```

#### Analysis
```http
POST /api/v1/detection/sessions/{session_id}/analyze
```

#### Dashboard
```http
GET /api/v1/dashboard/overview
GET /api/v1/dashboard/sessions
GET /api/v1/dashboard/sessions/{session_id}/details
```

#### Integrations
```http
POST /api/v1/integrations/webhooks/qualtrics
POST /api/v1/integrations/webhooks/decipher
GET /api/v1/integrations/status
```

### Example Usage

#### 1. Create a Session
```bash
curl -X POST "http://localhost:8000/api/v1/detection/sessions" \
  -H "Content-Type: application/json"
```

#### 2. Send Events
```bash
curl -X POST "http://localhost:8000/api/v1/detection/sessions/{session_id}/events" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "event_type": "keystroke",
      "timestamp": "2024-01-01T12:00:00Z",
      "key": "a",
      "element_id": "input-1"
    }
  ]'
```

#### 3. Analyze Session
```bash
curl -X POST "http://localhost:8000/api/v1/detection/sessions/{session_id}/analyze"
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/bot_detection

# Security
SECRET_KEY=your-super-secret-key
ALLOWED_ORIGINS=["http://localhost:3000"]

# Integrations
QUALTRICS_API_TOKEN=your-qualtrics-token
DECIPHER_API_KEY=your-decipher-key

# Bot Detection
DETECTION_THRESHOLD=0.7
SESSION_TIMEOUT_MINUTES=30
```

#### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Bot Detection Dashboard
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pip install -r requirements.txt
pytest
```

### Frontend Tests
```bash
cd frontend
npm install
npm test
```

### Integration Tests
```bash
# Run with Docker
docker-compose exec backend pytest tests/integration/
```

## 📊 Monitoring

### Metrics
The application exposes Prometheus metrics at `/metrics`:
- Request duration
- Error rates
- Session counts
- Detection accuracy

### Logging
Structured logging with configurable levels:
```python
import logging
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
logger.info("Application started")
```

## 🔒 Security

### Authentication
- API key authentication for external integrations
- JWT tokens for user sessions
- CORS configuration for cross-origin requests

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Rate limiting

## 🚀 Deployment

### Production Deployment
```bash
# Build and deploy
docker-compose --profile production up -d

# With monitoring
docker-compose --profile production --profile monitoring up -d
```

### Environment-Specific Configs
- **Development**: `docker-compose.yml`
- **Staging**: `docker-compose.staging.yml`
- **Production**: `docker-compose.prod.yml`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend
- Write comprehensive tests
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Reference](docs/api.md)
- [Integration Guide](docs/integration.md)
- [Deployment Guide](docs/deployment.md)

### Community
- [Issues](https://github.com/your-repo/issues)
- [Discussions](https://github.com/your-repo/discussions)

### Contact
- Email: support@botdetection.com
- Slack: #bot-detection

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ Core bot detection engine
- ✅ Basic API endpoints
- ✅ Survey platform integrations
- ✅ Dashboard UI

### Phase 2 (Next)
- 🔄 Machine learning models
- 🔄 Advanced analytics
- 🔄 Mobile SDK
- 🔄 Real-time alerts

### Phase 3 (Future)
- 📋 Multi-language support
- 📋 Advanced reporting
- 📋 Enterprise features
- 📋 API marketplace

---

**Built with ❤️ for secure and reliable bot detection** 