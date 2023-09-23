"""
References:
  - AWS Doc:
        - aws_cdk.Duration: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk/Duration.html#aws_cdk.Duration.plus
        - aws_ec2.Vpc: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html#aws_cdk.aws_ec2.Vpc
        - aws_ec2.SubnetType: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetType.html
        - aws_ec2.InstanceClass: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/InstanceClass.html#aws_cdk.aws_ec2.InstanceClass
        - aws_ec2.InstanceSize: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/InstanceSize.html
        - aws_ec2.SecurityGroup: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SecurityGroup.html#aws_cdk.aws_ec2.SecurityGroup
"""

from dataclasses import dataclass

from aws_cdk import (
    Duration,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_lambda as lambda_,
    aws_iam as iam
)


@dataclass
class ServicePrefix:
    id: str
    name: str


@dataclass
class SecurityGroupConfig:
    id: str
    name: str
    description: str
    vpc: ec2.Vpc


@dataclass
class VpcConfig:
    id: str = 'vpc'
    name: str = 'Vpc'
    max_azs: int = 2
    cidr: str = '10.0.0.0/24'
    nat_gateways: int = 0


@dataclass
class SubnetConfig:
    subnet_type: ec2.SubnetType
    subnet_id: str = 'private-subnet'
    cidr_mask: int = 28


@dataclass
class DbConfig:
    vpc: ec2.Vpc
    vpc_subnet_id: str
    id: str = 'rds-mysql'
    name: str = 'RdsMysql'
    engine_version: rds.MysqlEngineVersion = rds.MysqlEngineVersion.VER_8_0_28
    instance_class: ec2.InstanceClass = ec2.InstanceClass.M6I
    instance_size: ec2.InstanceSize = ec2.InstanceSize.LARGE
    allocated_storage: int = 500
    deletion_protection: bool = False
    delete_automated_backups: bool = True
    security_groups: list[ec2.SecurityGroup] = None
    credentials: rds.Credentials = None


@dataclass
class LambdaConfig:
    id: str
    vpc: ec2.Vpc
    vpc_subnet_id: str
    name: str
    description: str
    code_folder_path: str
    index_file_name: str
    handler: str = 'handler'
    runtime: lambda_.Runtime = lambda_.Runtime.PYTHON_3_8
    timeout: Duration = Duration.seconds(300)
    memory_size: int = 256
    environment: dict = None
    security_groups: list[ec2.SecurityGroup] = None,
    role: iam.Role = None


@dataclass
class Ec2Config:
    id: str
    vpc: ec2.Vpc
    vpc_subnet_id: str
    instance_class: ec2.InstanceClass = ec2.InstanceClass.T3
    instance_size: ec2.InstanceSize = ec2.InstanceSize.MICRO
    machine_image: ec2.IMachineImage = ec2.MachineImage.latest_amazon_linux2023()
    security_group: ec2.SecurityGroup = None
    role: iam.Role = None


@dataclass
class BastionHostConfig:
    vpc: ec2.Vpc
    vpc_subnet_id: str
    id: str = 'bastion-host'
    name: str = 'BastionHost'
    instance_class: ec2.InstanceClass = ec2.InstanceClass.T3
    instance_size: ec2.InstanceSize = ec2.InstanceSize.MICRO
    security_group: ec2.SecurityGroup = None
    ssh_key_path: str = None
