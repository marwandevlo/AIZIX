-- AIZIX — Supabase schema (Postgres)
-- Run in Supabase SQL editor or via supabase db push after linking project.

-- Extensions
create extension if not exists "pgcrypto";

-- -----------------------------------------------------------------------------
-- profiles — one row per auth user
-- -----------------------------------------------------------------------------
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text,
  avatar_url text,
  timezone text default 'UTC',
  paper_mode boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at
  before update on public.profiles
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- bot_settings — automation & risk knobs
-- -----------------------------------------------------------------------------
create table if not exists public.bot_settings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  is_running boolean not null default false,
  max_daily_loss_pct numeric(6,3) not null default 3.000,
  max_capital_pct_per_trade numeric(6,3) not null default 10.000,
  max_open_trades int not null default 3,
  emergency_stop boolean not null default false,
  trading_wallet_pct numeric(5,2) not null default 70.00,
  safety_wallet_pct numeric(5,2) not null default 30.00,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id)
);

drop trigger if exists bot_settings_set_updated_at on public.bot_settings;
create trigger bot_settings_set_updated_at
  before update on public.bot_settings
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- wallets — paper or future live allocation buckets
-- -----------------------------------------------------------------------------
create table if not exists public.wallets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  wallet_type text not null check (wallet_type in ('trading', 'safety')),
  label text,
  balance_usd numeric(18,2) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists wallets_user_id_idx on public.wallets (user_id);

drop trigger if exists wallets_set_updated_at on public.wallets;
create trigger wallets_set_updated_at
  before update on public.wallets
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- paper_trades — simulated fills (no real money)
-- -----------------------------------------------------------------------------
create table if not exists public.paper_trades (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  symbol text not null,
  side text not null check (side in ('buy', 'sell')),
  qty numeric(24,8) not null,
  price numeric(24,8) not null,
  notional_usd numeric(18,2),
  pnl_usd numeric(18,2),
  status text not null default 'filled' check (status in ('open', 'filled', 'cancelled')),
  meta jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists paper_trades_user_created_idx
  on public.paper_trades (user_id, created_at desc);

-- -----------------------------------------------------------------------------
-- signals — AI / rules engine outputs
-- -----------------------------------------------------------------------------
create table if not exists public.signals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles (id) on delete set null,
  symbol text not null,
  action text not null check (action in ('buy', 'sell', 'hold')),
  confidence numeric(5,4) not null check (confidence >= 0 and confidence <= 1),
  mood text not null,
  reason text,
  payload jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists signals_created_idx on public.signals (created_at desc);

-- -----------------------------------------------------------------------------
-- Row Level Security
-- -----------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.bot_settings enable row level security;
alter table public.wallets enable row level security;
alter table public.paper_trades enable row level security;
alter table public.signals enable row level security;

-- profiles: users manage own row
drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own" on public.profiles
  for select using (auth.uid() = id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own" on public.profiles
  for update using (auth.uid() = id);

drop policy if exists "profiles_insert_own" on public.profiles;
create policy "profiles_insert_own" on public.profiles
  for insert with check (auth.uid() = id);

-- bot_settings
drop policy if exists "bot_settings_crud_own" on public.bot_settings;
create policy "bot_settings_crud_own" on public.bot_settings
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- wallets
drop policy if exists "wallets_crud_own" on public.wallets;
create policy "wallets_crud_own" on public.wallets
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- paper_trades
drop policy if exists "paper_trades_crud_own" on public.paper_trades;
create policy "paper_trades_crud_own" on public.paper_trades
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- signals: users see own; optional global read for marketing — here, own only
drop policy if exists "signals_select_own" on public.signals;
create policy "signals_select_own" on public.signals
  for select using (auth.uid() = user_id or user_id is null);

-- Service role bypasses RLS by default in Supabase.
