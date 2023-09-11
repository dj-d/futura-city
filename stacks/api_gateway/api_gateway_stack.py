"""
References:
  - AWS Doc:
      - aws_apigateway.RestApi: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RestApi.html#aws_cdk.aws_apigateway.RestApi
"""

from dataclasses import dataclass

from constructs import Construct
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_apigateway as apigw_
)


@dataclass
class ApiGatewayModel:
    method: str
    lambda_integration: lambda_.Function


class ApiGatewayStack(Stack):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            apigw_description: str,
            api_id: str,
            api_name: str,
            endpoint: str,
            allowed_methods: list,
            api_models: list[ApiGatewayModel],
            **kwargs
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.__endpoint = endpoint
        self.__allowed_methods = allowed_methods
        self.__api_models = api_models

        self.__api_gateway = self.__create_rest_api(
            api_name=api_name,
            api_id=api_id,
            description=apigw_description
        )

        self.__entity = self.__api_gateway.root.add_resource(
            self.__endpoint,
            default_cors_preflight_options=apigw_.CorsOptions(
                allow_origins=apigw_.Cors.ALL_ORIGINS,
                allow_methods=self.__allowed_methods
            )
        )

        for api_model in self.__api_models:
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

    def __create_rest_api(self, api_id: str, description: str, api_name: str) -> apigw_.RestApi:
        return apigw_.RestApi(
            self,
            id=api_id,
            description=description,
            rest_api_name=api_name
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
