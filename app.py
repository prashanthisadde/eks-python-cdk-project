#!/usr/bin/env python3
import aws_cdk as cdk
from eks_stack.eks_stack import EksStack

app = cdk.App()

# You can change the environment value here: 'development', 'staging', or 'production'
environment = app.node.try_get_context("environment") or "development"

EksStack(
    app,
    "EksStack",
    environment=environment,
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1"
    ),
    description="EKS Stack with ingress-nginx Helm chart"
)

app.synth()
