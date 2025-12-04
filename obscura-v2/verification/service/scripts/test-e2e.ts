#!/usr/bin/env tsx
/**
 * Test End-to-End Flow: Backend API -> Contract
 * 
 * Usage: npx tsx scripts/test-e2e.ts
 */

import 'dotenv/config';

const API_URL = process.env.BACKEND_API_URL || 'http://localhost:3001';

interface Trade {
  trade_id: string;
  trader_user_id: string;
  symbol: string;
  exchange: string;
  side: 'buy' | 'sell';
  order_type: string;
  quantity: string;
  price: string;
  fee: string;
  timestamp: number;
}

interface GenerateProofRequest {
  trades: Trade[];
  trader_id: string;
  timestamp_start: number;
  timestamp_end: number;
}

interface SubmitProofRequest {
  trader_id: string;
  trader_address: string;
  timestamp_start: number;
  timestamp_end: number;
  trade_count: number;
  symbol_count: number;
  report_hash: string;
  commitment: string;
  total_pnl_value: string;
  total_pnl_negative: boolean;
}

async function testHealthCheck() {
  console.log('═'.repeat(50));
  console.log('Test 1: Health Check');
  console.log('═'.repeat(50));

  try {
    const response = await fetch(`${API_URL}/api/v1/health`);
    const data = await response.json();
    console.log('✅ Health check passed:', data);
    return true;
  } catch (error: any) {
    console.log(`❌ Health check failed: ${error.message}`);
    console.log('   Make sure the verification service is running: npm run dev');
    return false;
  }
}

async function testReadinessCheck() {
  console.log('\n' + '═'.repeat(50));
  console.log('Test 2: Readiness Check');
  console.log('═'.repeat(50));

  try {
    const response = await fetch(`${API_URL}/api/v1/health/ready`);
    const data = await response.json();
    console.log('✅ Readiness check:', data);
    return data.status === 'ready';
  } catch (error: any) {
    console.log(`⚠️  Readiness check failed: ${error.message}`);
    return false;
  }
}

