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
    aws_ec2 as ec2,
    aws_iam as iam
)

from lib.dataclasses import (
    ServicePrefix,
    VpcConfig,
    SubnetConfig,
    S3Config,
    Ec2Config,
    SecurityGroupConfig,
    IamRoleConfig
)

from lib.services import (
    create_vpc,
    create_s3_bucket,
    create_ec2,
    create_security_group as create_sg,
    create_role_inline_policy,
    get_secret_value_access_policy
)


service_prefix = ServicePrefix(
    id='da-',
    name='Da'
)

gh_token_id = f'GH_TOKEN_ID={service_prefix.id}gh-token'

with open('./stacks/data_analytics/userdata/ec2_init.sh') as f:
    ec2_init = f.read()


class DataAnalyticsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(
            scope,
            construct_id,
            description='This stack includes the resources needed for the FuturaCity project to achieve the goal of data analytics',
            **kwargs
        )

        # ---------------------------------------- #
        # VPC
        # ---------------------------------------- #
        public_subnet_config = SubnetConfig(
            subnet_id='public-subnet',
            subnet_type=ec2.SubnetType.PUBLIC,
            cidr_mask=28
        )

        self.__vpc = create_vpc(
            instance_class=self,
            service_prefix=service_prefix,
            vpc_config=VpcConfig(
                cidr='10.0.0.0/24'
            ),
            subnets_config=[
                public_subnet_config
            ]
        )

        # ---------------------------------------- #
        # Security Groups
        # ---------------------------------------- #
        ec2_sg = create_sg(
            instance_class=self,
            service_prefix=service_prefix,
            sg_config=SecurityGroupConfig(
                id='ec2',
                name='Ec2',
                description='Security group for EC2',
                vpc=self.__vpc
            )
        )

        # Allow ssh access from anywhere
        ec2_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22),
            description='Allow ssh access from anywhere'
        )

        ec2_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(8000),
            description='Allow access to the web server from anywhere'
        )

        # ---------------------------------------- #
        # IAM Roles
        # ---------------------------------------- #
        ec2_role = create_role_inline_policy(
            instance_class=self,
            service_prefix=service_prefix,
            iam_role_config=IamRoleConfig(
                id='ec2-role',
                name='Ec2Role',
                description='Role for EC2',
                assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
                inline_policies={
                    'ec2-secret-policy': iam.PolicyDocument(
                        statements=[
                            get_secret_value_access_policy(
                                resources=[f'arn:aws:secretsmanager:*:*:secret:{service_prefix.id}*']
                            ),
                            iam.PolicyStatement(
                                actions=[
                                    'kms:Decrypt',
                                    'secretmanager:ListSecrets'
                                ],
                                resources=['*']
                            )
                        ]
                    )
                }
            )
        )

        # ---------------------------------------- #
        # S3 Buckets
        # ---------------------------------------- #
        self.__data_lake = create_s3_bucket(
            instance_class=self,
            service_prefix=service_prefix,
            s3_config=S3Config(
                id='data-lake'
            )
        )

        # ---------------------------------------- #
        # EC2 Instances
        # ---------------------------------------- #
        self.__ec2 = create_ec2(
            instance_class=self,
            service_prefix=service_prefix,
            ec2_config=Ec2Config(
                id='ec2',
                vpc=self.__vpc,
                vpc_subnet_id=public_subnet_config.subnet_id,
                security_group=ec2_sg,
                role=ec2_role
            )
        )

        self.__ec2.user_data.add_commands(gh_token_id)
        self.__ec2.user_data.add_commands(f'S3_BUCKET={self.__data_lake.bucket_name}')
        self.__ec2.user_data.add_commands(ec2_init)

        self.__ec2.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=[
                    's3:PutObject',
                    's3:PutObjectAcl'
                ],
                resources=[
                    f'arn:aws:s3:::{self.__data_lake.bucket_name}/*'
                ]
            )
        )
