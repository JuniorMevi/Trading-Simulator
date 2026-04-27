"""
TP1 - Trading Simulator
A simple front-office prototype using live crypto prices from CoinGecko.
"""

import json
import os
import requests
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────

PORTFOLIO_FILE = "portfolio.json"
INITIAL_CASH   = 10_000.0
SUPPORTED_COINS = ["bitcoin", "ethereum", "solana"]

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,ethereum,solana&vs_currencies=usd"
)

COIN_SYMBOLS = {
    "bitcoin":  "BTC",
    "ethereum": "ETH",
    "solana":   "SOL",
}

# ─────────────────────────────────────────────
#  STEP 3 – API
# ─────────────────────────────────────────────

def fetch_prices() -> dict:
    """Fetch live USD prices for BTC, ETH and SOL from CoinGecko."""
    try:
        response = requests.get(COINGECKO_URL, timeout=10)
        response.raise_for_status()
        raw = response.json()

        # Print the raw dictionary (Step 3 requirement)
        print("\n[API] Raw response from CoinGecko:")
        print(raw)

        # Extract prices clearly
        prices = {coin: data["usd"] for coin, data in raw.items()}
        print("\n[API] Extracted prices (USD):")
        for coin, price in prices.items():
            symbol = COIN_SYMBOLS.get(coin, coin.upper())
            print(f"  {symbol:>3} ({coin:<10}) : ${price:>12,.2f}")

        return prices

    except requests.exceptions.RequestException as exc:
        print(f"[ERROR] Could not fetch prices: {exc}")
        return {}


# ─────────────────────────────────────────────
#  STEPS 4  – CREATE A PORTFOLIO STRUCTURE 
# ─────────────────────────────────────────────

def default_portfolio() -> dict:
    """Return the default initial portfolio structure."""
    return {
        "cash":      INITIAL_CASH,
        "positions": {},   # { "bitcoin": {"qty": 0.5, "avg_price": 60000} }
        "trades":    [],   # list of trade records
    }

# ─────────────────────────────────────────────
#  STEPS 5 – SAVE AND LOAD OUR PORTFOLIO STRUCTURE 
# ─────────────────────────────────────────────
def save_portfolio(portfolio: dict) -> None:
    """Save the portfolio dictionary to portfolio.json."""
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)
    print(f"[SAVE] Portfolio saved to {PORTFOLIO_FILE}")


def load_portfolio() -> dict:
    """Load portfolio from portfolio.json, or return default if not found."""
    if not os.path.exists(PORTFOLIO_FILE):
        print("[LOAD] No portfolio file found – starting with default.")
        return default_portfolio()

    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)
    print(f"[LOAD] Portfolio loaded from {PORTFOLIO_FILE}")
    return portfolio


# ─────────────────────────────────────────────
#  STEP 6 – BUY's IMPLEMENTATION
# ─────────────────────────────────────────────

def buy(portfolio: dict, coin: str, qty: float, prices: dict) -> None:
    """Buy `qty` units of `coin` at the current market price."""
    if coin not in prices:
        print(f"[ERROR] No price available for {coin}.")
        return

    price    = prices[coin]
    cost     = price * qty
    symbol   = COIN_SYMBOLS.get(coin, coin.upper())

    if cost > portfolio["cash"]:
        print(f"[BUY ] Insufficient funds. Need ${cost:,.2f} but have ${portfolio['cash']:,.2f}")
        return

    # Deduct cash
    portfolio["cash"] -= cost

    # Update position (weighted average price)
    pos = portfolio["positions"].get(coin, {"qty": 0.0, "avg_price": 0.0})
    total_qty   = pos["qty"] + qty
    avg_price   = (pos["qty"] * pos["avg_price"] + qty * price) / total_qty
    portfolio["positions"][coin] = {"qty": total_qty, "avg_price": avg_price}

    # Record trade
    trade = {
        "type":      "BUY",
        "coin":      coin,
        "symbol":    symbol,
        "qty":       qty,
        "price":     price,
        "total":     cost,
        "timestamp": datetime.utcnow().isoformat(),
    }
    portfolio["trades"].append(trade)

    print(f"[BUY ] {qty} {symbol} @ ${price:,.2f} = ${cost:,.2f} | Cash left: ${portfolio['cash']:,.2f}")

# ─────────────────────────────────────────────
#  STEP 7 – SELL's IMPLEMENTATION
# ─────────────────────────────────────────────

def sell(portfolio: dict, coin: str, qty: float, prices: dict) -> None:
    """Sell `qty` units of `coin` at the current market price."""
    if coin not in prices:
        print(f"[ERROR] No price available for {coin}.")
        return

    pos = portfolio["positions"].get(coin)
    if pos is None or pos["qty"] < qty:
        held = pos["qty"] if pos else 0
        print(f"[SELL] Not enough {coin}. Have {held}, tried to sell {qty}.")
        return

    price    = prices[coin]
    proceeds = price * qty
    symbol   = COIN_SYMBOLS.get(coin, coin.upper())
    pnl      = (price - pos["avg_price"]) * qty

    # Add cash
    portfolio["cash"] += proceeds

    # Update position
    new_qty = pos["qty"] - qty
    if new_qty < 1e-9:
        del portfolio["positions"][coin]
    else:
        portfolio["positions"][coin]["qty"] = new_qty

    # Record trade
    trade = {
        "type":      "SELL",
        "coin":      coin,
        "symbol":    symbol,
        "qty":       qty,
        "price":     price,
        "total":     proceeds,
        "pnl":       pnl,
        "timestamp": datetime.utcnow().isoformat(),
    }
    portfolio["trades"].append(trade)

    pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
    print(f"[SELL] {qty} {symbol} @ ${price:,.2f} = ${proceeds:,.2f} | PnL: {pnl_str} | Cash: ${portfolio['cash']:,.2f}")