async function testProofGeneration() {
  console.log('\n' + '═'.repeat(50));
  console.log('Test 3: Generate Proof from Trade Data');
  console.log('═'.repeat(50));

  const now = Math.floor(Date.now() / 1000);
  const traderAddress = process.env.STARKNET_ACCOUNT_ADDRESS || '0x0442b94543f5f4a79161c0c661741407f931492e01a067fdd7337d2f135cd29d';

  const request: GenerateProofRequest = {
    trader_id: 'test-trader-001',
    timestamp_start: now - 86400, // 24 hours ago
    timestamp_end: now,
    trades: [
      {
        trade_id: 'trade-001',
        trader_user_id: 'test-trader-001',
        symbol: 'BTC/USDT',
        exchange: 'binance',
        side: 'buy',
        order_type: 'market',
        quantity: '0.1',
        price: '45000',
        timestamp: now - 80000,
        fee: '4.5',
      },
      {
        trade_id: 'trade-002',
        trader_user_id: 'test-trader-001',
        symbol: 'BTC/USDT',
        exchange: 'binance',
        side: 'sell',
        order_type: 'market',
        quantity: '0.1',
        price: '46500',
        timestamp: now - 40000,
        fee: '4.65',
      },
      {
        trade_id: 'trade-003',
        trader_user_id: 'test-trader-001',
        symbol: 'ETH/USDT',
        exchange: 'binance',
        side: 'buy',
        order_type: 'limit',
        quantity: '1.0',
        price: '2500',
        timestamp: now - 60000,
        fee: '2.5',
      },
      {
        trade_id: 'trade-004',
        trader_user_id: 'test-trader-001',
        symbol: 'ETH/USDT',
        exchange: 'binance',
        side: 'sell',
        order_type: 'limit',
        quantity: '1.0',
        price: '2650',
        timestamp: now - 20000,
        fee: '2.65',
      },
    ],
  };

  console.log('\n📊 Test Trade Data:');
  console.log(`   Trader: ${request.trader_id}`);
  console.log(`   Trades: ${request.trades.length}`);
  console.log('   Expected PnL:');
  console.log('     BTC: (46500 - 45000) * 0.1 = $150');
  console.log('     ETH: (2650 - 2500) * 1.0 = $150');
  console.log('     Total: ~$300 (minus fees ~$14.30)');

  try {
    console.log('\n📝 Generating proof...');
    const response = await fetch(`${API_URL}/api/v1/proof/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    const data = await response.json();

    if (data.success) {
      console.log('\n✅ Proof generated!');
      console.log(`   Commitment: ${data.data.commitment}`);
      console.log(`   Report Hash: ${data.data.report_hash}`);
      console.log(`   Trade Count: ${data.data.trade_count}`);
      console.log(`   Symbol Count: ${data.data.symbol_count}`);
      console.log(`   PnL: ${data.data.total_pnl.is_negative ? '-' : '+'}$${parseInt(data.data.total_pnl.value) / 100}`);
      
      // Return data for next test
      return data.data;
    } else {
      console.log(`❌ Proof generation failed: ${data.error}`);
      return null;
    }
  } catch (error: any) {
    console.log(`❌ Request failed: ${error.message}`);
    return null;
  }
}

async function testSubmitProof(proofData: any) {
  console.log('\n' + '═'.repeat(50));
  console.log('Test 4: Submit Proof to Starknet');
  console.log('═'.repeat(50));

  if (!proofData) {
    console.log('⚠️  Skipping - no proof data from previous test');
    return false;
  }

  const now = Math.floor(Date.now() / 1000);
  const traderAddress = process.env.STARKNET_ACCOUNT_ADDRESS || '0x0442b94543f5f4a79161c0c661741407f931492e01a067fdd7337d2f135cd29d';

  const request: SubmitProofRequest = {
    trader_id: 'test-trader-001',
    trader_address: traderAddress,
    timestamp_start: now - 86400,
    timestamp_end: now,
    trade_count: proofData.trade_count,
    symbol_count: proofData.symbol_count,
    report_hash: proofData.report_hash,
    commitment: proofData.commitment,
    total_pnl_value: proofData.total_pnl.value,
    total_pnl_negative: proofData.total_pnl.is_negative,
  };

  try {
    console.log('\n📝 Submitting proof to Starknet...');
    const response = await fetch(`${API_URL}/api/v1/proof/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    const data = await response.json();

    if (data.success) {
      console.log('\n✅ Proof submitted to Starknet!');
      console.log(`   Report ID: ${data.data.report_id}`);
      console.log(`   Tx Hash: ${data.data.transaction_hash}`);
      console.log(`   Block: ${data.data.block_number}`);
      return true;
    } else {
      console.log(`❌ Submission failed: ${data.error}`);
      return false;
    }
  } catch (error: any) {
    console.log(`❌ Request failed: ${error.message}`);
    return false;
  }
}

async function testGetTraderStats() {
  console.log('\n' + '═'.repeat(50));
  console.log('Test 5: Get Trader Stats');
  console.log('═'.repeat(50));

  const traderAddress = process.env.STARKNET_ACCOUNT_ADDRESS || '0x0442b94543f5f4a79161c0c661741407f931492e01a067fdd7337d2f135cd29d';

  try {
    const response = await fetch(`${API_URL}/api/v1/proof/trader/${traderAddress}/stats`);
    const data = await response.json();

    if (data.success) {
      console.log('✅ Trader stats retrieved:');
      console.log(`   Total Reports: ${data.data.total_reports}`);
      console.log(`   Total Trades: ${data.data.total_trades}`);
      console.log(`   Total PnL: ${data.data.total_pnl.is_negative ? '-' : '+'}$${parseInt(data.data.total_pnl.value) / 100}`);
      return true;
    } else {
      console.log(`⚠️  Stats query failed: ${data.error}`);
      return false;
    }
  } catch (error: any) {
    console.log(`⚠️  Stats query failed: ${error.message}`);
    return false;
  }
}

async function main() {
  console.log('🧪 End-to-End Testing for Obscura Verification Service\n');
  console.log(`📡 API URL: ${API_URL}`);
  console.log(`🔗 Contract: ${process.env.VERIFIER_CONTRACT_ADDRESS || 'not set'}\n`);

  const results: boolean[] = [];

  // Test 1: Health check
  results.push(await testHealthCheck());
  
  if (!results[0]) {
    console.log('\n⚠️  Service not running. Start with: npm run dev');
    process.exit(1);
  }

  // Test 2: Readiness
  results.push(await testReadinessCheck());

  // Test 3: Generate proof
  const proofData = await testProofGeneration();
  results.push(proofData !== null);

  // Test 4: Submit proof (only if we have proof data)
  if (proofData) {
    results.push(await testSubmitProof(proofData));
  } else {
    results.push(false);
  }

  // Test 5: Get stats
  results.push(await testGetTraderStats());

  console.log('\n' + '═'.repeat(50));
  console.log('📊 Test Summary');
  console.log('═'.repeat(50));
  console.log(`   Passed: ${results.filter(r => r).length}/${results.length}`);
  console.log(`   Failed: ${results.filter(r => !r).length}/${results.length}`);

  if (results.every(r => r)) {
    console.log('\n🎉 All tests passed!');
  } else {
    console.log('\n⚠️  Some tests failed. Check the output above.');
  }
}

main().catch((error) => {
  console.error('❌ E2E tests failed:', error);
  process.exit(1);
});
