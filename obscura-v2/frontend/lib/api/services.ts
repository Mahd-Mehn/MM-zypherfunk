const CITADEL_URL = "http://localhost:8004";
const CONDUCTOR_URL = "http://localhost:8001";
const PAYMENTS_URL = "http://localhost:8005";

export const CitadelService = {
  async storeSecret(secret: string, name: string) {
    const res = await fetch(`${CITADEL_URL}/store`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ secret, name }),
    });
    return res.json();
  },
  async signPayload(storeId: string, payloadHash: string) {
    const res = await fetch(`${CITADEL_URL}/sign`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ store_id: storeId, payload_hash: payloadHash }),
    });
    return res.json();
  },
};

export const ConductorService = {
  async executeTrade(userId: string, chain: string, action: string, params: any) {
    const res = await fetch(`${CONDUCTOR_URL}/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, chain, action, params }),
    });
    return res.json();
  },
};

export const PaymentsService = {
  async subscribe(userId: string, tier: string) {
    const res = await fetch(`${PAYMENTS_URL}/subscribe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, tier }),
    });
    return res.json();
  },
  async checkPayment(paymentAddress: string) {
    const res = await fetch(`${PAYMENTS_URL}/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ payment_address: paymentAddress }),
    });
    return res.json();
  },
  async simulatePayment(paymentAddress: string) {
    const res = await fetch(`${PAYMENTS_URL}/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ payment_address: paymentAddress }),
    });
    return res.json();
  },
};
