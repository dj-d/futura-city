"""
References:
    - AWS Doc:
        - aws_ec2.Vpc: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html#aws_cdk.aws_ec2.Vpc
        - aws_ec2.SubnetConfiguration: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetConfiguration.html
        - aws_ec2.SubnetType: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetType.html
        - aws_ec2.IpAddresses: ttps://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/IpAddresses.html#aws_cdk.aws_ec2.IpAddresses

    - Examples:
        - aws-cdk-rfcs: https://github.com/aws/aws-cdk-rfcs/blob/main/text/0340-firehose-l2.md
"""

from constructs import Construct
from aws_cdk import (
    Stack,
    aws_ec2 as ec2
)


class DataAnalyticsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(
            scope,
            construct_id,
            description='This stack includes the resources needed for the FuturaCity project to achieve the goal of data analytics',
            **kwargs
        )

        self.service_id_prefix = 'da-'
        self.service_name_prefix = 'DA'

        self.__create_vpc()

    def __create_vpc(self) -> None:  # TODO: Add doc
        vpc_construct_id = self.service_id_prefix + 'vpc'
        vpc_name = self.service_name_prefix + 'Vpc'
        vpc_cidr = ec2.IpAddresses.cidr('10.0.0.0/24')

        private_subnet_id = self.service_id_prefix + 'private-subnet'
        self.__private_subnet_type = ec2.SubnetType.PRIVATE_ISOLATED

        private_subnet = ec2.SubnetConfiguration(
            name=private_subnet_id,
            subnet_type=self.__private_subnet_type,
            cidr_mask=28
        )

        self.__vpc = ec2.Vpc(
            self,
            vpc_construct_id,
            vpc_name=vpc_name,
            max_azs=2,
            ip_addresses=vpc_cidr,
            subnet_configuration=[
                private_subnet
            ]
        )
