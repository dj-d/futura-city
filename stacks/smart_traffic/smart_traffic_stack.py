"""
References:
  - AWS Doc:
      - aws_ec2.SubnetType: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetType.html
      - aws_ec2.InterfaceVpcEndpointAwsService: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/InterfaceVpcEndpointAwsService.html#interfacevpcendpointawsservice
      - aws_ec2.SubnetSelection: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetSelection.html#subnetselection
      - aws_rds.Credentials: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/Credentials.html#aws_cdk.aws_rds.Credentials
      - aws_iam.PolicyStatement: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/PolicyStatement.html#aws_cdk.aws_iam.PolicyStatement

  - Examples:
"""

from constructs import Construct
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_iam as iam
)

from lib.dataclasses import (
    ServicePrefix,
    SecurityGroupConfig,
    VpcConfig,
    SubnetConfig,
    DbConfig,
    LambdaConfig
)

from lib.services import (
    create_security_group as create_sg,
    create_vpc,
    create_rds_mysql,
    create_lambda
)


class SmartTrafficStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(
            scope,
            construct_id,
            description='This stack includes the resources needed for the FuturaCity project to achieve the goal of smart traffic management',
            **kwargs
        )

        self.__service_prefix = ServicePrefix(
            id='st-',
            name='St'
        )

        # ---------------------------------------- #
        # VPC
        # ---------------------------------------- #
        self.__vpc, self.__private_subnet_type = create_vpc(
            instance_class=self,
            service_prefix=self.__service_prefix,
            vpc_config=VpcConfig(
                cidr='10.0.0.0/24'
            ),
            subnet_config=SubnetConfig(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                subnet_id='private-subnet',
                cidr_mask=28
            )
        )

        vpc_endpoint_id_prefix = self.__service_prefix.id + 'vpc-ep-'

        self.__vpc.add_interface_endpoint(
            id=vpc_endpoint_id_prefix + 'secrets-manager',
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            subnets=ec2.SubnetSelection(
                subnet_type=self.__private_subnet_type
            )
        )

        self.__vpc.add_interface_endpoint(
            id=vpc_endpoint_id_prefix + 'lambda',
            service=ec2.InterfaceVpcEndpointAwsService.LAMBDA_,
            subnets=ec2.SubnetSelection(
                subnet_type=self.__private_subnet_type
            )
        )

        # ---------------------------------------- #
        # Security Groups
        # ---------------------------------------- #
        self.__mysql_sg = create_sg(
            instance_class=self,
            service_prefix=self.__service_prefix,
            sg_config=SecurityGroupConfig(
                id='rds',
                name='Rds',
                description='Security group for MySQL',
                vpc=self.__vpc
            )
        )

        self.__lambda_sg = create_sg(
            instance_class=self,
            service_prefix=self.__service_prefix,
            sg_config=SecurityGroupConfig(
                id='lambda',
                name='Lambda',
                description='Security group for Lambda',
                vpc=self.__vpc
            )
        )

        # ---------------------------------------- #
        # RDS - MySQL
        # ---------------------------------------- #
        self.__mysql = create_rds_mysql(
            instance_class=self,
            service_prefix=self.__service_prefix,
            db_config=DbConfig(
                vpc=self.__vpc,
                vpc_subnet_type=self.__private_subnet_type,
                security_groups=[self.__mysql_sg],
                # FIXME: The following instance_class and instance_size are not working
                # instance_class=ec2.InstanceClass.I4I,  # I/O-optimized instances with local NVME drive: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/InstanceClass.html#aws_cdk.aws_ec2.InstanceClass
                # instance_size=ec2.InstanceSize.LARGE,  # instances in eu-north-1
                credentials=rds.Credentials.from_generated_secret(
                    username='admin'
                )
            )
        )

        self.__mysql.connections.allow_default_port_from(
            other=self.__lambda_sg,
            description='Allow Lambda to access RDS'
        )

        # ---------------------------------------- #
        # Lambda Functions
        # ---------------------------------------- #
        # TODO: find a way to start the lambda_init only once to initialize the db
        self.__lambda_init = create_lambda(
            instance_class=self,
            service_prefix=self.__service_prefix,
            lambda_config=LambdaConfig(
                id='lambda-init',
                name='LambdaInit',
                description='Initialize or Delete the database table "energy_efficiency"',
                code_folder_path='stacks/energy_efficiency/lambda_init',
                index_file_name='lambda-handler.py',
                vpc=self.__vpc,
                vpc_subnet_type=self.__private_subnet_type,
                security_groups=[self.__lambda_sg],
                environment={
                    'DB_SECRET_ARN': self.__mysql.secret.secret_arn
                }
            )
        )

        self.__lambda_init.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=[
                    'secretsmanager:GetSecretValue'
                ],
                resources=[
                    self.__mysql.secret.secret_arn
                ]
            )
        )

        self.lambda_rd = create_lambda(
            instance_class=self,
            service_prefix=self.__service_prefix,
            lambda_config=LambdaConfig(
                id='lambda-read',
                name='LambdaRead',
                description='Read all data from the database table "energy_efficiency"',
                code_folder_path='stacks/energy_efficiency/lambda_read',
                index_file_name='lambda-handler.py',
                vpc=self.__vpc,
                vpc_subnet_type=self.__private_subnet_type,
                security_groups=[self.__lambda_sg],
                environment={
                    'DB_SECRET_ARN': self.__mysql.secret.secret_arn
                }
            )
        )

        self.lambda_rd.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=[
                    'secretsmanager:GetSecretValue'
                ],
                resources=[
                    self.__mysql.secret.secret_arn
                ]
            )
        )
