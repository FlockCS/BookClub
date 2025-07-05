import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as elasticache from 'aws-cdk-lib/aws-elasticache'
import * as ec2 from 'aws-cdk-lib/aws-ec2'

export interface BookClubBotStackProps extends cdk.StackProps {
  stage: string;
  discordPublicKey: string;
  env: { [key: string]: string };
}

export class BookClubBotStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BookClubBotStackProps) {
    super(scope, id, props);

    // Lambda
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

    // DynamoDB Book table
    // Create the table: one partition key (guild) + one sort key (ISO date)
    const historyTable = new dynamodb.Table(
      this,
      `${props.stage}BookHistory`, 
      {
      tableName: `${props.stage}-BookClubHistory`,
      partitionKey: { 
        name: 'guild_id', type: dynamodb.AttributeType.STRING 
      },
      billingMode:  dynamodb.BillingMode.PAY_PER_REQUEST,  // on-demand
      removalPolicy: cdk.RemovalPolicy.RETAIN,             // keep data if stack is destroyed
      }
    );
    historyTable.grantReadWriteData(dockerFunction);
    dockerFunction.addEnvironment('BOOK_TABLE', historyTable.tableName);

    // DynamoDB Cache table
    const cacheTable = new dynamodb.Table(
      this,
      `${props.stage}CacheTable`,
      {
        tableName: `${props.stage}-BookClubCache`,
        partitionKey: {
          name: 'guild_id',
          type: dynamodb.AttributeType.STRING
        },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        deletionProtection: true,
        removalPolicy: cdk.RemovalPolicy.RETAIN,
        timeToLiveAttribute: 'ttl'
      }
    );
    cacheTable.grantReadWriteData(dockerFunction);
    dockerFunction.addEnvironment('CACHE_TABLE', cacheTable.tableName);

    // Cloudformation output
    new cdk.CfnOutput(this, `${props.stage}FunctionUrl`, {
      value: functionUrl.url,
    });
  }
}
