import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as elasticache from 'aws-cdk-lib/aws-elasticache'
import * as ec2 from 'aws-cdk-lib/aws-ec2'

export interface BookClubBotStackProps extends cdk.StackProps {
  stage: string;
  discordPublicKey: string;
}

export class BookClubBotStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BookClubBotStackProps) {
    super(scope, id, props);

    // Default VPC
    const defaultVpc = ec2.Vpc.fromLookup(this, 'DefaultVPC', {
      isDefault: true
    });

    // Security groups
    const lambdaSecurityGroup = new ec2.SecurityGroup(
      this,
      `${props.stage}LambdaSecurityGroup`,
      {
        vpc: defaultVpc,
        description: 'Security group for Lambda',
        allowAllOutbound: true
      }
    );

    // Lambda
    const dockerFunction = new lambda.DockerImageFunction(
      this,
      `${props.stage}DockerFunction`,
      {
        code: lambda.DockerImageCode.fromImageAsset("./src"),
        memorySize: 1024,
        timeout: cdk.Duration.seconds(10),
        architecture: lambda.Architecture.X86_64,
        vpc: defaultVpc,
        vpcSubnets: {
          subnetType: ec2.SubnetType.PUBLIC
        },
        securityGroups: [lambdaSecurityGroup],
        environment: {
          DISCORD_PUBLIC_KEY: props.discordPublicKey,
          ELASTICACHE_CLUSTER_ENDPOINT: process.env.ELASTICACHE_CLUSTER_ENDPOINT || 'unknown'
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

    // DynamoDB
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

    // Valkey on Elasticache
    const cacheSecurityGroup = new ec2.SecurityGroup(
      this,
      `${props.stage}ElasticacheSecurityGroup`,
      {
        vpc: defaultVpc,
        description: 'Security group for Elasticache',
        allowAllOutbound: true
      }
    );

    cacheSecurityGroup.addIngressRule(
      lambdaSecurityGroup,
      ec2.Port.tcp(6379),
      'Allow lambda access'
    );

    const cacheSubnetGroup = new elasticache.CfnSubnetGroup(
      this,
      `${props.stage}ElasticacheSubnetGroup`,
      {
        subnetIds: defaultVpc.publicSubnets.map(subnet => subnet.subnetId)
      }
    );

    const cacheCluster = new elasticache.CfnReplicationGroup(
      this,
      `${props.stage}CacheCluster`,
      {
        engine: 'valkey',
        cacheNodeType: 'cache.t3.micro',
        numNodeGroups: 1, // leave as is
        replicasPerNodeGroup: 1, // increase to scale
        replicationGroupDescription: "Cache to store book info from Google API",
        transitEncryptionEnabled: false,
        securityGroupIds: [cacheSecurityGroup.securityGroupId],
        cacheSubnetGroupName: cacheSubnetGroup.ref,
        port:6379
    });

    // Cloudformation output
    new cdk.CfnOutput(this, `${props.stage}FunctionUrl`, {
      value: functionUrl.url,
    });

    new cdk.CfnOutput(this, `${props.stage}ElasticacheEndpoint`, {
      value: cacheCluster.attrPrimaryEndpointAddress,
    });
  }
}
