#!/bin/bash
# Script cài đặt Google Cloud SDK

set -e

echo "🚀 Installing Google Cloud SDK..."

# Set Python version
export CLOUDSDK_PYTHON=/usr/local/bin/python3.12

# Download và cài đặt
curl https://sdk.cloud.google.com | bash

# Thêm vào PATH
echo ""
echo "✅ Installation completed!"
echo ""
echo "📝 Add to your ~/.zshrc:"
echo "   export CLOUDSDK_PYTHON=/usr/local/bin/python3.12"
echo "   export PATH=\$HOME/google-cloud-sdk/bin:\$PATH"
echo ""
echo "Then run:"
echo "   source ~/.zshrc"
echo "   gcloud init"

