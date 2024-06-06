# Cloud Run Application Deployed via Terraform

This repository contains the code and configuration files for deploying a simple Cloud Run application on Google Cloud Platform (GCP) using Terraform. The application returns a simple message when accessed via its URL.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Usage](#usage)
- [Cleanup](#cleanup)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

Before you begin, ensure you have the following:

- A GCP account
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured
- [Terraform](https://www.terraform.io/downloads.html) installed
- Docker installed for building the application image

## Architecture

This setup involves the following components:

1. **Cloud Run Service**: The application is deployed as a containerized service on Cloud Run.
2. **Container Registry**: The Docker image for the application is stored in Google Container Registry (GCR).
3. **Terraform Configuration**: Terraform scripts are used to automate the deployment process.

## Getting Started

### Clone the Repository

```sh
git clone https://github.com/braianmobiledev/SoftwareDevelopmentGoodPractices.git
```
### Push Image To Registry
```sh
# Build image
 docker build -t clientes:<tag> .

# Add tag for GCR 
 docker tag clientes:06062024 us-central1-docker.pkg.dev/devopsterraform-425615/devops-artifacts/clientes-api:<tag>

# Push to registry
docker push us-central1-docker.pkg.dev/devopsterraform-425615/devops-artifacts/clientes-api:<tag>
```

### Create Cloud Run with Terraform

After successfully pushing image into registry and authenticate in gcloud CLI in your local machine you can proceed to create application 
```sh
# Init modules
terraform init 

# View changes to be applies
terraform plan

# Apply those changes in GCP cloud
terraform apply

# Optional
# Destroy resources
terraform destroy
```