import aws_cdk as core
import aws_cdk.assertions as assertions

from futura_city.futura_city_stack import FuturaCityStack

# example tests. To run these tests, uncomment this file along with the example
# resource in futura_city/futura_city_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = FuturaCityStack(app, "futura-city")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
