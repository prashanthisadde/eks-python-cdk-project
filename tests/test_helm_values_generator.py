"""
Unit tests for the Helm values generator Lambda function
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))

from helm_values_generator import get_environment_from_ssm, generate_helm_values


class TestGetEnvironmentFromSSM:
    """Tests for get_environment_from_ssm function"""

    @patch('helm_values_generator.ssm_client')
    def test_get_environment_development(self, mock_ssm_client):
        """Test retrieving development environment from SSM"""
        mock_ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'development'}
        }
        
        result = get_environment_from_ssm('/platform/account/env')
        
        assert result == 'development'
        mock_ssm_client.get_parameter.assert_called_once_with(Name='/platform/account/env')

    @patch('helm_values_generator.ssm_client')
    def test_get_environment_staging(self, mock_ssm_client):
        """Test retrieving staging environment from SSM"""
        mock_ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'staging'}
        }
        
        result = get_environment_from_ssm('/platform/account/env')
        
        assert result == 'staging'
        mock_ssm_client.get_parameter.assert_called_once_with(Name='/platform/account/env')

    @patch('helm_values_generator.ssm_client')
    def test_get_environment_production(self, mock_ssm_client):
        """Test retrieving production environment from SSM"""
        mock_ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'production'}
        }
        
        result = get_environment_from_ssm('/platform/account/env')
        
        assert result == 'production'
        mock_ssm_client.get_parameter.assert_called_once_with(Name='/platform/account/env')


class TestGenerateHelmValues:
    """Tests for generate_helm_values function"""

    def test_development_environment_returns_one_replica(self):
        """Test that development environment returns 1 replica"""
        helm_values = generate_helm_values('development')
        
        assert helm_values == {
            'controller': {
                'replicaCount': 1
            }
        }

    def test_staging_environment_returns_two_replicas(self):
        """Test that staging environment returns 2 replicas"""
        helm_values = generate_helm_values('staging')
        
        assert helm_values == {
            'controller': {
                'replicaCount': 2
            }
        }

    def test_production_environment_returns_two_replicas(self):
        """Test that production environment returns 2 replicas"""
        helm_values = generate_helm_values('production')
        
        assert helm_values == {
            'controller': {
                'replicaCount': 2
            }
        }

    def test_invalid_environment_raises_error(self):
        """Test that invalid environment raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            generate_helm_values('invalid')
        
        assert 'Invalid environment: invalid' in str(exc_info.value)

    def test_helm_values_structure(self):
        """Test that Helm values have correct structure"""
        for env in ['development', 'staging', 'production']:
            helm_values = generate_helm_values(env)
            
            assert 'controller' in helm_values
            assert 'replicaCount' in helm_values['controller']
            assert isinstance(helm_values['controller']['replicaCount'], int)
            assert helm_values['controller']['replicaCount'] in [1, 2]


class TestIntegration:
    """Integration tests combining SSM retrieval and Helm values generation."""

    @patch('helm_values_generator.ssm_client')
    def test_full_flow_development(self, mock_ssm_client):
        """Test full flow for development environment"""
        mock_ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'development'}
        }
        
        environment = get_environment_from_ssm('/platform/account/env')
        helm_values = generate_helm_values(environment)
        
        assert helm_values['controller']['replicaCount'] == 1

    @patch('helm_values_generator.ssm_client')
    def test_full_flow_staging(self, mock_ssm_client):
        """Test full flow for staging environment"""
        mock_ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'staging'}
        }
        
        environment = get_environment_from_ssm('/platform/account/env')
        helm_values = generate_helm_values(environment)
        
        assert helm_values['controller']['replicaCount'] == 2

    @patch('helm_values_generator.ssm_client')
    def test_full_flow_production(self, mock_ssm_client):
        """Test full flow for production environment"""
        mock_ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'production'}
        }
        
        environment = get_environment_from_ssm('/platform/account/env')
        helm_values = generate_helm_values(environment)
        
        assert helm_values['controller']['replicaCount'] == 2
