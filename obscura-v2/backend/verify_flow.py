import asyncio
import httpx
import time
import subprocess
import sys
import os

# Ports
CITADEL_PORT = 8004
CONDUCTOR_PORT = 8001
PAYMENTS_PORT = 8005

async def wait_for_service(port, name):
    url = f"http://localhost:{port}/health"
    print(f"Waiting for {name} at {url}...")
    for _ in range(10):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    print(f"{name} is UP!")
                    return True
        except:
            pass
        time.sleep(1)
    print(f"{name} failed to start.")
    return False

async def run_test():
    print("Starting Verification Flow...")
    
    async with httpx.AsyncClient() as client:
        # 1. Payments: Subscribe
        print("\n--- Testing Zcash Payments ---")
        resp = await client.post(f"http://localhost:{PAYMENTS_PORT}/subscribe", json={"user_id": "test_user", "tier": "pro"})
        print(f"Subscribe Response: {resp.json()}")
        payment_address = resp.json()["payment_address"]
        
        # Simulate Payment
        print("Simulating Payment...")
        await client.post(f"http://localhost:{PAYMENTS_PORT}/simulate", json={"payment_address": payment_address})
        
        # Check Payment
        resp = await client.post(f"http://localhost:{PAYMENTS_PORT}/check", json={"payment_address": payment_address})
        print(f"Payment Status: {resp.json()}")
        assert resp.json()["received"] == True

        # 2. Citadel: Store Secret
        print("\n--- Testing Citadel (Nillion) ---")
        resp = await client.post(f"http://localhost:{CITADEL_PORT}/store", json={"secret": "my_super_secret_key", "name": "binance"})
        print(f"Store Response: {resp.json()}")
        store_id = resp.json()["store_id"]
        
        # Sign Payload
        resp = await client.post(f"http://localhost:{CITADEL_PORT}/sign", json={"store_id": store_id, "payload_hash": "some_hash"})
        print(f"Sign Response: {resp.json()}")
        assert "signature" in resp.json()

        # 3. Conductor: Execute Trade
        print("\n--- Testing Conductor (NEAR) ---")
        resp = await client.post(f"http://localhost:{CONDUCTOR_PORT}/execute", json={
            "user_id": "test_user",
            "chain": "base",
            "action": "swap",
            "params": {"amount": 100}
        })
        print(f"Execution Response: {resp.json()}")
        assert resp.json()["status"] == "broadcasted"

    print("\n✅ ALL TESTS PASSED!")

def main():
    # Start Services
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    procs = []
    try:
        print("Starting Services...")
        procs.append(subprocess.Popen(["uvicorn", "citadel.main:app", "--port", str(CITADEL_PORT)], env=env))
        procs.append(subprocess.Popen(["uvicorn", "conductor.main:app", "--port", str(CONDUCTOR_PORT)], env=env))
        procs.append(subprocess.Popen(["uvicorn", "payments.main:app", "--port", str(PAYMENTS_PORT)], env=env))
        
        # Run Async Test
        asyncio.run(wait_for_service(CITADEL_PORT, "Citadel"))
        asyncio.run(wait_for_service(CONDUCTOR_PORT, "Conductor"))
        asyncio.run(wait_for_service(PAYMENTS_PORT, "Payments"))
        
        asyncio.run(run_test())
        
    finally:
        print("Stopping Services...")
        for p in procs:
            p.terminate()

if __name__ == "__main__":
    main()
