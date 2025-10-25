#!/bin/bash

echo "🚀 ChatterFix CMMS - API Setup Script"
echo "===================================="

echo "📋 This script will help you set up OpenAI API integration for enhanced AI responses."
echo ""
echo "📝 You have two options:"
echo "   1. Use built-in CMMS intelligence (current setup)"
echo "   2. Add OpenAI API for advanced AI responses"
echo ""

read -p "Would you like to add OpenAI API integration? (y/N): " add_api

if [[ $add_api =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔑 OpenAI API Setup:"
    echo "   1. Visit: https://platform.openai.com/account/api-keys"
    echo "   2. Create a new API key"
    echo "   3. Copy the API key (starts with sk-)"
    echo ""
    
    read -p "Enter your OpenAI API key (or press Enter to skip): " api_key
    
    if [ ! -z "$api_key" ]; then
        echo "OPENAI_API_KEY=$api_key" > .env
        echo "✅ API key saved to .env file"
        echo ""
        echo "📊 Estimated costs for typical CMMS usage:"
        echo "   • Light usage (100 AI queries/month): ~$2-5"
        echo "   • Medium usage (500 AI queries/month): ~$8-15" 
        echo "   • Heavy usage (1000 AI queries/month): ~$15-30"
        echo ""
    else
        echo "⏭️  Skipping API key setup - using built-in intelligence"
    fi
else
    echo "✅ Using built-in ChatterFix CMMS intelligence"
fi

echo ""
echo "🎯 Setup complete! Your ChatterFix CMMS will use:"
if [ -f .env ] && grep -q "OPENAI_API_KEY" .env; then
    echo "   • OpenAI API for enhanced AI responses"
    echo "   • Fallback to built-in intelligence if API fails"
else
    echo "   • Built-in ChatterFix CMMS intelligence"
    echo "   • You can add API integration later by running this script again"
fi

echo ""
echo "🚀 Ready to deploy enhanced ChatterFix CMMS!"