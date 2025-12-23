# Docker Hub Setup Guide

## Setting up Docker Hub Token for CI/CD

To enable the CI/CD pipeline to push images to your Docker Hub registry, you need to add a Docker Hub access token to your GitHub repository secrets.

### Step 1: Create Docker Hub Access Token

1. Go to [Docker Hub](https://hub.docker.com/)
2. Log in with your account (`aryansaurabhbhardwaj`)
3. Click on your username in the top right → **Account Settings**
4. Go to **Security** tab
5. Click **New Access Token**
6. Give it a name (e.g., "GitHub Actions CI/CD")
7. Set permissions to **Read, Write, Delete**
8. Click **Generate**
9. **Copy the token** (you won't be able to see it again!)

### Step 2: Add Token to GitHub Secrets

1. Go to your GitHub repository: https://github.com/Bhardwaj-Saurabh/workflow-automation-aiops
2. Click **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Name: `DOCKERHUB_TOKEN`
6. Value: Paste the Docker Hub access token you copied
7. Click **Add secret**

### Step 3: Verify Setup

Once you've added the secret, the CI/CD pipeline will automatically:

1. Run tests on every push
2. Build Docker images on push to `master` branch
3. Push images to Docker Hub:
   - `aryansaurabhbhardwaj/ai-assessment-backend:latest`
   - `aryansaurabhbhardwaj/ai-assessment-frontend:latest`

### Step 4: Trigger the Pipeline

The pipeline will run automatically on your next push to `master`. You can also:

- **Manual trigger**: Go to Actions tab → CI/CD Pipeline → Run workflow
- **Check status**: Actions tab shows all workflow runs

### Images Will Be Available At:

- Backend: https://hub.docker.com/r/aryansaurabhbhardwaj/ai-assessment-backend
- Frontend: https://hub.docker.com/r/aryansaurabhbhardwaj/ai-assessment-frontend

### Pull Images

Once built, anyone can pull your images:

```bash
# Backend
docker pull aryansaurabhbhardwaj/ai-assessment-backend:latest

# Frontend
docker pull aryansaurabhbhardwaj/ai-assessment-frontend:latest
```

### Update docker-compose.yml

You can now use your Docker Hub images in docker-compose:

```yaml
services:
  backend:
    image: aryansaurabhbhardwaj/ai-assessment-backend:latest
    # ... rest of config

  frontend:
    image: aryansaurabhbhardwaj/ai-assessment-frontend:latest
    # ... rest of config
```

---

## Troubleshooting

### Pipeline Fails with "unauthorized"

- Check that `DOCKERHUB_TOKEN` secret is set correctly
- Verify the token has Read, Write, Delete permissions
- Make sure the token hasn't expired

### Images Not Appearing on Docker Hub

- Check the Actions tab for build status
- Ensure the workflow ran on `master` branch
- Verify no errors in the build logs

### Need to Update Token

1. Revoke old token in Docker Hub Security settings
2. Create new token
3. Update `DOCKERHUB_TOKEN` secret in GitHub
