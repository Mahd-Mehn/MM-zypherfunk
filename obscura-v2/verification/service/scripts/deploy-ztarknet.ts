#!/usr/bin/env tsx
/**
 * Deploy Obscura Verifier Contract to Ztarknet
 * 
 * Usage: npx tsx scripts/deploy-ztarknet.ts
 */

import { Account, RpcProvider, json, CallData, hash, stark } from 'starknet';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import 'dotenv/config';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Ztarknet configuration
const ZTARKNET_RPC = 'https://ztarknet-madara.d.karnot.xyz';
const FEE_TOKEN_ADDRESS = '0x1ad102b4c4b3e40a51b6fb8a446275d600555bd63a95cdceed3e5cef8a6bc1d';

// UDC (Universal Deployer Contract) on Ztarknet
const UDC_ADDRESS = '0x041a78e741e5af2fec34b695679bc6891742439f7afb8484ecd7766661ad02bf';

async function main() {
  console.log('🚀 Deploying Obscura Verifier to Ztarknet...\n');

  // Load Ztarknet credentials from environment or use default account file
  const accountAddress = process.env.ZTARKNET_ACCOUNT_ADDRESS;
  const privateKey = process.env.ZTARKNET_PRIVATE_KEY;

  if (!accountAddress || !privateKey) {
    console.log('⚠️  ZTARKNET_ACCOUNT_ADDRESS and ZTARKNET_PRIVATE_KEY not set in .env');
    console.log('   Please add your Ztarknet account credentials to .env file:');
    console.log('');
    console.log('   ZTARKNET_ACCOUNT_ADDRESS=0x...');
    console.log('   ZTARKNET_PRIVATE_KEY=0x...');
    console.log('');
    console.log('   To create an account, run from quickstart folder:');
    console.log('   make account-create');
    console.log('   Then get tokens from: https://faucet.ztarknet.cash/');
    console.log('   Then deploy account: make account-deploy');
    process.exit(1);
  }

  // Initialize provider and account
  const provider = new RpcProvider({ nodeUrl: ZTARKNET_RPC });
  
  // starknet.js v8 uses object-based constructor
  const account = new Account({
    provider: provider,
    address: accountAddress,
    signer: privateKey,
    cairoVersion: '1',
  });

  console.log(`📡 RPC: ${ZTARKNET_RPC}`);
  console.log(`👤 Account: ${accountAddress}`);

  // Check balance
  try {
    const balanceResult = await provider.callContract({
      contractAddress: FEE_TOKEN_ADDRESS,
      entrypoint: 'balanceOf',
      calldata: [accountAddress],
    });
    const balance = BigInt(balanceResult[0]);
    console.log(`💰 Balance: ${Number(balance) / 1e18} STRK\n`);
    
    if (balance === 0n) {
      console.log('❌ Account has no funds. Please get tokens from:');
      console.log('   https://faucet.ztarknet.cash/');
      process.exit(1);
    }
  } catch (error: any) {
    console.log(`⚠️  Could not check balance: ${error.message}`);
  }

  // Load compiled contract
  const contractPath = path.join(__dirname, '../../cairo/target/dev');
  const sierraPath = path.join(contractPath, 'obscura_verification_ObscuraVerifier.contract_class.json');
  const casmPath = path.join(contractPath, 'obscura_verification_ObscuraVerifier.compiled_contract_class.json');

  if (!fs.existsSync(sierraPath) || !fs.existsSync(casmPath)) {
    console.log('❌ Contract not compiled. Run: cd ../cairo && scarb build');
    process.exit(1);
  }

  const sierra = json.parse(fs.readFileSync(sierraPath, 'utf-8'));
  const casm = json.parse(fs.readFileSync(casmPath, 'utf-8'));

  console.log('📝 Contract files loaded');

  // Step 1: Declare the contract
  console.log('\n═══════════════════════════════════════════════════');
  console.log('Step 1: Declaring contract...');
  console.log('═══════════════════════════════════════════════════\n');

  try {
    const declareResponse = await account.declare({
      contract: sierra,
      casm: casm,
    });

    console.log(`📝 Declare Tx: ${declareResponse.transaction_hash}`);
    console.log(`📦 Class Hash: ${declareResponse.class_hash}`);

    // Wait for declaration
    console.log('⏳ Waiting for declaration confirmation...');
    await provider.waitForTransaction(declareResponse.transaction_hash);
    console.log('✅ Contract declared!\n');

    // Step 2: Deploy the contract using UDC
    console.log('═══════════════════════════════════════════════════');
    console.log('Step 2: Deploying contract via UDC...');
    console.log('═══════════════════════════════════════════════════\n');

    // Constructor calldata (owner address)
    const constructorCalldata = CallData.compile({
      owner: accountAddress,
    });

    // Use UDC to deploy
    const deployResponse = await account.execute([{
      contractAddress: UDC_ADDRESS,
      entrypoint: 'deployContract',
      calldata: [
        declareResponse.class_hash,  // classHash
        stark.randomAddress(),        // salt (random for unique address)
        '0',                          // unique (0 = false)
        constructorCalldata.length.toString(),  // constructor calldata length
        ...constructorCalldata,       // constructor calldata
      ],
    }]);

    console.log(`📝 Deploy Tx: ${deployResponse.transaction_hash}`);
    console.log('⏳ Waiting for deployment confirmation...');
    
    const receipt = await provider.waitForTransaction(deployResponse.transaction_hash);
    
    // Parse deployed address from events
    let deployedAddress = '';
    if (receipt.events) {
      for (const event of receipt.events) {
        // UDC emits ContractDeployed event with address
        if (event.keys && event.keys.length > 0) {
          // The deployed address is typically in event data
          if (event.data && event.data.length > 0) {
            deployedAddress = event.data[0];
            break;
          }
        }
      }
    }

    if (!deployedAddress) {
      console.log('⚠️  Could not parse deployed address from events');
      console.log('   Check the explorer for the deployed contract address');
      console.log(`   https://explorer-zstarknet.d.karnot.xyz/tx/${deployResponse.transaction_hash}`);
    } else {
      console.log(`\n✅ Contract deployed at: ${deployedAddress}`);
    }

    console.log('\n═══════════════════════════════════════════════════');
    console.log('📋 Deployment Summary');
    console.log('═══════════════════════════════════════════════════');
    console.log(`   Network: Ztarknet Testnet`);
    console.log(`   Class Hash: ${declareResponse.class_hash}`);
    console.log(`   Contract Address: ${deployedAddress || 'Check explorer'}`);
    console.log(`   Owner: ${accountAddress}`);
    console.log('');
    console.log('📝 Add to .env:');
    console.log(`   ZTARKNET_VERIFIER_CONTRACT_ADDRESS=${deployedAddress || '<address>'}`);
    console.log('');
    console.log('🔍 Explorer:');
    console.log(`   https://explorer-zstarknet.d.karnot.xyz/tx/${deployResponse.transaction_hash}`);

  } catch (error: any) {
    if (error.message?.includes('already declared')) {
      console.log('ℹ️  Contract already declared');
      // Extract class hash and continue with deployment
    } else {
      console.log(`❌ Deployment failed: ${error.message}`);
      throw error;
    }
  }
}

main().catch((error) => {
  console.error('❌ Deployment failed:', error);
  process.exit(1);
});
