-- AIZIX API core tables (service role writes; RLS optional per product policy)
-- Compatible with infra/supabase/schema.sql — run after schema.sql on new projects.

create extension if not exists "pgcrypto";

-- -----------------------------------------------------------------------------
-- users — SaaS accounts (separate from auth.users; link later if needed)
-- -----------------------------------------------------------------------------
create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  email text unique,
  display_name text,
  created_at timestamptz not null default now()
);

-- -----------------------------------------------------------------------------
-- bot_state — singleton row keyed 'default' for demo / system bot
-- -----------------------------------------------------------------------------
create table if not exists public.bot_state (
  id text primary key default 'default',
  status text not null default 'STOPPED'
    check (status in ('ACTIVE', 'PAUSED', 'STOPPED')),
  compounding_enabled boolean not null default true,
  total_balance_usd numeric(18, 2) not null default 12540.00,
  trading_balance_usd numeric(18, 2) not null default 8778.00,
  safety_balance_usd numeric(18, 2) not null default 3762.00,
  win_rate_pct numeric(5, 2) not null default 78.00,
  daily_pnl_usd numeric(18, 2) not null default 240.00,
  updated_at timestamptz not null default now()
);

insert into public.bot_state (id)
values ('default')
on conflict (id) do nothing;

-- -----------------------------------------------------------------------------
-- trades — executed or simulated fills (API / engine)
-- -----------------------------------------------------------------------------
create table if not exists public.trades (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users (id) on delete set null,
  symbol text not null,
  side text not null check (side in ('buy', 'sell')),
  quantity numeric(24, 8),
  price numeric(24, 8),
  status text not null default 'simulated',
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists trades_created_idx on public.trades (created_at desc);

-- Optional RLS (anon has no access; service role bypasses)
alter table public.users enable row level security;
alter table public.bot_state enable row level security;
alter table public.trades enable row level security;

-- No policies = only service role / dashboard SQL can access.
-- Add policies when wiring Supabase Auth to public.users.
