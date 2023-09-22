"""
References:
  - AWS Doc:
        - aws_ec2.Vpc: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html#aws_cdk.aws_ec2.Vpc
        - aws_ec2.SubnetType: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetType.html
        - aws_ec2.SecurityGroup: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SecurityGroup.html#aws_cdk.aws_ec2.SecurityGroup
        - aws_ec2.IpAddresses: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/IpAddresses.html#aws_cdk.aws_ec2.IpAddresses
        - aws_ec2.SubnetConfiguration: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetConfiguration.html
        - aws_ec2.SubnetSelection: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetSelection.html
        - aws_ec2.InstanceType: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/InstanceType.html
        - aws_rds.DatabaseInstance: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseInstance.html#aws_cdk.aws_rds.DatabaseInstance.vpc
        - aws_rds.DatabaseInstanceEngine: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseInstanceEngine.html
        - aws_lambda_python_alpha.PythonFunction: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda_python_alpha/PythonFunction.html#aws_cdk.aws_lambda_python_alpha.PythonFunction.env
        - aws_ec2.BastionHostLinux: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/BastionHostLinux.html#aws_cdk.aws_ec2.BastionHostLinux.instance
"""

from aws_cdk import (
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_lambda_python_alpha as lambda_python
)

from lib.dataclasses import (
    ServicePrefix,
    SecurityGroupConfig,
    VpcConfig,
    SubnetConfig,
    DbConfig,
    LambdaConfig,
    Ec2Config,
    BastionHostConfig
)


def create_security_group(instance_class, service_prefix: ServicePrefix,
                          sg_config: SecurityGroupConfig) -> ec2.SecurityGroup:
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


def create_vpc(instance_class, service_prefix: ServicePrefix, vpc_config: VpcConfig,
               subnets_config: list[SubnetConfig]) -> ec2.Vpc:
    """
    Create a VPC with a private subnet

    :param instance_class:
    :param service_prefix:
    :param vpc_config:
    :param subnets_config:
    :return: ec2.Vpc
    """

    vpc_construct_id = service_prefix.id + vpc_config.id
    vpc_name = service_prefix.name + vpc_config.name
    vpc_cidr = ec2.IpAddresses.cidr(vpc_config.cidr)

    subnets = []
    for sc in subnets_config:
        sb_id = service_prefix.id + sc.subnet_id
        sb_type = sc.subnet_type

        sb = ec2.SubnetConfiguration(
            name=sb_id,
            subnet_type=sb_type,
            cidr_mask=sc.cidr_mask
        )

        subnets.append(sb)

    vpc = ec2.Vpc(
        instance_class,
        vpc_construct_id,
        vpc_name=vpc_name,
        max_azs=vpc_config.max_azs,
        ip_addresses=vpc_cidr,
        subnet_configuration=subnets,
        nat_gateways=vpc_config.nat_gateways
    )

    return vpc


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
    db_subnet_id = service_prefix.id + db_config.vpc_subnet_id

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
            subnet_group_name=db_subnet_id
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


def create_lambda(instance_class, service_prefix: ServicePrefix,
                  lambda_config: LambdaConfig) -> lambda_python.PythonFunction:
    """
    Create a Lambda function with custom dependencies

    :param instance_class:
    :param service_prefix:
    :param lambda_config:
    :return:
    """

    lambda_id = service_prefix.id + lambda_config.id
    lambda_function_name = service_prefix.name + lambda_config.name
    lambda_subnet_id = service_prefix.id + lambda_config.vpc_subnet_id

    base_lambda = lambda_python.PythonFunction(
        instance_class,
        id=lambda_id,
        function_name=lambda_function_name,
        description=lambda_config.description,
        entry=lambda_config.code_folder_path,
        index=lambda_config.index_file_name,
        handler=lambda_config.handler,
        runtime=lambda_config.runtime,
        vpc=lambda_config.vpc,
        vpc_subnets=ec2.SubnetSelection(
            subnet_group_name=lambda_subnet_id
        ),
        security_groups=lambda_config.security_groups,
        timeout=lambda_config.timeout,
        memory_size=lambda_config.memory_size,
        environment=lambda_config.environment
    )

    return base_lambda


def create_ec2(instance_class, service_prefix: ServicePrefix, ec2_config: Ec2Config) -> ec2.Instance:
    """
    Create an EC2 instance

    :param instance_class:
    :param service_prefix:
    :param ec2_config:
    :return:
    """

    ec2_id = service_prefix.id + ec2_config.id
    ec2_subnet_id = service_prefix.id + ec2_config.vpc_subnet_id

    instance = ec2.Instance(
        instance_class,
        id=ec2_id,
        instance_type=ec2.InstanceType.of(
            ec2_config.instance_class,
            ec2_config.instance_size
        ),
        machine_image=ec2_config.machine_image,
        vpc=ec2_config.vpc,
        vpc_subnets=ec2.SubnetSelection(
            subnet_group_name=ec2_subnet_id
        ),
        role=ec2_config.role,
        security_group=ec2_config.security_group,
        key_name='ec2-bastion-host'
    )

    # for sg in ec2_config.security_groups:
    #     instance.add_security_group(sg)

    return instance


def create_bastion_host(instance_class, service_prefix: ServicePrefix,
                        bh_config: BastionHostConfig) -> ec2.BastionHostLinux:
    """
    Create a Bastion Host

    :param instance_class:
    :param service_prefix:
    :param bh_config:
    :return:
    """
    bh = ec2.BastionHostLinux(
        instance_class,
        id=service_prefix.id + bh_config.id,
        vpc=bh_config.vpc,
        subnet_selection=ec2.SubnetSelection(
            subnet_group_name=service_prefix.id + bh_config.vpc_subnet_id
        ),
        instance_name=service_prefix.name + bh_config.name,
        instance_type=ec2.InstanceType.of(
            bh_config.instance_class,
            bh_config.instance_size
        ),
        security_group=bh_config.security_group
    )

    with open(bh_config.ssh_key_path) as f:
        bh_key = f.read()

    bh.instance.user_data.add_commands(
        f'echo {bh_key} > /mnt/id_rsa && '
        f'chmod 0400 /mnt/id_rsa && '
        f'chown ec2-user:ec2-user /mnt/id_rsa'
    )
