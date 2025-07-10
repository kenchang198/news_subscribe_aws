#!/bin/bash

# Environment-specific Deploy Script

function show_usage() {
    echo "Usage: $0 [stg|prod]"
    echo ""
    echo "Deploy to different environments:"
    echo "  stg   - Deploy to staging environment"
    echo "  prod  - Deploy to production environment"
    echo ""
    echo "Examples:"
    echo "  $0 stg      # Deploy to staging"
    echo "  $0 prod     # Deploy to production"
}

function confirm_deployment() {
    local env=$1
    echo ""
    echo "=========================================="
    echo "  Deployment Confirmation"
    echo "=========================================="
    echo "Environment: $env"
    echo "Stack Name: news-subscribe-$env"
    echo "Config File: .env.$env"
    echo ""
    read -p "Are you sure you want to deploy to $env? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
}

# Check arguments
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

ENVIRONMENT=$1

# Validate environment
if [[ "$ENVIRONMENT" != "stg" && "$ENVIRONMENT" != "prod" ]]; then
    echo "Error: Invalid environment '$ENVIRONMENT'"
    show_usage
    exit 1
fi

# Show confirmation for production
if [[ "$ENVIRONMENT" == "prod" ]]; then
    confirm_deployment "$ENVIRONMENT"
fi

# Call the main deploy script
echo "Starting deployment to $ENVIRONMENT environment..."
./deploy.sh "$ENVIRONMENT"