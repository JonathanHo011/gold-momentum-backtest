import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

print("Fetching GC=F (Gold Futures) daily data via yfinance...")
gold = yf.download("GC=F", interval="1d", period="3y", auto_adjust=True)

if isinstance(gold.columns, pd.MultiIndex):
    gold.columns = gold.columns.get_level_values(0)

gold = gold.reset_index()
gold = gold.rename(columns={"Date": "open_time", "Close": "close"})
gold["open_time"] = pd.to_datetime(gold["open_time"])
gold = gold.sort_values("open_time").reset_index(drop=True)

print(f"Downloaded {len(gold)} daily candles")
print(f"Period: {gold['open_time'].iloc[0].date()} to {gold['open_time'].iloc[-1].date()}")

gold.to_csv("gold_price_data.csv", index=False)
print("Saved gold_price_data.csv")

gold["MA20"]  = gold["close"].rolling(window=20).mean()
gold["MA200"] = gold["close"].rolling(window=200).mean()
gold["signal"] = np.where(gold["MA20"] > gold["MA200"], 1, -1)
gold["crossover"] = gold["signal"].diff()

df_valid = gold.dropna(subset=["MA200"]).reset_index(drop=True)
print(f"Backtest period (after MA200 warmup): {df_valid['open_time'].iloc[0].date()} to {df_valid['open_time'].iloc[-1].date()}")

initial_capital = 100_000.0
capital = initial_capital
position = 0
entry_price = 0.0
trades = []

price_series  = df_valid["close"].values
signal_series = df_valid["signal"].values
equity_curve  = [capital]
date_index    = [df_valid["open_time"].iloc[0]]

for i in range(1, len(df_valid)):
    price       = price_series[i]
    signal      = signal_series[i]
    prev_signal = signal_series[i - 1]

    if signal == 1 and prev_signal == -1:
        position   = 1
        entry_price = price
    elif signal == -1 and prev_signal == 1:
        position   = -1
        entry_price = price

    if prev_signal != signal and position != 0:
        if position == 1:
            pnl = (price - entry_price) / entry_price
            trades.append({"type": "LONG", "entry": entry_price, "exit": price, "pnl": pnl})
        else:
            pnl = (entry_price - price) / entry_price
            trades.append({"type": "SHORT", "entry": entry_price, "exit": price, "pnl": pnl})
        capital   = capital * (1 + pnl)
        position  = 0
        entry_price = 0.0

    equity_curve.append(capital)
    date_index.append(df_valid["open_time"].iloc[i])

if position != 0:
    final_price = price_series[-1]
    if position == 1:
        pnl = (final_price - entry_price) / entry_price
        trades.append({"type": "LONG (closed)", "entry": entry_price, "exit": final_price, "pnl": pnl})
    else:
        pnl = (entry_price - final_price) / entry_price
        trades.append({"type": "SHORT (closed)", "entry": entry_price, "exit": final_price, "pnl": pnl})
    capital = capital * (1 + pnl)
    equity_curve[-1] = capital

if trades:
    trade_df = pd.DataFrame(trades)
    winners = trade_df[trade_df["pnl"] > 0]
    losers  = trade_df[trade_df["pnl"] <= 0]
    win_rate     = len(winners) / len(trades) * 100
    avg_win      = winners["pnl"].mean() * 100 if len(winners) > 0 else 0
    avg_loss     = losers["pnl"].mean() * 100  if len(losers)  > 0 else 0
    avg_trade    = trade_df["pnl"].mean() * 100
    max_dd       = min(equity_curve) / max(equity_curve)
    max_drawdown = (1 - max_dd) * 100 if max_dd > 0 else 0
else:
    win_rate = avg_win = avg_loss = avg_trade = max_drawdown = 0

