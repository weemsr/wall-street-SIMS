# Wall Street War Room

A single-player portfolio-management roguelike game. Manage a $1M portfolio across 5 sectors over a 26-week season, reacting to macro regime shifts and shock events.

## Quick Start

```bash
cd "/Users/macpro/Desktop/SIMS Wallstreet"

# Create virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install ".[dev]"

# Play a full 26-week season
python -m wallstreet

# Quick 3-week test game with a fixed seed
python -m wallstreet --weeks 3 --seed 42

# Play with a custom name
python -m wallstreet --name "Gordon Gekko" --seed 100

# List saved games
python -m wallstreet --list-games
```

## How to Play

Each week you:
1. See the current macro environment (regime, rates, volatility)
2. See any shock events that occurred
3. Review your portfolio status
4. Choose your allocation across 5 sectors (must sum to 100%)
5. Receive a Risk Committee assessment
6. See your weekly results

After 26 weeks, you receive a final scorecard with:
- **CAGR** (annualized return)
- **Max Drawdown** (worst peak-to-trough decline)
- **Annualized Volatility**
- **Sharpe Ratio** (risk-adjusted return)
- **Letter Grade** (A+ through F)

## Sectors

| Sector | Style |
|--------|-------|
| Tech | High growth, rate-sensitive |
| Energy | Commodity-driven, volatile |
| Financials | Rate-sensitive, cyclical |
| Consumer | Defensive, lower volatility |
| Industrials | Cyclical, trade-sensitive |

## Macro Regimes

The economy transitions between **Bull**, **Bear**, **Recession**, and **Recovery** states via a Markov chain. Interest rates can be **Rising**, **Stable**, or **Falling**. Volatility ranges from **Low** to **Crisis**.

## Running Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Project Structure

```
src/wallstreet/
  models/       # Pydantic data models
  market_engine/ # Regime transitions, return generation
  event_engine/  # Shock events with narratives
  scoring/       # Performance metrics
  agents/        # Risk Committee (rules-based, swappable to LLM)
  persistence/   # SQLite storage
  cli/           # Rich terminal UI
```
