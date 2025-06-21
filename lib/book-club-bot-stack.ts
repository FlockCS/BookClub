import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from "aws-cdk-lib/aws-lambda";

export interface BookClubBotStackProps extends cdk.StackProps {
  stage: string;
  discordPublicKey: string;
}

export class BookClubBotStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BookClubBotStackProps) {
    super(scope, id, props);

    const dockerFunction = new lambda.DockerImageFunction(
      this,
      `${props.stage}DockerFunction`,
      {
        code: lambda.DockerImageCode.fromImageAsset("./src"),
        memorySize: 1024,
        timeout: cdk.Duration.seconds(10),
        architecture: lambda.Architecture.X86_64,
        environment: {
          DISCORD_PUBLIC_KEY: props.discordPublicKey,
        },
      }
    );

    const functionUrl = dockerFunction.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      cors: {
        allowedOrigins: ["*"],
        allowedMethods: [lambda.HttpMethod.ALL],
        allowedHeaders: ["*"],
      },
    });

    new cdk.CfnOutput(this, `${props.stage}FunctionUrl`, {
      value: functionUrl.url,
    });

  }
}