# ─────────────────────────────────────────────
#  STEP 7 – PORTFOLIO SUMMARY
# ─────────────────────────────────────────────

def display_summary(portfolio: dict, prices: dict) -> None:
    """Print a formatted portfolio summary in the terminal."""
    width = 60
    sep   = "─" * width

    print(f"\n{'═' * width}")
    print(f"{'PORTFOLIO SUMMARY':^{width}}")
    print(f"{'═' * width}")

    # Cash
    print(f"  {'Cash (USD)':<30} ${portfolio['cash']:>12,.2f}")
    print(sep)

    # Positions
    total_market_value = 0.0
    total_pnl          = 0.0

    if portfolio["positions"]:
        print(f"  {'Coin':<8} {'Qty':>10} {'Avg Cost':>12} {'Mkt Price':>12} {'Mkt Value':>12} {'PnL':>10}")
        print(sep)
        for coin, pos in portfolio["positions"].items():
            symbol  = COIN_SYMBOLS.get(coin, coin.upper())
            qty     = pos["qty"]
            avg     = pos["avg_price"]
            mkt     = prices.get(coin, avg)
            value   = mkt * qty
            pnl     = (mkt - avg) * qty
            total_market_value += value
            total_pnl          += pnl
            pnl_str = f"+{pnl:,.2f}" if pnl >= 0 else f"{pnl:,.2f}"
            print(f"  {symbol:<8} {qty:>10.4f} {avg:>12,.2f} {mkt:>12,.2f} {value:>12,.2f} {pnl_str:>10}")
    else:
        print("  No open positions.")

    print(sep)
    total_equity = portfolio["cash"] + total_market_value
    overall_pnl  = total_equity - INITIAL_CASH
    pnl_tag      = f"+${overall_pnl:,.2f}" if overall_pnl >= 0 else f"-${abs(overall_pnl):,.2f}"

    print(f"  {'Market Value':<30} ${total_market_value:>12,.2f}")
    print(f"  {'Total Equity':<30} ${total_equity:>12,.2f}")
    print(f"  {'Overall PnL vs initial':<30} {pnl_tag:>13}")
    print(f"{'═' * width}")

    # Trade history
    if portfolio["trades"]:
        print(f"\n  Last {min(5, len(portfolio['trades']))} trade(s):")
        print(f"  {'Type':<6} {'Symbol':<5} {'Qty':>8} {'Price':>12} {'Total':>12}  {'Time'}")
        print(sep)
        for t in portfolio["trades"][-5:]:
            print(
                f"  {t['type']:<6} {t['symbol']:<5} {t['qty']:>8.4f} "
                f"{t['price']:>12,.2f} {t['total']:>12,.2f}  {t['timestamp'][:19]}"
            )
    print()


# ─────────────────────────────────────────────
#  INTERACTIVE MENU
# ─────────────────────────────────────────────

def interactive_menu(portfolio: dict, prices: dict) -> None:
    """Simple text-based menu for manual trading."""
    while True:
        print("\n┌─────────────────────────────┐")
        print("|     TRADING SIMULATOR MENU  │")
        print("├─────────────────────────────┤")
        print("│  1 – Refresh prices         │")
        print("│  2 – Buy crypto             │")
        print("│  3 – Sell crypto            │")
        print("│  4 – Portfolio summary      │")
        print("│  5 – Save & quit            │")
        print("└─────────────────────────────┘")
        choice = input("Your choice: ").strip()

        if choice == "1":
            prices.update(fetch_prices())

        elif choice == "2":
            print(f"Available coins: {', '.join(SUPPORTED_COINS)}")
            coin = input("Coin to buy: ").strip().lower()
            if coin not in SUPPORTED_COINS:
                print("[ERROR] Unsupported coin.")
                continue
            try:
                qty = float(input(f"Quantity of {COIN_SYMBOLS.get(coin, coin)} to buy: "))
            except ValueError:
                print("[ERROR] Invalid quantity.")
                continue
            buy(portfolio, coin, qty, prices)

        elif choice == "3":
            print(f"Available coins: {', '.join(SUPPORTED_COINS)}")
            coin = input("Coin to sell: ").strip().lower()
            if coin not in SUPPORTED_COINS:
                print("[ERROR] Unsupported coin.")
                continue
            try:
                qty = float(input(f"Quantity of {COIN_SYMBOLS.get(coin, coin)} to sell: "))
            except ValueError:
                print("[ERROR] Invalid quantity.")
                continue
            sell(portfolio, coin, qty, prices)

        elif choice == "4":
            display_summary(portfolio, prices)

        elif choice == "5":
            save_portfolio(portfolio)
            print("Goodbye!\n")
            break

        else:
            print("[ERROR] Invalid option.")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("       TP1 – SIMPLE TRADING SIMULATOR")
    print("       Powered by CoinGecko live prices")
    print("=" * 60)

    # Step 3 – fetch & display live prices
    prices = fetch_prices()
    if not prices:
        print("[WARN] Prices unavailable – some features may be limited.")

    # Steps 4 & 5 – load portfolio (or create default)
    portfolio = load_portfolio()

    # Step 7 – show summary at startup
    display_summary(portfolio, prices)

    # Demo auto-trades (commented out by default)
    # buy(portfolio,  "bitcoin",  0.01, prices)
    # buy(portfolio,  "ethereum", 0.5,  prices)
    # sell(portfolio, "bitcoin",  0.005, prices)
    # display_summary(portfolio, prices)
    # save_portfolio(portfolio)

    # Step 8 – interactive menu
    interactive_menu(portfolio, prices)


if __name__ == "__main__":
    main()
