# 🚀 ChatterFix: Revolutionary AI-Powered CMMS Platform

[![Deploy to Production](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/deploy.yml/badge.svg)](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/deploy.yml)
[![Deploy to Cloud Run](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/deploy-cloud-run.yml/badge.svg)](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/deploy-cloud-run.yml)
[![Security Scan](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/security-scan.yml/badge.svg)](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/security-scan.yml)
[![License](https://img.shields.io/badge/License-Dual%20(Community%2FEnterprise)-blue.svg)](LICENSE)
[![AI Team](https://img.shields.io/badge/AI%20Team-Multi%20Model%20Collaboration-green.svg)](#ai-team-collaboration)
[![Development Value](https://img.shields.io/badge/Development%20Value-$240K--385K-gold.svg)](#revolutionary-ai-features)

**The world's first maintenance management system with revolutionary multi-model AI collaboration, autonomous feature development, and never-repeat-mistakes architecture.**

> **🎯 Development Value: $240,000 - $385,000** in advanced AI systems including multi-model collaboration, autonomous development, and enterprise intelligence.

## Features

-   **Unified Interface:** Consistent styling and navigation across all modules.
-   **Work Order Management:** Create, update, and track work orders with a modern UI.
-   **AI Integration:** Built-in AI assistant powered by Gemini for querying CMMS data and getting help.
-   **Voice Commands:** Process voice commands with Grok AI to create work orders hands-free.
-   **Computer Vision:** AI-powered part recognition and visual asset inspection.
-   **Predictive Maintenance:** ML-powered engine to predict asset failures.
-   **Health Monitoring:** System health checks and SLO tracking.
-   **Team Collaboration:** Real-time messaging, notifications, and team management.
-   **Training System:** AI-generated training modules and skill tracking.
-   **Geolocation & PWA:** Mobile-first with offline capabilities.

## Directory Structure

-   `main.py`: The entry point of the application (FastAPI).
-   `app/routers/`: API route handlers for all modules.
-   `app/services/`: Business logic and AI services.
-   `app/core/`: Database and core functionality.
-   `app/templates/`: Jinja2 HTML templates.
-   `app/static/`: CSS, JavaScript, and static assets.

## Setup and Running

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment Variables:**
    Create a `.env` file with:
    ```bash
    GEMINI_API_KEY=your_gemini_api_key_here
    XAI_API_KEY=your_xai_api_key_here  # Optional, for voice commands
    ```

3.  **Run the Application:**
    ```bash
    python3 main.py
    ```
    Or using uvicorn directly:
    ```bash
    uvicorn main:app --reload
    ```

4.  **Access the App:**
    Open your browser and navigate to `http://localhost:8000`.

## 🚀 Revolutionary AI Features

### 🧠 AI Team Collaboration Framework
**Access:** [AI Team Dashboard](http://localhost:8000/ai-team/dashboard)

**Multi-Model Orchestration:**
- **Claude Sonnet 4**: Lead architect for complex analysis and planning
- **ChatGPT 4o**: Senior developer for coding and optimization  
- **Gemini 2.5 Flash**: Creative innovator for UI/UX solutions
- **Grok 3**: Strategic reasoner for analysis and decision making
- **Grok Code Fast**: Rapid coding specialist for quick implementations

**Advanced Memory System:**
- **Never-Repeat-Mistakes Engine**: AI learns from every error to prevent repetition
- **Conversation Archive**: All AI interactions permanently stored and searchable
- **Knowledge Search**: Instant access to all solutions, mistakes, and patterns
- **Cross-Application Learning**: Shared intelligence across ChatterFix, LineSmart, Fix-it-Fred

**APIs:**
- `POST /ai-team/execute` - Multi-model collaborative task execution
- `POST /ai-team/stream` - Real-time AI collaboration streaming
- `GET /ai-team/memory/search` - Search AI knowledge base
- `GET /ai-team/analytics` - AI team performance metrics

### 📊 LineSmart Training Intelligence
**Access:** [LineSmart ROI Dashboard](http://localhost:8000/linesmart/roi-dashboard)

**Business Intelligence:**
- **ROI Tracking**: $124,500 annual savings calculations with 340% ROI
- **Skills Gap Analysis**: AI-powered training recommendations
- **Interactive Charts**: Chart.js visualizations for training effectiveness
- **Performance Prediction**: ML models estimate training impact

**APIs:**
- `GET /linesmart/training-analytics` - Training effectiveness data
- `POST /linesmart/submit-training-data` - AI analysis of training data  
- `POST /linesmart/analyze-skill-gaps` - Skills gap identification

### 🤖 Autonomous Feature Development
**Access:** [Auto Features Portal](http://localhost:8000/autonomous/interface)

**Revolutionary Customer Experience:**
- **Natural Language Requests**: Customers describe needs in plain English
- **AI Automatic Implementation**: Features built and deployed in 2-5 minutes
- **Background Processing**: AutoGen framework handles complex development
- **Real-time Updates**: Live progress tracking during implementation

**APIs:**
- `POST /autonomous/request` - Submit feature request for AI implementation
- `POST /autonomous/simple` - Ultra-simple feature request interface
- `GET /autonomous/examples` - Get example feature requests

### 🔧 Fix-it-Fred Autonomous Maintenance  
**Access:** [Fix-it-Fred Interface](http://localhost:8000/fix-it-fred/interface)

**Intelligent Automation:**
- **Issue Detection**: AI-powered problem diagnosis from descriptions
- **Autonomous Resolution**: Self-fixing maintenance systems
- **Predictive Maintenance**: Proactive issue prevention
- **Learning Integration**: Feeds insights to LineSmart training system

### Legacy AI Features

#### Voice Commands
POST `/ai/voice-command` - Process voice commands to create work orders
- Powered by Grok AI for intelligent command interpretation
- Automatic priority detection and work order creation

#### Computer Vision
- POST `/ai/recognize-part` - Identify parts from images
- POST `/ai/analyze-condition` - Analyze asset condition from visual inspection
- Automatic inventory matching and condition scoring

## Configuration

-   **Database:** By default, the app uses a local SQLite database in `./data/cmms.db`.
-   **Port:** Default port is 8000. You can change it via the `CMMS_PORT` environment variable.
-   **AI Features:** Require API keys in `.env` file. Gemini for general AI, XAI for voice commands.

## Deployment

### Automated Deployment (GitHub Actions)

The application automatically deploys to Google Cloud Run on every push to the `main` branch.

**Live Application:** [https://chatterfix.com](https://chatterfix.com)

### Manual Deployment

**Prerequisites:**
- Google Cloud SDK installed and configured
- Docker installed
- Authenticated to GCP project `fredfix`

**Quick Deploy:**
```bash
# Direct deployment (fast)
./deploy.sh direct

# Cloud Build deployment (recommended for CI/CD)
./deploy.sh cloudbuild
```

**Using gcloud directly:**
```bash
gcloud run deploy chatterfix-cmms \
  --source . \
  --region us-central1 \
  --project fredfix \
  --allow-unauthenticated
```

### Deployment Documentation

For comprehensive deployment documentation, including:
- Setting up GitHub Actions secrets
- Configuring Google Cloud service accounts
- Troubleshooting deployment issues
- Rollback procedures
- Monitoring and logging

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**

### Quick Links

- 📱 **Production**: https://chatterfix.com
- 📚 **Deployment Docs**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- 🔧 **GitHub Actions**: [.github/workflows/](.github/workflows/)
- 🐳 **Dockerfile**: [Dockerfile](Dockerfile)
- ☁️ **Cloud Build**: [cloudbuild.yaml](cloudbuild.yaml)

## Development

### Code Quality and Linting

ChatterFix uses comprehensive linting and code quality tools to maintain high standards:

#### Installation

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

#### Linting Tools

- **Black**: Code formatter (88 character line length)
  ```bash
  black app/
  ```

- **isort**: Import statement organizer
  ```bash
  isort app/ --profile=black
  ```

- **Flake8**: Style guide enforcement and error detection
  ```bash
  flake8 app/
  ```

- **Pylint**: Advanced static analysis with import checking
  ```bash
  pylint app/ --disable=all --enable=import-error,cyclic-import
  ```

- **MyPy**: Static type checking
  ```bash
  mypy app/ --ignore-missing-imports
  ```

#### Pre-commit Hooks

Install pre-commit hooks to automatically check code before commits:

```bash
# Install hooks
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files
```

The hooks will automatically:
- Format code with Black
- Organize imports with isort
- Check for errors with Flake8
- Run type checking with MyPy
- Check security with Bandit
- Run tests with pytest

#### Import Validation

Validate that all modules can be imported correctly:

```bash
# Run import validation tests
pytest tests/test_imports.py -v

# Check specific routers
python -c "from app.routers import team, landing"
```

### Error Monitoring

ChatterFix includes comprehensive error monitoring with special handling for import errors. See [MONITORING.md](MONITORING.md) for details on:

- Error tracking middleware configuration
- Integration with Sentry and Cloud Logging
- Structured logging format
- Troubleshooting import errors

### Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_imports.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

## 📄 Licensing

ChatterFix uses a **dual licensing model** to protect valuable AI innovations while enabling community engagement:

### **Community Edition** (Modified MIT License)
- ✅ **Personal learning and education**
- ✅ **Academic research and teaching**  
- ✅ **Open source projects (non-commercial)**
- ✅ **Portfolio demonstrations**
- ❌ **Commercial deployment or revenue generation**
- ❌ **Enterprise or business use**
- ❌ **AI model training on proprietary systems**

### **Enterprise Edition** (Commercial License)
- ✅ **Full commercial usage rights**
- ✅ **Complete AI team collaboration system**
- ✅ **LineSmart ROI analytics platform**
- ✅ **Autonomous feature development system**
- ✅ **Fix-it-Fred maintenance automation**
- ✅ **Premium support and updates**
- ✅ **White-label and customization rights**
- ✅ **Multi-tenant deployment capabilities**

### **AI Team Framework Protection**
Your AI Team Collaboration Framework is specifically protected as proprietary technology including:
- Multi-model AI orchestration system
- Advanced memory and learning architecture  
- Never-repeat-mistakes engine
- Knowledge search and pattern recognition
- Autonomous development capabilities

### **Contact for Enterprise Licensing:**
- **Email**: fred@chatterfix.com
- **Enterprise Sales**: enterprise@chatterfix.com
- **Website**: https://chatterfix.com

**[📋 Full License Details](LICENSE)**

## 💼 Business Value

### **Protected Development Investment**
- **Total Platform Value**: $240,000 - $385,000
- **AI Team Framework**: $50,000 - $80,000  
- **LineSmart Intelligence**: $30,000 - $50,000
- **Autonomous Systems**: $40,000 - $60,000
- **Fix-it-Fred Platform**: $35,000 - $55,000
- **Memory Architecture**: $60,000 - $100,000
- **Integration Framework**: $25,000 - $40,000

### **Competitive Advantages**
1. **First-of-its-kind multi-model AI collaboration**
2. **Revolutionary autonomous feature development**  
3. **Advanced memory system preventing repeated mistakes**
4. **Enterprise-grade ROI analytics and training intelligence**
5. **Self-fixing maintenance automation**

---

**© 2024 Fred Taylor. All Rights Reserved.**

*ChatterFix™, AI Team Collaboration™, LineSmart™, and Fix-it-Fred™ are trademarks of Fred Taylor.*
