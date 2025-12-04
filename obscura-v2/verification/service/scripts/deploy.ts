#!/usr/bin/env tsx
/**
 * Deploy Verifier Contract to Starknet Sepolia
 * 
 * Usage: npx tsx scripts/deploy.ts
 */

import { Account, RpcProvider, json, Contract, CallData, hash, stark } from 'starknet';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import 'dotenv/config';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
  console.log('🚀 Deploying Obscura Verifier Contract to Starknet Sepolia...\n');

  // Load environment
  const rpcUrl = process.env.STARKNET_RPC_URL;
  const accountAddress = process.env.STARKNET_ACCOUNT_ADDRESS;
  const privateKey = process.env.STARKNET_PRIVATE_KEY;

  if (!rpcUrl || !accountAddress || !privateKey) {
    throw new Error('Missing environment variables. Check .env file.');
  }

  // Initialize provider and account
  const provider = new RpcProvider({ nodeUrl: rpcUrl });
  const account = new Account(provider, accountAddress, privateKey);

  console.log(`📡 RPC: ${rpcUrl}`);
  console.log(`👤 Account: ${accountAddress}`);

  // Load compiled contract
  const contractPath = path.join(__dirname, '../../cairo/target/dev/obscura_verification_ObscuraVerifier.contract_class.json');
  const compiledContractPath = path.join(__dirname, '../../cairo/target/dev/obscura_verification_ObscuraVerifier.compiled_contract_class.json');

  if (!fs.existsSync(contractPath)) {
    throw new Error(`Contract class not found at ${contractPath}. Run 'scarb build' first.`);
  }

  const contractClass = json.parse(fs.readFileSync(contractPath, 'utf-8'));
  const compiledContract = json.parse(fs.readFileSync(compiledContractPath, 'utf-8'));

  console.log('\n📜 Declaring contract...');

  // Declare the contract
  const declareResponse = await account.declare({
    contract: contractClass,
    casm: compiledContract,
  });

  console.log(`✅ Class Hash: ${declareResponse.class_hash}`);
  console.log(`📝 Tx Hash: ${declareResponse.transaction_hash}`);

  // Wait for declaration to be confirmed
  console.log('\n⏳ Waiting for declaration confirmation...');
  await provider.waitForTransaction(declareResponse.transaction_hash);
  console.log('✅ Declaration confirmed!');

  // Deploy the contract
  console.log('\n🏗️  Deploying contract instance...');

  const deployResponse = await account.deployContract({
    classHash: declareResponse.class_hash,
    constructorCalldata: [], // No constructor args for our contract
  });

  console.log(`📝 Deploy Tx Hash: ${deployResponse.transaction_hash}`);

  // Wait for deployment
  console.log('\n⏳ Waiting for deployment confirmation...');
  await provider.waitForTransaction(deployResponse.transaction_hash);
  console.log('✅ Deployment confirmed!');

  console.log('\n🎉 Deployment Complete!');
  console.log('═'.repeat(50));
  console.log(`Contract Address: ${deployResponse.contract_address}`);
  console.log(`Class Hash: ${declareResponse.class_hash}`);
  console.log('═'.repeat(50));

  // Update .env file
  const envPath = path.join(__dirname, '../.env');
  let envContent = fs.readFileSync(envPath, 'utf-8');
  envContent = envContent.replace(
    /VERIFIER_CONTRACT_ADDRESS=.*/,
    `VERIFIER_CONTRACT_ADDRESS=${deployResponse.contract_address}`
  );
  fs.writeFileSync(envPath, envContent);
  console.log('\n✅ Updated .env with new contract address');
}

main().catch((error) => {
  console.error('❌ Deployment failed:', error);
  process.exit(1);
});
