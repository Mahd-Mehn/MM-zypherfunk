#!/usr/bin/env tsx
/**
 * Check Starknet Account Balance
 * 
 * Usage: npx tsx scripts/check-balance.ts
 */

import { RpcProvider } from 'starknet';
import 'dotenv/config';

async function main() {
  console.log('💰 Checking Starknet Account Balance...\n');

  const rpcUrl = process.env.STARKNET_RPC_URL;
  const accountAddress = process.env.STARKNET_ACCOUNT_ADDRESS;

  if (!rpcUrl || !accountAddress) {
    throw new Error('Missing environment variables.');
  }

  const provider = new RpcProvider({ nodeUrl: rpcUrl });

  console.log(`📡 RPC: ${rpcUrl}`);
  console.log(`👤 Account: ${accountAddress}\n`);

  // ETH token on Sepolia
  const ETH_ADDRESS = '0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7';
  // STRK token on Sepolia
  const STRK_ADDRESS = '0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d';

  try {
    // Get ETH balance
    const ethBalance = await provider.callContract({
      contractAddress: ETH_ADDRESS,
      entrypoint: 'balanceOf',
      calldata: [accountAddress],
    });
    
    const ethWei = BigInt(ethBalance[0]);
    const ethFormatted = Number(ethWei) / 1e18;
    console.log(`💎 ETH Balance: ${ethFormatted.toFixed(6)} ETH`);

    // Get STRK balance
    const strkBalance = await provider.callContract({
      contractAddress: STRK_ADDRESS,
      entrypoint: 'balanceOf',
      calldata: [accountAddress],
    });
    
    const strkWei = BigInt(strkBalance[0]);
    const strkFormatted = Number(strkWei) / 1e18;
    console.log(`🪙 STRK Balance: ${strkFormatted.toFixed(6)} STRK`);

    // Check if we have enough for transactions
    if (ethFormatted < 0.001 && strkFormatted < 0.1) {
      console.log('\n⚠️  Warning: Low balance. You may need testnet tokens.');
      console.log('   Get Sepolia ETH from: https://starknet-faucet.vercel.app/');
    } else {
      console.log('\n✅ Account has sufficient balance for transactions.');
    }

    // Get nonce
    const nonce = await provider.getNonceForAddress(accountAddress);
    console.log(`\n📝 Current Nonce: ${nonce}`);

  } catch (error: any) {
    console.log(`❌ Error checking balance: ${error.message}`);
  }
}

main().catch(console.error);
