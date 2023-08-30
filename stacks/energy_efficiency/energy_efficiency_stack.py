from constructs import Construct
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_lambda as lambda_,
    aws_rds as rds
)


class EnergyEfficiencyStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.subnet_name = 'DB'

        self.__create_vpc()

        self.lambda_wr = self.__create_lambda(
            name='LambdaWrite',
            dest_vpc=self.vpc,
            # dest_subnet=self.db_subnet,
            code_path='stacks/energy_efficiency/lambda_write'
            )

        self.lambda_rd = self.__create_lambda(
            name='LambdaRead',
            dest_vpc=self.vpc,
            code_path='stacks/energy_efficiency/lambda_read'
            )

        self.__create_db()

    def __create_vpc(self) -> None:
        vpc_construct_id = 'energy-efficiency-vpc'
        vpc_name = 'EnergyEfficiencyVpc'
        vpc_cidr = ec2.IpAddresses.cidr('10.0.0.0/24')

        self.db_subnet = ec2.SubnetConfiguration(
            name=self.subnet_name, 
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, 
            cidr_mask=28
        )

        self.vpc: ec2.Vpc = ec2.Vpc(
            self,
            vpc_construct_id,
            vpc_name=vpc_name,
            # max_azs=1,
            ip_addresses=vpc_cidr,
            subnet_configuration=[
                self.db_subnet
            ],
            nat_gateways=0
        )

    def __create_lambda(self, name: str, code_path: str, dest_vpc: ec2.Vpc, dest_subnet=None) -> lambda_.Function:
        base_lambda = lambda_.Function(
            self,
            name,
            handler='lambda-handler.handler',  # Name_of_file.Name_of_function_to_call
            runtime=lambda_.Runtime.PYTHON_3_7,
            vpc=dest_vpc,
            vpc_subnets=dest_subnet,
            code=lambda_.Code.from_asset(code_path)  # Path_to_folder_containing_lambda_handler.py
        )

        return base_lambda

    def __create_db(self) -> None:
        db_construct_id = 'energy-efficiency-db'
        db_name = 'EnergyEfficiencyDb'

        self.db = rds.DatabaseInstance(
            self,
            db_construct_id,
            database_name=db_name,
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_5_7
            ),
            multi_az=False,
            vpc=self.vpc,
            # vpc_subnets=ec2.SubnetSelection(
            #     subnet_group_name=self.subnet_name
            # ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.M5,  # TODO: Check if this is enough
                ec2.InstanceSize.LARGE  # TODO: Check if this is enough
            ),
            allocated_storage=20,  # TODO: Check if this is enough
            deletion_protection=False,
            delete_automated_backups=True
        )
