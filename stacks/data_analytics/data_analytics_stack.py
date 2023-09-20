"""
References:
  - AWS Doc:
      - aws_ec2.SubnetType: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetType.html
      - aws_ec2.InterfaceVpcEndpointAwsService: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/InterfaceVpcEndpointAwsService.html#interfacevpcendpointawsservice
      - aws_ec2.SubnetSelection: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetSelection.html#subnetselection

  - Examples:
      - aws-cdk-rfcs: https://github.com/aws/aws-cdk-rfcs/blob/main/text/0340-firehose-l2.md
"""

from constructs import Construct
from aws_cdk import (
    Stack,
    aws_ec2 as ec2
)

from ..api_gateway.api_gateway_stack import (
    ApiGatewayStack,
    ApiGatewayModel
)

from lib.dataclasses import (
    ServicePrefix,
    VpcConfig,
    SubnetConfig
)

from lib.services import (
    create_vpc
)


class DataAnalyticsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(
            scope,
            construct_id,
            description='This stack includes the resources needed for the FuturaCity project to achieve the goal of data analytics',
            **kwargs
        )

        self.service_prefix = ServicePrefix(
            id='da-',
            name='Da'
        )

        # ---------------------------------------- #
        # VPC
        # ---------------------------------------- #
        private_subnet_config = SubnetConfig(
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    subnet_id='private-subnet',
                    cidr_mask=28
                )

        self.__vpc = create_vpc(
            instance_class=self,
            service_prefix=self.service_prefix,
            vpc_config=VpcConfig(
                cidr='10.0.0.0/24'
            ),
            subnets_config=[
                private_subnet_config
            ]
        )

        # ---------------------------------------- #
        # Api Gateway
        # ---------------------------------------- #
        self.__api_gateway = ApiGatewayStack(
            self,
            construct_id=self.service_prefix.id + 'api-gateway',
            description='Data Analytics Api Gateway',
            service_prefix=self.service_prefix,
            endpoint='data-analytics',
            allowed_methods=['GET', 'POST'],
            api_models=[]
        )
