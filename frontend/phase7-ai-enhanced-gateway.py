#!/usr/bin/env python3
"""
🚀 ChatterFix CMMS - Phase 7 AI-Enhanced Gateway
Intelligent CMMS with predictive maintenance and AI insights
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import json
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix CMMS Phase 7 AI-Enhanced Gateway", version="7.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs and API keys
CHATTERFIX_API_KEY = os.getenv("CHATTERFIX_API_KEY", "chatterfix_secure_api_key_2025_cmms_prod_v1")

SERVICES = {
    "work_orders": os.getenv("WORK_ORDERS_URL", "https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app"),
    "assets": os.getenv("ASSETS_URL", "https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app"),
    "parts": os.getenv("PARTS_URL", "https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app"),
}

async def proxy_request(service_url: str, path: str, request: Request):
    """Proxy requests to backend services with performance optimizations"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{service_url.rstrip('/')}/{path.lstrip('/')}"
        
        # Forward headers
        headers = dict(request.headers)
        headers.pop('host', None)
        headers["x-api-key"] = CHATTERFIX_API_KEY
        
        try:
            if request.method == "GET":
                response = await client.get(url, headers=headers, params=request.query_params)
            elif request.method == "POST":
                body = await request.body()
                response = await client.post(url, headers=headers, content=body, params=request.query_params)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            return response
            
        except httpx.TimeoutException:
            logger.error(f"Timeout calling {url}")
            raise HTTPException(status_code=504, detail="Service timeout")
        except httpx.RequestError as e:
            logger.error(f"Request error calling {url}: {e}")
            raise HTTPException(status_code=502, detail="Service unavailable")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "7.0.0", "features": ["ai", "predictive_maintenance", "anomaly_detection"]}

