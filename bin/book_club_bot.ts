#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { BookClubBotStack } from '../lib/book-club-bot-stack';

const PROD_DISCORD_PUBLIC_KEY = "2250998ebe1d6f565a07459e0263009cc18c482351e53c3415921362e69f34d6";
const ALPHA_DISCORD_PUBLIC_KEY = "baabe337167c4c03b1da7a7b9aadb146ed493d59f58011f977de72406e4a51c5";

const app = new cdk.App();
new BookClubBotStack(app, 'ProdBookClubBotStack', {
  stage: 'Prod',
  discordPublicKey: PROD_DISCORD_PUBLIC_KEY,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-2'
  },
});

new BookClubBotStack(app, 'AlphaBookClubBotStack', { 
  stage: 'Alpha',
  discordPublicKey: ALPHA_DISCORD_PUBLIC_KEY,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-2'
  },
});