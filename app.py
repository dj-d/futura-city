#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.data_analytics.data_analytics_stack import DataAnalyticsStack
from stacks.energy_efficiency.energy_efficiency_stack import EnergyEfficiencyStack
from stacks.smart_traffic.smart_traffic_stack import SmartTrafficStack
from stacks.api_gateway.api_gateway_stack import ApiGatewayStack, ApiGatewayModel


env_EU = cdk.Environment(region='eu-north-1')

app = cdk.App()

data_analytics_stack = DataAnalyticsStack(
    scope=app,
    construct_id='DataAnalyticsStack',
    env=env_EU
)

energy_efficiency_stack = EnergyEfficiencyStack(
    scope=app,
    construct_id='EnergyEfficiencyStack',
    env=env_EU
)

smart_traffic_stack = SmartTrafficStack(
    scope=app,
    construct_id='SmartTrafficStack',
    env=env_EU
)

energy_efficiency_api_gw_stack = ApiGatewayStack(
    scope=app,
    construct_id='EnergyEfficiencyApiGatewayStack',
    apigw_description='Energy Efficiency Api Gateway',
    api_id=energy_efficiency_stack.service_id_prefix + 'api-gateway',
    api_name=energy_efficiency_stack.service_name_prefix + 'ApiGateway',
    endpoint='energy-efficiency',
    allowed_methods=['GET', 'POST'],
    api_models=[
        ApiGatewayModel(
            method='GET',
            lambda_integration=energy_efficiency_stack.lambda_rd
        ),
        ApiGatewayModel(
            method='POST',
            lambda_integration=energy_efficiency_stack.lambda_wr
        )
    ],
    env=env_EU
)

app.synth()
