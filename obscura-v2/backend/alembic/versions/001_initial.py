"""Initial migration - Create all tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE subscriptiontier AS ENUM ('free', 'basic', 'pro', 'premium', 'enterprise')")
    op.execute("CREATE TYPE paymentstatus AS ENUM ('pending', 'confirmed', 'failed', 'refunded', 'expired')")
    op.execute("CREATE TYPE orderside AS ENUM ('buy', 'sell')")
    op.execute("CREATE TYPE ordertype AS ENUM ('market', 'limit', 'stop_loss', 'take_profit')")
    op.execute("CREATE TYPE orderstatus AS ENUM ('pending', 'open', 'filled', 'partially_filled', 'cancelled', 'failed')")
    op.execute("CREATE TYPE exchangetype AS ENUM ('cex', 'dex')")
    op.execute("CREATE TYPE userrole AS ENUM ('user', 'trader', 'admin')")

    # Users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('wallet_address', sa.String(255), nullable=True),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('role', sa.Enum('user', 'trader', 'admin', name='userrole'), nullable=True, default='user'),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('wallet_address'),
        sa.UniqueConstraint('username'),
        sa.CheckConstraint('email IS NOT NULL OR wallet_address IS NOT NULL', name='user_must_have_email_or_wallet')
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_wallet_address', 'users', ['wallet_address'])
    op.create_index('ix_users_username', 'users', ['username'])

    # User subscriptions table
    op.create_table('user_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tier', sa.Enum('free', 'basic', 'pro', 'premium', 'enterprise', name='subscriptiontier'), nullable=False, default='free'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('auto_renew', sa.Boolean(), nullable=True, default=True),
        sa.Column('monthly_price_usd', sa.Numeric(10, 2), nullable=True, default=0),
        sa.Column('zcash_payment_address', sa.String(255), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_subscription_tier', 'user_subscriptions', ['tier'])
    op.create_index('idx_subscription_expires', 'user_subscriptions', ['expires_at'])

    # Payment transactions table
    op.create_table('payment_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount_usd', sa.Numeric(10, 2), nullable=False),
        sa.Column('amount_zec', sa.Numeric(18, 8), nullable=True),
        sa.Column('exchange_rate', sa.Numeric(18, 8), nullable=True),
        sa.Column('tx_hash', sa.String(255), nullable=True),
        sa.Column('from_address', sa.String(255), nullable=True),
        sa.Column('to_address', sa.String(255), nullable=True),
        sa.Column('memo', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'confirmed', 'failed', 'refunded', 'expired', name='paymentstatus'), nullable=True, default='pending'),
        sa.Column('confirmations', sa.Integer(), nullable=True, default=0),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['user_subscriptions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tx_hash')
    )
    op.create_index('idx_payment_status', 'payment_transactions', ['status'])
    op.create_index('idx_payment_tx_hash', 'payment_transactions', ['tx_hash'])

    # Trader profiles table
    op.create_table('trader_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=True, default=False),
        sa.Column('allows_copy_trading', sa.Boolean(), nullable=True, default=False),
        sa.Column('max_followers', sa.Integer(), nullable=True, default=100),
        sa.Column('monthly_fee_usd', sa.Numeric(10, 2), nullable=True, default=0),
        sa.Column('performance_fee_percent', sa.Numeric(5, 2), nullable=True, default=0),
        sa.Column('zcash_payout_address', sa.String(255), nullable=True),
        sa.Column('total_trades', sa.Integer(), nullable=True, default=0),
        sa.Column('win_rate', sa.Numeric(5, 2), nullable=True, default=0),
        sa.Column('total_pnl_usd', sa.Numeric(18, 2), nullable=True, default=0),
        sa.Column('sharpe_ratio', sa.Numeric(8, 4), nullable=True),
        sa.Column('max_drawdown', sa.Numeric(5, 2), nullable=True),
        sa.Column('avg_trade_duration_hours', sa.Numeric(10, 2), nullable=True),
        sa.Column('rank_overall', sa.Integer(), nullable=True),
        sa.Column('rank_monthly', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('stats_updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_trader_public', 'trader_profiles', ['is_public'])
    op.create_index('idx_trader_rank', 'trader_profiles', ['rank_overall'])

    # API key stores table
    op.create_table('api_key_stores',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('exchange_type', sa.Enum('cex', 'dex', name='exchangetype'), nullable=False),
        sa.Column('label', sa.String(100), nullable=True),
        sa.Column('nillion_key_store_id', sa.String(255), nullable=False),
        sa.Column('nillion_secret_store_id', sa.String(255), nullable=True),
        sa.Column('nillion_extra_store_ids', sa.JSON(), nullable=True, default={}),
        sa.Column('key_version', sa.Integer(), nullable=True, default=1),
        sa.Column('can_trade', sa.Boolean(), nullable=True, default=True),
        sa.Column('can_withdraw', sa.Boolean(), nullable=True, default=False),
        sa.Column('permissions', sa.JSON(), nullable=True, default={}),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_valid', sa.Boolean(), nullable=True, default=True),
        sa.Column('last_validated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'exchange', 'label', name='uq_user_exchange_label')
    )
    op.create_index('idx_apikey_exchange', 'api_key_stores', ['exchange'])
    op.create_index('idx_apikey_user', 'api_key_stores', ['user_id'])

    # Followers table
    op.create_table('followers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trader_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('follower_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_copying', sa.Boolean(), nullable=True, default=False),
        sa.Column('followed_at', sa.DateTime(), nullable=True),
        sa.Column('copy_started_at', sa.DateTime(), nullable=True),
        sa.Column('unfollowed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['trader_id'], ['users.id']),
        sa.ForeignKeyConstraint(['follower_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trader_id', 'follower_id', name='uq_trader_follower')
    )
    op.create_index('idx_follower_trader', 'followers', ['trader_id'])
    op.create_index('idx_follower_follower', 'followers', ['follower_id'])

    # Copy trading configs table
    op.create_table('copy_trading_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('follower_rel_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trader_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('copy_mode', sa.String(20), nullable=True, default='proportional'),
        sa.Column('fixed_amount_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('proportion_percent', sa.Numeric(5, 2), nullable=True, default=100),
        sa.Column('max_position_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('max_daily_loss_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('max_drawdown_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('stop_loss_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('allowed_exchanges', sa.JSON(), nullable=True),
        sa.Column('allowed_pairs', sa.JSON(), nullable=True),
        sa.Column('min_trade_size_usd', sa.Numeric(18, 2), nullable=True, default=10),
        sa.Column('max_trade_size_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_paused', sa.Boolean(), nullable=True, default=False),
        sa.Column('pause_reason', sa.String(255), nullable=True),
        sa.Column('total_copied_trades', sa.Integer(), nullable=True, default=0),
        sa.Column('total_pnl_usd', sa.Numeric(18, 2), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['follower_rel_id'], ['followers.id']),
        sa.ForeignKeyConstraint(['trader_id'], ['trader_profiles.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('follower_rel_id')
    )
    op.create_index('idx_copy_config_trader', 'copy_trading_configs', ['trader_id'])

    # Trades table
    op.create_table('trades',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('exchange_type', sa.Enum('cex', 'dex', name='exchangetype'), nullable=False),
        sa.Column('exchange_order_id', sa.String(255), nullable=True),
        sa.Column('symbol', sa.String(50), nullable=False),
        sa.Column('side', sa.Enum('buy', 'sell', name='orderside'), nullable=False),
        sa.Column('order_type', sa.Enum('market', 'limit', 'stop_loss', 'take_profit', name='ordertype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'open', 'filled', 'partially_filled', 'cancelled', 'failed', name='orderstatus'), nullable=True, default='pending'),
        sa.Column('amount', sa.Numeric(28, 18), nullable=False),
        sa.Column('filled_amount', sa.Numeric(28, 18), nullable=True, default=0),
        sa.Column('price', sa.Numeric(28, 18), nullable=True),
        sa.Column('average_fill_price', sa.Numeric(28, 18), nullable=True),
        sa.Column('notional_value_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('fees_usd', sa.Numeric(18, 8), nullable=True, default=0),
        sa.Column('pnl_usd', sa.Numeric(18, 2), nullable=True),
        sa.Column('is_copy_trade', sa.Boolean(), nullable=True, default=False),
        sa.Column('source_trade_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tx_hash', sa.String(255), nullable=True),
        sa.Column('block_number', sa.Integer(), nullable=True),
        sa.Column('gas_used', sa.Numeric(18, 0), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['source_trade_id'], ['trades.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_trade_user', 'trades', ['user_id'])
    op.create_index('idx_trade_symbol', 'trades', ['symbol'])
    op.create_index('idx_trade_exchange', 'trades', ['exchange'])
    op.create_index('idx_trade_status', 'trades', ['status'])
    op.create_index('idx_trade_created', 'trades', ['created_at'])

    # Positions table
    op.create_table('positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('symbol', sa.String(50), nullable=False),
        sa.Column('side', sa.Enum('buy', 'sell', name='orderside'), nullable=False),
        sa.Column('size', sa.Numeric(28, 18), nullable=False),
        sa.Column('entry_price', sa.Numeric(28, 18), nullable=False),
        sa.Column('current_price', sa.Numeric(28, 18), nullable=True),
        sa.Column('liquidation_price', sa.Numeric(28, 18), nullable=True),
        sa.Column('leverage', sa.Numeric(5, 2), nullable=True, default=1),
        sa.Column('margin_used', sa.Numeric(18, 2), nullable=True),
        sa.Column('unrealized_pnl_usd', sa.Numeric(18, 2), nullable=True, default=0),
        sa.Column('realized_pnl_usd', sa.Numeric(18, 2), nullable=True, default=0),
        sa.Column('is_open', sa.Boolean(), nullable=True, default=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'exchange', 'symbol', 'is_open', name='uq_open_position')
    )
    op.create_index('idx_position_user', 'positions', ['user_id'])
    op.create_index('idx_position_open', 'positions', ['is_open'])

    # Analytics snapshots table
    op.create_table('analytics_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_value_usd', sa.Numeric(18, 2), nullable=False),
        sa.Column('cash_balance_usd', sa.Numeric(18, 2), nullable=True, default=0),
        sa.Column('positions_value_usd', sa.Numeric(18, 2), nullable=True, default=0),
        sa.Column('pnl_usd', sa.Numeric(18, 2), nullable=True, default=0),
        sa.Column('pnl_percent', sa.Numeric(10, 4), nullable=True, default=0),
        sa.Column('trades_count', sa.Integer(), nullable=True, default=0),
        sa.Column('winning_trades', sa.Integer(), nullable=True, default=0),
        sa.Column('losing_trades', sa.Integer(), nullable=True, default=0),
        sa.Column('total_volume_usd', sa.Numeric(18, 2), nullable=True, default=0),
        sa.Column('sharpe_ratio', sa.Numeric(8, 4), nullable=True),
        sa.Column('sortino_ratio', sa.Numeric(8, 4), nullable=True),
        sa.Column('max_drawdown_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('volatility', sa.Numeric(8, 4), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'period_type', 'period_start', name='uq_analytics_period')
    )
    op.create_index('idx_analytics_user', 'analytics_snapshots', ['user_id'])
    op.create_index('idx_analytics_period', 'analytics_snapshots', ['period_type', 'period_start'])

    # Monitoring sessions table
    op.create_table('monitoring_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trader_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('symbols', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('connection_status', sa.String(20), nullable=True, default='disconnected'),
        sa.Column('events_received', sa.Integer(), nullable=True, default=0),
        sa.Column('trades_detected', sa.Integer(), nullable=True, default=0),
        sa.Column('last_event_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['trader_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_monitoring_trader', 'monitoring_sessions', ['trader_id'])
    op.create_index('idx_monitoring_active', 'monitoring_sessions', ['is_active'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('monitoring_sessions')
    op.drop_table('analytics_snapshots')
    op.drop_table('positions')
    op.drop_table('trades')
    op.drop_table('copy_trading_configs')
    op.drop_table('followers')
    op.drop_table('api_key_stores')
    op.drop_table('trader_profiles')
    op.drop_table('payment_transactions')
    op.drop_table('user_subscriptions')
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE userrole")
    op.execute("DROP TYPE exchangetype")
    op.execute("DROP TYPE orderstatus")
    op.execute("DROP TYPE ordertype")
    op.execute("DROP TYPE orderside")
    op.execute("DROP TYPE paymentstatus")
    op.execute("DROP TYPE subscriptiontier")
