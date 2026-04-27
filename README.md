# Simple Trading Simulator

A front-office prototype built in Python that fetches **live crypto prices** from the
CoinGecko public API, simulates buy/sell orders, and persists your portfolio between
sessions using a local JSON file.

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python      | 3.10 +  |
| pip         | any     |

---

## Installation

```bash
# 1 – Clone / unzip the project and enter the folder
cd Trading-Simulator

# 2 – (Optional but recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows

# 3 – Install the only external dependency
pip install requests
```

---

## Running the simulator

```bash
python trading_simulator.py
```

On first launch the script will:

1. **Fetch live prices** for Bitcoin, Ethereum and Solana from CoinGecko and print the raw API response.
2. **Create `portfolio.json`** with an initial cash balance of **$10 000**.
3. **Display your portfolio summary** (positions, market values, PnL).
4. **Open an interactive menu** so you can trade manually.

---

## Interactive menu

```
┌─────────────────────────────┐
│     TRADING SIMULATOR MENU  │
├─────────────────────────────┤
│  1 – Refresh prices         │
│  2 – Buy crypto             │
│  3 – Sell crypto            │
│  4 – Portfolio summary      │
│  5 – Save & quit            │
└─────────────────────────────┘
```

* Options **2** and **3** prompt you for the coin name (`bitcoin`, `ethereum`, `solana`)
  and the quantity.
* Prices are refreshed live on option **1**.
* Option **5** saves the portfolio to `portfolio.json` and exits.

---

## Project structure

```
tp1_trading_simulator/
├── trading_simulator.py   ← main script
├── README.md              ← this file
└── portfolio.json         ← auto-created on first run
```

---

## portfolio.json format

```json
{
  "cash": 9500.00,
  "positions": {
    "bitcoin": { "qty": 0.005, "avg_price": 62000.00 }
  },
  "trades": [
    {
      "type": "BUY",
      "coin": "bitcoin",
      "symbol": "BTC",
      "qty": 0.005,
      "price": 62000.00,
      "total": 310.00,
      "timestamp": "2025-04-21T14:30:00"
    }
  ]
}
```

---

## API used

**CoinGecko Simple Price** (no API key required)

```
GET https://api.coingecko.com/api/v3/simple/price
    ?ids=bitcoin,ethereum,solana
    &vs_currencies=usd
```

---

## Notes

* All prices are in **USD**.
* The simulator assumes **market orders** (execution at the live fetched price).
* PnL is calculated as: `(current_price − average_entry_price) × quantity`.
* There are no trading fees modelled in this prototype.
