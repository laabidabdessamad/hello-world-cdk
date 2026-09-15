from pathlib import Path

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as _lambda,
)
from constructs import Construct

# Resolve the app/ directory regardless of the current working directory
APP_DIR = str(Path(__file__).resolve().parent.parent / "app")


class HelloWorldStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        fn = _lambda.Function(
            self,
            "HelloWorldFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.X86_64,
            handler="main.handler",
            code=_lambda.Code.from_asset(APP_DIR),
            timeout=Duration.seconds(10),
            memory_size=128,
        )

        # Function URL = a public HTTPS endpoint with no API Gateway needed.
        fn_url = fn.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
        )

        CfnOutput(self, "FunctionUrl", value=fn_url.url)
