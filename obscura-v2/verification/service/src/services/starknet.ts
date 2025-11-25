/**
 * Starknet Client for Submitting Verified Reports
 */

import { Account, Contract, RpcProvider, CallData, cairo } from 'starknet';
import { config } from '../config/index.ts';
import { logger } from '../utils/logger.ts';

// Verifier contract ABI (simplified - real ABI would be generated from Cairo build)
const VERIFIER_ABI = [
  {
    name: 'submit_report',
    type: 'function',
    inputs: [
      { name: 'report', type: 'TradingReport' },
      { name: 'total_pnl_value', type: 'u128' },
      { name: 'total_pnl_negative', type: 'bool' },
    ],
    outputs: [{ type: 'u256' }],
  },
  {
    name: 'get_report',
    type: 'function',
    inputs: [{ name: 'report_id', type: 'u256' }],
    outputs: [{ type: 'StoredReport' }],
    state_mutability: 'view',
  },
  {
    name: 'get_trader_reports',
    type: 'function',
    inputs: [{ name: 'trader', type: 'ContractAddress' }],
    outputs: [{ type: 'Array<u256>' }],
    state_mutability: 'view',
  },
  {
    name: 'get_report_count',
    type: 'function',
    inputs: [],
    outputs: [{ type: 'u256' }],
    state_mutability: 'view',
  },
  {
    name: 'is_commitment_used',
    type: 'function',
    inputs: [{ name: 'commitment', type: 'felt252' }],
    outputs: [{ type: 'bool' }],
    state_mutability: 'view',
  },
  {
    name: 'get_trader_stats',
    type: 'function',
    inputs: [{ name: 'trader', type: 'ContractAddress' }],
    outputs: [{ type: 'TraderStats' }],
    state_mutability: 'view',
  },
];

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
 */
export class StarknetClient {
  private provider: RpcProvider;
  private account: Account | null = null;
  private contract: Contract | null = null;

  constructor() {
    this.provider = new RpcProvider({ nodeUrl: config.starknet.rpcUrl });
  }

  /**
   * Initialize the account and contract
   */
  async initialize(): Promise<void> {
    if (!config.starknet.accountAddress || !config.starknet.privateKey) {
      logger.warn('Starknet credentials not configured - running in read-only mode');
      return;
    }

    this.account = new Account(
      this.provider,
      config.starknet.accountAddress,
      config.starknet.privateKey
    );

    if (config.starknet.verifierContractAddress) {
      this.contract = new Contract(
        VERIFIER_ABI,
        config.starknet.verifierContractAddress,
        this.account
      );
    }
  }

  /**
   * Submit a verified trading report to the contract
   */
  async submitReport(
    report: TradingReportInput,
    totalPnlValue: bigint,
    totalPnlNegative: boolean
  ): Promise<SubmissionResult> {
    if (!this.contract || !this.account) {
      throw new Error('Starknet client not initialized');
    }

    logger.info({ report }, 'Submitting report to Starknet');

    // Prepare calldata
    const calldata = CallData.compile({
      report: {
        trader: report.trader,
        timestamp_start: cairo.uint256(report.timestampStart),
        timestamp_end: cairo.uint256(report.timestampEnd),
        trade_count: report.tradeCount,
        symbol_count: report.symbolCount,
        report_hash: report.reportHash.toString(),
        commitment: report.commitment.toString(),
      },
      total_pnl_value: cairo.uint256(totalPnlValue),
      total_pnl_negative: totalPnlNegative,
    });

    // Execute transaction
    const { transaction_hash } = await this.account.execute({
      contractAddress: config.starknet.verifierContractAddress,
      entrypoint: 'submit_report',
      calldata,
    });

    logger.info({ transaction_hash }, 'Transaction submitted');

    // Wait for confirmation
    const receipt = await this.provider.waitForTransaction(transaction_hash);

    // Extract report ID from events (simplified)
    const reportId = 0n; // Would parse from receipt.events

    // Fetch block number explicitly (receipt may not expose block_number)
    const blockNumber = await this.provider.getBlockNumber();

    return {
      reportId,
      transactionHash: transaction_hash,
      blockNumber,
    };
  }

  /**
   * Check if a commitment has already been used
   */
  async isCommitmentUsed(commitment: bigint): Promise<boolean> {
    if (!this.contract) {
      throw new Error('Contract not initialized');
    }

    const result = await this.contract.call('is_commitment_used', [commitment.toString()]);
    return Boolean(result);
  }

  /**
   * Get report count
   */
  async getReportCount(): Promise<bigint> {
    if (!this.contract) {
      throw new Error('Contract not initialized');
    }

    const result = await this.contract.call('get_report_count', []);
    return BigInt(result.toString());
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
    if (!this.contract) {
      throw new Error('Contract not initialized');
    }

    const result = await this.contract.call('get_trader_stats', [traderAddress]);
    
    // Parse result (structure depends on actual ABI)
    return {
      totalReports: 0,
      totalTrades: 0,
      totalPnlValue: 0n,
      totalPnlNegative: false,
    };
  }
}

// Singleton instance
export const starknetClient = new StarknetClient();
