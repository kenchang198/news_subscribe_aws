#!/bin/bash

# SAM Deploy Script using .env file

echo "Starting SAM deployment..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    exit 1
fi

# Load environment variables from .env file (improved parsing)
echo "Loading environment variables from .env..."
while IFS= read -r line; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Extract key=value pairs (handle spaces around =)
    if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        
        # Remove quotes and inline comments
        value=$(echo "$value" | sed "s/['\"]//g" | sed 's/#.*//' | xargs)
        
        # Export the variable
        export "$key"="$value"
        echo "  Loaded: $key=$value"
    fi
done < .env

# Set default values for missing parameters
S3_PREFIX=${S3_PREFIX:-"audio/"}
POLLY_VOICE_ID=${POLLY_VOICE_ID:-"Takumi"}
SUMMARY_MAX_LENGTH=${SUMMARY_MAX_LENGTH:-"400"}
TIME_ZONE=${TIME_ZONE:-"Asia/Tokyo"}
OPENAI_MODEL=${OPENAI_MODEL:-"gpt-3.5-turbo"}

# Ensure required variables are set
if [ -z "$S3_BUCKET_NAME" ]; then
    echo "Error: S3_BUCKET_NAME is not set in .env file"
    exit 1
fi

if [ -z "$GOOGLE_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: Either GOOGLE_API_KEY or OPENAI_API_KEY must be set in .env file"
    exit 1
fi

echo ""
echo "Final parameters:"
echo "  S3_BUCKET_NAME: $S3_BUCKET_NAME"
echo "  S3_PREFIX: $S3_PREFIX"
echo "  AI_PROVIDER: $AI_PROVIDER"
echo "  PROGRAM_NAME: $PROGRAM_NAME"
echo "  POLLY_VOICE_ID: $POLLY_VOICE_ID"
echo "  SUMMARY_MAX_LENGTH: $SUMMARY_MAX_LENGTH"
echo "  TIME_ZONE: $TIME_ZONE"
echo "  OPENAI_MODEL: $OPENAI_MODEL"

# Build the application
echo ""
echo "Building SAM application..."
sam build

if [ $? -ne 0 ]; then
    echo "Error: SAM build failed!"
    exit 1
fi

# Deploy with parameters
echo ""
echo "Deploying to AWS..."
sam deploy --parameter-overrides \
  S3BucketName="$S3_BUCKET_NAME" \
  S3Prefix="$S3_PREFIX" \
  OpenAIApiKey="${OPENAI_API_KEY:-dummy-key}" \
  GoogleApiKey="${GOOGLE_API_KEY:-dummy-key}" \
  AIProvider="${AI_PROVIDER:-gemini}" \
  GeminiModel="${GEMINI_MODEL:-gemini-pro}" \
  PollyVoiceId="$POLLY_VOICE_ID" \
  SummaryMaxLength="$SUMMARY_MAX_LENGTH" \
  ProgramName="$PROGRAM_NAME" \
  TimeZone="$TIME_ZONE" \
  OpenAIModel="$OPENAI_MODEL"

if [ $? -eq 0 ]; then
    echo ""
    echo "Deployment completed successfully!"
else
    echo ""
    echo "Deployment failed!"
    exit 1
fi 