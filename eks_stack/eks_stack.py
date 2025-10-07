import json
from aws_cdk import (
    Stack,
    CustomResource,
    aws_eks as eks,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_lambda as _lambda,
    custom_resources as cr,
)
from constructs import Construct
from aws_cdk.lambda_layer_kubectl_v29 import KubectlV29Layer
import aws_cdk as cdk


class EksStack(Stack):
    """
    CDK Stack containing EKS cluster, SSM parameter, CustomResource, and Helm chart
    """

    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if environment not in ['development', 'staging', 'production']:
            raise ValueError(f"Invalid environment: {environment}. Must be development, staging, or production")

        # Create VPC for EKS cluster
        vpc = ec2.Vpc(
            self, "EksVpc",
            max_azs=2,
            nat_gateways=1
        )

        # Create EKS cluster
        cluster = eks.Cluster(
            self, "EksCluster",
            version=eks.KubernetesVersion.V1_28,
            vpc=vpc,
            default_capacity=2,
            default_capacity_instance=ec2.InstanceType.of(
                ec2.InstanceClass.T3,
                ec2.InstanceSize.MEDIUM
            ),
            kubectl_layer=KubectlV29Layer(self, "KubectlLayer")
        )

        # Create SSM parameter with environment value
        parameter_name = "/platform/account/env"
        ssm_parameter = ssm.StringParameter(
            self, "EnvironmentParameter",
            parameter_name=parameter_name,
            string_value=environment,
            description=f"Account environment: {environment}"
        )

        # Create IAM role for Lambda function
        lambda_role = iam.Role(
            self, "HelmValuesGeneratorRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        ssm_parameter.grant_read(lambda_role)

        helm_values_function = _lambda.Function(
            self, "HelmValuesGenerator",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="helm_values_generator.handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            description="Generates Helm values based on environment from SSM"
        )

        provider = cr.Provider(
            self, "HelmValuesProvider",
            on_event_handler=helm_values_function
        )

        helm_values_resource = CustomResource(
            self, "HelmValuesResource",
            service_token=provider.service_token,
            properties={
                "ParameterName": parameter_name
            }
        )

        helm_values_resource.node.add_dependency(ssm_parameter)

        replica_count_from_cr = helm_values_resource.get_att_string("ReplicaCount")
        replica_count_number = cdk.Token.as_number(replica_count_from_cr)
        
        helm_values = {
            'controller': {
                'replicaCount': replica_count_number
            }
        }

        ingress_chart = cluster.add_helm_chart(
            "IngressNginx",
            chart="ingress-nginx",
            repository="https://kubernetes.github.io/ingress-nginx",
            namespace="ingress-nginx",
            create_namespace=True,
            values=helm_values
        )

        ingress_chart.node.add_dependency(helm_values_resource)
