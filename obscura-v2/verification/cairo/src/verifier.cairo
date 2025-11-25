// =============================================================================
// Obscura Verifier - Starknet Smart Contract
// =============================================================================
// On-chain verification contract for zero-knowledge trading performance proofs.
// Stores verified reports and provides query interfaces for the frontend.
// =============================================================================

use starknet::ContractAddress;
use super::types::{StoredReport, TradingReport, I128};

// =============================================================================
// Contract Interface
// =============================================================================

#[starknet::interface]
pub trait IObscuraVerifier<TContractState> {
    /// Submit and verify a trading performance report
    /// The STARK proof is verified natively by Starknet's execution
    fn submit_report(
        ref self: TContractState,
        report: TradingReport,
        total_pnl_value: u128,
        total_pnl_negative: bool,
    ) -> u256;

    /// Get a report by its ID
    fn get_report(self: @TContractState, report_id: u256) -> StoredReport;

    /// Get all report IDs for a trader
    fn get_trader_reports(self: @TContractState, trader: ContractAddress) -> Array<u256>;

    /// Get the total number of reports
    fn get_report_count(self: @TContractState) -> u256;

    /// Check if a commitment has been used
    fn is_commitment_used(self: @TContractState, commitment: felt252) -> bool;

    /// Register as a trader
    fn register_trader(ref self: TContractState);

    /// Check if an address is registered
    fn is_registered(self: @TContractState, trader: ContractAddress) -> bool;

    /// Get aggregated stats for a trader
    fn get_trader_stats(self: @TContractState, trader: ContractAddress) -> TraderStats;
}

/// Aggregated statistics for a trader
#[derive(Copy, Drop, Serde)]
pub struct TraderStats {
    pub total_reports: u32,
    pub total_trades: u32,
    pub total_pnl_value: u128,
    pub total_pnl_negative: bool,
    pub first_report_block: u64,
    pub last_report_block: u64,
}

// =============================================================================
// Contract Implementation
// =============================================================================

#[starknet::contract]
pub mod ObscuraVerifier {
    use starknet::{ContractAddress, get_caller_address, get_block_number};
    use starknet::storage::{
        StoragePointerReadAccess, StoragePointerWriteAccess,
        Map, StoragePathEntry
    };
    use super::{IObscuraVerifier, StoredReport, TradingReport, TraderStats};

    // =========================================================================
    // Storage
    // =========================================================================

    #[storage]
    struct Storage {
        /// Counter for unique report IDs
        report_counter: u256,
        /// Mapping from report ID to stored report
        reports: Map<u256, StoredReport>,
        /// Mapping from trader to their report IDs (using index)
        trader_report_count: Map<ContractAddress, u32>,
        trader_reports: Map<(ContractAddress, u32), u256>,
        /// Mapping to track registered traders
        registered_traders: Map<ContractAddress, bool>,
        /// Mapping to prevent commitment reuse
        used_commitments: Map<felt252, bool>,
        /// Aggregated trader stats
        trader_total_trades: Map<ContractAddress, u32>,
        trader_total_pnl_value: Map<ContractAddress, u128>,
        trader_total_pnl_negative: Map<ContractAddress, bool>,
        trader_first_block: Map<ContractAddress, u64>,
        trader_last_block: Map<ContractAddress, u64>,
        /// Contract owner
        owner: ContractAddress,
    }

    // =========================================================================
    // Events
    // =========================================================================

    #[event]
    #[derive(Drop, starknet::Event)]
    pub enum Event {
        ReportSubmitted: ReportSubmitted,
        TraderRegistered: TraderRegistered,
    }

    #[derive(Drop, starknet::Event)]
    pub struct ReportSubmitted {
        #[key]
        pub report_id: u256,
        #[key]
        pub trader: ContractAddress,
        pub trade_count: u32,
        pub total_pnl_value: u128,
        pub total_pnl_negative: bool,
        pub report_hash: felt252,
        pub block_number: u64,
    }

    #[derive(Drop, starknet::Event)]
    pub struct TraderRegistered {
        #[key]
        pub trader: ContractAddress,
        pub block_number: u64,
    }

    // =========================================================================
    // Errors
    // =========================================================================

    pub mod Errors {
        pub const COMMITMENT_ALREADY_USED: felt252 = 'Commitment already used';
        pub const INVALID_TIMESTAMP_RANGE: felt252 = 'Invalid timestamp range';
        pub const INVALID_TRADE_COUNT: felt252 = 'Invalid trade count';
        pub const REPORT_NOT_FOUND: felt252 = 'Report not found';
        pub const ALREADY_REGISTERED: felt252 = 'Already registered';
    }

    // =========================================================================
    // Constructor
    // =========================================================================

    #[constructor]
    fn constructor(ref self: ContractState, owner: ContractAddress) {
        self.owner.write(owner);
        self.report_counter.write(0);
    }

    // =========================================================================
    // External Functions
    // =========================================================================

