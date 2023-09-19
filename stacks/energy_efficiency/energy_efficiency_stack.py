"""
References:
  - AWS Doc:
      - aws_lambda.Function: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html#aws_cdk.aws_lambda.Function
      - aws_lambda.EcrImageCode: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/EcrImageCode.html#ecrimagecode
      - aws_lambda_python_alpha.PythonFunction: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda_python_alpha/PythonFunction.html#pythonfunction
      - aws_ec2.Vpc: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html#aws_cdk.aws_ec2.Vpc
      - aws_ec2.SubnetConfiguration: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetConfiguration.html
      - aws_ec2.SubnetSelection: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetSelection.html#subnetselection
      - aws_ec2.SubnetType: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetType.html
      - aws_ec2.IpAddresses: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/IpAddresses.html#aws_cdk.aws_ec2.IpAddresses
      - aws_ec2.SecurityGroup: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SecurityGroup.html#aws_cdk.aws_ec2.SecurityGroup
      - aws_rds.DatabaseInstance: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseInstance.html
      - aws_rds.DatabaseInstanceEngine: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseInstanceEngine.html
      - aws_ec2.InstanceType: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/InstanceType.html#aws_cdk.aws_ec2.InstanceType
      - aws_ec2.InstanceClass: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/InstanceClass.html

  - Examples:
      - Creating AWS VPC using CDK with Python: https://stories.fylehq.com/p/creating-aws-vpc-using-cdk-with-python
      - How to Connect to AWS RDS from AWS Lambda: https://www.freecodecamp.org/news/aws-lambda-rds/
      - lambda-from-container: https://github.com/aws-samples/aws-cdk-examples/tree/master/python/lambda-from-container
      - Use AWS CDK to initialize Amazon RDS instances: https://aws.amazon.com/it/blogs/infrastructure-and-automation/use-aws-cdk-to-initialize-amazon-rds-instances/
      - amazon-rds-init-cdk: https://github.com/aws-samples/amazon-rds-init-cdk
      - Grant AWS Lambda Access to Secrets Manager: https://bobbyhadz.com/blog/aws-grant-lambda-access-to-secrets-manager
      - How to add permissions to Lambda Functions in AWS CDK: https://bobbyhadz.com/blog/aws-cdk-add-lambda-permission
      - custom-resource: https://github.com/aws-samples/aws-cdk-examples/tree/master/python/custom-resource
      - amazon-rds-init-cdk: https://github.com/aws-samples/amazon-rds-init-cdk/tree/main
      - RDS (with Custom Resource for adding database, user and table) - AWS CDK using TypeScript: https://www.youtube.com/watch?v=faTaAJ-zIio&ab_channel=FarukAda
      - cdk-ts-rds: https://github.com/CodingWithFaruci/cdk-ts-rds/tree/main
      - DB instance supported combination: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html
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


# TODO: Add Cognito to ApiGateway
# TODO: Add CloudWatch
# TODO: Add Amplify (?)


class EnergyEfficiencyStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(
            scope,
            construct_id,
            description='This stack includes the resources needed for the FuturaCity project to achieve the goal of energy efficiency',
            **kwargs
        )

        self.service_prefix = ServicePrefix(
            id='ee-',
            name='Ee'
        )

        # ---------------------------------------- #
        # VPC
        # ---------------------------------------- #
        self.__vpc, self.__private_subnet_type = create_vpc(
            instance_class=self,
            service_prefix=self.service_prefix,
            vpc_config=VpcConfig(
                cidr='10.0.0.0/24'
            ),
            subnet_config=SubnetConfig(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                subnet_id='private-subnet',
                cidr_mask=28
            )
        )

        vpc_endpoint_id_prefix = self.service_prefix.id + 'vpc-ep-'

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
            service_prefix=self.service_prefix,
            sg_config=SecurityGroupConfig(
                id='rds',
                name='Rds',
                description='Security group for MySQL',
                vpc=self.__vpc
            )
        )

        self.__lambda_sg = create_sg(
            instance_class=self,
            service_prefix=self.service_prefix,
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
            service_prefix=self.service_prefix,
            db_config=DbConfig(
                vpc=self.__vpc,
                vpc_subnet_type=self.__private_subnet_type,
                security_groups=[self.__mysql_sg],
                credentials=rds.Credentials.from_generated_secret(
                    username='admin'
                )
            )
        )

        # OPT_1
        self.__mysql.connections.allow_default_port_from(
            other=self.__lambda_sg,
            description='Allow Lambda to access RDS'
        )
        # ---------------------------------------- #
        # OPT_2: Alternative way to connect to RDS
        # self.db_sg.add_ingress_rule(
        #     peer=ec2.Peer.ipv4('0.0.0.0/0'),
        #     connection=ec2.Port.tcp(3306)
        # )

        # ---------------------------------------- #
        # Lambda Functions
        # ---------------------------------------- #
        # TODO: find a way to start the lambda_init only once to initialize the db
        self.__lambda_init = create_lambda(
            instance_class=self,
            service_prefix=self.service_prefix,
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

        self.lambda_wr = create_lambda(
            instance_class=self,
            service_prefix=self.service_prefix,
            lambda_config=LambdaConfig(
                id='lambda-write',
                name='LambdaWrite',
                description='Write data to the database table "energy_efficiency"',
                code_folder_path='stacks/energy_efficiency/lambda_write',
                index_file_name='lambda-handler.py',
                vpc=self.__vpc,
                vpc_subnet_type=self.__private_subnet_type,
                security_groups=[self.__lambda_sg],
                environment={
                    'DB_SECRET_ARN': self.__mysql.secret.secret_arn
                }
            )
        )

        self.lambda_wr.add_to_role_policy(
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
            service_prefix=self.service_prefix,
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
