#!/bin/bash

# SPIDER AWS Lambda Deployment Script
# This script packages and deploys SPIDER to AWS Lambda

set -e

echo "🕷️  SPIDER AWS Lambda Deployment"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
FUNCTION_NAME="spider-scraper"
RUNTIME="python3.9"
HANDLER="lambda_handler.lambda_handler"
MEMORY_SIZE="1024"
TIMEOUT="300"
REGION="us-east-1"
ROLE_NAME="spider-lambda-role"
POLICY_NAME="spider-lambda-policy"

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if AWS credentials are configured
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    # Check if Docker is available (for building Lambda layers)
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not found. Lambda layers will be built without Docker."
    fi
    
    print_success "Prerequisites check completed"
}

# Create IAM role and policy
setup_iam() {
    print_status "Setting up IAM role and policy..."
    
    # Create IAM role
    if ! aws iam get-role --role-name $ROLE_NAME &> /dev/null; then
        aws iam create-role \
            --role-name $ROLE_NAME \
            --assume-role-policy-document '{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }'
        print_success "IAM role created: $ROLE_NAME"
    else
        print_warning "IAM role already exists: $ROLE_NAME"
    fi
    
    # Create IAM policy
    if ! aws iam get-policy --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/$POLICY_NAME" &> /dev/null; then
        aws iam create-policy \
            --policy-name $POLICY_NAME \
            --policy-document '{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": "arn:aws:logs:*:*:*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:DeleteObject"
                        ],
                        "Resource": "arn:aws:s3:::*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:GetItem",
                            "dynamodb:PutItem",
                            "dynamodb:UpdateItem",
                            "dynamodb:DeleteItem",
                            "dynamodb:Query",
                            "dynamodb:Scan"
                        ],
                        "Resource": "arn:aws:dynamodb:*:*:*"
                    }
                ]
            }'
        print_success "IAM policy created: $POLICY_NAME"
    else
        print_warning "IAM policy already exists: $POLICY_NAME"
    fi
    
    # Attach policy to role
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/$POLICY_NAME"
    
    # Attach basic execution role
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    
    print_success "IAM setup completed"
}

# Create Lambda deployment package
create_package() {
    print_status "Creating Lambda deployment package..."
    
    # Create deployment directory
    rm -rf lambda-deployment
    mkdir -p lambda-deployment
    
    # Copy source code
    cp -r spider lambda-deployment/
    cp -r config lambda-deployment/
    cp requirements.txt lambda-deployment/
    cp lambda_handler.py lambda-deployment/
    
    # Install dependencies
    cd lambda-deployment
    pip install -r requirements.txt -t .
    
    # Remove unnecessary files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    
    # Create deployment zip
    zip -r ../spider-lambda.zip . -x "*.pyc" "__pycache__/*" "tests/*" "*.egg-info/*"
    cd ..
    
    print_success "Lambda package created: spider-lambda.zip"
}

# Create Lambda function
create_lambda_function() {
    print_status "Creating Lambda function..."
    
    # Get role ARN
    ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
    
    # Check if function exists
    if aws lambda get-function --function-name $FUNCTION_NAME &> /dev/null; then
        print_warning "Lambda function already exists, updating..."
        
        # Update function code
        aws lambda update-function-code \
            --function-name $FUNCTION_NAME \
            --zip-file fileb://spider-lambda.zip
        
        # Update function configuration
        aws lambda update-function-configuration \
            --function-name $FUNCTION_NAME \
            --runtime $RUNTIME \
            --handler $HANDLER \
            --memory-size $MEMORY_SIZE \
            --timeout $TIMEOUT \
            --role $ROLE_ARN
        
        print_success "Lambda function updated"
    else
        # Create new function
        aws lambda create-function \
            --function-name $FUNCTION_NAME \
            --runtime $RUNTIME \
            --role $ROLE_ARN \
            --handler $HANDLER \
            --zip-file fileb://spider-lambda.zip \
            --memory-size $MEMORY_SIZE \
            --timeout $TIMEOUT \
            --description "SPIDER Web Scraping Function"
        
        print_success "Lambda function created"
    fi
}

