import os
import asyncio
from typing import Optional

try:
    # Nillion SDK: attempt to import the secretvaults client if available
    # The project repo: https://github.com/NillionNetwork/secretvaults-py
    # Users may need to install it via pip from the repo or PyPI
    from secretvaults import SecretVault, NetworkAPI
    _HAVE_NILLION = True
except Exception:
    SecretVault = None  # type: ignore
    NetworkAPI = None  # type: ignore
    _HAVE_NILLION = False


class NillionClient:
    """Nillion integration wrapper.

    Behaviour:
    - If `secretvaults` SDK is installed and environment configured, use it.
    - Otherwise, fall back to a local in-memory mock with clear logs.

    Environment variables:
    - `NILLION_NETWORK_URL` (optional): URL for the Nillion network API/relay.
    - `NILLION_API_KEY` (optional): API key if required by the deployment.
    """

    def __init__(self):
        self._mock_store = {}
        self.network_url = os.getenv("NILLION_NETWORK_URL")
        self.api_key = os.getenv("NILLION_API_KEY")
        if _HAVE_NILLION and self.network_url:
            # Initialize the SDK network client
            self.network = NetworkAPI(network_url=self.network_url, api_key=self.api_key)  # type: ignore
            print(f"Nillion Client initialized using SDK (URL={self.network_url})")
        elif _HAVE_NILLION:
            # Try default NetworkAPI init
            try:
                self.network = NetworkAPI.from_env()  # type: ignore
                print("Nillion Client initialized using SDK from env")
            except Exception:
                self.network = None
                print("Nillion SDK present but no network configuration found; falling back to mock")
        else:
            self.network = None
            print("Nillion SDK not installed; running Nillion client in MOCK mode")

    async def store_secret(self, secret: str, name: str) -> str:
        """Store a secret in nilDB (or mock).

        Returns a `store_id` handle used for later blind compute calls.
        """
        if self.network:
            # Real SDK path: create or open a vault and store secret
            vault = SecretVault(self.network, name=name)  # type: ignore
            # The SDK examples typically accept bytes; adapt as needed
            result = await asyncio.get_event_loop().run_in_executor(None, vault.put, secret)
            return result.get("store_id") if isinstance(result, dict) and "store_id" in result else str(result)

        # Mock path
        store_id = name + ":" + str(len(self._mock_store) + 1)
        self._mock_store[store_id] = secret
        print(f"[MOCK] Stored secret under {store_id}")
        return store_id

    async def retrieve_secret(self, store_id: str) -> Optional[str]:
        """Retrieve a secret for verification/debug (avoid in prod)."""
        if self.network:
            vault = SecretVault(self.network)
            res = await asyncio.get_event_loop().run_in_executor(None, vault.get, store_id)
            return res
        return self._mock_store.get(store_id)

    async def compute_signature(self, store_id: str, payload: bytes) -> str:
        """Perform a blind compute (nilCC) to sign `payload` using the secret stored under `store_id`.

        Returns a serialized signature string. In production the SDK will provide a proper signature object.
        """
        if self.network:
            # SDK blind compute example: run a computation on the vault without exposing the secret
            vault = SecretVault(self.network)
            # `compute` is a blocking call in many SDKs; run in executor
            res = await asyncio.get_event_loop().run_in_executor(None, vault.compute, store_id, payload)
            return res.get("signature") if isinstance(res, dict) and "signature" in res else str(res)

        # Mock signature (base64-like) to preserve interfaces for consumers
        import base64, hashlib

        h = hashlib.sha256(payload).digest()
        sig = base64.b64encode(h).decode()
        print(f"[MOCK] Computed mock signature for store_id={store_id}")
        return sig


# Singleton instance to be reused by the app
nillion = NillionClient()
