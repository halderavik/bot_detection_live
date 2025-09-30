# Backend deployment to Cloud Run
# Prereqs: gcloud SDK installed and authenticated

param(
  [string]$ProjectId = "survey-bot-detection",
  [string]$Region = "northamerica-northeast2",
  [string]$Service = "bot-backend",
  [string]$ConnectorName = "serverless-connector",
  [string]$InstanceName = "bot-db",
  [string]$AllowedOrigins = '["*"]',
  [bool]$UseCloudBuild = $true
)

Write-Host "Deploying backend to Cloud Run..." -ForegroundColor Green

<#
  Build and push image, either with Cloud Build (default) or local Docker when -UseCloudBuild:$false.
  Also ensure required APIs and IAM permissions are in place for Artifact Registry pulls.
#>

# Enable required APIs (idempotent)
Write-Host "Enabling required Google Cloud APIs..." -ForegroundColor Yellow
gcloud services enable artifactregistry.googleapis.com run.googleapis.com cloudbuild.googleapis.com --project $ProjectId --quiet

# Ensure Artifact Registry repo exists (idempotent)
Write-Host "Ensuring Artifact Registry repo exists..." -ForegroundColor Yellow
gcloud artifacts repositories create backend --repository-format=docker --location=$Region --project $ProjectId 2>$null

# Configure Docker auth for Artifact Registry (idempotent)
gcloud auth configure-docker "${Region}-docker.pkg.dev" --quiet

# Resolve project number
$ProjectNumber = (gcloud projects describe $ProjectId --format='value(projectNumber)')
Write-Host "Project number: $ProjectNumber" -ForegroundColor Yellow

# Grant Artifact Registry access (reader for Cloud Run service agent; writer for current user)
$RepoResource = "projects/$ProjectId/locations/$Region/repositories/backend"
$RunAgent = "service-$ProjectNumber@serverless-robot-prod.iam.gserviceaccount.com"
$CurrentAccount = (gcloud config get-value account)
Write-Host "Granting roles/artifactregistry.reader to $RunAgent on $RepoResource" -ForegroundColor Yellow
gcloud artifacts repositories add-iam-policy-binding backend `
  --location=$Region `
  --project=$ProjectId `
  --member="serviceAccount:$RunAgent" `
  --role="roles/artifactregistry.reader" 2>$null

Write-Host "Granting roles/artifactregistry.writer to $CurrentAccount on $RepoResource" -ForegroundColor Yellow
gcloud artifacts repositories add-iam-policy-binding backend `
  --location=$Region `
  --project=$ProjectId `
  --member="user:$CurrentAccount" `
  --role="roles/artifactregistry.writer" 2>$null

$ImageTag = "${Region}-docker.pkg.dev/${ProjectId}/backend/${Service}:$(git rev-parse --short HEAD)"
if ($UseCloudBuild) {
  Write-Host "Building image via Cloud Build: $ImageTag" -ForegroundColor Yellow
  gcloud builds submit ./backend --tag $ImageTag --project $ProjectId --quiet
} else {
  Write-Host "Building image locally with Docker: $ImageTag" -ForegroundColor Yellow
  docker build -t $ImageTag ./backend
  Write-Host "Pushing image to Artifact Registry..." -ForegroundColor Yellow
  docker push $ImageTag
}

Write-Host "Deploying to Cloud Run service: $Service" -ForegroundColor Yellow
gcloud run deploy $Service `
  --image $ImageTag `
  --region $Region `
  --platform managed `
  --allow-unauthenticated `
  --cpu 1 `
  --memory 512Mi `
  --concurrency 80 `
  --max-instances 10 `
  --add-cloudsql-instances ${ProjectId}:${Region}:${InstanceName} `
  --vpc-connector $ConnectorName `
  --set-secrets "DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest" `
  --set-env-vars "DEBUG=false,LOG_LEVEL=INFO,ALLOWED_ORIGINS=$AllowedOrigins"

Write-Host "Done. Retrieve URL:" -ForegroundColor Green
gcloud run services describe $Service --region $Region --format='value(status.url)'

