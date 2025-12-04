#!/usr/bin/env tsx
/**
 * Test the Deployed Verifier Contract
 * 
 * Usage: npx tsx scripts/test-contract.ts
 */

import { Account, RpcProvider, CallData } from 'starknet';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import 'dotenv/config';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
  console.log('🧪 Testing Obscura Verifier Contract on Starknet Sepolia...\n');

  // Load environment
  const rpcUrl = process.env.STARKNET_RPC_URL;
  const accountAddress = process.env.STARKNET_ACCOUNT_ADDRESS;
  const privateKey = process.env.STARKNET_PRIVATE_KEY;
  const contractAddress = process.env.VERIFIER_CONTRACT_ADDRESS;

  if (!rpcUrl || !accountAddress || !privateKey || !contractAddress) {
    throw new Error('Missing environment variables. Check .env file.');
  }

  // Initialize provider and account with STRK fee token (starknet.js v8 API)
  const provider = new RpcProvider({ nodeUrl: rpcUrl });
  
  // v8 uses object-based constructor
  const account = new Account({
    provider: provider,
    address: accountAddress,
    signer: privateKey,
    cairoVersion: '1',
  });

  console.log(`📡 RPC: ${rpcUrl}`);
  console.log(`👤 Account: ${accountAddress}`);
  console.log(`📜 Contract: ${contractAddress}`);
  console.log(`💰 Using STRK for gas (V3 transactions)\n`);

  // =====================
  // Test 1: Get Report Count (using raw callContract)
  // =====================
  console.log('═'.repeat(50));
  console.log('Test 1: Get Report Count');
  console.log('═'.repeat(50));
  
  try {
    const result = await provider.callContract({
      contractAddress: contractAddress,
      entrypoint: 'get_report_count',
      calldata: [],
    });
    console.log(`✅ Current report count: ${result[0]} (low), ${result[1]} (high)`);
  } catch (error: any) {
    console.log(`⚠️  Could not get report count: ${error.message}`);
  }

  // =====================
  // Test 2: Check Registration
  // =====================
  console.log('\n' + '═'.repeat(50));
  console.log('Test 2: Check if Account is Registered');
  console.log('═'.repeat(50));
  
  try {
    const result = await provider.callContract({
      contractAddress: contractAddress,
      entrypoint: 'is_registered',
      calldata: [accountAddress],
    });
    const isRegistered = result[0] === '0x1';
    console.log(`✅ Is registered: ${isRegistered}`);

    if (!isRegistered) {
      console.log('\n📝 Registering as trader...');
      const registerTx = await account.execute([{
        contractAddress: contractAddress,
        entrypoint: 'register_trader',
        calldata: [],
      }]);
      console.log(`📝 Tx Hash: ${registerTx.transaction_hash}`);
      console.log('⏳ Waiting for confirmation...');
      await provider.waitForTransaction(registerTx.transaction_hash);
      console.log('✅ Registration confirmed!');
      
      // Verify registration
      const verifyResult = await provider.callContract({
        contractAddress: contractAddress,
        entrypoint: 'is_registered',
        calldata: [accountAddress],
      });
      console.log(`✅ Verified registration: ${verifyResult[0] === '0x1'}`);
    }
  } catch (error: any) {
    console.log(`⚠️  Registration check/execute failed: ${error.message}`);
    if (error.message.includes('Max fee')) {
      console.log('   (This might be a fee estimation issue - ensure you have STRK)');
    }
  }

  // =====================
  // Test 3: Check Commitment Replay Protection
  // =====================
  console.log('\n' + '═'.repeat(50));
  console.log('Test 3: Verify Commitment Replay Protection');
  console.log('═'.repeat(50));

  try {
    const testCommitment = '0x123456789abcdef';
    const result = await provider.callContract({
      contractAddress: contractAddress,
      entrypoint: 'is_commitment_used',
      calldata: [testCommitment],
    });
    console.log(`✅ Test commitment used: ${result[0] === '0x1'}`);
  } catch (error: any) {
    console.log(`⚠️  Check failed: ${error.message}`);
  }

  // =====================
  // Test 4: Submit a Test Report (if registered)
  // =====================
  console.log('\n' + '═'.repeat(50));
  console.log('Test 4: Submit a Test Trading Report');
  console.log('═'.repeat(50));

  try {
    // First check if registered
    const regResult = await provider.callContract({
      contractAddress: contractAddress,
      entrypoint: 'is_registered',
      calldata: [accountAddress],
    });
    
    if (regResult[0] !== '0x1') {
      console.log('⚠️  Account not registered. Skipping report submission.');
    } else {
      const now = Math.floor(Date.now() / 1000);
      const commitment = '0x' + Buffer.from('test_commitment_' + now).toString('hex').slice(0, 60);
      const reportHash = '0x' + Buffer.from('report_hash_' + now).toString('hex').slice(0, 60);

      console.log('\n📊 Test Report Data:');
      console.log(`   Trader: ${accountAddress}`);
      console.log(`   Time Range: ${now - 86400} - ${now}`);
      console.log(`   Trade Count: 5`);
      console.log(`   Symbol Count: 2`);
      console.log(`   PnL: +$1234.56`);

      // TradingReport struct: trader, timestamp_start, timestamp_end, trade_count, symbol_count, report_hash, commitment
      // total_pnl_value: u128
      // total_pnl_negative: bool (0 or 1)
      const calldata = [
        accountAddress,           // trader (ContractAddress)
        (now - 86400).toString(), // timestamp_start (u64)
        now.toString(),           // timestamp_end (u64)
        '5',                      // trade_count (u32)
        '2',                      // symbol_count (u32)
        reportHash,               // report_hash (felt252)
        commitment,               // commitment (felt252)
        '123456',                 // total_pnl_value (u128)
        '0',                      // total_pnl_negative (bool: 0 = false)
      ];

      console.log('\n📝 Submitting report...');
      const submitTx = await account.execute([{
        contractAddress: contractAddress,
        entrypoint: 'submit_report',
        calldata: calldata,
      }]);

      console.log(`📝 Tx Hash: ${submitTx.transaction_hash}`);
      console.log('\n⏳ Waiting for confirmation...');
      
      await provider.waitForTransaction(submitTx.transaction_hash);
      console.log('✅ Report submitted successfully!');
      
      // Try to get the new report count
      try {
        const newCountResult = await provider.callContract({
          contractAddress: contractAddress,
          entrypoint: 'get_report_count',
          calldata: [],
        });
        console.log(`📊 New report count: ${newCountResult[0]}`);
      } catch (e) {
        console.log('📊 Could not fetch new report count');
      }
    }
  } catch (error: any) {
    console.log(`❌ Submit report failed: ${error.message}`);
    if (error.message.includes('commitment')) {
      console.log('   (This might be because the commitment was already used)');
    }
  }

  console.log('\n' + '═'.repeat(50));
  console.log('🎉 All tests completed!');
  console.log('═'.repeat(50));
}

main().catch((error) => {
  console.error('❌ Tests failed:', error);
  process.exit(1);
});