# API Proxy endpoints
@app.api_route("/api/work-orders/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def work_orders_proxy(path: str, request: Request):
    """Proxy to work orders service"""
    response = await proxy_request(SERVICES["work_orders"], f"work_orders/{path}", request)
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text

@app.api_route("/api/assets/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def assets_proxy(path: str, request: Request):
    """Proxy to assets service"""
    response = await proxy_request(SERVICES["assets"], f"assets/{path}", request)
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text

@app.api_route("/api/parts/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def parts_proxy(path: str, request: Request):
    """Proxy to parts service"""
    response = await proxy_request(SERVICES["parts"], f"parts/{path}", request)
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text

# AI endpoints
@app.api_route("/api/predictive-maintenance", methods=["GET"])
async def predictive_maintenance_proxy(request: Request):
    """Proxy to predictive maintenance endpoint"""
    response = await proxy_request(SERVICES["work_orders"], "predictive_maintenance", request)
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text

@app.api_route("/api/ai-insights", methods=["GET"])
async def ai_insights_proxy(request: Request):
    """Proxy to AI insights endpoint"""
    response = await proxy_request(SERVICES["work_orders"], "insights/summary", request)
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text

@app.api_route("/api/alerts", methods=["GET"])
async def alerts_proxy(request: Request):
    """Proxy to anomaly alerts endpoint"""
    response = await proxy_request(SERVICES["work_orders"], "alerts", request)
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text

@app.api_route("/api/analytics/log", methods=["POST"])
async def analytics_proxy(request: Request):
    """Proxy to analytics logging endpoint"""
    response = await proxy_request(SERVICES["work_orders"], "api/analytics/log", request)
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """AI-Enhanced dashboard with predictive maintenance and intelligent insights"""
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatterFix AI CMMS - Intelligent Maintenance Platform</title>
    
    <!-- Performance: Critical CSS inline -->
    <style>
        body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; }
        .loading-skeleton { background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%); background-size: 200% 100%; animation: loading 1.5s infinite; }
        @keyframes loading { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
        .hidden { display: none !important; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .nav-tabs .nav-link.active { background-color: #007bff; color: white; }
        .risk-high { color: #dc3545; }
        .risk-medium { color: #fd7e14; }
        .risk-low { color: #28a745; }
        .ai-tag { background: linear-gradient(45deg, #667eea, #764ba2); color: white; font-size: 0.7em; padding: 2px 6px; border-radius: 3px; }
    </style>
    
    <!-- Preload critical resources -->
    <link rel="preload" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" as="style">
    <link rel="preload" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" as="style">
    
    <!-- Analytics -->
    <script>
        function logAnalytics(action, endpoint, extra = {}) {
            const data = {
                timestamp: new Date().toISOString(),
                endpoint: endpoint,
                action: action,
                session_id: sessionStorage.getItem('session_id') || 'anonymous',
                ...extra
            };
            
            fetch('/api/analytics/log', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).catch(console.warn);
        }
        
        if (!sessionStorage.getItem('session_id')) {
            sessionStorage.setItem('session_id', 'sess_' + Math.random().toString(36).substr(2, 9));
        }
    </script>
    
    <!-- Deferred CSS loading -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" media="print" onload="this.media='all'">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" media="print" onload="this.media='all'">
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg" style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div class="container-fluid">
            <a class="navbar-brand text-white fw-bold" href="/">
                <i class="fas fa-brain me-2"></i>ChatterFix AI CMMS
            </a>
            
            <div class="mx-auto" style="flex: 1; max-width: 600px;">
                <div class="input-group">
                    <span class="input-group-text bg-white border-0">
                        <i class="fas fa-search text-muted"></i>
                    </span>
                    <input type="text" 
                           id="globalSearch" 
                           class="form-control border-0" 
                           placeholder="Search with AI assistance..." 
                           style="box-shadow: none;">
                    <button class="btn btn-outline-light" type="button" id="aiSearchBtn">
                        <i class="fas fa-magic"></i>
                    </button>
                </div>
            </div>
            
            <div class="d-flex">
                <button class="btn btn-outline-light me-2" onclick="refreshDashboard()">
                    <i class="fas fa-sync-alt" id="refreshIcon"></i>
                </button>
                <span class="text-white">AI Edition</span>
            </div>
        </div>
    </nav>

    <div class="container-fluid py-4">
        
        <!-- Tab Navigation -->
        <ul class="nav nav-tabs mb-4" id="mainTabs">
            <li class="nav-item">
                <a class="nav-link active" id="overview-tab" data-bs-toggle="tab" href="#overview">
                    <i class="fas fa-tachometer-alt me-2"></i>Overview
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" id="ai-insights-tab" data-bs-toggle="tab" href="#ai-insights">
                    <i class="fas fa-brain me-2"></i>AI Insights
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" id="predictions-tab" data-bs-toggle="tab" href="#predictions">
                    <i class="fas fa-chart-line me-2"></i>Predictive Maintenance
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" id="alerts-tab" data-bs-toggle="tab" href="#alerts">
                    <i class="fas fa-exclamation-triangle me-2"></i>Anomaly Alerts
                </a>
            </li>
        </ul>
        
        <!-- Tab Content -->
        <div class="tab-content" id="mainTabContent">
            
            <!-- Overview Tab -->
            <div class="tab-content active" id="overview">
                <div class="row mb-4">
                    <div class="col-12">
                        <h2 class="mb-4 text-dark fw-bold">
                            <i class="fas fa-brain me-2" style="color: #667eea;"></i>
                            Intelligent Operations Dashboard
                            <span class="ai-tag ms-2">AI Powered</span>
                        </h2>
                    </div>
                    
                    <!-- KPI Cards -->
                    <div class="col-lg-3 col-md-6 mb-4">
                        <div class="card border-0 shadow-sm h-100" style="border-radius: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                            <div class="card-body text-center text-white">
                                <div class="d-flex justify-content-between align-items-start mb-3">
                                    <i class="fas fa-tasks fa-2x opacity-75"></i>
                                    <span class="badge bg-light text-dark">AI Optimized</span>
                                </div>
                                <div class="loading-skeleton mb-2" id="skeleton-work-orders" style="height: 40px; border-radius: 8px;"></div>
                                <h2 class="fw-bold mb-1 hidden" id="total-work-orders">0</h2>
                                <p class="mb-2 opacity-90">Smart Work Orders</p>
                                <div class="d-flex justify-content-between">
                                    <small class="opacity-75">
                                        <span id="completion-percentage">0</span>% Completed
                                    </small>
                                    <small class="opacity-75">
                                        <span id="open-work-orders">0</span> Open
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-lg-3 col-md-6 mb-4">
                        <div class="card border-0 shadow-sm h-100" style="border-radius: 15px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                            <div class="card-body text-center text-white">
                                <div class="d-flex justify-content-between align-items-start mb-3">
                                    <i class="fas fa-shield-alt fa-2x opacity-75"></i>
                                    <span class="badge bg-light text-dark">Predicted</span>
                                </div>
                                <div class="loading-skeleton mb-2" id="skeleton-predictions" style="height: 40px; border-radius: 8px;"></div>
                                <h2 class="fw-bold mb-1 hidden" id="high-risk-assets">0</h2>
                                <p class="mb-2 opacity-90">High Risk Assets</p>
                                <div class="d-flex justify-content-between">
                                    <small class="opacity-75">
                                        <span id="medium-risk-assets">0</span> Medium
                                    </small>
                                    <small class="opacity-75">
                                        <span id="low-risk-assets">0</span> Low
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-lg-3 col-md-6 mb-4">
                        <div class="card border-0 shadow-sm h-100" style="border-radius: 15px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                            <div class="card-body text-center text-white">
                                <div class="d-flex justify-content-between align-items-start mb-3">
                                    <i class="fas fa-exclamation-triangle fa-2x opacity-75"></i>
                                    <span class="badge bg-light text-dark">Live</span>
                                </div>
                                <div class="loading-skeleton mb-2" id="skeleton-anomalies" style="height: 40px; border-radius: 8px;"></div>
                                <h2 class="fw-bold mb-1 hidden" id="active-anomalies">0</h2>
                                <p class="mb-2 opacity-90">Active Anomalies</p>
                                <div class="d-flex justify-content-between">
                                    <small class="opacity-75">
                                        <span id="critical-anomalies">0</span> Critical
                                    </small>
                                    <small class="opacity-75">
                                        <span id="warning-anomalies">0</span> Warning
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-lg-3 col-md-6 mb-4">
                        <div class="card border-0 shadow-sm h-100" style="border-radius: 15px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                            <div class="card-body text-center text-white">
                                <div class="d-flex justify-content-between align-items-start mb-3">
                                    <i class="fas fa-robot fa-2x opacity-75"></i>
                                    <span class="badge bg-light text-dark">AI Score</span>
                                </div>
                                <div class="loading-skeleton mb-2" id="skeleton-ai-score" style="height: 40px; border-radius: 8px;"></div>
                                <h2 class="fw-bold mb-1 hidden" id="ai-confidence-score">0</h2>
                                <p class="mb-2 opacity-90">AI Confidence</p>
                                <div class="d-flex justify-content-between">
                                    <small class="opacity-75">Model v1.0</small>
                                    <small class="opacity-75">
                                        <i class="fas fa-arrow-up me-1"></i><span id="confidence-trend">+2</span>%
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- AI Insights Tab -->
            <div class="tab-content" id="ai-insights">
                <div class="row">
                    <div class="col-lg-8 mb-4">
                        <div class="card border-0 shadow-sm" style="border-radius: 15px;">
                            <div class="card-header bg-transparent border-0 py-3">
                                <h5 class="mb-0 d-flex align-items-center">
                                    <i class="fas fa-brain me-2 text-primary"></i>
                                    AI Operational Summary
                                    <span class="ai-tag ms-2">Generated by AI</span>
                                    <button class="btn btn-sm btn-outline-primary ms-auto" onclick="regenerateAISummary()">
                                        <i class="fas fa-magic"></i> Regenerate
                                    </button>
                                </h5>
                            </div>
                            <div class="card-body">
                                <div id="ai-summary-skeleton">
                                    <div class="loading-skeleton mb-3" style="height: 20px; border-radius: 8px; width: 90%;"></div>
                                    <div class="loading-skeleton mb-3" style="height: 20px; border-radius: 8px; width: 75%;"></div>
                                    <div class="loading-skeleton mb-3" style="height: 20px; border-radius: 8px; width: 85%;"></div>
                                </div>
                                <div id="ai-summary-content" class="hidden">
                                    <!-- AI summary will be loaded here -->
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-lg-4 mb-4">
                        <div class="card border-0 shadow-sm" style="border-radius: 15px;">
                            <div class="card-header bg-transparent border-0 py-3">
                                <h5 class="mb-0">
                                    <i class="fas fa-lightbulb me-2 text-warning"></i>
                                    AI Recommendations
                                </h5>
                            </div>
                            <div class="card-body">
                                <div id="ai-recommendations-content">
                                    <!-- AI recommendations will be loaded here -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-12">
                        <div class="card border-0 shadow-sm" style="border-radius: 15px;">
                            <div class="card-header bg-transparent border-0 py-3">
                                <h5 class="mb-0">
                                    <i class="fas fa-search me-2 text-info"></i>
                                    Asset-Specific AI Insights
                                </h5>
                            </div>
                            <div class="card-body">
                                <div id="asset-insights-content">
                                    <!-- Asset insights will be loaded here -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Predictive Maintenance Tab -->
            <div class="tab-content" id="predictions">
                <div class="row">
                    <div class="col-lg-8 mb-4">
                        <div class="card border-0 shadow-sm" style="border-radius: 15px;">
                            <div class="card-header bg-transparent border-0 py-3">
                                <h5 class="mb-0 d-flex align-items-center">
                                    <i class="fas fa-chart-line me-2 text-success"></i>
                                    Top 5 At-Risk Assets
                                    <span class="ai-tag ms-2">ML Predicted</span>
                                </h5>
                            </div>
                            <div class="card-body">
                                <div id="predictions-content">
                                    <!-- Predictions will be loaded here -->
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-lg-4 mb-4">
                        <div class="card border-0 shadow-sm" style="border-radius: 15px;">
                            <div class="card-header bg-transparent border-0 py-3">
                                <h5 class="mb-0">
                                    <i class="fas fa-chart-pie me-2 text-primary"></i>
                                    Risk Distribution
                                </h5>
                            </div>
                            <div class="card-body">
                                <div id="risk-distribution-content">
                                    <!-- Risk distribution will be loaded here -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Anomaly Alerts Tab -->
            <div class="tab-content" id="alerts">
                <div class="row">
                    <div class="col-12 mb-4">
                        <div class="card border-0 shadow-sm" style="border-radius: 15px;">
                            <div class="card-header bg-transparent border-0 py-3">
                                <h5 class="mb-0 d-flex align-items-center">
                                    <i class="fas fa-exclamation-triangle me-2 text-danger"></i>
                                    Real-Time Anomaly Detection
                                    <span class="ai-tag ms-2">Statistical Analysis</span>
                                    <button class="btn btn-sm btn-outline-danger ms-auto" onclick="refreshAnomalies()">
                                        <i class="fas fa-sync-alt"></i> Refresh
                                    </button>
                                </h5>
                            </div>
                            <div class="card-body">
                                <div id="anomalies-content">
                                    <!-- Anomalies will be loaded here -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Performance: Load JavaScript at end -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Enhanced API cache for AI endpoints
        class AICache {
            constructor(ttl = 30000) {
                this.cache = new Map();
                this.ttl = ttl;
            }
            
            get(key) {
                const item = this.cache.get(key);
                if (!item) return null;
                
                if (Date.now() - item.timestamp > this.ttl) {
                    this.cache.delete(key);
                    return null;
                }
                
                return item.data;
            }
            
            set(key, data) {
                this.cache.set(key, {
                    data: data,
                    timestamp: Date.now()
                });
            }
        }
        
        const aiCache = new AICache();
        
        // Enhanced fetch with AI analytics
        async function fetchWithCache(url, options = {}) {
            const cacheKey = url + JSON.stringify(options);
            
            const cached = aiCache.get(cacheKey);
            if (cached && !options.skipCache) {
                return cached;
            }
            
            try {
                const startTime = performance.now();
                const response = await fetch(url, options);
                
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const data = await response.json();
                const duration = performance.now() - startTime;
                
                logAnalytics('ai_api_request', url, {
                    duration_ms: Math.round(duration),
                    status: 'success',
                    ai_powered: url.includes('ai-insights') || url.includes('predictive') || url.includes('alerts')
                });
                
                aiCache.set(cacheKey, data);
                return data;
                
            } catch (error) {
                logAnalytics('ai_api_request', url, {
                    status: 'error',
                    error: error.message
                });
                throw error;
            }
        }
        
        // Animation helpers
        function animateCounter(element, start, end, duration = 1000) {
            const startTimestamp = performance.now();
            const step = (timestamp) => {
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                const value = Math.floor(progress * (end - start) + start);
                element.textContent = value.toLocaleString();
                
                if (progress < 1) {
                    requestAnimationFrame(step);
                }
            };
            requestAnimationFrame(step);
        }
        
        function showContent(skeletonId, contentId) {
            document.getElementById(skeletonId).classList.add('hidden');
            document.getElementById(contentId).classList.remove('hidden');
        }
        
        // Load dashboard overview data
        async function loadDashboardData() {
            logAnalytics('page_view', 'ai_dashboard');
            
            try {
                const [workOrdersData, predictionsData, alertsData] = await Promise.all([
                    fetchWithCache('/api/work-orders/'),
                    fetchWithCache('/api/predictive-maintenance'),
                    fetchWithCache('/api/alerts')
                ]);
                
                // Update KPI cards
                const totalWorkOrders = workOrdersData.work_orders?.length || 0;
                const completedWorkOrders = workOrdersData.work_orders?.filter(wo => wo.status === 'Completed').length || 0;
                const completionRate = totalWorkOrders > 0 ? Math.round((completedWorkOrders / totalWorkOrders) * 100) : 0;
                
                showContent('skeleton-work-orders', 'total-work-orders');
                animateCounter(document.getElementById('total-work-orders'), 0, totalWorkOrders);
                animateCounter(document.getElementById('completion-percentage'), 0, completionRate);
                animateCounter(document.getElementById('open-work-orders'), 0, totalWorkOrders - completedWorkOrders);
                
                // Predictions data
                const highRiskAssets = predictionsData.summary?.risk_distribution?.high || 0;
                const mediumRiskAssets = predictionsData.summary?.risk_distribution?.medium || 0;
                const lowRiskAssets = predictionsData.summary?.risk_distribution?.low || 0;
                
                showContent('skeleton-predictions', 'high-risk-assets');
                animateCounter(document.getElementById('high-risk-assets'), 0, highRiskAssets);
                animateCounter(document.getElementById('medium-risk-assets'), 0, mediumRiskAssets);
                animateCounter(document.getElementById('low-risk-assets'), 0, lowRiskAssets);
                
                // Anomalies data
                const activeAnomalies = alertsData.alerts?.alert_summary?.total || 0;
                const criticalAnomalies = alertsData.alerts?.alert_summary?.critical || 0;
                const warningAnomalies = alertsData.alerts?.alert_summary?.high || 0;
                
                showContent('skeleton-anomalies', 'active-anomalies');
                animateCounter(document.getElementById('active-anomalies'), 0, activeAnomalies);
                animateCounter(document.getElementById('critical-anomalies'), 0, criticalAnomalies);
                animateCounter(document.getElementById('warning-anomalies'), 0, warningAnomalies);
                
                // AI confidence score (simulated)
                const aiScore = Math.round(85 + Math.random() * 10);
                showContent('skeleton-ai-score', 'ai-confidence-score');
                animateCounter(document.getElementById('ai-confidence-score'), 0, aiScore);
                
            } catch (error) {
                console.error('Failed to load dashboard data:', error);
                document.querySelectorAll('.loading-skeleton').forEach(el => {
                    el.style.background = '#ffebee';
                    el.innerHTML = '<small class="text-danger">Failed to load</small>';
                });
            }
        }
        
        // Load AI insights
        async function loadAIInsights() {
            logAnalytics('tab_view', 'ai_insights');
            
            try {
                const insightsData = await fetchWithCache('/api/ai-insights');
                
                // Load summary
                const summaryContent = document.getElementById('ai-summary-content');
                summaryContent.innerHTML = `
                    <div class="alert alert-info border-0" style="background: linear-gradient(45deg, #667eea, #764ba2); color: white;">
                        <h6 class="mb-2">
                            <i class="fas fa-brain me-2"></i>AI Analysis
                            <small class="ms-2 opacity-75">Generated ${new Date().toLocaleTimeString()}</small>
                        </h6>
                        <p class="mb-0">${insightsData.summary?.summary || 'Analyzing operational data...'}</p>
                    </div>
                `;
                
                // Load recommendations
                const recommendations = insightsData.summary?.recommendations || {};
                const recsContent = document.getElementById('ai-recommendations-content');
                recsContent.innerHTML = `
                    <div class="mb-3">
                        <h6 class="text-danger"><i class="fas fa-exclamation-circle me-2"></i>Immediate Actions</h6>
                        ${(recommendations.immediate_actions || []).map(action => `
                            <div class="p-2 bg-light rounded mb-2">
                                <small>${action}</small>
                            </div>
                        `).join('')}
                    </div>
                    <div class="mb-3">
                        <h6 class="text-warning"><i class="fas fa-calendar-week me-2"></i>Weekly Priorities</h6>
                        ${(recommendations.weekly_priorities || []).map(priority => `
                            <div class="p-2 bg-light rounded mb-2">
                                <small>${priority}</small>
                            </div>
                        `).join('')}
                    </div>
                `;
                
                // Load asset insights
                const assetInsights = insightsData.asset_insights || [];
                const assetContent = document.getElementById('asset-insights-content');
                assetContent.innerHTML = assetInsights.map(insight => `
                    <div class="card mb-3 border-0 shadow-sm">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <h6 class="mb-1">
                                        Asset #${insight.asset_id}
                                        <span class="badge ${insight.risk_level === 'high' ? 'bg-danger' : insight.risk_level === 'medium' ? 'bg-warning' : 'bg-success'} ms-2">
                                            ${insight.risk_level.toUpperCase()} RISK
                                        </span>
                                    </h6>
                                    <p class="mb-2 text-muted">${insight.insight}</p>
                                    <small class="text-muted">
                                        <i class="fas fa-chart-line me-1"></i>
                                        Risk Score: ${(insight.failure_risk * 100).toFixed(1)}%
                                    </small>
                                </div>
                                <span class="ai-tag">AI</span>
                            </div>
                        </div>
                    </div>
                `).join('') || '<p class="text-muted">No specific asset insights available.</p>';
                
                showContent('ai-summary-skeleton', 'ai-summary-content');
                
            } catch (error) {
                console.error('Failed to load AI insights:', error);
            }
        }
        
        // Load predictive maintenance data
        async function loadPredictiveMaintenanceData() {
            logAnalytics('tab_view', 'predictive_maintenance');
            
            try {
                const predictionsData = await fetchWithCache('/api/predictive-maintenance');
                
                // Load predictions table
                const predictions = predictionsData.predictions || [];
                const predictionsContent = document.getElementById('predictions-content');
                predictionsContent.innerHTML = predictions.slice(0, 5).map(prediction => `
                    <div class="card mb-3 border-0 shadow-sm">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="flex-grow-1">
                                    <h6 class="mb-1">
                                        Asset #${prediction.asset_id}
                                        <span class="badge ${prediction.risk_level === 'high' ? 'bg-danger' : prediction.risk_level === 'medium' ? 'bg-warning' : 'bg-success'} ms-2">
                                            🔴 ${prediction.risk_level === 'high' ? 'HIGH' : prediction.risk_level === 'medium' ? '🟠 MEDIUM' : '🟢 LOW'} RISK
                                        </span>
                                    </h6>
                                    <p class="mb-2">${prediction.recommendation}</p>
                                    <div class="d-flex justify-content-between">
                                        <small class="text-muted">
                                            <i class="fas fa-calendar me-1"></i>
                                            Next maintenance: ${prediction.next_due_date}
                                        </small>
                                        <small class="text-muted">
                                            <i class="fas fa-percentage me-1"></i>
                                            Risk: ${(prediction.failure_risk * 100).toFixed(1)}%
                                        </small>
                                    </div>
                                </div>
                                <div class="text-end">
                                    <div class="progress" style="width: 100px; height: 6px;">
                                        <div class="progress-bar ${prediction.risk_level === 'high' ? 'bg-danger' : prediction.risk_level === 'medium' ? 'bg-warning' : 'bg-success'}" 
                                             style="width: ${prediction.failure_risk * 100}%"></div>
                                    </div>
                                    <small class="text-muted mt-1 d-block">
                                        Confidence: ${(prediction.confidence * 100).toFixed(0)}%
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('') || '<p class="text-muted">No predictions available.</p>';
                
                // Load risk distribution
                const riskDistribution = predictionsData.summary?.risk_distribution || {};
                const riskContent = document.getElementById('risk-distribution-content');
                riskContent.innerHTML = `
                    <div class="text-center">
                        <div class="mb-3">
                            <h2 class="text-danger">${riskDistribution.high || 0}</h2>
                            <small class="text-muted">High Risk Assets</small>
                        </div>
                        <div class="mb-3">
                            <h3 class="text-warning">${riskDistribution.medium || 0}</h3>
                            <small class="text-muted">Medium Risk Assets</small>
                        </div>
                        <div class="mb-3">
                            <h4 class="text-success">${riskDistribution.low || 0}</h4>
                            <small class="text-muted">Low Risk Assets</small>
                        </div>
                        <hr>
                        <div class="mt-3">
                            <p class="text-muted mb-1">Estimated Savings</p>
                            <h5 class="text-primary">$${(predictionsData.summary?.cost_savings_estimated || 0).toLocaleString()}</h5>
                        </div>
                    </div>
                `;
                
            } catch (error) {
                console.error('Failed to load predictive maintenance data:', error);
            }
        }
        
        // Load anomaly alerts
        async function loadAnomalyAlerts() {
            logAnalytics('tab_view', 'anomaly_alerts');
            
            try {
                const alertsData = await fetchWithCache('/api/alerts');
                
                const alerts = alertsData.alerts?.recent_anomalies || [];
                const anomaliesContent = document.getElementById('anomalies-content');
                
                if (alerts.length === 0) {
                    anomaliesContent.innerHTML = `
                        <div class="text-center py-4">
                            <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
                            <h5 class="text-success">No Anomalies Detected</h5>
                            <p class="text-muted">All systems are operating within normal parameters.</p>
                        </div>
                    `;
                } else {
                    anomaliesContent.innerHTML = alerts.map(alert => `
                        <div class="alert ${alert.severity === 'critical' ? 'alert-danger' : alert.severity === 'high' ? 'alert-warning' : 'alert-info'} border-0 mb-3">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <h6 class="mb-1">
                                        <i class="fas fa-${alert.severity === 'critical' ? 'exclamation-triangle' : 'exclamation-circle'} me-2"></i>
                                        ${alert.metric_name.replace('_', ' ').toUpperCase()} ANOMALY
                                        <span class="badge bg-secondary ms-2">${alert.severity.toUpperCase()}</span>
                                    </h6>
                                    <p class="mb-2">${alert.description}</p>
                                    <small class="text-muted">
                                        Detected: ${new Date(alert.detected_at).toLocaleString()} | 
                                        Confidence: ${(alert.confidence * 100).toFixed(0)}%
                                    </small>
                                </div>
                                <div class="text-end">
                                    <div class="badge bg-light text-dark">
                                        Current: ${alert.current_value.toFixed(2)}
                                    </div>
                                    <div class="badge bg-light text-dark mt-1">
                                        Expected: ${alert.expected_range[0].toFixed(2)} - ${alert.expected_range[1].toFixed(2)}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('');
                }
                
            } catch (error) {
                console.error('Failed to load anomaly alerts:', error);
            }
        }
        
        // Tab switching
        document.addEventListener('DOMContentLoaded', function() {
            // Handle tab clicks
            document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
                tab.addEventListener('click', function(e) {
                    e.preventDefault();
                    
                    // Remove active class from all tabs and content
                    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                    
                    // Add active class to clicked tab
                    this.classList.add('active');
                    
                    // Show corresponding content
                    const target = this.getAttribute('href').substring(1);
                    document.getElementById(target).classList.add('active');
                    
                    // Load tab-specific data
                    switch(target) {
                        case 'ai-insights':
                            loadAIInsights();
                            break;
                        case 'predictions':
                            loadPredictiveMaintenanceData();
                            break;
                        case 'alerts':
                            loadAnomalyAlerts();
                            break;
                    }
                });
            });
            
            // Load initial dashboard data
            loadDashboardData();
        });
        
        // Utility functions
        function refreshDashboard() {
            logAnalytics('refresh_click', 'ai_dashboard');
            const refreshIcon = document.getElementById('refreshIcon');
            refreshIcon.classList.add('fa-spin');
            
            aiCache.cache.clear();
            loadDashboardData().finally(() => {
                refreshIcon.classList.remove('fa-spin');
            });
        }
        
        function regenerateAISummary() {
            logAnalytics('ai_regenerate', 'insights_summary');
            document.getElementById('ai-summary-skeleton').classList.remove('hidden');
            document.getElementById('ai-summary-content').classList.add('hidden');
            
            fetchWithCache('/api/ai-insights', {skipCache: true})
                .then(() => loadAIInsights())
                .catch(console.error);
        }
        
        function refreshAnomalies() {
            logAnalytics('refresh_click', 'anomaly_alerts');
            fetchWithCache('/api/alerts', {skipCache: true})
                .then(() => loadAnomalyAlerts())
                .catch(console.error);
        }
    </script>
</body>
</html>
    """)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)