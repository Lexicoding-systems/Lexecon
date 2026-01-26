#!/bin/bash

set -euo pipefail

# Deploy Lexecon to Kubernetes using Helm
# Usage: ./deploy.sh <environment> <version>
# Example: ./deploy.sh staging 0.9.0
#          ./deploy.sh production 0.9.0

ENVIRONMENT="${1:?Environment required (staging or production)}"
VERSION="${2:?Version required (format: X.Y.Z)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "🚀 Deploying Lexecon $VERSION to $ENVIRONMENT"

# Validate version format
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "❌ Invalid version format: $VERSION (expected: X.Y.Z)"
  exit 1
fi

# Validate environment
if ! [[ $ENVIRONMENT =~ ^(staging|production)$ ]]; then
  echo "❌ Invalid environment: $ENVIRONMENT (must be 'staging' or 'production')"
  exit 1
fi

# Set variables based on environment
case $ENVIRONMENT in
  staging)
    NAMESPACE="staging"
    HELM_RELEASE="lexecon-staging"
    ;;
  production)
    NAMESPACE="production"
    HELM_RELEASE="lexecon-prod"
    ;;
esac

echo "📋 Configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  Version: $VERSION"
echo "  Namespace: $NAMESPACE"
echo "  Release: $HELM_RELEASE"
echo ""

# Ensure namespace exists
echo "📦 Ensuring Kubernetes namespace exists..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create/update Kubernetes secrets from environment variables
echo "🔐 Setting up secrets..."
if [ -z "${DATABASE_URL:-}" ]; then
  echo "❌ DATABASE_URL environment variable not set"
  exit 1
fi

kubectl create secret generic lexecon-secrets \
  --from-literal=database-url="$DATABASE_URL" \
  --namespace=$NAMESPACE \
  --dry-run=client \
  -o yaml | kubectl apply -f -

# Deploy/upgrade using Helm
echo "🎯 Deploying Lexecon with Helm..."
helm upgrade --install \
  $HELM_RELEASE \
  "$PROJECT_ROOT/infrastructure/helm" \
  --namespace=$NAMESPACE \
  --values="$PROJECT_ROOT/infrastructure/helm/values.yaml" \
  --set image.tag=$VERSION \
  --set environment=$ENVIRONMENT \
  --wait \
  --timeout=5m

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/$HELM_RELEASE --namespace=$NAMESPACE --timeout=5m

# Get deployment info
echo "✅ Deployment successful!"
echo ""
echo "📊 Deployment Info:"
kubectl get deployment $HELM_RELEASE -n $NAMESPACE -o wide
echo ""
echo "🔗 Service Info:"
kubectl get service $HELM_RELEASE -n $NAMESPACE -o wide
echo ""
echo "📝 Recent Events:"
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -5

# Verify health check
echo ""
echo "🏥 Verifying health check..."
POD_NAME=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=lexecon -o jsonpath='{.items[0].metadata.name}')
if [ -z "$POD_NAME" ]; then
  echo "⚠️  No pods found, skipping health check"
else
  kubectl exec -it $POD_NAME -n $NAMESPACE -- curl -s http://localhost:8000/health | jq . || echo "⚠️  Health check failed (pod may still be starting)"
fi

echo ""
echo "🚀 Deployment of Lexecon $VERSION to $ENVIRONMENT complete!"
echo ""
echo "Next steps:"
echo "  - Monitor logs: kubectl logs -f deployment/$HELM_RELEASE -n $NAMESPACE"
echo "  - Port forward: kubectl port-forward svc/$HELM_RELEASE 8000:80 -n $NAMESPACE"
echo "  - Rollback: ./rollback.sh $ENVIRONMENT"
