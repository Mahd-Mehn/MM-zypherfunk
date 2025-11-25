/**
 * Obscura Verification Service - Main Entry Point
 * 
 * REST API for generating and submitting ZK proofs to Starknet.
 */

import Fastify from 'fastify';
import cors from '@fastify/cors';
import { config } from './config/index.ts';
import { logger } from './utils/logger.ts';
import { proofRoutes } from './routes/proof.ts';
import { healthRoutes } from './routes/health.ts';

const app = Fastify({
  logger: logger,
});

// Register plugins
await app.register(cors, {
  origin: true,
  credentials: true,
});

// Register routes
await app.register(proofRoutes, { prefix: '/api/v1/proof' });
await app.register(healthRoutes, { prefix: '/api/v1/health' });

// Start server
const start = async () => {
  try {
    await app.listen({ port: config.port, host: '0.0.0.0' });
    logger.info(`Verification service running on port ${config.port}`);
  } catch (err) {
    logger.error(err);
    process.exit(1);
  }
};

start();

export { app };
