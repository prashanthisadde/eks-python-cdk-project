"""
Lambda function to generate Helm values based on environment from SSM parameter
"""
import json
import boto3
from typing import Dict, Any

ssm_client = boto3.client('ssm')


def get_environment_from_ssm(parameter_name: str) -> str:
    """
    Retrieve the environment value from SSM Parameter Store
    
    Args:
        parameter_name: The name of the SSM parameter to retrieve
        
    Returns:
        The environment value (development, staging, or production)
    """
    response = ssm_client.get_parameter(Name=parameter_name)
    return response['Parameter']['Value']


def generate_helm_values(environment: str) -> Dict[str, Any]:
    """
    Generate Helm chart values based on the environment
    
    Args:
        environment: The environment name (development, staging, or production)
        
    Returns:
        Dictionary containing Helm values
    """
    if environment == 'development':
        replica_count = 1
    elif environment in ['staging', 'production']:
        replica_count = 2
    else:
        raise ValueError(f"Invalid environment: {environment}. Must be development, staging, or production")
    
    helm_values = {
        'controller': {
            'replicaCount': replica_count
        }
    }
    
    return helm_values


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for CloudFormation Custom Resource
    
    Args:
        event: Lambda event containing request type and resource properties
        context: Lambda context
        
    Returns:
        Response for CloudFormation Custom Resource
    """
    import cfnresponse
    
    try:
        request_type = event['RequestType']
        
        if request_type in ['Create', 'Update']:
            # Get SSM parameter name from resource properties
            parameter_name = event['ResourceProperties']['ParameterName']
            
            # Retrieve environment from SSM
            environment = get_environment_from_ssm(parameter_name)
            
            # Generate Helm values
            helm_values = generate_helm_values(environment)
            
            # Return success with the Helm values as attributes
            response_data = {
                'HelmValues': json.dumps(helm_values),
                'Environment': environment,
                'ReplicaCount': str(helm_values['controller']['replicaCount'])
            }
            
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
            
        elif request_type == 'Delete':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
            
    except Exception as e:
        print(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': str(e)})
