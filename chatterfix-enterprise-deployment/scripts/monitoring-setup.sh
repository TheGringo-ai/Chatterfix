#!/bin/bash
set -e

echo "📊 Setting up Enterprise Monitoring Stack"

NAMESPACE="chatterfix-enterprise"

# Install Prometheus
echo "📈 Installing Prometheus..."
kubectl apply -f monitoring/prometheus-deployment.yaml

# Install Grafana
echo "📊 Installing Grafana..."
kubectl apply -f monitoring/grafana-deployment.yaml

# Install ELK Stack
echo "📝 Installing ELK Stack..."
kubectl apply -f monitoring/elasticsearch-deployment.yaml
kubectl apply -f monitoring/kibana-deployment.yaml
kubectl apply -f monitoring/logstash-deployment.yaml

echo "✅ Monitoring stack deployed!"
echo "📊 Grafana: https://grafana.chatterfix.com"
echo "📝 Kibana: https://kibana.chatterfix.com"