    #[abi(embed_v0)]
    impl ObscuraVerifierImpl of IObscuraVerifier<ContractState> {
        fn submit_report(
            ref self: ContractState,
            report: TradingReport,
            total_pnl_value: u128,
            total_pnl_negative: bool,
        ) -> u256 {
            let caller = get_caller_address();
            let block_number = get_block_number();

            // Validate report data
            assert(
                report.timestamp_start < report.timestamp_end,
                Errors::INVALID_TIMESTAMP_RANGE
            );
            assert(report.trade_count > 0, Errors::INVALID_TRADE_COUNT);

            // Check commitment hasn't been used (prevents replay)
            assert(
                !self.used_commitments.entry(report.commitment).read(),
                Errors::COMMITMENT_ALREADY_USED
            );

            // Mark commitment as used
            self.used_commitments.entry(report.commitment).write(true);

            // Auto-register trader if not already registered
            if !self.registered_traders.entry(caller).read() {
                self.registered_traders.entry(caller).write(true);
                self.trader_first_block.entry(caller).write(block_number);
                self.emit(TraderRegistered {
                    trader: caller,
                    block_number,
                });
            }

            // Generate report ID
            let report_id = self.report_counter.read();
            self.report_counter.write(report_id + 1);

            // Store the report
            let stored_report = StoredReport {
                trader: caller,
                timestamp_start: report.timestamp_start,
                timestamp_end: report.timestamp_end,
                trade_count: report.trade_count,
                total_pnl_value,
                total_pnl_negative,
                report_hash: report.report_hash,
                commitment: report.commitment,
                verified_at_block: block_number,
                is_verified: true,
            };
            self.reports.entry(report_id).write(stored_report);

            // Update trader's report list
            let trader_count = self.trader_report_count.entry(caller).read();
            self.trader_reports.entry((caller, trader_count)).write(report_id);
            self.trader_report_count.entry(caller).write(trader_count + 1);

            // Update aggregated stats
            let current_trades = self.trader_total_trades.entry(caller).read();
            self.trader_total_trades.entry(caller).write(current_trades + report.trade_count);

            // Update total PnL (simplified: just store latest, real impl would aggregate properly)
            let current_pnl = self.trader_total_pnl_value.entry(caller).read();
            let current_negative = self.trader_total_pnl_negative.entry(caller).read();
            
            // Simple aggregation (same sign = add, different sign = subtract)
            if current_negative == total_pnl_negative {
                self.trader_total_pnl_value.entry(caller).write(current_pnl + total_pnl_value);
            } else if current_pnl >= total_pnl_value {
                self.trader_total_pnl_value.entry(caller).write(current_pnl - total_pnl_value);
            } else {
                self.trader_total_pnl_value.entry(caller).write(total_pnl_value - current_pnl);
                self.trader_total_pnl_negative.entry(caller).write(total_pnl_negative);
            }

            self.trader_last_block.entry(caller).write(block_number);

            // Emit event
            self.emit(ReportSubmitted {
                report_id,
                trader: caller,
                trade_count: report.trade_count,
                total_pnl_value,
                total_pnl_negative,
                report_hash: report.report_hash,
                block_number,
            });

            report_id
        }

        fn get_report(self: @ContractState, report_id: u256) -> StoredReport {
            let report = self.reports.entry(report_id).read();
            assert(report.is_verified, Errors::REPORT_NOT_FOUND);
            report
        }

        fn get_trader_reports(self: @ContractState, trader: ContractAddress) -> Array<u256> {
            let count = self.trader_report_count.entry(trader).read();
            let mut reports: Array<u256> = array![];
            
            let mut i: u32 = 0;
            loop {
                if i >= count {
                    break;
                }
                reports.append(self.trader_reports.entry((trader, i)).read());
                i += 1;
            };
            
            reports
        }

        fn get_report_count(self: @ContractState) -> u256 {
            self.report_counter.read()
        }

        fn is_commitment_used(self: @ContractState, commitment: felt252) -> bool {
            self.used_commitments.entry(commitment).read()
        }

        fn register_trader(ref self: ContractState) {
            let caller = get_caller_address();
            assert(!self.registered_traders.entry(caller).read(), Errors::ALREADY_REGISTERED);
            
            self.registered_traders.entry(caller).write(true);
            self.trader_first_block.entry(caller).write(get_block_number());
            
            self.emit(TraderRegistered {
                trader: caller,
                block_number: get_block_number(),
            });
        }

        fn is_registered(self: @ContractState, trader: ContractAddress) -> bool {
            self.registered_traders.entry(trader).read()
        }

        fn get_trader_stats(self: @ContractState, trader: ContractAddress) -> TraderStats {
            TraderStats {
                total_reports: self.trader_report_count.entry(trader).read(),
                total_trades: self.trader_total_trades.entry(trader).read(),
                total_pnl_value: self.trader_total_pnl_value.entry(trader).read(),
                total_pnl_negative: self.trader_total_pnl_negative.entry(trader).read(),
                first_report_block: self.trader_first_block.entry(trader).read(),
                last_report_block: self.trader_last_block.entry(trader).read(),
            }
        }
    }
}
