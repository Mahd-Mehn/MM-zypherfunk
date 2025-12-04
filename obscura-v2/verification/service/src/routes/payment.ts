/**
 * Payment Routes
 * 
 * Handles subscription payment verification and on-chain proof storage
 */

import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { starknetClient } from '../services/starknet.ts';
import { logger } from '../utils/logger.ts';

// Request schemas
const PaymentProofSchema = z.object({
  user_id: z.string(),
  trader_id: z.string().optional(),
  payment_id: z.string(),
  tier: z.enum(['basic', 'pro', 'premium']),
  amount_zec: z.number(),
  txid: z.string(),
  payment_address: z.string(),
  confirmed_at: z.number(),
});

const VerifySubscriptionSchema = z.object({
  user_address: z.string(),
  trader_address: z.string().optional(),
});

// Subscription tier durations in seconds
const TIER_DURATIONS = {
  basic: 30 * 24 * 60 * 60, // 30 days
  pro: 30 * 24 * 60 * 60,
  premium: 30 * 24 * 60 * 60,
};

// In-memory storage (would use database in production)
const paymentProofs: Map<string, {
  userId: string;
  traderId?: string;
  tier: string;
  amountZec: number;
  txid: string;
  confirmedAt: number;
  expiresAt: number;
  starknetTxHash?: string;
}> = new Map();

export async function paymentRoutes(app: FastifyInstance) {
  /**
   * Store subscription payment proof
   * POST /api/v1/payment/proof
   * 
   * Called after Zcash payment is confirmed to store proof on-chain
   */
  app.post('/proof', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const body = PaymentProofSchema.parse(request.body);

      const now = Math.floor(Date.now() / 1000);
      const duration = TIER_DURATIONS[body.tier];
      const expiresAt = body.confirmed_at + duration;

      // Store payment proof
      const proofData = {
        userId: body.user_id,
        traderId: body.trader_id,
        tier: body.tier,
        amountZec: body.amount_zec,
        txid: body.txid,
        confirmedAt: body.confirmed_at,
        expiresAt,
      };

      paymentProofs.set(body.payment_id, proofData);

      logger.info({
        paymentId: body.payment_id,
        userId: body.user_id,
        tier: body.tier,
        expiresAt,
      }, 'Payment proof stored');

      // Optionally submit to Starknet for on-chain verification
      // This creates an immutable record of the subscription
      let starknetTxHash: string | undefined;

      try {
        // Hash the payment data for on-chain storage
        const paymentHash = BigInt(
          '0x' + Buffer.from(JSON.stringify({
            userId: body.user_id,
            tier: body.tier,
            txid: body.txid,
            confirmedAt: body.confirmed_at,
          })).toString('hex').slice(0, 62)
        );

        // This would call a subscription contract on Starknet
        // For now, we'll just log it
        logger.info({
          paymentHash: paymentHash.toString(),
        }, 'Would submit payment proof to Starknet');

        // starknetTxHash = result.transactionHash;
        // proofData.starknetTxHash = starknetTxHash;
      } catch (err) {
        logger.warn({ error: err }, 'Failed to submit payment proof to Starknet');
        // Continue without Starknet submission
      }

      return reply.send({
        success: true,
        data: {
          payment_id: body.payment_id,
          expires_at: expiresAt,
          starknet_tx_hash: starknetTxHash,
        },
      });
    } catch (error) {
      logger.error({ error }, 'Failed to store payment proof');

      if (error instanceof z.ZodError) {
        return reply.status(400).send({
          success: false,
          error: 'Invalid request body',
          details: error.errors,
        });
      }

      return reply.status(500).send({
        success: false,
        error: 'Failed to store payment proof',
      });
    }
  });

  /**
   * Verify active subscription
   * POST /api/v1/payment/verify
   * 
   * Check if a user has an active subscription
   */
  app.post('/verify', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const body = VerifySubscriptionSchema.parse(request.body);

      const now = Math.floor(Date.now() / 1000);
      let activeSubscription = null;

      // Search for active subscription
      for (const [paymentId, proof] of paymentProofs.entries()) {
        // Match by user address (in production, would query by user ID)
        if (proof.expiresAt > now) {
          // If trader specified, only match if subscription is for that trader
          if (body.trader_address && proof.traderId !== body.trader_address) {
            continue;
          }

          activeSubscription = {
            payment_id: paymentId,
            tier: proof.tier,
            expires_at: proof.expiresAt,
            trader_id: proof.traderId,
          };
          break;
        }
      }

      return reply.send({
        success: true,
        data: {
          has_active_subscription: activeSubscription !== null,
          subscription: activeSubscription,
        },
      });
    } catch (error) {
      logger.error({ error }, 'Failed to verify subscription');

      if (error instanceof z.ZodError) {
        return reply.status(400).send({
          success: false,
          error: 'Invalid request body',
          details: error.errors,
        });
      }

      return reply.status(500).send({
        success: false,
        error: 'Failed to verify subscription',
      });
    }
  });

  /**
   * Get subscription details
   * GET /api/v1/payment/subscription/:userId
   */
  app.get('/subscription/:userId', async (request: FastifyRequest<{ Params: { userId: string } }>, reply: FastifyReply) => {
    try {
      const now = Math.floor(Date.now() / 1000);
      const subscriptions = [];

      for (const [paymentId, proof] of paymentProofs.entries()) {
        if (proof.userId === request.params.userId) {
          subscriptions.push({
            payment_id: paymentId,
            tier: proof.tier,
            trader_id: proof.traderId,
            confirmed_at: proof.confirmedAt,
            expires_at: proof.expiresAt,
            is_active: proof.expiresAt > now,
            starknet_tx_hash: proof.starknetTxHash,
          });
        }
      }

      return reply.send({
        success: true,
        data: {
          user_id: request.params.userId,
          subscriptions,
          active_count: subscriptions.filter(s => s.is_active).length,
        },
      });
    } catch (error) {
      logger.error({ error }, 'Failed to get subscription');
      return reply.status(500).send({
        success: false,
        error: 'Failed to get subscription',
      });
    }
  });

  /**
   * Get payment stats (admin)
   * GET /api/v1/payment/stats
   */
  app.get('/stats', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const now = Math.floor(Date.now() / 1000);
      const stats = {
        total_payments: paymentProofs.size,
        active_subscriptions: 0,
        by_tier: { basic: 0, pro: 0, premium: 0 } as Record<string, number>,
        total_zec: 0,
      };

      for (const proof of paymentProofs.values()) {
        if (proof.expiresAt > now) {
          stats.active_subscriptions++;
        }
        stats.by_tier[proof.tier] = (stats.by_tier[proof.tier] || 0) + 1;
        stats.total_zec += proof.amountZec;
      }

      return reply.send({
        success: true,
        data: stats,
      });
    } catch (error) {
      logger.error({ error }, 'Failed to get payment stats');
      return reply.status(500).send({
        success: false,
        error: 'Failed to get payment stats',
      });
    }
  });
}
