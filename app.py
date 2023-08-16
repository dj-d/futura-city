#!/usr/bin/env python3
import aws_cdk as cdk

from data_analytics.data_analytics_stack import DataAnalyticsStack
from energy_efficiency.energy_efficiency_stack import EnergyEfficiencyStack
from smart_traffic.smart_traffic_stack import SmartTrafficStack


app = cdk.App()

data_analytics_stack = DataAnalyticsStack(app, "DataAnalyticsStack")
energy_efficiency_stack = EnergyEfficiencyStack(app, "EnergyEfficiencyStack")
smart_traffic_stack = SmartTrafficStack(app, "SmartTrafficStack")

app.synth()
