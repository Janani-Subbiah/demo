# Deployment Setup

This document describes how to set up automated deployment to Google Cloud Platform (GCP) Cloud Run using GitHub Actions.

## Prerequisites

1. A GCP project with billing enabled
2. Cloud Run API enabled
3. Artifact Registry API enabled
4. A service account with appropriate permissions

## GCP Setup

### 1. Create a Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions-sa \
    --description="Service account for GitHub Actions deployments" \
    --display-name="GitHub Actions SA"

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.admin"

# Generate and download service account key
gcloud iam service-accounts keys create github-actions-sa-key.json \
    --iam-account=github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 2. Create Artifact Registry Repository

```bash
# Create repository for Docker images
gcloud artifacts repositories create YOUR_REPOSITORY_NAME \
    --repository-format=docker \
    --location=YOUR_REGION \
    --description="Docker repository for demo app"
```

## GitHub Secrets Configuration

Configure the following secrets in your GitHub repository settings (Settings > Secrets and variables > Actions):

### Required Secrets

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `GCP_PROJECT_ID` | Your GCP project ID | `my-project-123456` |
| `GCP_SA_KEY` | Service account JSON key (entire contents) | `{"type": "service_account", ...}` |
| `GAR_LOCATION` | Artifact Registry location | `us-central1` |
| `GAR_REPOSITORY` | Artifact Registry repository name | `my-repo` |
| `CLOUD_RUN_SERVICE` | Cloud Run service name | `demo-app` |
| `CLOUD_RUN_REGION` | Cloud Run deployment region | `us-central1` |

### Setting up Secrets

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add each secret with the corresponding value

## Deployment Workflow

The GitHub Actions workflow (`.github/workflows/deploy-to-gcp.yml`) will:

1. **Build**: Compile the Kotlin Spring Boot application using Gradle
2. **Docker**: Build and push a Docker image to Google Artifact Registry
3. **Deploy**: Deploy the image to Cloud Run
4. **Status**: Update deployment status and provide the service URL

### Trigger Deployment

The workflow can be triggered in two ways:

1. **Automatic**: Push to the `master` branch
2. **Manual**: Use the "Actions" tab in GitHub and run the workflow manually

### Environment Variables

The application will be deployed with the following environment variables:
- `SPRING_PROFILES_ACTIVE=test`

You can modify these in the workflow file as needed.

## Monitoring and Logs

After deployment, you can:

1. **View logs**: `gcloud logs read --service=YOUR_SERVICE_NAME`
2. **Check status**: Visit the Cloud Run console
3. **Access app**: Use the URL provided in the workflow output

## Troubleshooting

### Common Issues

1. **Permission denied**: Ensure the service account has all required roles
2. **Image not found**: Check Artifact Registry repository exists and is accessible
3. **Build failures**: Review Gradle build logs in GitHub Actions

### Debug Commands

```bash
# Check service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID

# List Artifact Registry repositories
gcloud artifacts repositories list

# View Cloud Run services
gcloud run services list
```

## Security Notes

- Service account keys should be rotated regularly
- Use least-privilege principle for IAM roles
- Consider using Workload Identity Federation instead of service account keys for enhanced security
- Keep secrets secure and never commit them to the repository
