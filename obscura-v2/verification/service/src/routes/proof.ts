/**
 * Proof Routes
 */

import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { generateProof, type ProofRequest } from '../services/prover.ts';
import { starknetClient } from '../services/starknet.ts';
import { stringToFelt } from '../utils/trade-processor.ts';
import { logger } from '../utils/logger.ts';

// Request schemas
const TradeSchema = z.object({
  trade_id: z.string(),
  trader_user_id: z.string(),
  symbol: z.string(),
  exchange: z.string(),
  side: z.enum(['buy', 'sell']),
  order_type: z.string(),
  quantity: z.string(),
  price: z.string(),
  fee: z.string(),
  timestamp: z.number(),
});

const GenerateProofRequestSchema = z.object({
  trades: z.array(TradeSchema).min(1).max(10),
  trader_id: z.string(),
  timestamp_start: z.number(),
  timestamp_end: z.number(),
});

const SubmitProofRequestSchema = z.object({
  trader_id: z.string(),
  trader_address: z.string(),
  timestamp_start: z.number(),
  timestamp_end: z.number(),
  trade_count: z.number(),
  symbol_count: z.number(),
  report_hash: z.string(),
  commitment: z.string(),
  total_pnl_value: z.string(),
  total_pnl_negative: z.boolean(),
});

export async function proofRoutes(app: FastifyInstance) {
  /**
   * Generate a proof from trade data
   * POST /api/v1/proof/generate
   */
  app.post('/generate', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const body = GenerateProofRequestSchema.parse(request.body);

      const proofRequest: ProofRequest = {
        trades: body.trades,
        traderId: body.trader_id,
        timestampStart: body.timestamp_start,
        timestampEnd: body.timestamp_end,
      };

      const result = await generateProof(proofRequest);

      return reply.send({
        success: true,
        data: {
          commitment: result.commitment.toString(),
          report_hash: result.reportHash.toString(),
          trade_count: result.tradeCount,
          symbol_count: result.symbolCount,
          total_pnl: {
            value: result.totalPnl.value.toString(),
            is_negative: result.totalPnl.isNegative,
          },
          symbol_pnls: result.symbolPnls.map(pnl => ({
            symbol: pnl.symbol.toString(),
            pnl_value: pnl.pnl_value.toString(),
            pnl_negative: pnl.pnl_negative,
            is_profitable: pnl.is_profitable,
          })),
        },
      });
    } catch (error) {
      logger.error({ error }, 'Failed to generate proof');
      
      if (error instanceof z.ZodError) {
        return reply.status(400).send({
          success: false,
          error: 'Invalid request body',
          details: error.errors,
        });
      }

      return reply.status(500).send({
        success: false,
        error: 'Failed to generate proof',
      });
    }
  });

  /**
   * Submit a proof to Starknet
   * POST /api/v1/proof/submit
   */
  app.post('/submit', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const body = SubmitProofRequestSchema.parse(request.body);

      // Check if commitment already used
      const commitment = BigInt(body.commitment);
      const isUsed = await starknetClient.isCommitmentUsed(commitment);
      
      if (isUsed) {
        return reply.status(400).send({
          success: false,
          error: 'Commitment already used',
        });
      }

      // Submit to Starknet
      const result = await starknetClient.submitReport(
        {
          trader: body.trader_address,
          timestampStart: BigInt(body.timestamp_start),
          timestampEnd: BigInt(body.timestamp_end),
          tradeCount: body.trade_count,
          symbolCount: body.symbol_count,
          reportHash: BigInt(body.report_hash),
          commitment,
        },
        BigInt(body.total_pnl_value),
        body.total_pnl_negative
      );

      return reply.send({
        success: true,
        data: {
          report_id: result.reportId.toString(),
          transaction_hash: result.transactionHash,
          block_number: result.blockNumber,
        },
      });
    } catch (error) {
      logger.error({ error }, 'Failed to submit proof');

      if (error instanceof z.ZodError) {
        return reply.status(400).send({
          success: false,
          error: 'Invalid request body',
          details: error.errors,
        });
      }

      return reply.status(500).send({
        success: false,
        error: 'Failed to submit proof to Starknet',
      });
    }
  });

  /**
   * Get report status
   * GET /api/v1/proof/report/:id
   */
  app.get('/report/:id', async (request: FastifyRequest<{ Params: { id: string } }>, reply: FastifyReply) => {
    try {
      const reportCount = await starknetClient.getReportCount();
      
      return reply.send({
        success: true,
        data: {
          report_id: request.params.id,
          total_reports: reportCount.toString(),
          // Would fetch actual report data here
        },
      });
    } catch (error) {
      logger.error({ error }, 'Failed to get report');
      return reply.status(500).send({
        success: false,
        error: 'Failed to get report',
      });
    }
  });

  /**
   * Get trader stats
   * GET /api/v1/proof/trader/:address/stats
   */
  app.get('/trader/:address/stats', async (request: FastifyRequest<{ Params: { address: string } }>, reply: FastifyReply) => {
    try {
      const stats = await starknetClient.getTraderStats(request.params.address);
      
      return reply.send({
        success: true,
        data: {
          trader_address: request.params.address,
          total_reports: stats.totalReports,
          total_trades: stats.totalTrades,
          total_pnl: {
            value: stats.totalPnlValue.toString(),
            is_negative: stats.totalPnlNegative,
          },
        },
      });
    } catch (error) {
      logger.error({ error }, 'Failed to get trader stats');
      return reply.status(500).send({
        success: false,
        error: 'Failed to get trader stats',
      });
    }
  });
}
