# ChatterFix CMMS

![CI](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/ci-cd.yml/badge.svg)
![Deploy](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/deploy.yml/badge.svg)

A comprehensive Computerized Maintenance Management System (CMMS) with AI-powered features and full DevOps automation.

> **Latest Update**: Production-ready architecture with merged AI Empire features including multi-provider AI Brain service, Fix It Fred MVP, and comprehensive deployment automation. All working changes consolidated and validated for GCP deployment.

## 🚀 Features

### Core CMMS Features
- **AI-Enhanced Maintenance**: Multi-provider AI support (OpenAI, xAI, Anthropic, Ollama)
- **Work Order Management**: Complete lifecycle tracking from creation to completion
- **Asset Management**: Comprehensive equipment tracking and maintenance history
- **Parts Intelligence**: Smart inventory management with predictive ordering
- **Voice Commands**: Natural language work order creation and updates
- **Mobile-First Design**: Optimized for technicians in the field
- **Real-Time Analytics**: Performance dashboards and KPI tracking

### AI Brain Service
- Multi-provider AI integration with intelligent fallback
- Predictive maintenance and analytics
- Real-time insights and automation workflows
- 80+ error handlers for production stability

### Fix It Fred MVP
- Standalone AI maintenance assistant for lead generation
- Voice, photo analysis, and AI troubleshooting
- Freemium pricing model
- Lead generation funnel to ChatterFix CMMS

## 🛠️ Technology Stack

- **Backend**: FastAPI with PostgreSQL database
- **Frontend**: Modern HTML5 with responsive CSS
- **AI**: Multi-provider support (OpenAI, xAI, Anthropic, Ollama)
- **Testing**: Pytest with comprehensive unit and performance tests (18 passing)
- **DevOps**: Full CI/CD pipeline with GitHub Actions
- **Security**: Pre-commit hooks, secret scanning, and vulnerability detection
- **Cloud**: Google Cloud Platform (Cloud Run, Cloud SQL)
- **Architecture**: Microservices with 3 unified services (71% CPU reduction)

## 📋 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend tools)
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/TheGringo-ai/CXhatterfix.git
   cd CXhatterfix
   ```

2. **Set up development environment**
   ```bash
   # Install pre-commit hooks for code quality
   pip install pre-commit
   pre-commit install
   
   # Set up CMMS application
   cd core/cmms
   pip install -r requirements.txt
   ```

3. **Initialize database**
   ```bash
   python init_db.py
   ```

4. **Start the application**
   ```bash
   python app.py
   ```

Visit `http://localhost:8080` to access the CMMS dashboard.

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Unit tests
pytest core/cmms/tests/unit/ -v

# Performance testing
cd core/cmms/tests/performance
locust -f locustfile.py --host http://localhost:8000
```

## 🚀 Deployment

The application is production-ready with comprehensive deployment automation:

### Quick Deployment to GCP

```bash
# Validate deployment readiness
./validate-deployment-readiness.sh

# Deploy to Google Cloud Platform
cd core/cmms
./deployment/deploy-consolidated-services.sh

# Validate AI endpoints
./deployment/validate-ai-endpoints.sh
```

### Deployment Options
- **GCP Cloud Run**: Automated deployment with 3 unified services
- **Local Development**: Run locally with `python app.py`
- **Docker**: Containerized deployment with provided Dockerfiles

### Documentation
- 📖 **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- ✅ **[Deployment Checklist](DEPLOYMENT_CHECKLIST.md)** - Quick reference checklist
- 🔧 **[Fix It Fred Guide](core/cmms/FIX_IT_FRED_README.md)** - Standalone service deployment
- 🤖 **[TechBot Guide](core/cmms/TECHBOT_DEPLOYMENT_GUIDE.md)** - AI assistant deployment

### Architecture
- **Backend Unified Service**: Database + Work Orders + Assets + Parts (1 CPU)
- **AI Unified Service**: AI Brain + Document Intelligence (1 CPU)
- **Frontend Gateway**: Main UI and API Gateway (1 CPU)

### Deployment Workflows
- **Staging**: Automatic deployment on push to `develop` branch
- **Production**: Deployment on push to `main` branch with validation
- **Rollback**: One-click rollback capability with automated backups

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and ensure tests pass
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📊 Project Status

- ✅ Core CMMS functionality complete
- ✅ AI Brain Service with multi-provider support deployed
- ✅ Fix It Fred MVP ready for production
- ✅ Full DevOps automation with CI/CD
- ✅ Comprehensive testing framework (18 unit tests passing)
- ✅ Production deployment validated and ready
- ✅ All working changes merged from relevant branches
- ✅ GCP deployment scripts and documentation complete
- 🚀 Ready for production deployment to Google Cloud Platform

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Claude Code](https://claude.ai/code) for AI-assisted development
- Multi-provider AI integration (OpenAI, xAI, Anthropic, Ollama)
- FastAPI framework for robust backend architecture
- GitHub Actions for seamless CI/CD automation
- Google Cloud Platform for scalable infrastructure
