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
    Duration,
    aws_ec2 as ec2,
    aws_lambda as lambda_,
    aws_rds as rds,
    aws_lambda_python_alpha as lambda_python,
    aws_iam as iam
)


class EnergyEfficiencyStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(
            scope,
            construct_id,
            description='This stack includes the resources needed for the FuturaCity project to achieve the goal of energy efficiency',
            **kwargs
        )

        self.service_id_prefix = 'ee-'
        self.service_name_prefix = 'EE'
        self.__sg_id_postfix = self.service_id_prefix + 'sg-'
        self.__sg_name_postfix = self.service_name_prefix + 'SG'

        self.__create_vpc()

        self.__rds_sg = self.__create_sg(
            sg_id='rds',
            sg_name='Rds',
            description='Security group for RDS'
        )

        self.__lambda_sg = self.__create_sg(
            sg_id='lambda',
            sg_name='Lambda',
            description='Security group for Lambda'
        )

        self.__create_db()

        # TODO: find a way to start the lambda_init only once to initialize the db
        self.__lambda_init = self.__create_lambda_with_custom_dependencies(
            lambda_id='lambda-init',
            lambda_name='LambdaInit',
            description='Initialize or Delete the database table "energy_efficiency"',
            folder_code_path='stacks/energy_efficiency/lambda_init',
            index_file_name='lambda-handler.py',
            dest_vpc=self.__vpc,
            security_group=self.__lambda_sg,
            secret_arn=self.__db.secret.secret_arn
        )

        self.lambda_wr = self.__create_lambda_with_custom_dependencies(
            lambda_id='lambda-write',
            lambda_name='LambdaWrite',
            description='Write data to the database table "energy_efficiency"',
            folder_code_path='stacks/energy_efficiency/lambda_write',
            index_file_name='lambda-handler.py',
            dest_vpc=self.__vpc,
            security_group=self.__lambda_sg,
            secret_arn=self.__db.secret.secret_arn
        )

        self.lambda_rd = self.__create_lambda_with_custom_dependencies(
            lambda_id='lambda-read',
            lambda_name='LambdaRead',
            description='Read all data from the database table "energy_efficiency"',
            folder_code_path='stacks/energy_efficiency/lambda_read',
            index_file_name='lambda-handler.py',
            dest_vpc=self.__vpc,
            security_group=self.__lambda_sg,
            secret_arn=self.__db.secret.secret_arn
        )

    def __create_sg(self, sg_id: str, sg_name: str, description: str) -> ec2.SecurityGroup:  # TODO: Add doc
        return ec2.SecurityGroup(
            self,
            id=self.__sg_id_postfix + sg_id,
            security_group_name=self.__sg_name_postfix + sg_name,
            description=description,
            vpc=self.__vpc
        )

    def __create_vpc(self) -> None:  # TODO: Add doc
        vpc_construct_id = self.service_id_prefix + 'vpc'
        vpc_name = self.service_name_prefix + 'Vpc'
        vpc_cidr = ec2.IpAddresses.cidr('10.0.0.0/24')

        private_subnet_id = self.service_id_prefix + 'private-subnet'
        self.__private_subnet_type = ec2.SubnetType.PRIVATE_ISOLATED

        vpc_endpoint_id_prefix = self.service_id_prefix + 'vpc-ep-'

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

    def __create_lambda_with_custom_dependencies(self, lambda_id: str, lambda_name: str, description: str, folder_code_path: str, index_file_name: str, dest_vpc: ec2.Vpc,
                                                 security_group: list[ec2.SecurityGroup], secret_arn: str) -> lambda_python.PythonFunction:  # TODO: Add doc
        base_lambda = lambda_python.PythonFunction(
            self,
            id=self.service_id_prefix + lambda_id,
            function_name=self.service_name_prefix + lambda_name,
            description=description,
            entry=folder_code_path,
            index=index_file_name,
            handler='handler',
            runtime=lambda_.Runtime.PYTHON_3_8,
            vpc=dest_vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=self.__private_subnet_type
            ),
            security_groups=[security_group],
            timeout=Duration.seconds(300),
            memory_size=256,
            environment={
                'DB_SECRET_ARN': secret_arn
            }
        )

        base_lambda.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=[
                    'secretsmanager:GetSecretValue',
                ],
                resources=[
                    secret_arn
                ]
            )
        )

        return base_lambda

    def __create_db(self) -> None:  # TODO: Add doc
        db_id = self.service_id_prefix + 'rds-mysql'
        self.__db_name = self.service_name_prefix + 'RdsMysql'
        db_engine_version = rds.MysqlEngineVersion.VER_8_0_28

        self.__db = rds.DatabaseInstance(
            self,
            id=db_id,
            database_name=self.__db_name,
            engine=rds.DatabaseInstanceEngine.mysql(
                version=db_engine_version
            ),
            multi_az=False,
            vpc=self.__vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=self.__private_subnet_type
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.M6I,
                ec2.InstanceSize.LARGE
            ),
            allocated_storage=500,
            deletion_protection=False,
            delete_automated_backups=True,
            security_groups=[self.__rds_sg],
            credentials=rds.Credentials.from_generated_secret(
                username='admin'
            )
        )

        # OPT_1
        self.__db.connections.allow_default_port_from(
            other=self.__lambda_sg,
            description='Allow Lambda to access RDS'
        )
        # ---------------------------------------- #
        # OPT_2: Alternative way to connect to RDS
        # self.db_sg.add_ingress_rule(
        #     peer=ec2.Peer.ipv4('0.0.0.0/0'),
        #     connection=ec2.Port.tcp(3306)
        # )
