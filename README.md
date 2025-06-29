# Bot Detection API

A comprehensive bot detection system with behavioral analysis, survey platform integration, and real-time monitoring capabilities.

## 🚀 Features

- **Advanced Bot Detection**: Rule-based analysis of user behavior patterns with 5 detection methods
- **Multi-Platform Integration**: Support for Qualtrics and Decipher survey platforms
- **Real-time Analytics**: Live dashboard with session monitoring and detection statistics
- **Scalable Architecture**: FastAPI backend with PostgreSQL and Redis
- **Client SDKs**: Python and JavaScript client libraries for easy integration
- **Webhook Support**: Automated survey response processing
- **Monitoring & Logging**: Comprehensive observability with Prometheus and Grafana
- **Performance Testing**: Locust load testing and async performance validation
- **Error Handling**: Comprehensive validation and user-friendly error messages
- **Architecture Documentation**: Comprehensive system architecture and interaction patterns

## 🏗️ Architecture

For detailed architecture information, see [Architecture Documentation](architecture.md).

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

### Key Architectural Features

- **Async/Await Pattern**: Non-blocking I/O operations throughout the system
- **Layered Architecture**: Clear separation between API, business logic, and data layers
- **Real-time Updates**: WebSocket support for live dashboard updates
- **Error Handling**: Comprehensive error handling at all layers
- **Performance Optimization**: Database optimization, caching, and frontend optimizations
- **Security**: Multi-layered security approach with validation and protection

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
│   ├── requirements-test.txt # Test dependencies
│   ├── create_test_data.py  # Test data generation
│   ├── performance_test.py  # Async performance testing
│   ├── locustfile.py        # Load testing configuration
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
├── architecture.md           # System architecture documentation
├── API.md                    # API reference documentation
├── planning.md               # Technical planning document
├── prd.md                    # Product requirements document
├── task.md                   # Development tasks and progress
└── README.md                # This file
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework with async support
- **SQLAlchemy**: Database ORM with async support and relationship management
- **PostgreSQL**: Primary database with optimized schemas
- **Redis**: Caching and session storage
- **Pydantic**: Data validation and settings management
- **Uvicorn**: ASGI server for production deployment

### Frontend
- **React**: UI framework with modern hooks
- **Vite**: Build tool and dev server for fast development
- **Tailwind CSS**: Utility-first CSS framework with responsive design
- **Axios**: HTTP client for API communication

### Infrastructure
- **Docker**: Containerization for consistent environments
- **Docker Compose**: Multi-container orchestration
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Monitoring dashboards and visualization

### Testing & Performance
- **Locust**: Load testing and performance validation
- **Pytest**: Unit testing framework
- **AsyncIO**: Asynchronous performance testing

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### 1. Clone the Repository
```bash
git clone https://github.com/halderavik/bot_detection_live.git
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

## 📚 Documentation

### Core Documentation
- **[Architecture Documentation](architecture.md)**: Comprehensive system architecture and interaction patterns
- **[API Reference](API.md)**: Complete API documentation with examples
- **[Technical Planning](planning.md)**: Production deployment and scaling considerations
- **[Product Requirements](prd.md)**: Product specifications and success metrics
- **[Development Tasks](task.md)**: Current progress and upcoming features

### API Documentation

#### Core Endpoints

#### Sessions
```http
POST /api/v1/detection/sessions
GET /api/v1/detection/sessions/{session_id}/status
GET /api/v1/detection/sessions/{session_id}/ready-for-analysis
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

#### Health & Monitoring
```http
GET /health
GET /metrics
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

#### 3. Check if Session is Ready for Analysis
```bash
curl -X GET "http://localhost:8000/api/v1/detection/sessions/{session_id}/ready-for-analysis"
```

#### 4. Analyze Session
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

# Debug Mode
DEBUG=true
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
pip install -r requirements-test.txt
pytest
```

### Performance Testing
```bash
# Run Locust load testing
cd backend
locust -f locustfile.py

# Run async performance test
python performance_test.py
```

### Create Test Data
```bash
cd backend
python create_test_data.py
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
- Processing time statistics

### Logging
Structured logging with configurable levels:
```python
import logging
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
logger.info("Application started")
```

### Health Checks
- **Health endpoint**: `/health` - Basic system status
- **Database connectivity**: Automatic connection testing
- **API responsiveness**: Response time monitoring

## 🔒 Security

### Authentication
- API key authentication for external integrations
- JWT tokens for user sessions (planned)
- CORS configuration for cross-origin requests

### Data Protection
- Input validation and sanitization with Pydantic
- SQL injection prevention with parameterized queries
- XSS protection
- Rate limiting (configurable)

### Error Handling
- Comprehensive 400/404/500 error responses
- User-friendly error messages
- Detailed logging for debugging
- Input validation with clear feedback

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
- Run performance tests before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [Architecture Guide](architecture.md)
- [API Reference](API.md)
- [Integration Guide](API.md#integration-apis)
- [Deployment Guide](planning.md)

### Community
- [Issues](https://github.com/halderavik/bot_detection_live/issues)
- [Discussions](https://github.com/halderavik/bot_detection_live/discussions)

### Contact
- Email: support@botdetection.com
- Slack: #bot-detection

## 🗺️ Roadmap

### Phase 1 (Current) ✅
- ✅ Core bot detection engine
- ✅ Basic API endpoints
- ✅ Survey platform integrations
- ✅ Dashboard UI
- ✅ Performance testing
- ✅ Error handling improvements
- ✅ Client SDKs
- ✅ Architecture documentation
- ✅ Comprehensive API documentation

### Phase 2 (Next)
- 🔄 Machine learning models
- 🔄 Advanced analytics
- 🔄 Mobile SDK
- 🔄 Real-time alerts
- 🔄 Authentication system
- 🔄 Rate limiting

### Phase 3 (Future)
- 📋 Multi-language support
- 📋 Advanced reporting
- 📋 Enterprise features
- 📋 API marketplace
- 📋 Billing system
- 📋 Multi-tenant support

## 🎯 Performance Achievements

- **Response Times**: Sub-100ms for most endpoints
- **Database**: Async operations with connection pooling
- **Error Handling**: Comprehensive validation and user-friendly messages
- **Scalability**: Modular architecture ready for horizontal scaling
- **Testing**: Automated performance validation with Locust
- **Architecture**: Well-documented system design with clear interaction patterns

---

**Built with ❤️ for secure and reliable bot detection** 