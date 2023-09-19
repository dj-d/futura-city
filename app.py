#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.data_analytics.data_analytics_stack import DataAnalyticsStack
from stacks.energy_efficiency.energy_efficiency_stack import EnergyEfficiencyStack
from stacks.smart_traffic.smart_traffic_stack import SmartTrafficStack


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

app.synth()
