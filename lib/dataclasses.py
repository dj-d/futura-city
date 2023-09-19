from dataclasses import dataclass

from aws_cdk import (
    Duration,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_lambda as lambda_,

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


@dataclass
class SubnetConfig:
    subnet_type: ec2.SubnetType
    subnet_id: str = 'private-subnet'
    cidr_mask: int = 28


@dataclass
class DbConfig:
    vpc: ec2.Vpc
    vpc_subnet_type: ec2.SubnetType
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
    vpc: ec2.Vpc
    vpc_subnet_type: ec2.SubnetType
    id: str
    name: str
    description: str
    code_folder_path: str
    index_file_name: str
    handler: str = 'handler'
    runtime: lambda_.Runtime = lambda_.Runtime.PYTHON_3_8
    timeout: Duration = Duration.seconds(300)
    memory_size: int = 256
    environment: dict = None
    security_groups: list[ec2.SecurityGroup] = None
