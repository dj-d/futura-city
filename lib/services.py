from aws_cdk import (
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_lambda_python_alpha as lambda_python
)

from typing import Union

from lib.dataclasses import (
    ServicePrefix,
    SecurityGroupConfig,
    VpcConfig,
    SubnetConfig,
    DbConfig,
    LambdaConfig
)


def create_security_group(instance_class, service_prefix: ServicePrefix, sg_config: SecurityGroupConfig) -> ec2.SecurityGroup:
    """
    Create a Security Group

    :param instance_class:
    :param service_prefix:
    :param sg_config:
    :return: ec2.SecurityGroup
    """

    sg_id = service_prefix.id + 'sg-' + sg_config.id
    sg_name = service_prefix.name + 'Sg' + sg_config.name

    return ec2.SecurityGroup(
        instance_class,
        id=sg_id,
        security_group_name=sg_name,
        description=sg_config.description,
        vpc=sg_config.vpc
    )


def create_vpc(instance_class, service_prefix: ServicePrefix, vpc_config: VpcConfig, subnet_config: SubnetConfig) -> Union[ec2.Vpc, ec2.SubnetType]:
    """
    Create a VPC with a private subnet

    :param instance_class:
    :param service_prefix:
    :param vpc_config:
    :param subnet_config:
    :return: Union[ec2.Vpc, ec2.SubnetType]
    """

    vpc_construct_id = service_prefix.id + vpc_config.id
    vpc_name = service_prefix.name + vpc_config.name
    vpc_cidr = ec2.IpAddresses.cidr(vpc_config.cidr)

    private_subnet_id = service_prefix.id + subnet_config.subnet_id
    private_subnet_type = subnet_config.subnet_type

    private_subnet = ec2.SubnetConfiguration(
        name=private_subnet_id,
        subnet_type=private_subnet_type,
        cidr_mask=subnet_config.cidr_mask
    )

    vpc = ec2.Vpc(
        instance_class,
        vpc_construct_id,
        vpc_name=vpc_name,
        max_azs=vpc_config.max_azs,
        ip_addresses=vpc_cidr,
        subnet_configuration=[
            private_subnet
        ]
    )

    return vpc, private_subnet_type


def create_rds_mysql(instance_class, service_prefix: ServicePrefix, db_config: DbConfig) -> rds.DatabaseInstance:
    """
    Create an RDS MySQL instance

    :param instance_class:
    :param service_prefix:
    :param db_config:
    :return: rds.DatabaseInstance
    """

    db_id = service_prefix.id + 'rds-mysql'
    db_name = service_prefix.name + 'RdsMysql'
    db_engine_version = db_config.engine_version

    return rds.DatabaseInstance(
        instance_class,
        id=db_id,
        database_name=db_name,
        engine=rds.DatabaseInstanceEngine.mysql(
            version=db_engine_version
        ),
        multi_az=False,
        vpc=db_config.vpc,
        vpc_subnets=ec2.SubnetSelection(
            subnet_type=db_config.vpc_subnet_type
        ),
        instance_type=ec2.InstanceType.of(
            db_config.instance_class,
            db_config.instance_size
        ),
        allocated_storage=db_config.allocated_storage,
        deletion_protection=db_config.deletion_protection,
        delete_automated_backups=db_config.delete_automated_backups,
        security_groups=db_config.security_groups,
        credentials=db_config.credentials
    )


def create_lambda(instance_class, service_prefix: ServicePrefix, lambda_config: LambdaConfig) -> lambda_python.PythonFunction:
    """
    Create a Lambda function with custom dependencies

    :param instance_class:
    :param service_prefix:
    :param lambda_config:
    :return:
    """

    base_lambda = lambda_python.PythonFunction(
        instance_class,
        id=service_prefix.id + lambda_config.id,
        function_name=service_prefix.name + lambda_config.name,
        description=lambda_config.description,
        entry=lambda_config.code_folder_path,
        index=lambda_config.index_file_name,
        handler=lambda_config.handler,
        runtime=lambda_config.runtime,
        vpc=lambda_config.vpc,
        vpc_subnets=ec2.SubnetSelection(
            subnet_type=lambda_config.vpc_subnet_type
        ),
        security_groups=lambda_config.security_groups,
        timeout=lambda_config.timeout,
        memory_size=lambda_config.memory_size,
        environment=lambda_config.environment
    )
    return base_lambda
