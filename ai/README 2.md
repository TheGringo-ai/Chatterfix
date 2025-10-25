# ChatterFix AI Services

Multi-provider AI backend with predictive maintenance capabilities.

## Structure
- `services/` - AI microservices (Fix It Fred, AI Brain, Predictive Intelligence)
- `assistants/` - AI assistants (technician, terminal chat)
- `providers/` - AI provider integrations (OpenAI, Anthropic, Google, xAI, Ollama)
- `gateway/` - AI service gateways and proxies
- `utils/` - AI utilities and shared functions

## Supported Providers
- OpenAI GPT-4
- Anthropic Claude
- Google Gemini
- xAI Grok
- Local Ollama

## Getting Started
```bash
python services/fix_it_fred_service.py
```