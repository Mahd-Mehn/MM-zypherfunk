"""
Uniswap DEX Connector
Supports Uniswap V2/V3 on Ethereum and Base via Web3
"""

import os
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import json

try:
    from web3 import Web3
    from web3.middleware import geth_poa_middleware
    _HAVE_WEB3 = True
except ImportError:
    Web3 = None  # type: ignore
    _HAVE_WEB3 = False

from .base import (
    ExchangeConnector, TradeOrder, OrderResult, Balance,
    MarketData, OrderType, OrderSide, ExchangeType
)


class UniswapConnector(ExchangeConnector):
    """Uniswap DEX integration using Web3"""
    
    # Uniswap V2 Router ABI (essential methods only)
    ROUTER_ABI = [
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactTokensForTokens",
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactETHForTokens",
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "payable",
            "type": "function"
        }
    ]
    
    # Token addresses (Base Mainnet examples)
    TOKEN_ADDRESSES = {
        'WETH': '0x4200000000000000000000000000000000000006',  # Base WETH
        'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',  # Base USDC
        'DAI': '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb',   # Base DAI
    }
    
    def __init__(self, private_key: Optional[str] = None, rpc_url: Optional[str] = None):
        super().__init__()
        self.name = "Uniswap"
        self.exchange_type = ExchangeType.DEX
        self.w3 = None
        self.account = None
        self._initialized = False
        
        self.private_key = private_key or os.getenv("ETH_PRIVATE_KEY")
        self.rpc_url = rpc_url or os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
        self.router_address = os.getenv("UNISWAP_ROUTER", "0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24")  # Base Uniswap V2
        self.chain_id = int(os.getenv("CHAIN_ID", "8453"))  # Base mainnet
    
    async def initialize(self) -> bool:
        """Initialize Web3 connection"""
        if not _HAVE_WEB3:
            print("Warning: Web3.py not installed. Install with: pip install web3")
            return False
        
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            # Add POA middleware for some chains
            if self.chain_id in [8453, 84531]:  # Base
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if not self.w3.is_connected():
                print("Failed to connect to RPC")
                return False
            
            if self.private_key:
                self.account = self.w3.eth.account.from_key(self.private_key)
            
            self._initialized = True
            print(f"Uniswap connector initialized on chain {self.chain_id}")
            return True
            
        except Exception as e:
            print(f"Failed to initialize Uniswap connector: {e}")
            return False
    
    async def place_order(self, order: TradeOrder) -> OrderResult:
        """Place swap on Uniswap"""
        if not self._initialized:
            await self.initialize()
        
        if not self.w3 or not self.account:
            raise RuntimeError("Uniswap connector not initialized or no private key")
        
        try:
            # Parse symbol (e.g., "WETH/USDC")
            base, quote = order.symbol.split('/')
            
            # Get token addresses
            token_in = self.TOKEN_ADDRESSES.get(base if order.side == OrderSide.SELL else quote)
            token_out = self.TOKEN_ADDRESSES.get(quote if order.side == OrderSide.SELL else base)
            
            if not token_in or not token_out:
                raise ValueError(f"Token addresses not found for {order.symbol}")
            
            # Calculate amounts
            amount_in = int(order.amount * Decimal(10 ** 18))  # Assuming 18 decimals
            slippage = order.slippage or Decimal('0.01')  # 1% default
            amount_out_min = int(amount_in * (1 - float(slippage)))
            
            # Build swap path
            path = [token_in, token_out]
            
            # Get router contract
            router = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.router_address),
                abi=self.ROUTER_ABI
            )
            
            # Build transaction
            deadline = order.deadline or (int(datetime.now().timestamp()) + 1200)  # 20 min default
            
            tx = router.functions.swapExactTokensForTokens(
                amount_in,
                amount_out_min,
                path,
                self.account.address,
                deadline
            ).build_transaction({
                'from': self.account.address,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price if not order.gas_price else int(order.gas_price),
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'chainId': self.chain_id
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return OrderResult(
                order_id=tx_hash.hex(),
                exchange=self.name,
                exchange_type=self.exchange_type,
                symbol=order.symbol,
                side=order.side,
                amount=order.amount,
                filled_amount=order.amount,  # DEX swaps are atomic
                average_price=Decimal(str(amount_out_min / amount_in)),
                status='filled' if receipt['status'] == 1 else 'failed',
                tx_hash=tx_hash.hex(),
                timestamp=datetime.now(),
                fees={'gas_used': Decimal(str(receipt['gasUsed']))},
                metadata={'receipt': dict(receipt)}
            )
            
        except Exception as e:
            raise RuntimeError(f"Uniswap swap failed: {e}")
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cannot cancel DEX transactions once submitted"""
        return False
    
    async def get_order_status(self, order_id: str, symbol: str) -> OrderResult:
        """Get transaction status"""
        if not self.w3:
            raise RuntimeError("Not initialized")
        
        try:
            receipt = self.w3.eth.get_transaction_receipt(order_id)
            
            return OrderResult(
                order_id=order_id,
                exchange=self.name,
                exchange_type=self.exchange_type,
                symbol=symbol,
                side=OrderSide.BUY,  # Unknown from receipt
                amount=Decimal('0'),
                filled_amount=Decimal('0'),
                average_price=Decimal('0'),
                status='filled' if receipt['status'] == 1 else 'failed',
                tx_hash=order_id,
                timestamp=datetime.now(),
                metadata={'receipt': dict(receipt)}
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get transaction status: {e}")
    
    async def get_balance(self, asset: Optional[str] = None) -> List[Balance]:
        """Get wallet balance"""
        if not self.w3 or not self.account:
            raise RuntimeError("Not initialized")
        
        try:
            balances = []
            
            # ETH balance
            eth_balance = self.w3.eth.get_balance(self.account.address)
            balances.append(Balance(
                asset='ETH',
                free=Decimal(str(eth_balance / 10**18)),
                locked=Decimal('0'),
                total=Decimal(str(eth_balance / 10**18))
            ))
            
            # Filter by asset if specified
            if asset and asset != 'ETH':
                return []
            
            return balances if not asset or asset == 'ETH' else []
            
        except Exception as e:
            raise RuntimeError(f"Failed to get balance: {e}")
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get market data from Uniswap (requires price oracle or subgraph)"""
        # This would typically query Uniswap's price oracle or The Graph
        raise NotImplementedError("Market data fetching requires oracle integration")
    
    async def get_supported_pairs(self) -> List[str]:
        """Get supported pairs"""
        # Return common pairs
        return [
            'WETH/USDC',
            'WETH/DAI',
            'USDC/DAI'
        ]
    
    def format_symbol(self, base: str, quote: str) -> str:
        """Format symbol for Uniswap"""
        return f"{base}/{quote}"
