# ChatterFix AI Configuration Guide

ChatterFix uses **Google Gemini** (not ChatGPT) for AI features. Here's how to set it up:

## 🤖 AI Integration Overview

**Current AI Features:**
- ✅ **Gemini AI** - Maintenance chat assistant
- ✅ **Predictive Maintenance** - Equipment failure prediction
- ✅ **Image Analysis** - Asset condition assessment
- ✅ **Training Generation** - Automated training content
- ✅ **Work Order Intelligence** - Smart prioritization

## 🔑 API Key Setup

### Option 1: Environment Variable (Recommended for Production)
```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

### Option 2: User-Specific Keys (In-App Configuration)
Users can add their own Gemini API keys in Settings → AI Configuration

### Option 3: System-Wide Setting
Administrators can set a system-wide key in the admin panel

## 🚀 Getting a Gemini API Key

1. **Go to Google AI Studio**
   - Visit: https://makersuite.google.com/app/apikey
   - Sign in with your Google account

2. **Create API Key**
   - Click "Create API Key"
   - Select your Google Cloud project (or create new)
   - Copy the generated key

3. **Set the Key**
   ```bash
   # For development
   echo "GEMINI_API_KEY=your_key_here" >> .env
   
   # For production deployment
   gcloud run services update chatterfix-cmms \
     --region=us-central1 \
     --set-env-vars="GEMINI_API_KEY=your_key_here"
   ```

## 🔧 API Key Priority

The system checks for API keys in this order:
1. **User-specific key** (from user settings)
2. **System-wide key** (from admin settings)  
3. **Environment variable** (GEMINI_API_KEY)

## 📋 Testing AI Features

### Health Check
```bash
curl https://chatterfix.com/health
# Should show: "status": "healthy"
```

### Test AI Chat
```bash
curl -X POST https://chatterfix.com/ai/chat \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "message=Hello AI assistant"
```

### Test Image Analysis
```bash
curl -X POST https://chatterfix.com/ai/analyze-image \
  -F "image=@path/to/equipment.jpg" \
  -F "prompt=Assess this equipment condition"
```

## ⚙️ Configuration Examples

### Local Development (.env file)
```bash
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
USE_FIRESTORE=false
LOG_LEVEL=debug
```

### Production (Environment Variables)
```bash
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
USE_FIRESTORE=true
GOOGLE_CLOUD_PROJECT=chatterfix-cmms
LOG_LEVEL=info
```

## 🛠️ Advanced AI Configuration

### Enable/Disable AI Features
In `app/services/ai_assistant.py`, you can configure:

```python
class ChatterFixAIClient:
    def __init__(self):
        # Enable/disable specific AI features
        self.enable_predictive = True
        self.enable_image_analysis = True
        self.enable_training_generation = True
```

### Custom AI Models
You can switch Gemini models:

```python
# In gemini_service.py
model = genai.GenerativeModel('gemini-pro')          # Text only
model = genai.GenerativeModel('gemini-pro-vision')   # Text + Images
```

## 💡 AI Feature Details

### 1. Maintenance Chat Assistant
- **Purpose**: Answer maintenance questions, provide guidance
- **Endpoint**: `/ai/chat`
- **Requirements**: Gemini API key

### 2. Image Analysis
- **Purpose**: Analyze equipment photos for condition assessment
- **Endpoint**: `/ai/analyze-image`
- **Requirements**: Gemini API key + vision model

### 3. Predictive Maintenance
- **Purpose**: Predict equipment failures using historical data
- **Implementation**: Built-in ML models + Gemini insights
- **Requirements**: Historical maintenance data

### 4. Training Content Generation
- **Purpose**: Generate training materials for technicians
- **Endpoint**: `/training/generate`
- **Requirements**: Gemini API key

## 🔒 Security & Best Practices

### API Key Security
- ✅ Store keys as environment variables
- ✅ Use user-specific keys when possible
- ✅ Never commit keys to version control
- ✅ Rotate keys regularly

### Rate Limiting
- Default: 100 requests/minute per user
- Configurable in `slowapi` settings

### Error Handling
- Graceful fallback when AI is unavailable
- User-friendly error messages
- Logging for debugging

## 🚨 Troubleshooting

### AI Features Not Working
```bash
# Check if API key is set
echo $GEMINI_API_KEY

# Check service logs
gcloud run logs read --service=chatterfix-cmms --region=us-central1 | grep -i "gemini\|ai"

# Test API key manually
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

### Common Issues
1. **Invalid API Key**: Check key format and permissions
2. **Quota Exceeded**: Monitor usage in Google Cloud Console
3. **Model Not Available**: Verify model name and region
4. **Network Issues**: Check firewall/proxy settings

## 📊 Monitoring AI Usage

### View Usage Stats
```bash
# AI interaction logs
gcloud run logs read --service=chatterfix-cmms \
  --filter="resource.labels.service_name=chatterfix-cmms AND textPayload:ai_interactions"
```

### Track API Costs
- Monitor in Google Cloud Console
- Set up billing alerts
- Review usage patterns

---

**🎯 Result**: ChatterFix with fully functional AI assistant powered by Google Gemini!