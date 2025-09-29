# Provision Cloud SQL (PostgreSQL), Secret Manager, and VPC Connector for Cloud Run
# Usage: .\provision-cloudsql.ps1 -ProjectId <ID> -Region <REGION> -InstanceName <NAME> -DbName <DB> -DbUser <USER> -FrontendDomain <DOMAIN>

param(
  [string]$ProjectId = "survey-bot-detection-119522247395",
  [string]$Region = "northamerica-northeast2",
  [string]$InstanceName = "bot-db",
  [string]$DbName = "bot_detection",
  [string]$DbUser = "bot_user",
  [string]$ConnectorName = "serverless-connector",
  [string]$FrontendDomain = "localhost"
)

function New-RandomSecret {
  param([int]$Length = 48)
  $bytes = New-Object 'System.Byte[]' ($Length)
  (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes)
  [Convert]::ToBase64String($bytes)
}

Write-Host "Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable vpcaccess.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

Write-Host "Creating Cloud SQL Postgres instance..." -ForegroundColor Yellow
gcloud sql instances create $InstanceName `
  --database-version=POSTGRES_15 `
  --tier=db-custom-1-3840 `
  --region=$Region `
  --storage-auto-increase `
  --backup `
  --enable-point-in-time-recovery

Write-Host "Creating database and user..." -ForegroundColor Yellow
gcloud sql databases create $DbName --instance=$InstanceName

$DbPassword = New-RandomSecret 32
gcloud sql users create $DbUser --instance=$InstanceName --password=$DbPassword

Write-Host "Creating Serverless VPC Connector..." -ForegroundColor Yellow
gcloud compute networks vpc-access connectors create $ConnectorName `
  --network=default `
  --region=$Region `
  --range=10.8.0.0/28

Write-Host "Storing secrets in Secret Manager..." -ForegroundColor Yellow
$ConnectionName = "${ProjectId}:${Region}:${InstanceName}"
$DatabaseUrl = "postgresql+asyncpg://${DbUser}:${DbPassword}@/${DbName}?host=/cloudsql/${ConnectionName}"

gcloud secrets create DATABASE_URL 2>$null
Set-Content -Path tmp_dburl.txt -Value $DatabaseUrl -NoNewline
gcloud secrets versions add DATABASE_URL --data-file=tmp_dburl.txt
Remove-Item tmp_dburl.txt -Force

$SecretKey = New-RandomSecret 48
gcloud secrets create SECRET_KEY 2>$null
Set-Content -Path tmp_secret.txt -Value $SecretKey -NoNewline
gcloud secrets versions add SECRET_KEY --data-file=tmp_secret.txt
Remove-Item tmp_secret.txt -Force

Write-Host "All done." -ForegroundColor Green
Write-Host "Cloud SQL Connection: $ConnectionName" -ForegroundColor Cyan
Write-Host "Serverless VPC Connector: $ConnectorName" -ForegroundColor Cyan
Write-Host "DATABASE_URL stored in Secret Manager" -ForegroundColor Cyan

