# IBKR First Candle Market Scanner | Interactive Brokers Stock Screener

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![IBKR](https://img.shields.io/badge/IBKR-TWS%20API-red.svg)](https://interactivebrokers.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A powerful **real-time stock scanner** for **Interactive Brokers (IBKR)** that detects **bullish Heikin Ashi candles** and **normal candlestick patterns** at market open. Perfect for **day traders**, **swing traders**, and **algorithmic trading** enthusiasts looking for automated stock screening solutions.

## 🔥 Why Use This Scanner?

- **First Candle Detection** - Catch momentum at market open (9:30 AM EST)
- **Heikin Ashi Analysis** - TradingView-matching calculations for accuracy
- **Real-time Scanning** - Live data from IBKR TWS with minimal delay
- **Multi-Exchange Support** - Scan NASDAQ, NYSE, or both simultaneously
- **Customizable Filters** - Price, volume, market cap, and timeframe filters
- **Modern GUI** - Professional dark theme interface with CustomTkinter

## 📊 Key Features

### Stock Screening Capabilities
- ✅ **Heikin Ashi Bullish Candle Detection** - Identify trend reversals
- ✅ **Normal Candlestick Pattern Recognition** - Standard bullish pattern detection
- ✅ **Multiple Timeframes** - 1, 2, 3, 5, 10, 15 minute candles
- ✅ **Volume Confirmation** - Filter by first candle volume
- ✅ **Price Range Filter** - Set minimum and maximum stock prices
- ✅ **Market Cap Filter** - Filter stocks by market capitalization

### Trading Tools Integration
- 📈 **Interactive Brokers TWS API** - Direct connection to your IBKR account
- 📈 **Real-time Market Data** - Live bid/ask, last price, volume
- 📈 **Scan History** - Track previous scans with parameters used
- 📈 **Persistent Settings** - Save your configurations

### Display Columns
| Column | Description |
|--------|-------------|
| Ticker | Stock symbol |
| Last Price | Current trading price |
| Change % | Percentage change from previous close |
| Bid | Current bid price |
| Ask | Current ask price |
| Market Cap (B) | Market capitalization in billions |
| Volume | Trading volume |
| HA Bullish | 🟢 Heikin Ashi bullish signal |
| Normal Bullish | 🟢 Normal candle bullish signal |
| Scan Time | Time of the scan |

## 🎯 Perfect For

- **Day Traders** looking for momentum stocks at market open
- **Swing Traders** identifying trend reversals with Heikin Ashi
- **Algorithmic Traders** building automated trading strategies
- **Stock Screener Users** who want customizable real-time scanning
- **IBKR Users** seeking better stock screening than TWS built-in scanner

## 🖥️ Prerequisites

### 1. Interactive Brokers Account
- Active IBKR account (Paper Trading or Live)
- Market data subscription for NASDAQ/NYSE

### 2. IBKR Trader Workstation (TWS)
- Download: [IBKR TWS Download](https://www.interactivebrokers.com/en/trading/tws.php)
- Version 1023 or higher recommended

### 3. TWS API Configuration
1. Open TWS → **File** → **Global Configuration**
2. Navigate to **API** → **Settings**
3. ✅ Enable **Enable ActiveX and Socket Clients**
4. ✅ Enable **Allow connections from localhost only**
5. Note **Socket Port**: 7497 (Paper) / 7496 (Live)

### 4. Python Environment
- Python 3.9 or higher
- Download: [Python Downloads](https://www.python.org/downloads/)

## 📦 Installation

### Clone Repository
```bash
git clone https://github.com/jahanzaib-codes/ibkr-first-candle-scanner.git
cd ibkr-first-candle-scanner
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Manual Installation
```bash
pip install ib_insync customtkinter pandas numpy pytz
```

## 🚀 Quick Start

### 1. Start IBKR TWS
- Launch Trader Workstation
- Login to your account
- Ensure API is enabled

### 2. Run Scanner
```bash
python main.py
```

### 3. Connect to TWS
- Click **Connect to TWS**
- Enter: Host `127.0.0.1`, Port `7497` (Paper) or `7496` (Live)
- Click **Connect**

### 4. Configure Settings
- Click **Configure Settings**
- Set Exchange, Timeframe, Price, Volume, Market Cap filters
- Click **💾 Save & Apply** to persist settings

### 5. Start Scanning
- Click **Start Scan** for continuous monitoring
- Or **Run Single Scan** for one-time scan

## 🧮 Heikin Ashi Calculation

TradingView-matching formulas for accurate signal detection:

```python
HA_Close = (Open + High + Low + Close) / 4
HA_Open  = (Previous_HA_Open + Previous_HA_Close) / 2
HA_High  = max(High, HA_Open, HA_Close)
HA_Low   = min(Low, HA_Open, HA_Close)

# Bullish Signal
Bullish = HA_Close > HA_Open
```

## 📂 Project Structure

```
ibkr-first-candle-scanner/
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── README.md                # Documentation
├── scanner_settings.json    # Saved settings (auto-generated)
├── scanner.log              # Runtime logs
└── src/
    ├── scanner.py           # IBKR scanner logic & HA calculations
    ├── gui.py               # CustomTkinter GUI
    ├── config.py            # Configuration constants
    ├── utils.py             # Helper functions
    └── __init__.py          # Package init
```

## ⚙️ Default Configuration

| Setting | Default Value |
|---------|---------------|
| Exchange | NASDAQ + NYSE |
| Timeframe | 2 minutes |
| Min Price | $0 |
| Max Price | $100 |
| Min Market Cap | $0B |
| Max Market Cap | $100B |
| Min Volume | 100,000 |

## 🔧 Troubleshooting

### Connection Issues
- Ensure TWS is running and logged in
- Check API is enabled in TWS settings
- Verify port: 7497 (Paper) / 7496 (Live)
- Use unique Client ID

### No Results
- Check if market is open (9:30 AM - 4:00 PM EST)
- Verify filters are not too restrictive
- Ensure market data subscription is active

## 📈 How It Works

1. **Fetch Universe** - Gets stocks from IBKR scanner matching filters
2. **Historical Data** - Fetches intraday bars for each stock
3. **Candle Analysis** - Calculates Heikin Ashi and checks patterns
4. **Volume Check** - Confirms first candle meets volume threshold
5. **Display Results** - Shows matching stocks in real-time table

## 🏷️ Keywords

`Interactive Brokers` `IBKR` `TWS API` `Stock Scanner` `Stock Screener` `Heikin Ashi` `Candlestick Patterns` `Day Trading` `Swing Trading` `Algorithmic Trading` `Python Trading Bot` `Market Scanner` `Real-time Scanner` `NASDAQ Scanner` `NYSE Scanner` `First Candle` `Market Open` `Trading Tools` `Stock Analysis` `Technical Analysis`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for **educational and informational purposes only**. It is **NOT financial advice**. Trading stocks involves significant risk of loss. Always do your own research before making trading decisions. The developers are not responsible for any financial losses incurred from using this software.

## 📧 Contact

- GitHub: [@jahanzaib-codes](https://github.com/jahanzaib-codes)

---

**⭐ If you find this project useful, please give it a star!**

Made with ❤️ for the trading community
