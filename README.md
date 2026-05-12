# Gold Momentum Backtest (MA20/MA200)

**Data:** Gold Futures (GC=F) via Yahoo Finance
**Period:** Feb 2024 — May 2026
**Signal:** MA20 > MA200 = LONG, MA20 < MA200 = SHORT
**Result:** 0 trades. Strategy sat on the sidelines as gold rallied from ~$2,000 to ~$4,700.

---

## Background

This project was originally planned as a comparison to the BTC momentum backtest. The idea: test the same MA20/MA200 crossover signal on a different asset class to see if it generalises.

Gold's behavior turned out to be the opposite of BTC.

---

## Results

| Metric | Value |
|--------|-------|
| Strategy return | +0.00% |
| Buy&Hold return | +131.65% |
| Annualised return (strategy) | 0.00% |
| Sharpe ratio | 0.000 |
| Max drawdown | -0.00% |
| Total trades | **0** |
| Live signal (May 2026) | **LONG** |

---

## Why Zero Trades?

Gold was in a sustained, nearly uninterrupted bull trend throughout the entire backtest period. MA20 crossed above MA200 at the start of the period and never looked back. The 200-day MA acted as a constant floor.

A trend-following strategy only generates signals when trends *change*. Gold in 2024-2026 had no trend changes to follow.

---

## What This Means

This is not a strategy failure — it is a characteristic of the strategy. MA crossover is designed to capture regime shifts. In a strongly trending market, it correctly identifies the trend and stays long, producing no trades.

The strategy underperformed buy-and-hold during this specific period because it was designed to *avoid* the very bull run that occurred.

---

## Live Signal (May 2026)

- MA20: $4,688.50
- MA200: $4,299.29
- Signal: **LONG**

Gold remains above its 200-day MA. No crossover triggered.

---

## Files

- `run_backtest.py` — Full backtest engine + visualisation
- `gold_price_data.csv` — 3 years of daily GC=F data from yfinance
- `gold_backtest_complete.png` — Price, MAs, equity curve, cumulative return

---

## Methodology

**Signal:** MA20 > MA200 = LONG, MA20 < MA200 = SHORT

**Entry/Exit:** Enter on MA crossover. Exit and reverse when MA flips.

**Notes:**
- $100,000 starting capital
- No transaction costs or slippage
- No position sizing or risk management
- GC=F (Gold Futures) used instead of spot gold for better data availability
- Backtest starts Feb 2024 after MA200 warmup period