# Create Lambda layer for Playwright
create_playwright_layer() {
    print_status "Creating Playwright Lambda layer..."
    
    if command -v docker &> /dev/null; then
        # Create layer directory
        mkdir -p lambda-layers/playwright
        
        # Create Dockerfile for Playwright layer
        cat > lambda-layers/playwright/Dockerfile << EOF
FROM public.ecr.aws/lambda/python:3.9

# Install Playwright
RUN pip install playwright
RUN playwright install chromium
RUN playwright install-deps

# Copy the layer
COPY . /opt/
EOF
        
        # Build and extract layer
        cd lambda-layers/playwright
        docker build -t playwright-layer .
        docker run --rm -v $(pwd):/output playwright-layer cp -r /opt /output/
        cd ../..
        
        # Create layer zip
        cd lambda-layers
        zip -r ../playwright-layer.zip .
        cd ..
        
        # Upload layer to Lambda
        LAYER_ARN=$(aws lambda publish-layer-version \
            --layer-name spider-playwright \
            --zip-file fileb://playwright-layer.zip \
            --compatible-runtimes python3.9 \
            --query 'LayerVersionArn' --output text)
        
        print_success "Playwright layer created: $LAYER_ARN"
    else
        print_warning "Docker not available, skipping Playwright layer creation"
    fi
}

# Create API Gateway (optional)
create_api_gateway() {
    print_status "Creating API Gateway (optional)..."
    
    if [ "$1" = "--api" ]; then
        # Create REST API
        API_ID=$(aws apigateway create-rest-api \
            --name spider-api \
            --description "SPIDER Web Scraping API" \
            --query 'id' --output text)
        
        # Get root resource
        ROOT_RESOURCE_ID=$(aws apigateway get-resources \
            --rest-api-id $API_ID \
            --query 'items[0].id' --output text)
        
        # Create /scrape resource
        SCRAPE_RESOURCE_ID=$(aws apigateway create-resource \
            --rest-api-id $API_ID \
            --parent-id $ROOT_RESOURCE_ID \
            --path-part scrape \
            --query 'id' --output text)
        
        # Create POST method
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $SCRAPE_RESOURCE_ID \
            --http-method POST \
            --authorization-type NONE
        
        # Set up Lambda integration
        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $SCRAPE_RESOURCE_ID \
            --http-method POST \
            --type AWS_PROXY \
            --integration-http-method POST \
            --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:$FUNCTION_NAME/invocations"
        
        # Deploy API
        aws apigateway create-deployment \
            --rest-api-id $API_ID \
            --stage-name prod
        
        print_success "API Gateway created. Endpoint: https://$API_ID.execute-api.$REGION.amazonaws.com/prod/scrape"
    else
        print_warning "Skipping API Gateway creation. Use --api flag to enable."
    fi
}

# Test Lambda function
test_lambda() {
    print_status "Testing Lambda function..."
    
    # Create test event
    cat > test-event.json << EOF
{
    "urls": ["https://httpbin.org/html", "https://httpbin.org/json"],
    "engine": "httpx",
    "extract_data": true
}
EOF
    
    # Invoke function
    aws lambda invoke \
        --function-name $FUNCTION_NAME \
        --payload file://test-event.json \
        --cli-binary-format raw-in-base64-out \
        response.json
    
    # Check response
    if [ -f response.json ]; then
        print_success "Lambda function test completed"
        echo "Response:"
        cat response.json | jq '.' 2>/dev/null || cat response.json
        rm -f response.json test-event.json
    else
        print_error "Lambda function test failed"
    fi
}

# Cleanup
cleanup() {
    print_status "Cleaning up temporary files..."
    
    rm -rf lambda-deployment
    rm -rf lambda-layers
    rm -f spider-lambda.zip
    rm -f playwright-layer.zip
    
    print_success "Cleanup completed"
}

# Main deployment function
main() {
    echo "Starting SPIDER AWS Lambda deployment..."
    echo
    
    check_prerequisites
    setup_iam
    create_package
    create_lambda_function
    create_playwright_layer
    create_api_gateway "$@"
    test_lambda
    cleanup
    
    echo
    print_success "SPIDER AWS Lambda deployment completed successfully!"
    echo
    echo "Lambda function: $FUNCTION_NAME"
    echo "Region: $REGION"
    echo "Runtime: $RUNTIME"
    echo
    echo "To invoke the function:"
    echo "aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"urls\":[\"https://httpbin.org/html\"]}' response.json"
    echo
    echo "To view logs:"
    echo "aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
    echo
}

# Run main function with all arguments
main "$@"
