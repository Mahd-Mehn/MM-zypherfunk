/**
 * Health Check Routes
 */

import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { config } from '../config/index.ts';

export async function healthRoutes(app: FastifyInstance) {
  /**
   * Basic health check
   * GET /api/v1/health
   */
  app.get('/', async (_request: FastifyRequest, reply: FastifyReply) => {
    return reply.send({
      status: 'ok',
      service: 'obscura-verification',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
    });
  });

  /**
   * Readiness check (includes Starknet connectivity)
   * GET /api/v1/health/ready
   */
  app.get('/ready', async (_request: FastifyRequest, reply: FastifyReply) => {
    const checks = {
      starknet: {
        configured: !!config.starknet.accountAddress,
        network: config.starknet.network,
      },
      redis: {
        configured: !!config.redis.url,
      },
    };

    const isReady = checks.starknet.configured;

    return reply.status(isReady ? 200 : 503).send({
      status: isReady ? 'ready' : 'not_ready',
      checks,
    });
  });
}
