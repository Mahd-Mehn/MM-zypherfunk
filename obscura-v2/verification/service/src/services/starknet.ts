/**
 * Starknet Client for Submitting Verified Reports
 * Updated for starknet.js v8 API
 */

import { Account, RpcProvider } from 'starknet';
import { config } from '../config/index.ts';
import { logger } from '../utils/logger.ts';

/**
 * Trading report structure for submission
 */
export interface TradingReportInput {
  trader: string;
  timestampStart: bigint;
  timestampEnd: bigint;
  tradeCount: number;
  symbolCount: number;
  reportHash: bigint;
  commitment: bigint;
}

/**
 * Submission result
 */
export interface SubmissionResult {
  reportId: bigint;
  transactionHash: string;
  blockNumber: number;
}

/**
 * Starknet client for interacting with the verifier contract
 * Updated for starknet.js v8 API
 */
export class StarknetClient {
  private provider: RpcProvider;
  private account: Account | null = null;

  constructor() {
    this.provider = new RpcProvider({ nodeUrl: config.starknet.rpcUrl });
  }

  /**
   * Initialize the account
   */
  async initialize(): Promise<void> {
    if (!config.starknet.accountAddress || !config.starknet.privateKey) {
      logger.warn('Starknet credentials not configured - running in read-only mode');
      return;
    }

    // starknet.js v8 uses object-based constructor
    this.account = new Account({
      provider: this.provider,
      address: config.starknet.accountAddress,
      signer: config.starknet.privateKey,
      cairoVersion: '1',
    });

    logger.info({ address: config.starknet.accountAddress }, 'Starknet account initialized');
  }

  /**
   * Get the provider (for read operations)
   */
  getProvider(): RpcProvider {
    return this.provider;
  }

  /**
   * Submit a verified trading report to the contract
   */
  async submitReport(
    report: TradingReportInput,
    totalPnlValue: bigint,
    totalPnlNegative: boolean
  ): Promise<SubmissionResult> {
    if (!this.account) {
      throw new Error('Starknet account not initialized');
    }

    if (!config.starknet.verifierContractAddress) {
      throw new Error('Verifier contract address not configured');
    }

    logger.info({ report }, 'Submitting report to Starknet');

    // Prepare calldata - flatten struct for raw call
    const calldata = [
      report.trader,                         // trader (ContractAddress)
      report.timestampStart.toString(),      // timestamp_start (u64)
      report.timestampEnd.toString(),        // timestamp_end (u64)
      report.tradeCount.toString(),          // trade_count (u32)
      report.symbolCount.toString(),         // symbol_count (u32)
      '0x' + report.reportHash.toString(16), // report_hash (felt252)
      '0x' + report.commitment.toString(16), // commitment (felt252)
      totalPnlValue.toString(),              // total_pnl_value (u128)
      totalPnlNegative ? '1' : '0',          // total_pnl_negative (bool)
    ];

    // Execute transaction
    const { transaction_hash } = await this.account.execute([{
      contractAddress: config.starknet.verifierContractAddress,
      entrypoint: 'submit_report',
      calldata,
    }]);

    logger.info({ transaction_hash }, 'Transaction submitted');

    // Wait for confirmation
    await this.provider.waitForTransaction(transaction_hash);

    // Fetch block number
    const blockNumber = await this.provider.getBlockNumber();

    // Get report count to determine report ID
    const reportCount = await this.getReportCount();

    return {
      reportId: reportCount,
      transactionHash: transaction_hash,
      blockNumber,
    };
  }

  /**
   * Check if a commitment has already been used
   */
  async isCommitmentUsed(commitment: bigint): Promise<boolean> {
    if (!config.starknet.verifierContractAddress) {
      throw new Error('Verifier contract address not configured');
    }

    const result = await this.provider.callContract({
      contractAddress: config.starknet.verifierContractAddress,
      entrypoint: 'is_commitment_used',
      calldata: ['0x' + commitment.toString(16)],
    });

    return result[0] === '0x1';
  }

  /**
   * Get report count
   */
  async getReportCount(): Promise<bigint> {
    if (!config.starknet.verifierContractAddress) {
      throw new Error('Verifier contract address not configured');
    }

    const result = await this.provider.callContract({
      contractAddress: config.starknet.verifierContractAddress,
      entrypoint: 'get_report_count',
      calldata: [],
    });

    // Result is u256 (low, high)
    const low = BigInt(result[0]);
    const high = BigInt(result[1]);
    return low + (high << 128n);
  }

  /**
   * Check if a trader is registered
   */
  async isTraderRegistered(traderAddress: string): Promise<boolean> {
    if (!config.starknet.verifierContractAddress) {
      throw new Error('Verifier contract address not configured');
    }

    const result = await this.provider.callContract({
      contractAddress: config.starknet.verifierContractAddress,
      entrypoint: 'is_registered',
      calldata: [traderAddress],
    });

    return result[0] === '0x1';
  }

  /**
   * Register a trader
   */
  async registerTrader(): Promise<string> {
    if (!this.account) {
      throw new Error('Starknet account not initialized');
    }

    if (!config.starknet.verifierContractAddress) {
      throw new Error('Verifier contract address not configured');
    }

    const { transaction_hash } = await this.account.execute([{
      contractAddress: config.starknet.verifierContractAddress,
      entrypoint: 'register_trader',
      calldata: [],
    }]);

    await this.provider.waitForTransaction(transaction_hash);
    return transaction_hash;
  }

  /**
   * Get trader stats
   */
  async getTraderStats(traderAddress: string): Promise<{
    totalReports: number;
    totalTrades: number;
    totalPnlValue: bigint;
    totalPnlNegative: boolean;
  }> {
    if (!config.starknet.verifierContractAddress) {
      throw new Error('Verifier contract address not configured');
    }

    try {
      const result = await this.provider.callContract({
        contractAddress: config.starknet.verifierContractAddress,
        entrypoint: 'get_trader_stats',
        calldata: [traderAddress],
      });

      // Parse TraderStats struct
      // total_reports (u32), total_trades (u32), total_pnl_value (u128), 
      // total_pnl_negative (bool), first_report_block (u64), last_report_block (u64)
      return {
        totalReports: parseInt(result[0], 16),
        totalTrades: parseInt(result[1], 16),
        totalPnlValue: BigInt(result[2]),
        totalPnlNegative: result[3] === '0x1',
      };
    } catch (error) {
      logger.warn({ error, traderAddress }, 'Failed to get trader stats');
      return {
        totalReports: 0,
        totalTrades: 0,
        totalPnlValue: 0n,
        totalPnlNegative: false,
      };
    }
  }
}

// Singleton instance
export const starknetClient = new StarknetClient();
