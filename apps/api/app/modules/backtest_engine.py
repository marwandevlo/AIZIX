"""Synthetic and Binance OHLC backtests: structured metrics, drawdown series, SL/TP grid optimization."""

from __future__ import annotations

import random
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from app.modules.market_engine import underlying_symbol_for_pair

ObjectiveName = Literal["total_return", "return_over_drawdown", "profit_factor"]


class TradeStats(BaseModel):
    closed: int = Field(ge=0)
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    gross_profit_usd: float = 0.0
    gross_loss_usd: float = 0.0


class PerformanceBlock(BaseModel):
    total_return_pct: float
    win_rate_pct: float
    profit_factor: float
    max_drawdown_pct: float
    trades: TradeStats


class SeriesBlock(BaseModel):
    equity: list[float]
    drawdown_pct: list[float]
    bar_count: int


class OptimizationCandidate(BaseModel):
    rank: int
    sl_pct: float
    tp_pct: float
    objective_score: float
    total_return_pct: float
    max_drawdown_pct: float
    profit_factor: float
    win_rate_pct: float


class OptimizationBlock(BaseModel):
    method: str = "grid_search"
    objective: ObjectiveName
    grid_size: int
    best: OptimizationCandidate
    leaderboard: list[OptimizationCandidate] = Field(default_factory=list)


class BacktestStructured(BaseModel):
    schema_version: int = 2
    source: Literal["synthetic", "binance"]
    pair: str
    symbol: str | None = None
    inputs: dict[str, Any]
    performance: PerformanceBlock
    series: SeriesBlock
    optimization: OptimizationBlock


