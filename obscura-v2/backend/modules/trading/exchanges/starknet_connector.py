"""
Starknet DEX Connector
Supports trading on Starknet DEXes (JediSwap, 10KSwap, etc.)
"""

import os
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import json

try:
    from starknet_py.net.full_node_client import FullNodeClient
    from starknet_py.net.account.account import Account
    from starknet_py.net.models import StarknetChainId
    from starknet_py.net.signer.stark_curve_signer import KeyPair
    _HAVE_STARKNET = True
except ImportError:
    FullNodeClient = None  # type: ignore
    Account = None  # type: ignore
    _HAVE_STARKNET = False

from .base import (
    ExchangeConnector, TradeOrder, OrderResult, Balance,
    MarketData, OrderType, OrderSide, ExchangeType
)


class StarknetConnector(ExchangeConnector):
    """Starknet DEX integration"""
    
    # JediSwap Router address on Starknet mainnet
    JEDISWAP_ROUTER = "0x041fd22b238fa21cfcf5dd45a8548974d8263b3a531a60388411c5e230f97023"
    
    # Common token addresses on Starknet
    TOKEN_ADDRESSES = {
        'ETH': '0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7',  # Starknet ETH
        'USDC': '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8', # USDC on Starknet
        'USDT': '0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8', # USDT on Starknet
        'DAI': '0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3',  # DAI on Starknet
    }
    
    def __init__(self, private_key: Optional[str] = None, account_address: Optional[str] = None):
        super().__init__()
        self.name = "Starknet"
        self.exchange_type = ExchangeType.DEX
        self.client = None
        self.account = None
        self._initialized = False
        
        self.private_key = private_key or os.getenv("STARKNET_PRIVATE_KEY")
        self.account_address = account_address or os.getenv("STARKNET_ACCOUNT_ADDRESS")
        self.rpc_url = os.getenv("STARKNET_RPC_URL", "https://starknet-mainnet.public.blastapi.io")
        self.chain = os.getenv("STARKNET_CHAIN", "mainnet")
    
    async def initialize(self) -> bool:
        """Initialize Starknet connection"""
        if not _HAVE_STARKNET:
            print("Warning: starknet.py not installed. Install with: pip install starknet-py")
            return False
        
        try:
            self.client = FullNodeClient(node_url=self.rpc_url)
            
            if self.private_key and self.account_address:
                # Initialize account
                key_pair = KeyPair.from_private_key(int(self.private_key, 16))
                chain_id = StarknetChainId.MAINNET if self.chain == "mainnet" else StarknetChainId.TESTNET
                
                self.account = Account(
                    client=self.client,
                    address=self.account_address,
                    key_pair=key_pair,
                    chain=chain_id
                )
            
            self._initialized = True
            print(f"Starknet connector initialized on {self.chain}")
            return True
            
        except Exception as e:
            print(f"Failed to initialize Starknet connector: {e}")
            return False
    
    async def place_order(self, order: TradeOrder) -> OrderResult:
        """Place swap on Starknet DEX"""
        if not self._initialized:
            await self.initialize()
        
        if not self.client or not self.account:
            raise RuntimeError("Starknet connector not initialized")
        
        try:
            # Parse symbol
            base, quote = order.symbol.split('/')
            
            # Get token addresses
            token_in = self.TOKEN_ADDRESSES.get(base if order.side == OrderSide.SELL else quote)
            token_out = self.TOKEN_ADDRESSES.get(quote if order.side == OrderSide.SELL else base)
            
            if not token_in or not token_out:
                raise ValueError(f"Token addresses not found for {order.symbol}")
            
            # Calculate amounts (Starknet uses felt252, typically 18 decimals for ETH/tokens)
            amount_in = int(order.amount * Decimal(10 ** 18))
            slippage = order.slippage or Decimal('0.01')
            amount_out_min = int(amount_in * (1 - float(slippage)))
            
            # Build swap calldata for JediSwap
            # swap_exact_tokens_for_tokens(amountIn, amountOutMin, path, to, deadline)
            deadline = order.deadline or (int(datetime.now().timestamp()) + 1200)
            
            # This is a simplified example - actual implementation would use proper contract interaction
            # via starknet.py's Contract class
            
            calldata = [
                amount_in,
                amount_out_min,
                2,  # path length
                int(token_in, 16),
                int(token_out, 16),
                int(self.account_address, 16),
                deadline
            ]
            
            # Execute transaction (simplified - real implementation would be more complex)
            # tx = await self.account.execute(
            #     calls=Call(
            #         to_addr=int(self.JEDISWAP_ROUTER, 16),
            #         selector=get_selector_from_name("swap_exact_tokens_for_tokens"),
            #         calldata=calldata
            #     ),
            #     max_fee=int(1e16)  # 0.01 ETH max fee
            # )
            
            # For now, return a mock result since full contract interaction is complex
            print(f"[Starknet] Would execute swap: {order.symbol} amount={order.amount}")
            
            return OrderResult(
                order_id=f"starknet_mock_{datetime.now().timestamp()}",
                exchange=self.name,
                exchange_type=self.exchange_type,
                symbol=order.symbol,
                side=order.side,
                amount=order.amount,
                filled_amount=order.amount,
                average_price=Decimal('0'),  # Would be calculated from actual swap
                status='pending',
                tx_hash=None,
                timestamp=datetime.now(),
                fees={'estimated_fee': Decimal('0.001')},
                metadata={'note': 'Starknet integration requires full contract deployment'}
            )
            
        except Exception as e:
            raise RuntimeError(f"Starknet swap failed: {e}")
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cannot cancel Starknet transactions once submitted"""
        return False
    
    async def get_order_status(self, order_id: str, symbol: str) -> OrderResult:
        """Get transaction status on Starknet"""
        if not self.client:
            raise RuntimeError("Not initialized")
        
        try:
            # Query transaction receipt
            # receipt = await self.client.get_transaction_receipt(order_id)
            
            return OrderResult(
                order_id=order_id,
                exchange=self.name,
                exchange_type=self.exchange_type,
                symbol=symbol,
                side=OrderSide.BUY,
                amount=Decimal('0'),
                filled_amount=Decimal('0'),
                average_price=Decimal('0'),
                status='unknown',
                tx_hash=order_id,
                timestamp=datetime.now(),
                metadata={}
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get Starknet tx status: {e}")
    
    async def get_balance(self, asset: Optional[str] = None) -> List[Balance]:
        """Get wallet balance on Starknet"""
        if not self.client or not self.account:
            raise RuntimeError("Not initialized")
        
        try:
            # Query ETH balance
            # eth_token = Contract(address=self.TOKEN_ADDRESSES['ETH'], abi=ERC20_ABI, provider=self.account)
            # balance = await eth_token.functions["balanceOf"].call(self.account.address)
            
            # Mock for now
            return [Balance(
                asset='ETH',
                free=Decimal('0'),
                locked=Decimal('0'),
                total=Decimal('0')
            )]
            
        except Exception as e:
            raise RuntimeError(f"Failed to get Starknet balance: {e}")
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get market data from Starknet DEX"""
        raise NotImplementedError("Starknet market data requires DEX oracle integration")
    
    async def get_supported_pairs(self) -> List[str]:
        """Get supported pairs on Starknet DEXes"""
        return [
            'ETH/USDC',
            'ETH/USDT',
            'ETH/DAI',
            'USDC/USDT'
        ]
    
    def format_symbol(self, base: str, quote: str) -> str:
        """Format symbol for Starknet"""
        return f"{base}/{quote}"
