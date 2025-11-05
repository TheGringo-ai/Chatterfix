#!/usr/bin/env python3
"""
Fix Grok Integration - Update ChatterFix to use real Grok API
"""

import subprocess
import sys
import time

def run_command(cmd, description=""):
    """Run command and return result"""
    print(f"🔧 {description}")
    print(f"   Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"   ✅ Success: {result.stdout.strip()[:100]}...")
            return True
        else:
            print(f"   ❌ Error: {result.stderr.strip()[:100]}...")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ⏰ Timeout after 2 minutes")
        return False
    except Exception as e:
        print(f"   💥 Exception: {e}")
        return False

def main():
    """Fix Grok API integration"""
    print("🤖 ChatterFix Grok Integration Fix Starting...")
    print("=" * 50)
    
    # Step 1: Update environment variables
    print("\n📋 Step 1: Setting up environment...")
    run_command('export XAI_API_KEY=$(gcloud secrets versions access latest --secret="xai-api-key" --project=fredfix)', 
                "Getting XAI API key from GCP secrets")
    
    # Step 2: Deploy with correct environment
    print("\n🚀 Step 2: Deploying with Grok integration...")
    
    deploy_cmd = '''
    cd /Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms && \
    gcloud run deploy chatterfix \
        --source . \
        --platform managed \
        --region us-central1 \
        --allow-unauthenticated \
        --set-env-vars="XAI_API_KEY=$(gcloud secrets versions access latest --secret='xai-api-key' --project=fredfix)" \
        --memory 2Gi \
        --cpu 2 \
        --timeout 300 \
        --max-instances 10 \
        --project fredfix
    '''
    
    success = run_command(deploy_cmd, "Deploying ChatterFix with Grok integration")
    
    if success:
        print("\n🎉 Step 3: Testing Grok integration...")
        time.sleep(30)  # Wait for deployment
        
        # Test the sales AI with Grok
        test_cmd = '''
        curl -s -X POST "https://chatterfix.com/api/sales-ai" \
            -H "Content-Type: application/json" \
            -d '{"message":"What makes ChatterFix better than competitors for a manufacturing company?","context":"sales"}' \
            | jq .
        '''
        
        run_command(test_cmd, "Testing Grok-powered sales AI")
        
        print("\n✅ Grok integration fix completed!")
        print("🔗 Test at: https://chatterfix.com")
        print("💬 Sales chat should now use Grok AI for intelligent responses")
        
    else:
        print("\n❌ Deployment failed. Check logs and try again.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)