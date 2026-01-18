import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import pandas as pd
import numpy as np
import pytz
import threading
import queue
import logging
from dataclasses import dataclass, field
from enum import Enum

from ib_insync import IB, Stock, Contract, ScannerSubscription, TagValue, util

logger = logging.getLogger(__name__)


class Exchange(Enum):
    """Supported stock exchanges."""
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    BOTH = "BOTH"


@dataclass
class ScannerSettings:
    """Scanner configuration settings."""
    exchange: Exchange = Exchange.BOTH
    min_price: float = 0.0
    max_price: float = 100.0
    min_market_cap: float = 0.0  # in billions
    max_market_cap: float = 100.0  # in billions
    min_volume: int = 100000
    timeframe_minutes: int = 2
    detect_ha_candle: bool = True
    detect_normal_candle: bool = True


@dataclass
class ScanResult:
    """Individual scan result for a stock."""
    symbol: str
    last_price: float = 0.0
    change_percent: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    market_cap: float = 0.0  # in billions
    volume: int = 0
    ha_bullish: bool = False
    normal_bullish: bool = False
    first_candle_volume: int = 0
    scan_time: datetime = field(default_factory=datetime.now)
    parameters_used: str = ""


class HeikinAshiCalculator:
    """
    Calculates Heikin Ashi candles matching TradingView's implementation.
    
    HA formulas:
    - HA_Close = (Open + High + Low + Close) / 4
    - HA_Open = (Previous HA_Open + Previous HA_Close) / 2
    - HA_High = max(High, HA_Open, HA_Close)
    - HA_Low = min(Low, HA_Open, HA_Close)
    """
    
    @staticmethod
    def calculate(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Heikin Ashi candles from OHLC data.
        
        Args:
            df: DataFrame with columns ['open', 'high', 'low', 'close']
            
        Returns:
            DataFrame with HA columns added ['ha_open', 'ha_high', 'ha_low', 'ha_close']
        """
        if df.empty:
            return df
            
        ha_df = df.copy()
        
        # HA Close = (Open + High + Low + Close) / 4
        ha_df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        
        # Initialize HA Open with first regular candle open
        ha_open = [df['open'].iloc[0]]
        
        # HA Open = (Previous HA Open + Previous HA Close) / 2
        for i in range(1, len(df)):
            prev_ha_open = ha_open[i - 1]
            prev_ha_close = ha_df['ha_close'].iloc[i - 1]
            ha_open.append((prev_ha_open + prev_ha_close) / 2)
        
        ha_df['ha_open'] = ha_open
        
        # HA High = max(High, HA Open, HA Close)
        ha_df['ha_high'] = ha_df[['high', 'ha_open', 'ha_close']].max(axis=1)
        
        # HA Low = min(Low, HA Open, HA Close)
        ha_df['ha_low'] = ha_df[['low', 'ha_open', 'ha_close']].min(axis=1)
        
        return ha_df
    
    @staticmethod
    def is_bullish(ha_df: pd.DataFrame, index: int = -1) -> bool:
        """
        Check if a Heikin Ashi candle is bullish.
        
        Bullish condition: HA_Close > HA_Open
        
        Args:
            ha_df: DataFrame with HA columns
            index: Index of the candle to check (default: last candle)
            
        Returns:
            True if bullish, False otherwise
        """
        if ha_df.empty or 'ha_close' not in ha_df.columns:
            return False
            
        return ha_df['ha_close'].iloc[index] > ha_df['ha_open'].iloc[index]


class IBKRScanner:
    """
    IBKR TWS Scanner for first candle detection.
    
    Connects to TWS, fetches stock universe, and monitors for
    bullish Heikin Ashi and Normal candles at market open.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        """
        Initialize the scanner.
        
        Args:
            host: TWS host address
            port: TWS port (7497 for paper, 7496 for live)
            client_id: Client ID for the connection
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib: Optional[IB] = None
        self.connected = False
        self.settings = ScannerSettings()
        self.results: Dict[str, ScanResult] = {}
        self.scan_history: List[Dict] = []  # Store previous scan runs
        self._callback: Optional[Callable] = None
        self._running = False
        self._scan_thread: Optional[threading.Thread] = None
        self.est_tz = pytz.timezone('US/Eastern')
        
    def connect(self) -> bool:
        """
        Connect to IBKR TWS.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # Create new event loop for this thread if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            self.ib = IB()
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            logger.info(f"Connected to IBKR TWS at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IBKR TWS: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from IBKR TWS."""
        if self.ib and self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR TWS")
    
    def set_callback(self, callback: Callable):
        """Set callback function for scan result updates."""
        self._callback = callback
    
    def update_settings(self, settings: ScannerSettings):
        """Update scanner settings."""
        self.settings = settings
        logger.info(f"Scanner settings updated: {settings}")
    
    def _get_scanner_location(self) -> str:
        """Get location code based on exchange setting."""
        if self.settings.exchange == Exchange.NASDAQ:
            return "STK.NASDAQ"
        elif self.settings.exchange == Exchange.NYSE:
            return "STK.NYSE"
        else:
            return "STK.US.MAJOR"
    
    def _get_scanner_filters(self) -> List[TagValue]:
        """Build scanner filter list based on settings."""
        filters = []
        
        # Price filters
        if self.settings.min_price > 0:
            filters.append(TagValue("priceAbove", str(self.settings.min_price)))
        if self.settings.max_price < float('inf'):
            filters.append(TagValue("priceBelow", str(self.settings.max_price)))
        
        # Market cap filters (convert billions to actual value)
        if self.settings.min_market_cap > 0:
            filters.append(TagValue("marketCapAbove", str(int(self.settings.min_market_cap * 1e9))))
        if self.settings.max_market_cap < float('inf'):
            filters.append(TagValue("marketCapBelow", str(int(self.settings.max_market_cap * 1e9))))
        
        # Volume filter
        if self.settings.min_volume > 0:
            filters.append(TagValue("volumeAbove", str(self.settings.min_volume)))
        
        return filters
    
    def _fetch_stock_universe(self) -> List[Contract]:
        """
        Fetch list of stocks from IBKR scanner matching the criteria.
        
        Returns:
            List of Contract objects
        """
        if not self.connected:
            return []
        
        try:
            # Create scanner subscription
            sub = ScannerSubscription()
            sub.instrument = "STK"
            sub.locationCode = self._get_scanner_location()
            sub.scanCode = "MOST_ACTIVE"  # Start with most active stocks
            sub.numberOfRows = 50
            
            # Get scanner data
            scan_data = self.ib.reqScannerData(
                sub,
                scannerSubscriptionFilterOptions=self._get_scanner_filters()
            )
            
            contracts = [sd.contractDetails.contract for sd in scan_data]
            logger.info(f"Fetched {len(contracts)} stocks from scanner")
            return contracts
            
        except Exception as e:
            logger.error(f"Error fetching stock universe: {e}")
            return []
    
    def _get_historical_bars(self, contract: Contract, duration_str: str = "1 D") -> pd.DataFrame:
        """
        Get historical bar data for a contract.
        
        Args:
            contract: Stock contract
            duration_str: Duration string (e.g., "1 D")
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.connected:
            return pd.DataFrame()
        
        try:
            bar_size = f"{self.settings.timeframe_minutes} mins"
            
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration_str,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,  # Regular Trading Hours only
                formatDate=1
            )
            
            if bars:
                df = util.df(bars)
                df = df.rename(columns={
                    'date': 'datetime',
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume'
                })
                return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {contract.symbol}: {e}")
        
        return pd.DataFrame()
    
    def _get_market_data(self, contract: Contract) -> Dict:
        """
        Get real-time market data for a contract.
        
        Args:
            contract: Stock contract
            
        Returns:
            Dictionary with market data
        """
        if not self.connected:
            return {}
        
        try:
            # Request snapshot market data
            ticker = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(1)  # Wait for data
            
            data = {
                'last_price': ticker.last if ticker.last else ticker.close,
                'bid': ticker.bid if ticker.bid else 0,
                'ask': ticker.ask if ticker.ask else 0,
                'volume': ticker.volume if ticker.volume else 0,
            }
            
            # Cancel market data subscription
            self.ib.cancelMktData(contract)
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching market data for {contract.symbol}: {e}")
            return {}
    
    def _get_fundamental_data(self, contract: Contract) -> Dict:
        """
        Get fundamental data (market cap) for a contract.
        
        Args:
            contract: Stock contract
            
        Returns:
            Dictionary with fundamental data
        """
        if not self.connected:
            return {}
        
        try:
            # Request fundamental data
            fundamental = self.ib.reqFundamentalData(
                contract,
                reportType='ReportSnapshot'
            )
            
            # Parse market cap from fundamental data (simplified)
            market_cap = 0.0
            if fundamental:
                # In real implementation, parse XML to get market cap
                pass
            
            return {'market_cap': market_cap}
            
        except Exception as e:
            logger.debug(f"Could not fetch fundamental data for {contract.symbol}: {e}")
            return {'market_cap': 0.0}
    
    def _is_market_open(self) -> bool:
        """Check if US stock market is open."""
        now = datetime.now(self.est_tz)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        # Check if it's a weekday
        if now.weekday() >= 5:
            return False
        
        return market_open <= now <= market_close
    
    def _get_first_candle_time(self) -> datetime:
        """Get the timestamp for the first candle after market open."""
        now = datetime.now(self.est_tz)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        
        # First candle closes after timeframe_minutes
        first_candle_close = market_open + timedelta(minutes=self.settings.timeframe_minutes)
        
        return first_candle_close
    
    def _analyze_first_candle(self, df: pd.DataFrame) -> tuple:
        """
        Analyze the first candle for bullish signals.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Tuple of (ha_bullish, normal_bullish, first_candle_volume)
        """
        if df.empty:
            return False, False, 0
        
        # Get market open time
        now = datetime.now(self.est_tz)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        
        # Filter to today's data only
        today_df = df[df['datetime'].dt.date == now.date()].copy()
        
        if today_df.empty:
            return False, False, 0
        
        # Get the first candle (should be the one starting at 9:30)
        first_candle = today_df.iloc[0]
        first_candle_volume = int(first_candle['volume'])
        
        # Check normal bullish: Close > Open
        normal_bullish = first_candle['close'] > first_candle['open']
        
        # Check HA bullish
        ha_bullish = False
        if self.settings.detect_ha_candle:
            ha_df = HeikinAshiCalculator.calculate(today_df)
            ha_bullish = HeikinAshiCalculator.is_bullish(ha_df, index=0)
        
        return ha_bullish, normal_bullish, first_candle_volume
    
    def _scan_stock(self, contract: Contract) -> Optional[ScanResult]:
        """
        Perform full scan analysis on a single stock.
        
        Args:
            contract: Stock contract
            
        Returns:
            ScanResult if conditions met, None otherwise
        """
        try:
            symbol = contract.symbol
            
            # Get historical data
            df = self._get_historical_bars(contract)
            if df.empty:
                return None
            
            # Analyze first candle
            ha_bullish, normal_bullish, first_candle_volume = self._analyze_first_candle(df)
            
            # Check volume condition on first candle
            if first_candle_volume < self.settings.min_volume:
                return None
            
            # Check if any condition is met
            if self.settings.detect_ha_candle and not ha_bullish:
                if self.settings.detect_normal_candle and not normal_bullish:
                    return None
                elif not self.settings.detect_normal_candle:
                    return None
            
            if self.settings.detect_normal_candle and not normal_bullish:
                if self.settings.detect_ha_candle and not ha_bullish:
                    return None
                elif not self.settings.detect_ha_candle:
                    return None
            
            # Get market data
            mkt_data = self._get_market_data(contract)
            
            # Get fundamental data
            fund_data = self._get_fundamental_data(contract)
            
            # Calculate change percent
            if not df.empty:
                prev_close = df['close'].iloc[-2] if len(df) > 1 else df['close'].iloc[-1]
                last_price = mkt_data.get('last_price', df['close'].iloc[-1])
                change_percent = ((last_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
            else:
                change_percent = 0
                last_price = 0
            
            # Build parameters string for tracking
            params = f"TF:{self.settings.timeframe_minutes}m | Vol:{self.settings.min_volume} | Price:${self.settings.min_price}-${self.settings.max_price}"
            
            result = ScanResult(
                symbol=symbol,
                last_price=mkt_data.get('last_price', last_price),
                change_percent=change_percent,
                bid=mkt_data.get('bid', 0),
                ask=mkt_data.get('ask', 0),
                market_cap=fund_data.get('market_cap', 0),
                volume=mkt_data.get('volume', 0),
                ha_bullish=ha_bullish,
                normal_bullish=normal_bullish,
                first_candle_volume=first_candle_volume,
                scan_time=datetime.now(self.est_tz),
                parameters_used=params
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error scanning {contract.symbol}: {e}")
            return None
    
    def run_scan(self) -> Dict[str, ScanResult]:
        """
        Run a full scan of the stock universe.
        
        Returns:
            Dictionary of symbol -> ScanResult
        """
        if not self.connected:
            logger.error("Not connected to IBKR TWS")
            return {}
        
        logger.info("Starting scan...")
        
        # Store current results as previous run
        if self.results:
            self.scan_history.append({
                'timestamp': datetime.now(self.est_tz),
                'parameters': f"TF:{self.settings.timeframe_minutes}m",
                'results': dict(self.results)
            })
        
        # Fetch stock universe
        contracts = self._fetch_stock_universe()
        
        # Scan each stock
        new_results = {}
        for contract in contracts:
            result = self._scan_stock(contract)
            if result:
                new_results[result.symbol] = result
                logger.info(f"Found signal: {result.symbol} - HA:{result.ha_bullish} Normal:{result.normal_bullish}")
        
        self.results = new_results
        
        if self._callback:
            self._callback(self.results)
        
        logger.info(f"Scan complete. Found {len(self.results)} stocks meeting criteria.")
        return self.results
    
    def start_monitoring(self, interval_seconds: int = 30):
        """
        Start continuous monitoring for first candle signals.
        
        Args:
            interval_seconds: Update interval in seconds
        """
        self._running = True
        
        def monitor_loop():
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            import time
            while self._running:
                if self._is_market_open():
                    self.run_scan()
                else:
                    logger.info("Market is closed")
                
                # Wait for next interval using time.sleep instead of ib.sleep
                for _ in range(interval_seconds):
                    if not self._running:
                        break
                    time.sleep(1)
        
        self._scan_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._scan_thread.start()
        logger.info(f"Started monitoring with {interval_seconds}s interval")
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self._running = False
        if self._scan_thread:
            self._scan_thread.join(timeout=5)
        logger.info("Stopped monitoring")
    
    def get_previous_runs(self) -> List[Dict]:
        """Get history of previous scan runs."""
        return self.scan_history
