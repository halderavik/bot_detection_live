# Frontend Deployment Script for Cloud Storage + Cloud CDN
# Run this script from the project root directory

# Configuration
$PROJECT_ID = "survey-bot-detection-119522247395"
$REGION = "northamerica-northeast2"
$BUCKET_NAME = "bot-detection-frontend-$(Get-Date -Format 'yyyyMMdd')"
$FRONTEND_DOMAIN = "bot-detection-frontend.com"  # Replace with your actual domain

Write-Host "🚀 Starting Frontend Deployment to Cloud Storage + CDN" -ForegroundColor Green
Write-Host "Project: $PROJECT_ID" -ForegroundColor Cyan
Write-Host "Region: $REGION" -ForegroundColor Cyan
Write-Host "Bucket: $BUCKET_NAME" -ForegroundColor Cyan

# Step 1: Create bucket
Write-Host "`n📦 Creating Cloud Storage bucket..." -ForegroundColor Yellow
gcloud storage buckets create gs://$BUCKET_NAME --location=$REGION --project=$PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create bucket. It might already exist." -ForegroundColor Red
    Write-Host "Using existing bucket: $BUCKET_NAME" -ForegroundColor Yellow
}

# Step 2: Set bucket as website
Write-Host "`n🌐 Configuring bucket as website..." -ForegroundColor Yellow
gcloud storage buckets update gs://$BUCKET_NAME --web-main-page-suffix=index.html --web-error-page=index.html

# Step 3: Upload frontend build
Write-Host "`n📤 Uploading frontend build to bucket..." -ForegroundColor Yellow
gcloud storage rsync -r -d frontend/dist gs://$BUCKET_NAME

# Step 4: Make all objects publicly readable
Write-Host "`n🔓 Setting public access permissions..." -ForegroundColor Yellow
gcloud storage objects update gs://$BUCKET_NAME/** --canned-acl=publicRead

# Step 5: Set cache headers for assets
Write-Host "`n⚡ Setting cache headers for assets..." -ForegroundColor Yellow
gcloud storage objects update gs://$BUCKET_NAME/assets/** --cache-control="public, max-age=31536000, immutable"

# Step 6: Set no-cache for index.html
Write-Host "`n🔄 Setting no-cache for index.html..." -ForegroundColor Yellow
gcloud storage objects update gs://$BUCKET_NAME/index.html --cache-control="no-cache"

Write-Host "`n✅ Frontend deployment completed!" -ForegroundColor Green
Write-Host "Bucket URL: https://storage.googleapis.com/$BUCKET_NAME/index.html" -ForegroundColor Cyan
Write-Host "`n📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Create HTTPS Load Balancer with Cloud CDN" -ForegroundColor White
Write-Host "2. Configure backend bucket as origin" -ForegroundColor White
Write-Host "3. Set up managed SSL certificate for your domain" -ForegroundColor White
Write-Host "4. Update DNS to point to load balancer IP" -ForegroundColor White
Write-Host "5. Update backend CORS to allow your frontend domain" -ForegroundColor White

Write-Host "`n🔧 Manual steps for Load Balancer + CDN:" -ForegroundColor Magenta
Write-Host "1. Go to Cloud Console > Network Services > Load Balancing" -ForegroundColor White
Write-Host "2. Create HTTP(S) Load Balancer" -ForegroundColor White
Write-Host "3. Add backend bucket: $BUCKET_NAME" -ForegroundColor White
Write-Host "4. Enable Cloud CDN" -ForegroundColor White
Write-Host "5. Configure host and path rules" -ForegroundColor White
Write-Host "6. Reserve static IP and attach managed SSL certificate" -ForegroundColor White
