"""
References:
  - AWS Doc:
      - aws_cdk.NestedStack: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk/NestedStack.html
      - aws_apigateway.RestApi: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RestApi.html#aws_cdk.aws_apigateway.RestApi
      - aws_apigateway.Cors: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/Cors.html
      - aws_apigateway.MethodResponse: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/MethodResponse.html
      - aws_apigateway.LambdaIntegration: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/LambdaIntegration.html
      - aws_apigateway.IntegrationResponse: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/IntegrationResponse.html
      - aws_lambda.Function: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html#aws_cdk.aws_lambda.Function
"""

from dataclasses import dataclass

from constructs import Construct
from aws_cdk import (
    NestedStack,
    aws_lambda as lambda_,
    aws_apigateway as apigw_
)

from lib.dataclasses import (
    ServicePrefix
)


@dataclass
class ApiGatewayModel:
    method: str
    lambda_integration: lambda_.Function


class ApiGatewayStack(NestedStack):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            description: str,
            service_prefix: ServicePrefix,
            endpoint: str,
            allowed_methods: list,
            api_models: list[ApiGatewayModel],
            **kwargs
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.__api_gateway = apigw_.RestApi(
            self,
            id=service_prefix.id + 'api-gateway',
            rest_api_name=service_prefix.name + 'ApiGateway',
            description=description
        )

        self.__entity = self.__api_gateway.root.add_resource(
            endpoint,
            default_cors_preflight_options=apigw_.CorsOptions(
                allow_origins=apigw_.Cors.ALL_ORIGINS,
                allow_methods=allowed_methods
            )
        )

        for api_model in api_models:
            self.__entity.add_method(
                api_model.method,
                self._lambda_integration(api_model.lambda_integration),
                method_responses=[
                    apigw_.MethodResponse(
                        status_code='200',
                        response_parameters={
                            'method.response.header.Access-Control-Allow-Origin': True,
                        }
                    )
                ]
            )

    @staticmethod
    def _lambda_integration(lambda_function: lambda_.Function) -> apigw_.LambdaIntegration:
        return apigw_.LambdaIntegration(
            lambda_function,
            proxy=False,
            integration_responses=[
                apigw_.IntegrationResponse(
                    status_code='200',
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'",
                    }
                )
            ]
        )
