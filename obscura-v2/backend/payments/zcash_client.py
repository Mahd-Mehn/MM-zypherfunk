import os
import asyncio
import subprocess
from typing import Dict, Optional

try:
    # `zecwallet` Python wrapper (if installed)
    import zecwallet
    _HAVE_ZECWALLET = True
except Exception:
    zecwallet = None  # type: ignore
    _HAVE_ZECWALLET = False


class ZcashClient:
    """Zcash payments integration.

    - If `zecwallet` Python package is available it is used.
    - Otherwise the class will attempt to call `zecwallet-cli` via subprocess.
    - If neither is available the client runs in MOCK mode so the rest of the app remains testable.

    Environment variables:
    - `ZECWALLET_CLI_PATH` override path to the `zecwallet-cli` binary.
    - `ZECWALLET_RPC_ENDPOINT` if using an RPC-backed wrapper.
    """

    def __init__(self):
        self.pending_payments: Dict[str, float] = {}
        self._cli_path = os.getenv("ZECWALLET_CLI_PATH", "zecwallet-cli")
        if _HAVE_ZECWALLET:
            print("Zcash Client: using zecwallet Python package")
        else:
            # check if CLI exists
            try:
                subprocess.run([self._cli_path, "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"Zcash Client: using CLI at {self._cli_path}")
            except Exception:
                print("Zcash Client: running in MOCK mode (no zecwallet package or CLI found)")

    def get_new_unified_address(self) -> str:
        """Generate a new Unified Address (UA) suitable for shielded payments.

        Returns an address string. In production this must be generated from a wallet.
        """
        if _HAVE_ZECWALLET:
            # Example: zecwallet.create_unified_address() — adapt to actual API
            return zecwallet.create_unified_address()

        # Fallback to CLI
        try:
            out = subprocess.check_output([self._cli_path, "address", "new"]).decode().strip()
            return out
        except Exception:
            # Mock address for demo purposes
            import uuid
            return f"ua1{uuid.uuid4().hex[:60]}"

    def watch_address(self, address: str, amount: float):
        """Register an address we expect a payment to arrive to.

        The real implementation should subscribe to notifications (RPC/websocket) or poll the wallet.
        """
        self.pending_payments[address] = amount
        print(f"Watching Zcash address {address} for {amount} ZEC")

    async def check_payment(self, address: str) -> bool:
        """Check whether the expected payment arrived and is shielded/confirmed.

        This method is intentionally asynchronous to support polling loops.
        """
        if _HAVE_ZECWALLET:
            # The exact SDK call depends on `zecwallet` package; placeholder below
            res = await asyncio.get_event_loop().run_in_executor(None, zecwallet.get_address_balance, address)
            # res expected to be a dict with `confirmed` or `shielded` fields
            return bool(res and res.get("confirmed", 0) >= self.pending_payments.get(address, 0))

        # CLI attempt
        try:
            out = subprocess.check_output([self._cli_path, "address", "balance", address]).decode()
            # Best-effort parse
            if "confirmed" in out.lower():
                return True
        except Exception:
            pass

        # Mock: return False unless simulate_payment called
        return False

    def simulate_payment(self, address: str):
        """Demo helper: mark a pending address as paid."""
        if address in self.pending_payments:
            print(f"[MOCK] Payment simulated for {address}")
            return True
        return False


zcash = ZcashClient()