def _downsample(seq: list[float], max_points: int = 150) -> list[float]:
    if len(seq) <= max_points:
        return list(seq)
    step = max(1, len(seq) // max_points)
    return seq[::step]


def _downsample_equity_dd(
    equity: list[float], dd_pct: list[float], *, max_points: int = 150
) -> tuple[list[float], list[float]]:
    if len(equity) <= max_points:
        return list(equity), list(dd_pct[: len(equity)])
    step = max(1, len(equity) // max_points)
    eq_ds = equity[::step]
    dd_ds = dd_pct[::step]
    n = min(len(eq_ds), len(dd_ds))
    return eq_ds[:n], dd_ds[:n]


def _drawdown_from_equity(equity: list[float]) -> tuple[list[float], float]:
    if not equity:
        return [], 0.0
    peak = equity[0]
    curve: list[float] = []
    max_dd = 0.0
    for e in equity:
        peak = max(peak, e)
        dd = (peak - e) / peak * 100 if peak > 1e-12 else 0.0
        curve.append(round(dd, 4))
        max_dd = max(max_dd, dd)
    return curve, max_dd


def _profit_factor_from_gross(gross_profit: float, gross_loss: float) -> float:
    if gross_loss > 1e-9:
        return gross_profit / gross_loss
    return 999.999 if gross_profit > 1e-9 else 0.0


def _objective_score(
    ret_pct: float,
    max_dd: float,
    pf: float,
    *,
    objective: ObjectiveName,
) -> float:
    if objective == "total_return":
        return ret_pct
    if objective == "return_over_drawdown":
        return ret_pct / max(max_dd, 0.25)
    return pf * 100.0 + ret_pct * 0.01


def _simulate_equity(
    *,
    rng: random.Random,
    sl_pct: float,
    tp_pct: float,
    days: int,
) -> tuple[list[float], float, float, float, int, int, float, float, float]:
    sl_pct = max(0.2, min(sl_pct, 12.0))
    tp_pct = max(0.3, min(tp_pct, 25.0))
    equity: list[float] = [10_000.0]
    wins = losses = 0
    gross_win = gross_loss = 0.0

    for _ in range(days):
        daily_ret = rng.gauss(0.0008, 0.018)
        shock = (
            -sl_pct / 100
            if rng.random() < 0.22
            else (tp_pct / 100 if rng.random() < 0.38 else daily_ret)
        )
        last = equity[-1]
        nxt = max(500.0, last * (1.0 + shock))
        equity.append(round(nxt, 2))
        delta = nxt - last
        if shock >= tp_pct / 200:
            wins += 1
            if delta > 0:
                gross_win += delta
        elif shock <= -sl_pct / 200:
            losses += 1
            if delta < 0:
                gross_loss += abs(delta)

    dd_curve, max_dd = _drawdown_from_equity(equity)
    total_ret_pct = (equity[-1] / equity[0] - 1.0) * 100
    pf = _profit_factor_from_gross(gross_win, gross_loss)
    denom = wins + losses or 1
    win_rate = 100.0 * wins / denom
    return equity, total_ret_pct, win_rate, pf, wins, losses, max_dd, gross_win, gross_loss


def _equity_from_ohlc(
    ohlc: list[tuple[float, float, float, float]],
    *,
    sl_pct: float,
    tp_pct: float,
) -> tuple[list[float], float, float, float, int, int, float, float]:
    sl_pct = max(0.2, min(sl_pct, 12.0))
    tp_pct = max(0.3, min(tp_pct, 25.0))
    cash = 10_000.0
    qty = 0.0
    entry = 0.0
    equity_curve: list[float] = []
    wins = losses = 0
    gross_win = gross_loss = 0.0

    for i in range(1, len(ohlc)):
        o, h, l, c = ohlc[i]
        prev_o, _prev_h, _prev_l, prev_c = ohlc[i - 1]
        mom = (prev_c - prev_o) / prev_o * 100 if prev_o > 0 else 0.0

        if qty > 0:
            sl_px = entry * (1 - sl_pct / 100)
            tp_px = entry * (1 + tp_pct / 100)
            exit_px: float | None = None
            if l <= sl_px:
                exit_px = sl_px
            elif h >= tp_px:
                exit_px = tp_px
            if exit_px is not None:
                pnl_usd = qty * (exit_px - entry)
                cash = qty * exit_px
                if pnl_usd >= 0:
                    wins += 1
                    gross_win += pnl_usd
                else:
                    losses += 1
                    gross_loss += abs(pnl_usd)
                qty = 0.0
                entry = 0.0

        if qty == 0 and cash > 1.0 and mom > 0.06:
            qty = cash / o
            entry = o
            cash = 0.0

        equity = cash + qty * c
        equity_curve.append(round(equity, 2))

    _, max_dd = _drawdown_from_equity(equity_curve)
    total_ret_pct = (
        (equity_curve[-1] / equity_curve[0] - 1.0) * 100 if len(equity_curve) > 1 else 0.0
    )
    denom = wins + losses or 1
    win_rate = 100.0 * wins / denom
    return equity_curve, total_ret_pct, win_rate, max_dd, wins, losses, gross_win, gross_loss


def _optimize_grid_ohlc(
    ohlc: list[tuple[float, float, float, float]],
    *,
    objective: ObjectiveName,
    sl_grid: list[float] | None = None,
    tp_grid: list[float] | None = None,
    top_k: int = 15,
) -> OptimizationBlock:
    sl_vals = sl_grid or [round(1.0 + 0.5 * i, 2) for i in range(0, 10)]  # 1.0 .. 5.5
    tp_vals = tp_grid or [round(2.0 + 0.5 * i, 2) for i in range(0, 15)]  # 2.0 .. 9.0
    evaluations: list[tuple[float, float, float, float, float, float, float, int, int]] = []

    for s in sl_vals:
        for t in tp_vals:
            if t <= s + 0.05:
                continue
            eq, ret_pct, wr, mdd, wn, ls, gw, gl = _equity_from_ohlc(ohlc, sl_pct=s, tp_pct=t)
            pf = _profit_factor_from_gross(gw, gl)
            score = _objective_score(ret_pct, mdd, pf, objective=objective)
            evaluations.append((score, s, t, ret_pct, mdd, pf, wr, wn, ls))

    evaluations.sort(key=lambda x: x[0], reverse=True)
    grid_size = len(evaluations)
    if not evaluations:
        placeholder = OptimizationCandidate(
            rank=1,
            sl_pct=2.0,
            tp_pct=4.0,
            objective_score=0.0,
            total_return_pct=0.0,
            max_drawdown_pct=0.0,
            profit_factor=0.0,
            win_rate_pct=0.0,
        )
        return OptimizationBlock(
            objective=objective,
            grid_size=0,
            best=placeholder,
            leaderboard=[],
        )

    best_row = evaluations[0]
    leaderboard: list[OptimizationCandidate] = []
    for idx, row in enumerate(evaluations[: max(top_k, 1)], start=1):
        _, s, t, ret_pct, mdd, pf, wr, wn, ls = row
        leaderboard.append(
            OptimizationCandidate(
                rank=idx,
                sl_pct=s,
                tp_pct=t,
                objective_score=round(row[0], 6),
                total_return_pct=round(ret_pct, 4),
                max_drawdown_pct=round(mdd, 4),
                profit_factor=round(pf, 4),
                win_rate_pct=round(wr, 2),
            )
        )

    _sc0, bs, bt, br, bm, bpf, bwr, _bwn, _bls = best_row
    best = OptimizationCandidate(
        rank=1,
        sl_pct=bs,
        tp_pct=bt,
        objective_score=round(best_row[0], 6),
        total_return_pct=round(br, 4),
        max_drawdown_pct=round(bm, 4),
        profit_factor=round(bpf, 4),
        win_rate_pct=round(bwr, 2),
    )

    return OptimizationBlock(
        objective=objective,
        grid_size=grid_size,
        best=best,
        leaderboard=leaderboard,
    )


def _optimize_grid_synthetic(
    *,
    rng_base: random.Random,
    pair: str,
    days: int,
    objective: ObjectiveName,
    sl_grid: list[float] | None = None,
    tp_grid: list[float] | None = None,
    top_k: int = 15,
) -> OptimizationBlock:
    sl_vals = sl_grid or [round(1.0 + 0.5 * i, 2) for i in range(0, 10)]
    tp_vals = tp_grid or [round(2.0 + 0.5 * i, 2) for i in range(0, 15)]
    evaluations: list[tuple[float, float, float, float, float, float, float, int, int]] = []

    for s in sl_vals:
        for t in tp_vals:
            if t <= s + 0.05:
                continue
            seed = rng_base.randint(0, 2**30) ^ (abs(hash((pair, s, t))) % (2**31))
            r = random.Random(seed)
            eq, ret_pct, wr, pf, wn, ls, mdd, gw, gl = _simulate_equity(
                rng=r, sl_pct=s, tp_pct=t, days=days
            )
            score = _objective_score(ret_pct, mdd, pf, objective=objective)
            evaluations.append((score, s, t, ret_pct, mdd, pf, wr, wn, ls))

    evaluations.sort(key=lambda x: x[0], reverse=True)
    grid_size = len(evaluations)
    if not evaluations:
        ph = OptimizationCandidate(
            rank=1,
            sl_pct=2.0,
            tp_pct=4.0,
            objective_score=0.0,
            total_return_pct=0.0,
            max_drawdown_pct=0.0,
            profit_factor=0.0,
            win_rate_pct=0.0,
        )
        return OptimizationBlock(objective=objective, grid_size=0, best=ph, leaderboard=[])

    leaderboard = []
    for idx, row in enumerate(evaluations[: max(top_k, 1)], start=1):
        sc, s, t, ret_pct, mdd, pf, wr, wn, ls = row
        leaderboard.append(
            OptimizationCandidate(
                rank=idx,
                sl_pct=s,
                tp_pct=t,
                objective_score=round(sc, 6),
                total_return_pct=round(ret_pct, 4),
                max_drawdown_pct=round(mdd, 4),
                profit_factor=round(pf, 4),
                win_rate_pct=round(wr, 2),
            )
        )
    best_row = evaluations[0]
    sc, bs, bt, br, bm, bpf, bwr, bwn, bls = best_row
    best = OptimizationCandidate(
        rank=1,
        sl_pct=bs,
        tp_pct=bt,
        objective_score=round(sc, 6),
        total_return_pct=round(br, 4),
        max_drawdown_pct=round(bm, 4),
        profit_factor=round(bpf, 4),
        win_rate_pct=round(bwr, 2),
    )
    return OptimizationBlock(
        objective=objective,
        grid_size=grid_size,
        best=best,
        leaderboard=leaderboard,
    )


def _hourly_klines(*, symbol: str, limit: int, base_url: str) -> list[list[Any]]:
    limit = max(10, min(1000, limit))
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=30.0) as client:
        r = client.get(
            "/api/v3/klines",
            params={"symbol": symbol, "interval": "1h", "limit": limit},
        )
        r.raise_for_status()
        return r.json()


def _build_performance(
    *,
    equity: list[float],
    total_ret_pct: float,
    win_rate: float,
    pf: float,
    max_dd: float,
    wins: int,
    losses: int,
    gross_win: float,
    gross_loss: float,
) -> PerformanceBlock:
    return PerformanceBlock(
        total_return_pct=round(total_ret_pct, 4),
        win_rate_pct=round(win_rate, 2),
        profit_factor=round(pf, 4),
        max_drawdown_pct=round(max_dd, 4),
        trades=TradeStats(
            closed=wins + losses,
            wins=wins,
            losses=losses,
            gross_profit_usd=round(gross_win, 4),
            gross_loss_usd=round(gross_loss, 4),
        ),
    )


def run_backtest(
    *,
    pair: str,
    sl_pct: float,
    tp_pct: float,
    days: int = 42,
    seed: int | None = None,
    objective: ObjectiveName = "return_over_drawdown",
) -> dict[str, Any]:
    rng = random.Random((seed or 0) ^ (abs(hash(pair)) % (2**31)))
    days = max(10, min(days, 365))

    equity, total_ret_pct, win_rate, pf, wins, losses, max_dd, gw, gl = _simulate_equity(
        rng=rng, sl_pct=sl_pct, tp_pct=tp_pct, days=days
    )
    dd_curve, _ = _drawdown_from_equity(equity)

    opt = _optimize_grid_synthetic(
        rng_base=rng, pair=pair, days=days, objective=objective
    )

    perf = _build_performance(
        equity=equity,
        total_ret_pct=total_ret_pct,
        win_rate=win_rate,
        pf=pf,
        max_dd=max_dd,
        wins=wins,
        losses=losses,
        gross_win=gw,
        gross_loss=gl,
    )

    eq_ds, dd_ds = _downsample_equity_dd(equity, dd_curve)

    structured = BacktestStructured(
        source="synthetic",
        pair=pair,
        symbol=None,
        inputs={"sl_pct": sl_pct, "tp_pct": tp_pct, "days": days, "seed": seed},
        performance=perf,
        series=SeriesBlock(equity=eq_ds, drawdown_pct=dd_ds, bar_count=len(equity)),
        optimization=opt,
    )

    nested = structured.model_dump()
    out = {
        "structured": nested,
        "pair": pair,
        "equity_curve": eq_ds,
        "drawdown_pct_curve": dd_ds,
        "performance": nested["performance"],
        "optimization": nested["optimization"],
        "total_return_pct": perf.total_return_pct,
        "win_rate_pct": perf.win_rate_pct,
        "profit_factor": perf.profit_factor,
        "max_drawdown_pct": perf.max_drawdown_pct,
        "days": days,
        "sl_pct_used": sl_pct,
        "tp_pct_used": tp_pct,
        "recommended_sl_pct": opt.best.sl_pct,
        "recommended_tp_pct": opt.best.tp_pct,
        "optimization_objective": objective,
        "note": "Synthetic daily-style path — not venue history.",
    }
    return out


def run_backtest_binance(
    *,
    pair: str,
    sl_pct: float,
    tp_pct: float,
    days: int = 42,
    base_url: str = "https://api.binance.com",
    objective: ObjectiveName = "return_over_drawdown",
) -> dict[str, Any]:
    symbol = underlying_symbol_for_pair(pair)
    limit = min(1000, max(24, days * 24))
    raw = _hourly_klines(symbol=symbol, limit=limit, base_url=base_url)
    ohlc = [(float(x[1]), float(x[2]), float(x[3]), float(x[4])) for x in raw]

    equity, total_ret_pct, win_rate, max_dd, wins, losses, gw, gl = _equity_from_ohlc(
        ohlc, sl_pct=sl_pct, tp_pct=tp_pct
    )
    dd_curve, max_dd_series = _drawdown_from_equity(equity)
    max_dd = max(max_dd, max_dd_series)
    pf = _profit_factor_from_gross(gw, gl)

    opt = _optimize_grid_ohlc(ohlc, objective=objective)

    perf = _build_performance(
        equity=equity,
        total_ret_pct=total_ret_pct,
        win_rate=win_rate,
        pf=pf,
        max_dd=max_dd,
        wins=wins,
        losses=losses,
        gross_win=gw,
        gross_loss=gl,
    )

    eq_ds, dd_ds = _downsample_equity_dd(equity, dd_curve)

    structured = BacktestStructured(
        source="binance",
        pair=pair,
        symbol=symbol,
        inputs={"sl_pct": sl_pct, "tp_pct": tp_pct, "days_requested": days, "bars": len(equity)},
        performance=perf,
        series=SeriesBlock(equity=eq_ds, drawdown_pct=dd_ds, bar_count=len(equity)),
        optimization=opt,
    )

    nested = structured.model_dump()
    return {
        "structured": nested,
        "pair": pair,
        "symbol": symbol,
        "equity_curve": eq_ds,
        "drawdown_pct_curve": dd_ds,
        "performance": nested["performance"],
        "optimization": nested["optimization"],
        "total_return_pct": perf.total_return_pct,
        "win_rate_pct": perf.win_rate_pct,
        "profit_factor": perf.profit_factor,
        "max_drawdown_pct": perf.max_drawdown_pct,
        "days": days,
        "sl_pct_used": sl_pct,
        "tp_pct_used": tp_pct,
        "bars": len(equity),
        "recommended_sl_pct": opt.best.sl_pct,
        "recommended_tp_pct": opt.best.tp_pct,
        "optimization_objective": objective,
        "note": "Hourly Binance spot bars — long-only toy execution model.",
    }


def compare_backtests_binance(
    *,
    configs: list[dict[str, Any]],
    days: int,
    base_url: str,
    objective: ObjectiveName = "return_over_drawdown",
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for cfg in configs:
        pair = str(cfg.get("pair", "BTC3L/USDT"))
        sl_pct = float(cfg.get("sl_pct", 2.0))
        tp_pct = float(cfg.get("tp_pct", 4.0))
        try:
            res = run_backtest_binance(
                pair=pair,
                sl_pct=sl_pct,
                tp_pct=tp_pct,
                days=days,
                base_url=base_url,
                objective=objective,
            )
            rows.append(
                {
                    "label": cfg.get("label") or pair,
                    "pair": pair,
                    "performance": res["performance"],
                    "total_return_pct": res["total_return_pct"],
                    "max_drawdown_pct": res["max_drawdown_pct"],
                    "win_rate_pct": res["win_rate_pct"],
                    "profit_factor": res["profit_factor"],
                    "recommended_sl_pct": res["recommended_sl_pct"],
                    "recommended_tp_pct": res["recommended_tp_pct"],
                    "equity_curve": res["equity_curve"],
                    "drawdown_pct_curve": res.get("drawdown_pct_curve"),
                    "optimization": res["optimization"],
                }
            )
        except httpx.HTTPError as e:
            rows.append({"label": cfg.get("label") or pair, "error": str(e)})

    ranked = sorted(
        [r for r in rows if "total_return_pct" in r],
        key=lambda r: r["total_return_pct"],
        reverse=True,
    )
    best = ranked[0] if ranked else None
    return {"days": days, "objective": objective, "results": rows, "best": best}


def compare_backtests_synthetic(
    *,
    configs: list[dict[str, Any]],
    days: int,
    objective: ObjectiveName = "return_over_drawdown",
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for cfg in configs:
        pair = str(cfg.get("pair", "BTC3L/USDT"))
        sl_pct = float(cfg.get("sl_pct", 2.0))
        tp_pct = float(cfg.get("tp_pct", 4.0))
        res = run_backtest(
            pair=pair, sl_pct=sl_pct, tp_pct=tp_pct, days=days, objective=objective
        )
        rows.append(
            {
                "label": cfg.get("label") or pair,
                "pair": pair,
                "performance": res["performance"],
                "total_return_pct": res["total_return_pct"],
                "max_drawdown_pct": res["max_drawdown_pct"],
                "win_rate_pct": res["win_rate_pct"],
                "profit_factor": res["profit_factor"],
                "recommended_sl_pct": res["recommended_sl_pct"],
                "recommended_tp_pct": res["recommended_tp_pct"],
                "equity_curve": res["equity_curve"],
                "drawdown_pct_curve": res.get("drawdown_pct_curve"),
                "optimization": res["optimization"],
            }
        )
    ranked = sorted(rows, key=lambda r: r["total_return_pct"], reverse=True)
    return {"days": days, "objective": objective, "results": rows, "best": ranked[0] if ranked else None}
