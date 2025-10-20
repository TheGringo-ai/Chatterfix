#!/bin/bash
# Enable hot reload on your VM

gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="
# Update the app to run with auto-reload
sudo sed -i 's/uvicorn.run(app, host=\"0.0.0.0\", port=8000)/uvicorn.run(app, host=\"0.0.0.0\", port=8000, reload=True)/' /opt/chatterfix-cmms/current/app.py

# Restart service
sudo systemctl restart chatterfix-cmms

echo '✅ Hot reload enabled! Files will auto-update when changed.'
"
