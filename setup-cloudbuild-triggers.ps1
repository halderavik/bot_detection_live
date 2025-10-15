# Setup Cloud Build Triggers for GCP Production Deployment
# This script creates Cloud Build triggers for backend and frontend deployments

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId = "survey-bot-detection",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "northamerica-northeast2",
    
    [Parameter(Mandatory=$false)]
    [string]$Repository = "bot_detection_live"
)

Write-Host "Setting up Cloud Build triggers for project: $ProjectId" -ForegroundColor Green

# Set the project
gcloud config set project $ProjectId

# Create backend trigger
Write-Host "Creating backend trigger..." -ForegroundColor Yellow
gcloud builds triggers create github `
    --repo-name=$Repository `
    --repo-owner=halderavik `
    --branch-pattern="^main$" `
    --build-config="cloudbuild.yaml" `
    --included-files="backend/**" `
    --name="backend-deploy" `
    --description="Deploy backend to Cloud Run on main branch changes"

# Create frontend trigger
Write-Host "Creating frontend trigger..." -ForegroundColor Yellow
gcloud builds triggers create github `
    --repo-name=$Repository `
    --repo-owner=halderavik `
    --branch-pattern="^main$" `
    --build-config="cloudbuild-frontend.yaml" `
    --included-files="frontend/**" `
    --name="frontend-deploy" `
    --description="Deploy frontend to GCS on main branch changes"

Write-Host "Cloud Build triggers created successfully!" -ForegroundColor Green
Write-Host "Backend trigger: backend-deploy" -ForegroundColor Cyan
Write-Host "Frontend trigger: frontend-deploy" -ForegroundColor Cyan
Write-Host ""
Write-Host "To test the triggers, push changes to the main branch:" -ForegroundColor Yellow
Write-Host "  - Backend changes in backend/ folder will trigger backend deployment" -ForegroundColor White
Write-Host "  - Frontend changes in frontend/ folder will trigger frontend deployment" -ForegroundColor White
