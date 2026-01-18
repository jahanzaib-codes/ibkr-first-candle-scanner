from datetime import datetime, timedelta
from typing import List, Optional
import pytz


def get_est_time() -> datetime:
    """Get current time in US Eastern timezone."""
    return datetime.now(pytz.timezone('US/Eastern'))


def is_market_open() -> bool:
    """
    Check if US stock market is currently open.
    
    Market hours: 9:30 AM - 4:00 PM EST, Monday-Friday
    
    Returns:
        True if market is open, False otherwise
    """
    now = get_est_time()
    
    # Check if it's a weekday
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check time
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= now <= market_close


def get_market_open_time(date: Optional[datetime] = None) -> datetime:
    """
    Get market open time for a given date.
    
    Args:
        date: Date to get market open for (default: today)
        
    Returns:
        datetime for market open (9:30 AM EST)
    """
    if date is None:
        date = get_est_time()
    
    return date.replace(hour=9, minute=30, second=0, microsecond=0)


def get_first_candle_close_time(timeframe_minutes: int, date: Optional[datetime] = None) -> datetime:
    """
    Get the close time of the first candle after market open.
    
    Args:
        timeframe_minutes: Candle timeframe in minutes
        date: Date to calculate for (default: today)
        
    Returns:
        datetime when first candle closes
    """
    market_open = get_market_open_time(date)
    return market_open + timedelta(minutes=timeframe_minutes)


def format_volume(volume: int) -> str:
    """
    Format volume with K/M/B suffixes.
    
    Args:
        volume: Raw volume number
        
    Returns:
        Formatted string (e.g., "1.5M")
    """
    if volume >= 1_000_000_000:
        return f"{volume / 1_000_000_000:.2f}B"
    elif volume >= 1_000_000:
        return f"{volume / 1_000_000:.2f}M"
    elif volume >= 1_000:
        return f"{volume / 1_000:.2f}K"
    else:
        return str(volume)


def format_market_cap(market_cap_billions: float) -> str:
    """
    Format market cap for display.
    
    Args:
        market_cap_billions: Market cap in billions
        
    Returns:
        Formatted string
    """
    if market_cap_billions >= 1000:
        return f"${market_cap_billions / 1000:.2f}T"
    elif market_cap_billions >= 1:
        return f"${market_cap_billions:.2f}B"
    else:
        return f"${market_cap_billions * 1000:.2f}M"


def format_price(price: float) -> str:
    """
    Format price for display.
    
    Args:
        price: Price value
        
    Returns:
        Formatted string with $ sign
    """
    return f"${price:.2f}"


def format_percent(percent: float) -> str:
    """
    Format percentage for display with + sign for positive values.
    
    Args:
        percent: Percentage value
        
    Returns:
        Formatted string
    """
    if percent >= 0:
        return f"+{percent:.2f}%"
    else:
        return f"{percent:.2f}%"


def validate_settings(settings: dict) -> List[str]:
    """
    Validate scanner settings.
    
    Args:
        settings: Dictionary of settings to validate
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Price validation
    if settings.get('min_price', 0) < 0:
        errors.append("Minimum price cannot be negative")
    
    if settings.get('max_price', 0) < settings.get('min_price', 0):
        errors.append("Maximum price must be greater than minimum price")
    
    # Market cap validation
    if settings.get('min_market_cap', 0) < 0:
        errors.append("Minimum market cap cannot be negative")
    
    if settings.get('max_market_cap', 0) < settings.get('min_market_cap', 0):
        errors.append("Maximum market cap must be greater than minimum")
    
    # Volume validation
    if settings.get('min_volume', 0) < 0:
        errors.append("Minimum volume cannot be negative")
    
    # Timeframe validation
    valid_timeframes = [1, 2, 3, 5, 10, 15, 30, 60]
    if settings.get('timeframe_minutes') not in valid_timeframes:
        errors.append(f"Timeframe must be one of: {valid_timeframes}")
    
    return errors
