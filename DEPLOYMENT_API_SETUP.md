# Fix It Fred Deployment API Setup

## 🚀 Natural Language CI/CD with Fix It Fred

Fix It Fred now supports natural language deployment commands! Just ask Fred to deploy, and he'll handle commits, pushes, and deployment triggers automatically.

## 🔑 Required Environment Variables

Add these to your `.env` file or VM environment:

```bash
# GitHub Configuration
GITHUB_TOKEN=ghp_your_github_personal_access_token
GITHUB_REPO=your-username/your-repo
REPO_PATH=/path/to/your/repo

# Deployment API Security
DEPLOYMENT_API_KEY=your-secure-api-key-here

# Ollama Configuration (already set)
OLLAMA_HOST=http://localhost:11434
```

## 📝 GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
   - `write:packages` (if using packages)
4. Generate and copy the token
5. Add to `.env`: `GITHUB_TOKEN=ghp_...`

## 🎯 API Endpoints

### 1. Natural Language Deployment

**Endpoint:** `POST /api/fix-it-fred/deploy`

Ask Fred to deploy in plain English!

```bash
curl -X POST http://35.237.149.25:8080/api/fix-it-fred/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "command": "deploy to production",
    "api_key": "your-api-key"
  }'
```

**Supported Commands:**
- `"deploy to production"` - Trigger production deployment
- `"commit and push changes"` - Commit all changes and push
- `"ship it"` - Full deployment flow (commit + push + deploy)
- `"create a pull request"` - Create PR for review
- `"check git status"` - See what changed
- `"commit changes with message 'Fix bug in X'"` - Custom commit message

### 2. GitHub Status

**Endpoint:** `GET /api/github/status`

```bash
curl http://35.237.149.25:8080/api/github/status
```

**Response:**
```json
{
  "success": true,
  "has_changes": true,
  "changes": ["M app.py", "A new_file.py"],
  "change_count": 2
}
```

### 3. Direct Commit

**Endpoint:** `POST /api/github/commit`

```bash
curl -X POST http://35.237.149.25:8080/api/github/commit \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Update ChatterFix features",
    "api_key": "your-api-key"
  }'
```

If no message provided, AI will generate one based on git diff!

### 4. Trigger Deployment

**Endpoint:** `POST /api/github/deploy`

```bash
curl -X POST http://35.237.149.25:8080/api/github/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "production",
    "api_key": "your-api-key"
  }'
```

### 5. Inter-Service Communication

**Endpoint:** `POST /api/services/communicate`

For AI Brain, Parts Service, Assets Service to communicate with Fix It Fred:

```bash
curl -X POST http://35.237.149.25:8080/api/services/communicate \
  -H "Content-Type: application/json" \
  -d '{
    "source": "ai-brain",
    "target": "fix_it_fred",
    "action": "deploy",
    "payload": {
      "command": "deploy to production"
    }
  }'
```

**Actions:**
- `deploy` - Trigger deployment
- `troubleshoot` - Get HVAC troubleshooting help

## 🔒 Security

1. **API Key Authentication**: All deployment endpoints support optional API key authentication
2. **Set your API key**: `DEPLOYMENT_API_KEY` in environment variables
3. **GitHub Token**: Never commit your `GITHUB_TOKEN` - keep it in `.env` only

## 🤖 Examples

### Example 1: Full Deployment Flow

```python
import requests

response = requests.post(
    "http://35.237.149.25:8080/api/fix-it-fred/deploy",
    json={
        "command": "ship it",
        "api_key": "your-api-key"
    }
)

print(response.json())
# {
#   "success": true,
#   "action": "full_deploy",
#   "steps": [
#     {"step": "commit", "success": true},
#     {"step": "push", "success": true},
#     {"step": "deployment_triggered", "success": true}
#   ]
# }
```

### Example 2: AI-Generated Commit Messages

```python
# Commit without message - AI will generate based on git diff
response = requests.post(
    "http://35.237.149.25:8080/api/github/commit",
    json={"api_key": "your-api-key"}
)

# AI analyzes changes and creates message like:
# "Add Fix It Fred deployment API with natural language support"
```

### Example 3: Service-to-Service Communication

```python
# AI Brain asks Fix It Fred to deploy
response = requests.post(
    "http://35.237.149.25:8080/api/services/communicate",
    json={
        "source": "ai-brain",
        "target": "fix_it_fred",
        "action": "deploy",
        "payload": {
            "command": "deploy new AI features to production"
        }
    }
)
```

## 🎬 Quick Start

1. **Set up environment variables**:
   ```bash
   echo "GITHUB_TOKEN=ghp_your_token" >> .env
   echo "DEPLOYMENT_API_KEY=my-secure-key-2025" >> .env
   echo "REPO_PATH=$(pwd)" >> .env
   ```

2. **Test the API**:
   ```bash
   curl http://35.237.149.25:8080/api/github/status
   ```

3. **Deploy with Fred**:
   ```bash
   curl -X POST http://35.237.149.25:8080/api/fix-it-fred/deploy \
     -H "Content-Type: application/json" \
     -d '{"command": "check git status"}'
   ```

## 📚 Integration with Other Services

### From AI Brain:
```python
# AI Brain decides to deploy based on monitoring
await ai_brain.communicate_with_service(
    target="fix_it_fred",
    action="deploy",
    payload={"command": "deploy hotfix to production"}
)
```

### From Parts Service:
```python
# Low inventory triggers alert, ask Fred to troubleshoot
await parts_service.communicate_with_service(
    target="fix_it_fred",
    action="troubleshoot",
    payload={
        "equipment": "Compressor Unit 3",
        "issue_description": "Low refrigerant detected"
    }
)
```

## 🚨 Troubleshooting

**Issue:** "GitHub API not available"
- **Fix:** Ensure `GITHUB_TOKEN` is set in environment

**Issue:** "Invalid API key"
- **Fix:** Check `DEPLOYMENT_API_KEY` matches what you're sending

**Issue:** "Command not recognized"
- **Fix:** Use one of the supported natural language patterns
  - ✅ "deploy to production"
  - ✅ "ship it"
  - ❌ "make it go live" (not recognized yet)

## 🎉 Success!

You can now deploy ChatterFix CMMS by simply asking Fix It Fred! No more manual git commands - just talk to Fred like you would a DevOps engineer.

**"Hey Fred, ship this to production!"** 🚀
