# Chatterfix CMMS

![CI](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/ci-cd.yml/badge.svg)
![Deploy](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/deploy.yml/badge.svg)

A comprehensive Computerized Maintenance Management System (CMMS) with AI-powered features and full DevOps automation.

## 🚀 Features

- **AI-Enhanced Maintenance**: LLaMA-powered diagnostic assistance and predictive maintenance
- **Work Order Management**: Complete lifecycle tracking from creation to completion
- **Asset Management**: Comprehensive equipment tracking and maintenance history
- **Parts Intelligence**: Smart inventory management with predictive ordering
- **Voice Commands**: Natural language work order creation and updates
- **Mobile-First Design**: Optimized for technicians in the field
- **Real-Time Analytics**: Performance dashboards and KPI tracking

## 🛠️ Technology Stack

- **Backend**: FastAPI with SQLite database
- **Frontend**: Modern HTML5 with responsive CSS
- **AI**: LLaMA 3.1:8b via Ollama for intelligent assistance
- **Testing**: Pytest with comprehensive unit and performance tests
- **DevOps**: Full CI/CD pipeline with GitHub Actions
- **Security**: Pre-commit hooks, secret scanning, and vulnerability detection

## 📋 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend tools)
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/TheGringo-ai/Chatterfix.git
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

Visit `http://localhost:8000` to access the CMMS dashboard.

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

The application includes automated deployment workflows:

- **Staging**: Automatic deployment on push to `develop` branch
- **Production**: Deployment on push to `main` branch with manual approval
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
- ✅ AI integration active
- ✅ Full DevOps automation
- ✅ Comprehensive testing framework
- ✅ Production deployment ready
- 🔄 Continuous improvements and feature additions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Claude Code](https://claude.ai/code) for AI-assisted development
- LLaMA integration for intelligent maintenance assistance
- FastAPI framework for robust backend architecture
- GitHub Actions for seamless CI/CD automation# GCP authentication configured Sat Sep 20 11:20:53 CDT 2025
# Test deployment trigger Sat Sep 20 11:31:36 CDT 2025
# Deployment test for renamed repo Sat Sep 20 11:36:33 CDT 2025
# Test post-formatting deployment Sat Sep 20 11:46:50 CDT 2025
# Deploy AI assistant to production Sat Sep 20 12:34:42 CDT 2025
# Force deployment refresh Sat Sep 20 12:37:37 CDT 2025
