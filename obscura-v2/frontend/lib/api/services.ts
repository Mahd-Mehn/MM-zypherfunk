/**
 * Legacy Services - Direct service connections
 * 
 * NOTE: For Zcash payments, prefer using zcashPaymentsAPI from './zcash-payments'
 * This file provides direct service access for Citadel (TEE) and Conductor (execution)
 */

import { zcashPaymentsAPI } from './zcash-payments'

const CITADEL_URL = process.env.NEXT_PUBLIC_CITADEL_URL || "http://localhost:8004";
const CONDUCTOR_URL = process.env.NEXT_PUBLIC_CONDUCTOR_URL || "http://localhost:8001";

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

// Re-export zcashPaymentsAPI as PaymentsService for backward compatibility
export const PaymentsService = {
  async subscribe(userId: string, tier: string, traderId?: string) {
    return zcashPaymentsAPI.createPayment({ userId, tier: tier as 'basic' | 'pro' | 'premium', traderId });
  },
  async checkPayment(paymentAddress: string) {
    return zcashPaymentsAPI.checkPaymentByAddress(paymentAddress);
  },
  async simulatePayment(paymentAddress: string) {
    return zcashPaymentsAPI.simulatePayment(paymentAddress);
  },
};
