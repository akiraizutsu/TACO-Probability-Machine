# TACO Probability Machine

**Trump Always Chickens Out** — A satirical dashboard tracking anomalous trading patterns observed before major U.S. policy reversals and geopolitical announcements (2025-2026).

Live: [akiraizutsu.github.io/taco-probability-machine](https://akiraizutsu.github.io/taco-probability-machine/)

## Background

Between April 2025 and April 2026, a series of high-profile U.S. policy announcements were preceded by statistically unusual trading activity across equities, derivatives, commodities, and prediction markets. In several cases, newly created accounts on decentralized platforms executed large, precisely timed bets minutes before public announcements, generating significant profits.

This dashboard aggregates publicly available data from these incidents into a single interface for research and commentary purposes.

## Tracked Events

| Date | Event | Pre-signal Window | Estimated Profit | Score |
|------|-------|-------------------|-----------------|-------|
| 2025-04-09 | 90-day tariff pause | 18 min | $30M+ | 95 |
| 2025-10-10 | China 100% tariff (rare earth retaliation) | 30 min | $160M | 88 |
| 2026-01-03 | Venezuela — Maduro detention | Hours | $400K | 82 |
| 2026-02-28 | Iran strikes commenced | 6 days (crypto prep) | $2M+ | 91 |
| 2026-03-23 | Iran energy facility strike postponement | 15 min | est. $760M volume | 97 |
| 2026-04-07 | U.S.–Iran ceasefire announcement | Minutes | $72K-$200K per acct | 96 |

## Features

### Anomaly Score Gauge
Composite score (0-100) derived from pre-announcement signal timing, abnormal volume ratios, estimated profit scale, new account surges, and cross-market correlation. Rendered with spring-physics animation (requestAnimationFrame with damped oscillation).

### TACO Probability Simulator
Interactive tool allowing users to adjust four market indicators and compute a hypothetical anomaly score in real-time:

- **VIX Index** (weight: 25%) — Market fear gauge
- **Put/Call Ratio** (weight: 20%) — Options sentiment
- **Abnormal Options Volume Multiplier** (weight: 35%) — Deviation from baseline
- **Polymarket New Accounts** (weight: 20%) — Prediction market activity spike

### Event Timeline
Horizontal scrollable timeline plotting events chronologically. Node size scales with anomaly score. Click-to-expand interaction links timeline nodes to detailed signal cards below.

### Signal Detail Cards
Expandable cards per event showing granular anomaly indicators (pre-signal timing, position sizes, platform, price movements, account patterns). Filterable by category: tariff, military, geopolitical.

## Scoring Methodology

Each event is scored on a 0-100 scale based on five factors:

1. **Signal timing** — Shorter pre-announcement windows score higher (18 minutes > 6 days)
2. **Volume anomaly** — Ratio of observed volume to historical baseline
3. **Profit concentration** — Estimated returns relative to position size
4. **Account novelty** — Proportion of newly created or single-use accounts
5. **Cross-market correlation** — Simultaneous anomalies across asset classes

Scores are editorial assessments informed by quantitative data, not algorithmic outputs. They reflect the combined severity and specificity of observed anomalies.

## Data Sources

All data is derived from publicly available sources:

- **Market data**: LSEG, Dow Jones Market Data, Unusual Whales
- **Regulatory filings**: SEC EDGAR
- **Blockchain analytics**: Dune Analytics, Polymarket on-chain transaction data
- **Reporting**: Reuters, Financial Times, NPR, ProPublica, Al Jazeera

No proprietary data or non-public information was used.

## Technical Details

- Single HTML file (~1,200 lines), zero build step
- No external JavaScript dependencies
- External dependency: Google Fonts (Space Mono, Outfit, Zen Kaku Gothic New)
- Hosted on GitHub Pages as a static site
- Animation: requestAnimationFrame with spring physics (damped harmonic oscillator)
- Responsive design with mobile breakpoints

## Disclaimer

This is satirical commentary based on public market data. It is not a trading tool, financial advice, or accusation of wrongdoing. The presence of anomalous trading patterns does not, by itself, establish illegal activity. Correlation in timing does not prove causation or coordination.

If you are engaged in insider trading, this dashboard is redundant — you already know.

## License

MIT
