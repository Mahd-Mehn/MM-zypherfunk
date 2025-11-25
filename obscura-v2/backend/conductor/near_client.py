import os
import hashlib
import json
from typing import Optional
import httpx


class NearMpcClient:
    """NEAR chain-signature helper.

    This class provides a simple wrapper to request chain-signatures from either:
    - A configured relayer endpoint (recommended for local/dev), or
    - By constructing a NEAR transaction payload to be sent to a contracts-based signer.

    Environment variables:
    - `NEAR_CHAINSIG_RELAYER_URL`: If set, requests will POST to this endpoint with JSON
      payload {"account":..., "path":..., "payload": ...} and expect a JSON {"signature":...}.

    The implementation intentionally keeps the network logic minimal so it is easy to
    replace with the example scripts from https://github.com/near-examples/chainsig-script
    """

    def __init__(self, relayer_url: Optional[str] = None):
        self.relayer_url = relayer_url or os.getenv("NEAR_CHAINSIG_RELAYER_URL")
        if self.relayer_url:
            print(f"NEAR MPC Client: using relayer {self.relayer_url}")
        else:
            print("NEAR MPC Client: no relayer configured; requests will raise unless implemented")

    def derive_eth_address(self, near_account_id: str, path: str) -> str:
        """Derive an EVM address deterministically from NEAR account + path.

        This uses a SHA256-derived mock address format to match downstream expectations.
        In production use the NEAR MPC derivation from the Chain Signatures docs.
        """
        raw = f"{near_account_id}:{path}".encode()
        h = hashlib.sha256(raw).hexdigest()
        return f"0x{h[:40]}"

    async def request_signature(self, payload: bytes, path: str, near_account_id: str) -> str:
        """Request a chain-signature for `payload`.

        - If `NEAR_CHAINSIG_RELAYER_URL` is configured, POST to it and return the signature.
        - Otherwise raise NotImplementedError and explain how to wire a relayer.
        """
        if not self.relayer_url:
            raise NotImplementedError(
                "No NEAR_CHAINSIG_RELAYER_URL configured. Please run a chainsig relayer or set env var."
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            payload_b64 = payload.hex()
            body = {
                "account": near_account_id,
                "derivation_path": path,
                "payload_hex": payload_b64,
            }
            resp = await client.post(self.relayer_url, json=body)
            resp.raise_for_status()
            data = resp.json()
            sig = data.get("signature") or data.get("sig")
            if not sig:
                raise ValueError("Relayer returned no signature field")
            return sig


near_mpc = NearMpcClient()
