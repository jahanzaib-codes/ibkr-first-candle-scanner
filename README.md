# 📈 IBKR First Candle Market Scanner

A professional-grade market scanner that monitors stocks for bullish first candle patterns at market open using Interactive Brokers TWS API.

## 🔧 Features

- **Real-time First Candle Detection**: Monitors stocks at market open for bullish signals
- **Heikin Ashi Analysis**: Detects bullish Heikin Ashi candles (matching TradingView implementation)
- **Normal Candle Analysis**: Detects regular bullish candles (Close > Open)
- **Customizable Filters**:
  - Exchange: NASDAQ, NYSE, or Both
  - Price Range
  - Market Cap Range
  - Minimum Volume
  - Timeframe (1, 2, 3, 5, 10, 15 minutes)
- **Dark Mode GUI**: Modern, professional interface
- **Settings Persistence**: Save and load scanner settings

## 🖥️ Requirements

### Software Requirements
- Python 3.10+
- Interactive Brokers TWS or IB Gateway
- Windows 10/11

### Python Dependencies
```bash
pip install ib_insync customtkinter pytz pandas numpy
```

## ⚠️ IMPORTANT: Market Data Subscription Required

**This scanner requires an active IBKR market data subscription to function properly.**

### Required Subscriptions

| Data Type | Subscription Needed | Monthly Cost |
|-----------|---------------------|--------------|
| Scanner Data | US Securities Snapshot Bundle | Included with account |
| Historical Data | Market Data for US stocks | ~$1.50/month |
| Real-time Quotes | US Equity Add-On | ~$4.95/month |

### Recommended Package

**US Equity and Options Add-On Bundle** (~$4.95/month)
- Real-time quotes for US stocks
- Required for live trading and accurate scanning

### How to Subscribe

1. Log in to **IBKR Account Management**
2. Navigate to **Settings** → **User Settings**
3. Click on **Market Data Subscriptions**
4. Search for and subscribe to:
   - **US Securities Snapshot and Futures Value Bundle**
   - **US Equity and Options Add-On Bundle** (for real-time data)

### Free Alternative (Limited)
- Paper Trading accounts receive limited delayed market data
- Delayed data (15 minutes) is available for free but not suitable for first candle scanning

## 📅 Market Hours

The scanner only operates during US regular trading hours:

| Parameter | Value |
|-----------|-------|
| **Trading Days** | Monday - Friday |
| **Market Open** | 9:30 AM EST |
| **Market Close** | 4:00 PM EST |

### US Stock Market Holidays (2026)

| Holiday | Date | Market Status |
|---------|------|---------------|
| New Year's Day | January 1 | Closed |
| Martin Luther King Jr. Day | January 19 | Closed |
| Presidents Day | February 16 | Closed |
| Good Friday | April 3 | Closed |
| Memorial Day | May 25 | Closed |
| Juneteenth | June 19 | Closed |
| Independence Day | July 3 | Closed |
| Labor Day | September 7 | Closed |
| Thanksgiving | November 26 | Closed |
| Christmas | December 25 | Closed |

## 🚀 Quick Start

### 1. Configure TWS API
Open TWS → File → Global Configuration → API → Settings:
- ✅ Enable ActiveX and Socket Clients
- ✅ Allow connections from localhost only
- Set Socket Port: **7497** (Paper) or **7496** (Live)
- Set Master API client ID: **1**

### 2. Run the Scanner
```bash
python main.py
```

### 3. Connect to TWS
1. Click **"Connect to TWS"** button
2. Enter connection settings:
   - Host: `127.0.0.1`
   - Port: `7497` (Paper) / `7496` (Live)
   - Client ID: `1`
3. Click **Connect**

### 4. Configure Scanner Settings
Click **"Configure Settings"** to set:
- Exchange (NASDAQ/NYSE/Both)
- Timeframe (2 min recommended)
- Price Range
- Market Cap Range
- Minimum Volume

### 5. Start Scanning
- **Start Scan**: Continuous monitoring (30-second intervals)
- **Run Single Scan**: One-time scan

## 📊 Understanding Results

| Column | Description |
|--------|-------------|
| Ticker | Stock symbol |
| Last Price | Current trading price |
| Change % | Percentage change from previous close |
| Market Cap (B) | Market capitalization in billions |
| Volume | Trading volume |
| HA Bullish | 🟢 if Heikin Ashi candle is bullish |
| Normal Bullish | 🟢 if regular candle is bullish |
| Scan Time | Time of the scan |

## ⚙️ Technical Details

### Heikin Ashi Formula
```
HA_Close = (Open + High + Low + Close) / 4
HA_Open = (Previous HA_Open + Previous HA_Close) / 2
HA_High = max(High, HA_Open, HA_Close)
HA_Low = min(Low, HA_Open, HA_Close)

Bullish: HA_Close > HA_Open
```

### File Structure
```
├── main.py              # Application entry point
├── src/
│   ├── gui.py           # GUI implementation
│   └── scanner.py       # IBKR scanner logic
├── scanner_settings.json # Saved settings
└── scanner.log          # Application logs
```

## 🔧 Troubleshooting

### "Market is closed" message
- Check if today is a weekday (Mon-Fri)
- Verify current time is between 9:30 AM - 4:00 PM EST
- Check for US market holidays

### Connection Failed
- Ensure TWS/IB Gateway is running
- Verify API settings are enabled in TWS
- Check port number (7497 for Paper, 7496 for Live)
- Confirm no other application is using the same Client ID

### No Scanner Results
- Verify market data subscription is active
- Check scanner filter settings (may be too restrictive)
- Ensure market is open

### "Event loop" Errors
- Make sure you're using Python 3.10+
- Restart the application

## 📝 License

This software is provided for educational and personal use only. 
Not financial advice. Trade at your own risk.

## 📧 Support

For issues or feature requests, please contact the developer.

---
*Developed for Interactive Brokers TWS API integration*
</CodeContent>
<parameter name="EmptyFile">false
