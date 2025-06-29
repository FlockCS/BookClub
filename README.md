# Changes to be made
- Implement Valkey on Elasticache (750 hours free)
- Implement dataclass/pydantic class for books
- Add unit tests
- 


# Book Club Bot

A Discord bot built with AWS Lambda and CDK for managing book club activities. The bot supports multiple environments (Alpha and Prod) with separate Discord applications and configurations.

## Description

This Discord bot is designed to help manage book club activities. It's built using:
- **AWS Lambda** with Docker containerization
- **AWS CDK** for infrastructure as code
- **Flask** for the web framework
- **Discord Interactions API** for bot functionality

The project supports multiple deployment environments (Alpha and Prod) with separate Discord applications, allowing for independent testing and production deployments.

## Project Structure

```
BookClub/
├── bin/                    # CDK entry point
├── commands/              # Discord command definitions
│   ├── discord_commands.yaml
│   └── register_commands.py
├── lib/                   # CDK stack definitions
│   └── book-club-bot-stack.ts
├── src/                   # Lambda function source
│   ├── app/
│   │   └── main.py        # Main Flask application
│   ├── Dockerfile         # Docker configuration
│   └── requirements.txt   # Python dependencies
├── test/                  # Test files
├── package.json           # Node.js dependencies
└── cdk.json              # CDK configuration
```

## Prerequisites

- **Node.js** (v18 or later)
- **Python** (3.8 or later)
- **AWS CLI** configured with appropriate credentials
- **Docker** (for building Lambda container)
- **Discord Application** with bot added to a server

## Environment Setup

### 1. Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies (for local development)
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Alpha Environment
ALPHA_DISCORD_TOKEN=your_alpha_bot_token
ALPHA_DISCORD_APPLICATION_ID=your_alpha_application_id
ALPHA_DISCORD_PUBLIC_KEY=your_alpha_public_key

# Prod Environment
PROD_DISCORD_TOKEN=your_prod_bot_token
PROD_DISCORD_APPLICATION_ID=your_prod_application_id
PROD_DISCORD_PUBLIC_KEY=your_prod_public_key
```

**Note:** Contact the project owner Prabhav to obtain the actual values for these environment variables.

## Deployment

### Deploy Alpha Environment

```bash
# Deploy the Alpha stack
npx cdk deploy AlphaBookClubBotStack
```

### Deploy Prod Environment

```bash
# Deploy the Prod stack
npx cdk deploy ProdBookClubBotStack
```

### Register Discord Commands

After deployment, register the Discord commands for each environment:

```bash
# Register commands for Alpha
python commands/register_commands.py alpha

# Register commands for Prod
python commands/register_commands.py prod
```

## Development

### Local Development

```bash
# Run the Flask app locally
cd src
python app/main.py
```

### Testing

```bash
# Run tests
npm test
```

### CDK Commands

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy stack
cdk deploy

# Destroy stack
cdk destroy

# List stacks
cdk list
```

## Available Commands

The bot currently supports these Discord slash commands:

- `/hello` - Responds with a greeting
- `/echo <message>` - Echoes back the provided message

Commands are defined in `commands/discord_commands.yaml` and can be extended as needed.

## Architecture

- **AWS Lambda**: Serverless compute for the bot logic
- **Docker**: Containerization for consistent deployment
- **Flask**: Web framework for handling Discord interactions
- **Mangum**: ASGI adapter for AWS Lambda
- **CDK**: Infrastructure as code for AWS resources

## Environment Separation

The project supports multiple environments with:
- Separate Discord applications (Alpha vs Prod)
- Independent Lambda functions
- Environment-specific configuration
- Isolated command registrations

## Troubleshooting

### Common Issues

1. **CDK deployment fails**: Ensure AWS credentials are configured
2. **Discord commands not working**: Verify the bot token and application ID are correct
3. **Lambda timeout**: Check the function timeout settings in the CDK stack

### Debugging

- Check CloudWatch logs for Lambda function errors
- Verify Discord application permissions and scopes
- Ensure environment variables are correctly set

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request