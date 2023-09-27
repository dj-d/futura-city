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
    aws_iam as iam,
    aws_cognito as cognito,
    aws_amplify_alpha as amplify
)

from lib.dataclasses import (
    ServicePrefix,
    SecurityGroupConfig,
    VpcConfig,
    SubnetConfig,
    DbConfig,
    LambdaConfig,
    Ec2Config,
    BastionHostConfig,
    IamRoleConfig,
    S3Config
)

from lib.services import (
    create_security_group as create_sg,
    create_vpc,
    create_rds_mysql,
    create_lambda,
    create_ec2,
    create_bastion_host,
    create_role_inline_policy,
    get_secret_value_access_policy,
    create_s3_bucket
)

from stacks.api_gateway.api_gateway_stack import (
    ApiGatewayStack,
    ApiGatewayModel
)

service_prefix = ServicePrefix(
    id='st-',
    name='St'
)

gh_token_id = f'GH_TOKEN_ID={service_prefix.id}gh-token'

with open('./stacks/smart_traffic/userdata/ec2_wr_init.sh') as f:
    ec2_wr_init = f.read()

with open('./stacks/smart_traffic/userdata/ec2_ai_engine_init.sh') as f:
    ec2_ai_engine_init = f.read()

with open('./stacks/smart_traffic/userdata/ec2_sensor_listener_init.sh') as f:
    ec2_sensors_listener_init = f.read()


class SmartTrafficStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(
            scope,
            construct_id,
            description='This stack includes the resources needed for the FuturaCity project to achieve the goal of smart traffic management',
            **kwargs
        )

        # ---------------------------------------- #
        # VPC
        # ---------------------------------------- #
        public_subnet_config = SubnetConfig(
            subnet_id='public-subnet',
            subnet_type=ec2.SubnetType.PUBLIC,
            cidr_mask=24
        )

        sensor_subnet_config = SubnetConfig(
            subnet_id='sensor-subnet',
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            cidr_mask=24
        )

        ai_subnet_config = SubnetConfig(
            subnet_id='ai-subnet',
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            cidr_mask=24
        )

        storage_subnet_config = SubnetConfig(
            subnet_id='storage-subnet',
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            cidr_mask=24
        )

        self.__vpc = create_vpc(
            instance_class=self,
            service_prefix=service_prefix,
            vpc_config=VpcConfig(
                cidr='10.0.0.0/16',
                nat_gateways=1
            ),
            subnets_config=[
                public_subnet_config,
                sensor_subnet_config,
                ai_subnet_config,
                storage_subnet_config
            ]
        )

        # ---------------------------------------- #
        # Security Groups
        # ---------------------------------------- #
        mysql_sg = create_sg(
            instance_class=self,
            service_prefix=service_prefix,
            sg_config=SecurityGroupConfig(
                id='rds',
                name='Rds',
                description='Security group for MySQL',
                vpc=self.__vpc
            )
        )

        lambda_sg = create_sg(
            instance_class=self,
            service_prefix=service_prefix,
            sg_config=SecurityGroupConfig(
                id='lambda',
                name='Lambda',
                description='Security group for Lambda',
                vpc=self.__vpc
            )
        )

        bh_sg = create_sg(
            instance_class=self,
            service_prefix=service_prefix,
            sg_config=SecurityGroupConfig(
                id='bh',
                name='BastionHost',
                description='Security group for Bastion Host',
                vpc=self.__vpc
            )
        )

        bh_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22),
            description='Allow ssh access from anywhere'
        )

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
        # RDS - MySQL
        # ---------------------------------------- #
        self.__mysql = create_rds_mysql(
            instance_class=self,
            service_prefix=service_prefix,
            db_config=DbConfig(
                vpc=self.__vpc,
                vpc_subnet_id=storage_subnet_config.subnet_id,
                security_groups=[mysql_sg],
                # FIXME: The following instance_class and instance_size are not working
                # instance_class=ec2.InstanceClass.I4I,  # I/O-optimized instances with local NVME drive: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/InstanceClass.html#aws_cdk.aws_ec2.InstanceClass
                # instance_size=ec2.InstanceSize.LARGE,  # instances in eu-north-1
                credentials=rds.Credentials.from_generated_secret(
                    username='admin'
                )
            )
        )

        self.__mysql.connections.allow_default_port_from(
            other=lambda_sg,
            description='Allow Lambda to access RDS'
        )

        self.__mysql.connections.allow_default_port_from(
            other=ec2_sg,
            description='Allow EC2 to access RDS'
        )

        # ---------------------------------------- #
        # S3 Buckets
        # ---------------------------------------- #
        self.__image_backups_bucket = create_s3_bucket(
            instance_class=self,
            service_prefix=service_prefix,
            s3_config=S3Config(
                id='image-backups-bucket'
            )
        )

        # ---------------------------------------- #
        # Lambda Functions
        # ---------------------------------------- #
        # TODO: find a way to start the lambda_init only once to initialize the db
        self.__lambda_init = create_lambda(
            instance_class=self,
            service_prefix=service_prefix,
            lambda_config=LambdaConfig(
                id='lambda-init',
                name='LambdaInit',
                description='Initialize or Delete the database table "energy_efficiency"',
                code_folder_path='stacks/smart_traffic/lambda_init',
                index_file_name='lambda-handler.py',
                vpc=self.__vpc,
                vpc_subnet_id=storage_subnet_config.subnet_id,
                security_groups=[lambda_sg],
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
            service_prefix=service_prefix,
            lambda_config=LambdaConfig(
                id='lambda-read',
                name='LambdaRead',
                description='Read all data from the database table "energy_efficiency"',
                code_folder_path='stacks/smart_traffic/lambda_read',
                index_file_name='lambda-handler.py',
                vpc=self.__vpc,
                vpc_subnet_id=storage_subnet_config.subnet_id,
                security_groups=[lambda_sg],
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

        # ---------------------------------------- #
        # Bastion Host
        # ---------------------------------------- #
        self.__bastion_host = create_bastion_host(
            instance_class=self,
            service_prefix=service_prefix,
            bh_config=BastionHostConfig(
                vpc=self.__vpc,
                vpc_subnet_id=public_subnet_config.subnet_id,
                security_group=bh_sg,
                ssh_key_path='./stacks/smart_traffic/userdata/ec2-bastion-host.pem'
            )
        )

        # ---------------------------------------- #
        # EC2 Instances
        # ---------------------------------------- #
        self.__ec2_wr = create_ec2(
            instance_class=self,
            service_prefix=service_prefix,
            ec2_config=Ec2Config(
                id='ec2-wr',
                vpc=self.__vpc,
                vpc_subnet_id=storage_subnet_config.subnet_id,
                security_group=ec2_sg,
                role=ec2_role,
                key_name='ec2-bastion-host'
            )
        )

        self.__ec2_wr.user_data.add_commands(gh_token_id)
        self.__ec2_wr.user_data.add_commands(f'DB_SECRET_ARN={self.__mysql.secret.secret_arn}')
        self.__ec2_wr.user_data.add_commands(ec2_wr_init)
        self.__ec2_wr.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=[
                    'secretsmanager:GetSecretValue'
                ],
                resources=[
                    self.__mysql.secret.secret_arn
                ]
            )
        )

        self.__ec2_ai_engine = create_ec2(
            instance_class=self,
            service_prefix=service_prefix,
            ec2_config=Ec2Config(
                id='ec2-ai-engine',
                vpc=self.__vpc,
                vpc_subnet_id=ai_subnet_config.subnet_id,
                security_group=ec2_sg,
                role=ec2_role,
                key_name='ec2-bastion-host'
            )
        )

        self.__ec2_ai_engine.user_data.add_commands(gh_token_id)
        self.__ec2_ai_engine.user_data.add_commands(f'EC2_WR_PRIVATE_IP={self.__ec2_wr.instance_private_ip}')
        self.__ec2_ai_engine.user_data.add_commands(ec2_ai_engine_init)

        self.__ec2_sensor_listener = create_ec2(
            instance_class=self,
            service_prefix=service_prefix,
            ec2_config=Ec2Config(
                id='ec2-sensor-listener',
                vpc=self.__vpc,
                vpc_subnet_id=sensor_subnet_config.subnet_id,
                security_group=ec2_sg,
                role=ec2_role,
                key_name='ec2-bastion-host'
            )
        )

        self.__ec2_sensor_listener.user_data.add_commands(gh_token_id)
        self.__ec2_sensor_listener.user_data.add_commands(
            f'IMAGE_BACKUPS_BUCKET={self.__image_backups_bucket.bucket_name}')
        self.__ec2_sensor_listener.user_data.add_commands(
            f'EC2_AI_ENGINE_PRIVATE_IP={self.__ec2_ai_engine.instance_private_ip}')
        self.__ec2_sensor_listener.user_data.add_commands(ec2_sensors_listener_init)

        self.__ec2_sensor_listener.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=[
                    's3:PutObject',
                    's3:PutObjectAcl'
                ],
                resources=[
                    f'arn:aws:s3:::{self.__image_backups_bucket.bucket_name}/*'
                ]
            )
        )

        # ---------------------------------------- #
        # Cognito
        # ---------------------------------------- #
        self.__auth_pool = cognito.UserPool(
            self,
            id=service_prefix.id + 'auth-pool',
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=True
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
        )

        self.__auth_client = cognito.UserPoolClient(
            self,
            id=service_prefix.id + 'auth-client',
            user_pool=self.__auth_pool,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                custom=True
            )
        )

        # ---------------------------------------- #
        # Api Gateway
        # ---------------------------------------- #
        self.__api_gateway = ApiGatewayStack(
            scope=self,
            construct_id=service_prefix.id + 'api-gateway',
            description='Api Gateway for the Smart Traffic project',
            service_prefix=service_prefix,
            endpoint='smart-traffic-api',
            allowed_methods=[
                'GET'
            ],
            api_models=[
                ApiGatewayModel(
                    method='GET',
                    lambda_integration=self.lambda_rd
                )
            ]
        )

        # ---------------------------------------- #
        # Amplify
        # ---------------------------------------- #
        self.__ui = amplify.App(
            self,
            id=service_prefix.id + 'ui',
            source_code_provider=amplify.GitHubSourceCodeProvider(
                owner='dj-d',
                repository='fc-st-frontend',
                oauth_token=SecretValue.secrets_manager(
                    service_prefix.id + 'gh-token',
                    json_field='github-token'
                )
            ),
            environment_variables={
                'API_ENDPOINT': self.__api_gateway.url,
                'REGION': 'eu-north-1',
                'USER_POOL_ID': self.__auth_pool.user_pool_id,
                'USER_POOL_CLIENT_ID': self.__auth_client.user_pool_client_id
            }
        )

        self.__ui.add_branch('main')
