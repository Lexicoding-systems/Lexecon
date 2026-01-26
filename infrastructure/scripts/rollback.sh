#!/bin/bash

set -euo pipefail

# Rollback Lexecon to previous version
# Usage: ./rollback.sh <environment>
# Example: ./rollback.sh staging
#          ./rollback.sh production

ENVIRONMENT="${1:?Environment required (staging or production)}"

echo "🔙 Rolling back Lexecon in $ENVIRONMENT"

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
echo "  Namespace: $NAMESPACE"
echo "  Release: $HELM_RELEASE"
echo ""

# Show release history
echo "📜 Release History:"
helm history $HELM_RELEASE -n $NAMESPACE

echo ""
echo "Current revision:"
CURRENT_REVISION=$(helm list -n $NAMESPACE -f $HELM_RELEASE -o json | jq '.[0].revision')
PREVIOUS_REVISION=$((CURRENT_REVISION - 1))

if [ $PREVIOUS_REVISION -lt 1 ]; then
  echo "❌ No previous version to rollback to"
  exit 1
fi

echo "  Current: $CURRENT_REVISION"
echo "  Previous: $PREVIOUS_REVISION"
echo ""

# Ask for confirmation
read -p "⚠️  Rollback to revision $PREVIOUS_REVISION? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "❌ Rollback cancelled"
  exit 1
fi

# Perform rollback
echo "🔄 Rolling back..."
helm rollback $HELM_RELEASE $PREVIOUS_REVISION -n $NAMESPACE --wait --timeout=5m

# Wait for rollback to complete
echo "⏳ Waiting for rollback to complete..."
kubectl rollout status deployment/$HELM_RELEASE --namespace=$NAMESPACE --timeout=5m

echo "✅ Rollback successful!"
echo ""
echo "📊 Current Deployment:"
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
echo "🔙 Rollback to revision $PREVIOUS_REVISION complete!"
echo ""
echo "Next steps:"
echo "  - Monitor logs: kubectl logs -f deployment/$HELM_RELEASE -n $NAMESPACE"
echo "  - Investigate issue"
echo "  - Deploy fix and try again"
