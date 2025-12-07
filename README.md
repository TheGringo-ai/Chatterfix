# ChatterFix CMMS (Enhanced with AI)

[![Deploy to Production](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/deploy.yml/badge.svg)](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/deploy.yml)
[![Deploy to Cloud Run](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/deploy-cloud-run.yml/badge.svg)](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/deploy-cloud-run.yml)
[![Security Scan](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/security-scan.yml/badge.svg)](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/security-scan.yml)

This is the enhanced version of the ChatterFix CMMS application, combining modular architecture with advanced AI capabilities.

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

## New AI Features

### Voice Commands
POST `/ai/voice-command` - Process voice commands to create work orders
- Powered by Grok AI for intelligent command interpretation
- Automatic priority detection and work order creation

### Computer Vision
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
