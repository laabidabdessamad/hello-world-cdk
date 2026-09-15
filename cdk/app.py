#!/usr/bin/env python3
import aws_cdk as cdk

from stack import HelloWorldStack

app = cdk.App()
HelloWorldStack(app, "HelloWorldStack")
app.synth()
