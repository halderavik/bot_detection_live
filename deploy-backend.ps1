# Backend deployment to Cloud Run
# Prereqs: gcloud SDK installed and authenticated

param(
  [string]$ProjectId = "survey-bot-detection-119522247395",
  [string]$Region = "northamerica-northeast2",
  [string]$Service = "bot-backend",
  [string]$ConnectorName = "serverless-connector",
  [string]$InstanceName = "bot-db",
  [string]$AllowedOrigins = '["*"]'
)

Write-Host "Deploying backend to Cloud Run..." -ForegroundColor Green

# Ensure Artifact Registry repo exists
Write-Host "Ensuring Artifact Registry repo exists..." -ForegroundColor Yellow
gcloud artifacts repositories create backend --repository-format=docker --location=$Region 2>$null

# Build and push image
$ImageTag = "${Region}-docker.pkg.dev/${ProjectId}/backend/${Service}:$(git rev-parse --short HEAD)"
Write-Host "Building image: $ImageTag" -ForegroundColor Yellow
docker build -t $ImageTag ./backend

Write-Host "Pushing image..." -ForegroundColor Yellow
docker push $ImageTag

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
  --set-env-vars DEBUG=false,LOG_LEVEL=INFO,ALLOWED_ORIGINS=$AllowedOrigins

Write-Host "Done. Retrieve URL:" -ForegroundColor Green
gcloud run services describe $Service --region $Region --format='value(status.url)'

