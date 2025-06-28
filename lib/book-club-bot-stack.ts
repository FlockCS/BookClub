import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

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

    // Create the table: one partition key (guild) + one sort key (ISO date)
    const historyTable = new dynamodb.Table(this, `${props.stage}BookHistory`, {
      tableName: `${props.stage}-BookClubHistory`,
      partitionKey: { name: 'guild_id', type: dynamodb.AttributeType.STRING },
      billingMode:  dynamodb.BillingMode.PAY_PER_REQUEST,  // on-demand
      removalPolicy: cdk.RemovalPolicy.RETAIN,             // keep data if stack is destroyed
    });

    // Let the Lambda read/write the table
    historyTable.grantReadWriteData(dockerFunction);

    // Pass table name to the container
    dockerFunction.addEnvironment('BOOK_TABLE', historyTable.tableName);

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