bh_start   = price_series[0]
bh_return  = (price_series[-1] - bh_start) / bh_start * 100
strat_ret  = (capital - initial_capital) / initial_capital * 100
total_days = (df_valid["open_time"].iloc[-1] - df_valid["open_time"].iloc[0]).days
years      = total_days / 365.25
ann_ret    = ((capital / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
ann_vol    = np.std(pd.DataFrame(trades)["pnl"].values) * np.sqrt(252) * 100 if len(trades) > 1 else 0
sharpe     = ann_ret / ann_vol if ann_vol > 0 else 0
last_ma20  = df_valid["MA20"].iloc[-1]
last_ma200 = df_valid["MA200"].iloc[-1]
last_price = price_series[-1]
live_sig   = "LONG" if last_ma20 > last_ma200 else "SHORT"

print()
print("=======================================================")
print("  GOLD (GC=F) MA20/MA200 MOMENTUM BACKTEST")
print("=======================================================")
print(f"  Backtest period   : {df_valid['open_time'].iloc[0].date()} to {df_valid['open_time'].iloc[-1].date()}")
print(f"  Strategy return   : {strat_ret:+.2f}%")
print(f"  Buy&Hold return  : {bh_return:+.2f}%")
print(f"  Annualised return: {ann_ret:+.2f}%")
print(f"  Sharpe ratio     : {sharpe:.3f}")
print(f"  Max drawdown     : -{max_drawdown:.2f}%")
print(f"  Total trades     : {len(trades)}")
print(f"  Win rate         : {win_rate:.1f}%")
print(f"  Avg trade PnL    : {avg_trade:+.3f}%")
print(f"  Avg win          : {avg_win:+.3f}%")
print(f"  Avg loss         : {avg_loss:+.3f}%")
print()
print(f"  LAST PRICE       : ${last_price:.2f}")
print(f"  MA20             : ${last_ma20:.2f}")
print(f"  MA200            : ${last_ma200:.2f}")
print(f"  LIVE SIGNAL      : {live_sig}")
print("=======================================================")

if trades:
    print()
    print("  TRADE LOG:")
    for t in trades:
        tag = "BUY" if t["pnl"] > 0 else "SELL"
        print(f"  {tag}  Entry: ${t['entry']:,.2f}  Exit: ${t['exit']:,.2f}  PnL: {t['pnl']*100:+.2f}%")

fig, axes = plt.subplots(3, 1, figsize=(16, 12), facecolor="#0d1117")
fig.suptitle("Gold (GC=F) MA20/MA200 Momentum Backtest", fontsize=16, fontweight="bold", color="white", y=0.98)
c = {"bg": "#0d1117", "gold": "#f5c842", "ma20": "#4fc3f7", "ma200": "#ef5350", "equity": "#81c784", "text": "#c9d1d9"}

ax1 = axes[0]
ax1.set_facecolor(c["bg"])
ax1.plot(df_valid["open_time"], df_valid["MA20"],  color=c["ma20"],  lw=1.2, label="MA20",  alpha=0.9)
ax1.plot(df_valid["open_time"], df_valid["MA200"], color=c["ma200"], lw=1.5, label="MA200", alpha=0.9)
ax1.plot(df_valid["open_time"], df_valid["close"], color=c["gold"], lw=0.8, label="GC=F", alpha=0.6)
buys  = df_valid[df_valid["crossover"] ==  2]
sells = df_valid[df_valid["crossover"] == -2]
ax1.scatter(buys["open_time"],  buys["close"],  marker="^", color="#00e676", s=120, label="BUY",  zorder=5, edgecolors="white", linewidths=0.5)
ax1.scatter(sells["open_time"], sells["close"], marker="v", color="#ff1744", s=120, label="SELL", zorder=5, edgecolors="white", linewidths=0.5)
ax1.set_ylabel("Price (USD)", color=c["text"], fontsize=11)
ax1.tick_params(colors=c["text"])
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax1.legend(loc="upper left", framealpha=0.1, labelcolor=c["text"])
ax1.grid(True, alpha=0.1, color=c["text"])

ax2 = axes[1]
ax2.set_facecolor(c["bg"])
ax2.plot(date_index, equity_curve, color=c["equity"], lw=1.5, label="Strategy")
bh_equity = [initial_capital * (p / bh_start) for p in price_series]
ax2.plot(date_index, bh_equity, color=c["gold"], lw=1.2, linestyle="--", label="Buy & Hold", alpha=0.7)
ax2.axhline(initial_capital, color="white", lw=0.5, alpha=0.3)
ax2.set_ylabel("Portfolio Value (USD)", color=c["text"], fontsize=11)
ax2.tick_params(colors=c["text"])
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax2.legend(loc="upper left", framealpha=0.1, labelcolor=c["text"])
ax2.grid(True, alpha=0.1, color=c["text"])

ax3 = axes[2]
ax3.set_facecolor(c["bg"])
strat_cum = [(v / initial_capital - 1) * 100 for v in equity_curve]
bh_cum    = [(v / initial_capital - 1) * 100 for v in bh_equity]
ax3.plot(date_index, strat_cum, color=c["equity"], lw=1.5, label="Strategy")
ax3.plot(date_index, bh_cum,    color=c["gold"],  lw=1.2, linestyle="--", label="Buy & Hold", alpha=0.7)
ax3.axhline(0, color="white", lw=0.5, alpha=0.3)
ax3.fill_between(date_index, strat_cum, 0, where=[s > 0 for s in strat_cum], color="#00e676", alpha=0.15)
ax3.fill_between(date_index, strat_cum, 0, where=[s <= 0 for s in strat_cum], color="#ff1744", alpha=0.15)
ax3.set_ylabel("Cumulative Return (%)", color=c["text"], fontsize=11)
ax3.tick_params(colors=c["text"])
ax3.grid(True, alpha=0.1, color=c["text"])
ax3.legend(loc="upper left", framealpha=0.1, labelcolor=c["text"])

for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.tick_params(colors=c["text"])
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig("gold_backtest_complete.png", dpi=150, bbox_inches="tight", facecolor=c["bg"], edgecolor="none")
print()
print("Saved gold_backtest_complete.png")
plt.close()