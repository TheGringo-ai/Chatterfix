# Fix It Fred Test Endpoint
# Add this to app.py to test hot reload

@app.get("/api/fix-it-fred-test")
async def fix_it_fred_test():
    """Test endpoint to verify Fix It Fred hot reload works"""
    return {
        "message": "🔥 Fix It Fred hot reload is working!",
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "deployment": "hot_reload",
        "version": "fix-it-fred-1.0.0"
    }