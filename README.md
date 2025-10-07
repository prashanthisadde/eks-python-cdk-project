# EKS Python CDK Project

## Overview

This project implements a Python-based AWS CDK solution that creates an EKS cluster with ingress-nginx Helm chart. The Helm chart replica count is dynamically determined by a Lambda-backed CustomResource that retrieves the environment value from AWS Systems Manager Parameter Store.

## Architecture

The project creates the following AWS resources:

1. **EKS Cluster**: A simple Amazon EKS cluster with 2 worker nodes
2. **SSM Parameter**: A parameter at `/platform/account/env` storing the environment value
3. **Lambda Function**: Retrieves the environment from SSM and generates Helm values
4. **Custom Resource**: CloudFormation Custom Resource backed by the Lambda function
5. **Ingress-Nginx Helm Chart**: Installed with values from the Custom Resource

### Helm Values Logic

- **Development**: `controller.replicaCount = 1`
- **Staging**: `controller.replicaCount = 2`
- **Production**: `controller.replicaCount = 2`

### Unit Tests

- 11 comprehensive pytest tests
- Tests only Lambda function code (as required)
- Coverage includes all three environments
- Mock SSM client to avoid AWS calls
- All tests passing (100% pass rate)

**Test file:** `tests/test_helm_values_generator.py`

## Architecture Flow

```
1. SSM Parameter stores environment value (development/staging/production)
                    ↓
2. Lambda function retrieves environment from SSM (boto3)
                    ↓
3. Lambda calculates replica count and returns as CustomResource attribute
                    ↓
4. CDK stack gets replica count from CustomResource attribute
                    ↓
5. Helm chart installed with values from CustomResource
```

## Project Structure

```
.
├── app.py                          # CDK app entry point
├── cdk.json                        # CDK configuration
├── requirements.txt                # Python dependencies
├── requirements-dev.txt            # Development dependencies
├── pytest.ini                      # Pytest configuration
├── README.md                       # This file
├── eks_stack/
│   ├── __init__.py
│   └── eks_stack.py               # Main CDK stack definition
├── lambda/
│   ├── __init__.py
│   ├── helm_values_generator.py   # Lambda function handler
│   └── cfnresponse.py             # CloudFormation response helper
└── tests/
    ├── __init__.py
    └── test_helm_values_generator.py  # Unit tests
```

## Setup and Deployment

### Prerequisites

- Python
- AWS CLI configured
- AWS CDK CLI installed: `npm install -g aws-cdk`

### Installation

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 3. Bootstrap CDK (first time only)
cdk bootstrap
```

### Run Tests

```bash
pytest
```

Expected output: `11 passed`

### Deploy

**Development environment (default):**

```bash
cdk deploy
```

**Staging environment:**

```bash
cdk deploy -c environment=staging
```

**Production environment:**

```bash
cdk deploy -c environment=production
```

### Verify Deployment

```bash
# 1. Check SSM parameter
aws ssm get-parameter --name /platform/account/env

# 2. Configure kubectl
aws eks update-kubeconfig --name <cluster-name> --region <region>

# 3. Verify ingress-nginx pods
kubectl get pods -n ingress-nginx

# 4. Check replica count
kubectl get deployment -n ingress-nginx ingress-nginx-controller -o jsonpath='{.spec.replicas}'
```

Expected replica counts:

- **Development**: 1
- **Staging**: 2
- **Production**: 2

### Cleanup

```bash
cdk destroy
```
