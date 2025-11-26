# Obscura V2 Workers

This directory contains the background workers that power the Obscura V2 platform.

## Workers

### 1. Copy Trading Worker (`copy_trader.py`)
- **Role**: Consumer
- **Input**: Listens to `queue:copy_trade` Redis channel.
- **Action**: Executes trades for followers of a leader.
- **Logic**:
    - Receives trade signal (Leader ID, Symbol, Side, Amount).
    - Fetches active followers for that leader.
    - Retrieves follower exchange credentials (decrypted).
    - Executes the trade on the follower's exchange account using `OrderExecutionService`.

### 2. Proof Generation Worker (`proof_worker.py`)
- **Role**: Consumer
- **Input**: Listens to `queue:proof_generation` Redis channel.
- **Action**: Verifies trade performance and generates ZK proofs.
- **Logic**:
    - Receives closed trade data (Entry, Exit, Amount, PnL).
    - Verifies PnL calculation using `AnalyticsService`.
    - Generates a ZK Proof (currently mocked) asserting the ROI without revealing trade details.
    - Updates the Trade record in the database with the Proof ID.

## Running the Workers

Ensure your virtual environment is active and dependencies are installed.

```bash
# Run Copy Trader
python -m backend.workers.copy_trader

# Run Proof Worker
python -m backend.workers.proof_worker
```

## Architecture

The system uses a Producer-Consumer architecture via Redis Pub/Sub:
- **Producer**: `RealTimeExchangeService` (in `backend/shared/services`) detects trades and publishes messages.
- **Consumers**: These workers process the messages asynchronously, ensuring the main API remains responsive.
