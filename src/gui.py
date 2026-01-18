import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
import pytz
import threading
import json
import os
from typing import Dict, Optional
from pathlib import Path
import logging

from scanner import IBKRScanner, ScannerSettings, ScanResult, Exchange

logger = logging.getLogger(__name__)

# Settings file path
SETTINGS_FILE = Path(__file__).parent.parent / "scanner_settings.json"


def load_saved_settings() -> Optional[ScannerSettings]:
    """Load settings from JSON file."""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                return ScannerSettings(
                    exchange=Exchange[data.get('exchange', 'BOTH')],
                    min_price=data.get('min_price', 0.0),
                    max_price=data.get('max_price', 100.0),
                    min_market_cap=data.get('min_market_cap', 0.0),
                    max_market_cap=data.get('max_market_cap', 100.0),
                    min_volume=data.get('min_volume', 100000),
                    timeframe_minutes=data.get('timeframe_minutes', 2),
                    detect_ha_candle=data.get('detect_ha_candle', True),
                    detect_normal_candle=data.get('detect_normal_candle', True)
                )
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
    return None


def save_settings_to_file(settings: ScannerSettings) -> bool:
    """Save settings to JSON file."""
    try:
        data = {
            'exchange': settings.exchange.value,
            'min_price': settings.min_price,
            'max_price': settings.max_price,
            'min_market_cap': settings.min_market_cap,
            'max_market_cap': settings.max_market_cap,
            'min_volume': settings.min_volume,
            'timeframe_minutes': settings.timeframe_minutes,
            'detect_ha_candle': settings.detect_ha_candle,
            'detect_normal_candle': settings.detect_normal_candle
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Settings saved to {SETTINGS_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return False


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog for scanner configuration."""
    
    def __init__(self, parent, current_settings: ScannerSettings):
        super().__init__(parent)
        
        self.title("Scanner Settings")
        self.geometry("520x750")
        self.resizable(True, True)
        self.minsize(500, 700)
        
        self.current_settings = current_settings
        self.result_settings: Optional[ScannerSettings] = None
        
        self._create_widgets()
        self._load_current_settings()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
    def _create_widgets(self):
        """Create dialog widgets."""
        # Use scrollable frame to ensure all content is visible
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="⚙️ Scanner Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Exchange Selection
        exchange_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        exchange_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            exchange_frame,
            text="Exchange:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        self.exchange_var = ctk.StringVar(value="BOTH")
        exchange_options = ctk.CTkSegmentedButton(
            exchange_frame,
            values=["NASDAQ", "NYSE", "BOTH"],
            variable=self.exchange_var
        )
        exchange_options.pack(fill="x", pady=5)
        
        # Timeframe Selection
        tf_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        tf_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            tf_frame,
            text="Candle Timeframe (minutes):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        self.timeframe_var = ctk.StringVar(value="2")
        tf_options = ctk.CTkSegmentedButton(
            tf_frame,
            values=["1", "2", "3", "5", "10", "15"],
            variable=self.timeframe_var
        )
        tf_options.pack(fill="x", pady=5)
        
        # Price Filter
        price_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        price_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            price_frame,
            text="Price Range ($):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        price_input_frame = ctk.CTkFrame(price_frame, fg_color="transparent")
        price_input_frame.pack(fill="x", pady=5)
        
        self.min_price_entry = ctk.CTkEntry(price_input_frame, placeholder_text="Min", width=100)
        self.min_price_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(price_input_frame, text="to").pack(side="left")
        
        self.max_price_entry = ctk.CTkEntry(price_input_frame, placeholder_text="Max", width=100)
        self.max_price_entry.pack(side="left", padx=(10, 0))
        
        # Market Cap Filter
        mcap_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        mcap_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            mcap_frame,
            text="Market Cap (Billions $):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        mcap_input_frame = ctk.CTkFrame(mcap_frame, fg_color="transparent")
        mcap_input_frame.pack(fill="x", pady=5)
        
        self.min_mcap_entry = ctk.CTkEntry(mcap_input_frame, placeholder_text="Min", width=100)
        self.min_mcap_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(mcap_input_frame, text="to").pack(side="left")
        
        self.max_mcap_entry = ctk.CTkEntry(mcap_input_frame, placeholder_text="Max", width=100)
        self.max_mcap_entry.pack(side="left", padx=(10, 0))
        
        # Volume Filter
        vol_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        vol_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            vol_frame,
            text="Minimum Volume (First Candle):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        self.min_volume_entry = ctk.CTkEntry(vol_frame, placeholder_text="100000", width=150)
        self.min_volume_entry.pack(anchor="w", pady=5)
        
        # Candle Detection Options
        detect_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        detect_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            detect_frame,
            text="Candle Detection:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        self.detect_ha_var = ctk.BooleanVar(value=True)
        self.detect_normal_var = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(
            detect_frame,
            text="Heikin Ashi Bullish Candle",
            variable=self.detect_ha_var,
            onvalue=True,
            offvalue=False
        ).pack(anchor="w", pady=2)
        
        ctk.CTkCheckBox(
            detect_frame,
            text="Normal Bullish Candle",
            variable=self.detect_normal_var,
            onvalue=True,
            offvalue=False
        ).pack(anchor="w", pady=2)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="gray50",
            hover_color="gray40",
            command=self.destroy,
            width=100
        ).pack(side="left", padx=5)
        
        # Save & Apply button (saves to file and applies)
        ctk.CTkButton(
            button_frame,
            text="💾 Save & Apply",
            fg_color="#28a745",
            hover_color="#218838",
            command=self._save_and_apply_settings,
            width=130
        ).pack(side="right", padx=5)
        
        # Apply button (applies without saving)
        ctk.CTkButton(
            button_frame,
            text="Apply",
            command=self._apply_settings,
            width=100
        ).pack(side="right", padx=5)
    
    def _load_current_settings(self):
        """Load current settings into form fields."""
        self.exchange_var.set(self.current_settings.exchange.value)
        self.timeframe_var.set(str(self.current_settings.timeframe_minutes))
        self.min_price_entry.insert(0, str(self.current_settings.min_price))
        self.max_price_entry.insert(0, str(self.current_settings.max_price))
        self.min_mcap_entry.insert(0, str(self.current_settings.min_market_cap))
        self.max_mcap_entry.insert(0, str(self.current_settings.max_market_cap))
        self.min_volume_entry.insert(0, str(self.current_settings.min_volume))
        self.detect_ha_var.set(self.current_settings.detect_ha_candle)
        self.detect_normal_var.set(self.current_settings.detect_normal_candle)
    
    def _apply_settings(self):
        """Apply settings and close dialog."""
        try:
            self.result_settings = ScannerSettings(
                exchange=Exchange[self.exchange_var.get()],
                min_price=float(self.min_price_entry.get() or 0),
                max_price=float(self.max_price_entry.get() or 100),
                min_market_cap=float(self.min_mcap_entry.get() or 0),
                max_market_cap=float(self.max_mcap_entry.get() or 100),
                min_volume=int(self.min_volume_entry.get() or 100000),
                timeframe_minutes=int(self.timeframe_var.get()),
                detect_ha_candle=self.detect_ha_var.get(),
                detect_normal_candle=self.detect_normal_var.get()
            )
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please enter valid numbers: {e}")
    
    def _save_and_apply_settings(self):
        """Save settings to file and apply them."""
        try:
            self.result_settings = ScannerSettings(
                exchange=Exchange[self.exchange_var.get()],
                min_price=float(self.min_price_entry.get() or 0),
                max_price=float(self.max_price_entry.get() or 100),
                min_market_cap=float(self.min_mcap_entry.get() or 0),
                max_market_cap=float(self.max_mcap_entry.get() or 100),
                min_volume=int(self.min_volume_entry.get() or 100000),
                timeframe_minutes=int(self.timeframe_var.get()),
                detect_ha_candle=self.detect_ha_var.get(),
                detect_normal_candle=self.detect_normal_var.get()
            )
            
            # Save settings to file
            if save_settings_to_file(self.result_settings):
                messagebox.showinfo("Settings Saved", "Settings have been saved successfully!")
            else:
                messagebox.showwarning("Save Warning", "Settings applied but could not save to file.")
            
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please enter valid numbers: {e}")


class ConnectionDialog(ctk.CTkToplevel):
    """Connection settings dialog."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("IBKR Connection")
        self.geometry("400x300")
        self.resizable(False, False)
        
        self.host = "127.0.0.1"
        self.port = 7497
        self.client_id = 1
        self.connected = False
        
        self._create_widgets()
        
        self.transient(parent)
        self.grab_set()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            main_frame,
            text="🔌 IBKR TWS Connection",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 20))
        
        # Host
        ctk.CTkLabel(main_frame, text="Host:").pack(anchor="w")
        self.host_entry = ctk.CTkEntry(main_frame, width=200)
        self.host_entry.insert(0, "127.0.0.1")
        self.host_entry.pack(anchor="w", pady=(0, 10))
        
        # Port
        ctk.CTkLabel(main_frame, text="Port:").pack(anchor="w")
        self.port_entry = ctk.CTkEntry(main_frame, width=200)
        self.port_entry.insert(0, "7497")
        self.port_entry.pack(anchor="w", pady=(0, 10))
        
        # Client ID
        ctk.CTkLabel(main_frame, text="Client ID:").pack(anchor="w")
        self.client_id_entry = ctk.CTkEntry(main_frame, width=200)
        self.client_id_entry.insert(0, "1")
        self.client_id_entry.pack(anchor="w", pady=(0, 20))
        
        # Info
        ctk.CTkLabel(
            main_frame,
            text="Use port 7497 for Paper Trading\nUse port 7496 for Live Trading",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(pady=5)
        
        # Connect Button
        ctk.CTkButton(
            main_frame,
            text="Connect",
            command=self._connect
        ).pack(pady=10)
    
    def _connect(self):
        """Set connection parameters and close."""
        try:
            self.host = self.host_entry.get()
            self.port = int(self.port_entry.get())
            self.client_id = int(self.client_id_entry.get())
            self.connected = True
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid connection parameters")


class ScannerGUI(ctk.CTk):
    """Main GUI application for the IBKR First Candle Scanner."""
    
    def __init__(self):
        super().__init__()
        
        self.title("IBKR First Candle Market Scanner")
        self.geometry("1400x800")
        self.minsize(900, 600)  # Smaller min size for flexibility
        
        # Initialize scanner
        self.scanner: Optional[IBKRScanner] = None
        self.is_scanning = False
        self.est_tz = pytz.timezone('US/Eastern')
        
        # Load saved settings or use defaults
        self.current_settings = load_saved_settings() or ScannerSettings()
        
        # Create GUI
        self._create_styles()
        self._create_widgets()
        self._update_time()
        
        # Display loaded settings in summary
        self._update_settings_summary(self.current_settings)
    
    def _create_styles(self):
        """Create custom styles for ttk widgets."""
        style = ttk.Style()
        
        # Configure Treeview style for dark theme
        style.theme_use('clam')
        
        style.configure(
            "Scanner.Treeview",
            background="#2b2b2b",
            foreground="white",
            rowheight=30,
            fieldbackground="#2b2b2b",
            font=('Segoe UI', 11)
        )
        
        style.configure(
            "Scanner.Treeview.Heading",
            background="#1f538d",
            foreground="white",
            font=('Segoe UI', 11, 'bold')
        )
        
        style.map(
            "Scanner.Treeview",
            background=[('selected', '#1f538d')],
            foreground=[('selected', 'white')]
        )
    
    def _create_widgets(self):
        """Create main GUI widgets."""
        # Header Frame
        self._create_header()
        
        # Main Content Frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left Panel - Controls
        self._create_control_panel(main_frame)
        
        # Right Panel - Results Table
        self._create_results_panel(main_frame)
        
        # Status Bar
        self._create_status_bar()
    
    def _create_header(self):
        """Create header section."""
        header_frame = ctk.CTkFrame(self, height=70, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Title
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(
            title_frame,
            text="📈 IBKR First Candle Market Scanner",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left")
        
        # Time Display
        time_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        time_frame.pack(side="right", padx=20)
        
        self.time_label = ctk.CTkLabel(
            time_frame,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.time_label.pack(side="right")
        
        self.market_status_label = ctk.CTkLabel(
            time_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.market_status_label.pack(side="right", padx=10)
    
    def _create_control_panel(self, parent):
        """Create left control panel with scrollable content."""
        # Outer frame for control panel
        control_outer = ctk.CTkFrame(parent, width=300)
        control_outer.pack(side="left", fill="y", padx=(0, 10), pady=0)
        control_outer.pack_propagate(False)
        
        # Scrollable inner frame
        control_frame = ctk.CTkScrollableFrame(control_outer, width=280)
        control_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Connection Section
        conn_section = ctk.CTkFrame(control_frame)
        conn_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            conn_section,
            text="🔌 Connection",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        self.connection_status = ctk.CTkLabel(
            conn_section,
            text="⚫ Not Connected",
            font=ctk.CTkFont(size=12)
        )
        self.connection_status.pack(anchor="w", padx=10)
        
        self.connect_btn = ctk.CTkButton(
            conn_section,
            text="Connect to TWS",
            command=self._show_connection_dialog
        )
        self.connect_btn.pack(fill="x", padx=10, pady=10)
        
        # Settings Section
        settings_section = ctk.CTkFrame(control_frame)
        settings_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            settings_section,
            text="⚙️ Scanner Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        self.settings_summary = ctk.CTkLabel(
            settings_section,
            text="Exchange: BOTH\nTimeframe: 2 min\nVolume: 100,000+\nPrice: $0 - $100",
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        self.settings_summary.pack(anchor="w", padx=10)
        
        ctk.CTkButton(
            settings_section,
            text="Configure Settings",
            command=self._show_settings_dialog
        ).pack(fill="x", padx=10, pady=10)
        
        # Scan Controls
        scan_section = ctk.CTkFrame(control_frame)
        scan_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            scan_section,
            text="🔍 Scan Controls",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        self.scan_btn = ctk.CTkButton(
            scan_section,
            text="▶️ Start Scan",
            fg_color="#28a745",
            hover_color="#218838",
            command=self._toggle_scan,
            state="disabled"
        )
        self.scan_btn.pack(fill="x", padx=10, pady=5)
        
        self.manual_scan_btn = ctk.CTkButton(
            scan_section,
            text="🔄 Run Single Scan",
            command=self._run_single_scan,
            state="disabled"
        )
        self.manual_scan_btn.pack(fill="x", padx=10, pady=5)
        
        # Statistics Section
        stats_section = ctk.CTkFrame(control_frame)
        stats_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            stats_section,
            text="📊 Statistics",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        self.stats_label = ctk.CTkLabel(
            stats_section,
            text="Stocks Found: 0\nHA Bullish: 0\nNormal Bullish: 0\nLast Scan: N/A",
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        self.stats_label.pack(anchor="w", padx=10, pady=5)
        
        # Legend
        legend_section = ctk.CTkFrame(control_frame)
        legend_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            legend_section,
            text="📋 Legend",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        ctk.CTkLabel(
            legend_section,
            text="🟢 = Bullish Condition Met\n🔴 = Condition Not Met",
            font=ctk.CTkFont(size=11),
            justify="left"
        ).pack(anchor="w", padx=10)
    
    def _create_results_panel(self, parent):
        """Create results table panel."""
        results_frame = ctk.CTkFrame(parent)
        results_frame.pack(side="right", fill="both", expand=True)
        
        # Header
        header_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text="📋 Scan Results",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")
        
        self.params_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.params_label.pack(side="right")
        
        # Table Frame
        table_frame = ctk.CTkFrame(results_frame)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create Treeview
        columns = (
            "symbol", "last_price", "change_pct", "bid", "ask",
            "market_cap", "volume", "ha_signal", "normal_signal", "scan_time"
        )
        
        self.results_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Scanner.Treeview"
        )
        
        # Define column headings
        headings = {
            "symbol": "Ticker",
            "last_price": "Last Price",
            "change_pct": "Change %",
            "bid": "Bid",
            "ask": "Ask",
            "market_cap": "Market Cap (B)",
            "volume": "Volume",
            "ha_signal": "HA Bullish",
            "normal_signal": "Normal Bullish",
            "scan_time": "Scan Time"
        }
        
        widths = {
            "symbol": 80,
            "last_price": 100,
            "change_pct": 100,
            "bid": 80,
            "ask": 80,
            "market_cap": 120,
            "volume": 100,
            "ha_signal": 100,
            "normal_signal": 120,
            "scan_time": 120
        }
        
        for col in columns:
            self.results_tree.heading(col, text=headings[col], anchor="center")
            self.results_tree.column(col, width=widths[col], anchor="center")
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.results_tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.results_tree.xview)
        
        self.results_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        # Pack scrollbars and tree
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        self.results_tree.pack(fill="both", expand=True)
        
        # Previous Runs Section
        prev_frame = ctk.CTkFrame(results_frame)
        prev_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(
            prev_frame,
            text="📜 Previous Scan Runs",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=5, pady=5)
        
        self.prev_runs_label = ctk.CTkLabel(
            prev_frame,
            text="No previous runs",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.prev_runs_label.pack(anchor="w", padx=5)
    
    def _create_status_bar(self):
        """Create status bar."""
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready. Connect to IBKR TWS to begin scanning.",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(side="left", padx=10)
    
    def _update_time(self):
        """Update time display."""
        now = datetime.now(self.est_tz)
        time_str = now.strftime("%Y-%m-%d %H:%M:%S EST")
        self.time_label.configure(text=time_str)
        
        # Check market status
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        if now.weekday() < 5 and market_open <= now <= market_close:
            self.market_status_label.configure(text="🟢 Market Open", text_color="#28a745")
        else:
            self.market_status_label.configure(text="🔴 Market Closed", text_color="#dc3545")
        
        # Schedule next update
        self.after(1000, self._update_time)
    
    def _show_connection_dialog(self):
        """Show connection settings dialog."""
        dialog = ConnectionDialog(self)
        self.wait_window(dialog)
        
        if dialog.connected:
            self._connect_to_tws(dialog.host, dialog.port, dialog.client_id)
    
    def _connect_to_tws(self, host: str, port: int, client_id: int):
        """Connect to IBKR TWS."""
        self.status_label.configure(text=f"Connecting to {host}:{port}...")
        
        def connect():
            self.scanner = IBKRScanner(host, port, client_id)
            if self.scanner.connect():
                self.scanner.set_callback(self._on_scan_results)
                self.after(0, self._on_connected)
            else:
                self.after(0, self._on_connection_failed)
        
        threading.Thread(target=connect, daemon=True).start()
    
    def _on_connected(self):
        """Handle successful connection."""
        self.connection_status.configure(text="🟢 Connected to TWS")
        self.connect_btn.configure(text="Disconnect", command=self._disconnect)
        self.scan_btn.configure(state="normal")
        self.manual_scan_btn.configure(state="normal")
        self.status_label.configure(text="Connected to IBKR TWS. Ready to scan.")
    
    def _on_connection_failed(self):
        """Handle connection failure."""
        self.connection_status.configure(text="🔴 Connection Failed")
        self.status_label.configure(text="Failed to connect to IBKR TWS. Check if TWS is running.")
        messagebox.showerror("Connection Error", 
            "Could not connect to IBKR TWS.\n\n"
            "Please ensure:\n"
            "1. TWS or IB Gateway is running\n"
            "2. API connections are enabled in settings\n"
            "3. Port number is correct (7497 for Paper, 7496 for Live)")
    
    def _disconnect(self):
        """Disconnect from TWS."""
        if self.scanner:
            self.scanner.stop_monitoring()
            self.scanner.disconnect()
            self.scanner = None
        
        self.connection_status.configure(text="⚫ Not Connected")
        self.connect_btn.configure(text="Connect to TWS", command=self._show_connection_dialog)
        self.scan_btn.configure(state="disabled", text="▶️ Start Scan")
        self.manual_scan_btn.configure(state="disabled")
        self.is_scanning = False
        self.status_label.configure(text="Disconnected from IBKR TWS.")
    
    def _show_settings_dialog(self):
        """Show scanner settings dialog."""
        # Use stored settings, or scanner settings if connected
        settings_to_use = self.scanner.settings if self.scanner else self.current_settings
        
        dialog = SettingsDialog(self, settings_to_use)
        self.wait_window(dialog)
        
        if dialog.result_settings:
            # Update stored settings
            self.current_settings = dialog.result_settings
            
            # Update scanner if connected
            if self.scanner:
                self.scanner.update_settings(dialog.result_settings)
            
            self._update_settings_summary(dialog.result_settings)
    
    
    def _update_settings_summary(self, settings: ScannerSettings):
        """Update settings summary display."""
        vol_str = f"{settings.min_volume:,}"
        summary = (
            f"Exchange: {settings.exchange.value}\n"
            f"Timeframe: {settings.timeframe_minutes} min\n"
            f"Volume: {vol_str}+\n"
            f"Price: ${settings.min_price} - ${settings.max_price}\n"
            f"Market Cap: ${settings.min_market_cap}B - ${settings.max_market_cap}B"
        )
        self.settings_summary.configure(text=summary)
        
        self.params_label.configure(
            text=f"TF: {settings.timeframe_minutes}m | Vol: {vol_str} | Exchange: {settings.exchange.value}"
        )
    
    def _toggle_scan(self):
        """Toggle continuous scanning."""
        if not self.scanner:
            return
        
        if self.is_scanning:
            self.scanner.stop_monitoring()
            self.scan_btn.configure(text="▶️ Start Scan", fg_color="#28a745", hover_color="#218838")
            self.status_label.configure(text="Scanning stopped.")
            self.is_scanning = False
        else:
            self.scanner.start_monitoring(interval_seconds=30)
            self.scan_btn.configure(text="⏹️ Stop Scan", fg_color="#dc3545", hover_color="#c82333")
            self.status_label.configure(text="Scanning started. Monitoring for first candle signals...")
            self.is_scanning = True
    
    def _run_single_scan(self):
        """Run a single scan."""
        if not self.scanner:
            return
        
        self.status_label.configure(text="Running scan...")
        self.manual_scan_btn.configure(state="disabled")
        
        def scan():
            results = self.scanner.run_scan()
            self.after(0, lambda: self.manual_scan_btn.configure(state="normal"))
        
        threading.Thread(target=scan, daemon=True).start()
    
    def _on_scan_results(self, results: Dict[str, ScanResult]):
        """Handle scan results callback."""
        self.after(0, lambda: self._update_results_table(results))
    
    def _update_results_table(self, results: Dict[str, ScanResult]):
        """Update results table with new scan data."""
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Add new results
        ha_count = 0
        normal_count = 0
        
        for symbol, result in results.items():
            ha_signal = "🟢" if result.ha_bullish else "🔴"
            normal_signal = "🟢" if result.normal_bullish else "🔴"
            
            if result.ha_bullish:
                ha_count += 1
            if result.normal_bullish:
                normal_count += 1
            
            change_color = "green" if result.change_percent >= 0 else "red"
            change_str = f"+{result.change_percent:.2f}%" if result.change_percent >= 0 else f"{result.change_percent:.2f}%"
            
            self.results_tree.insert("", "end", values=(
                result.symbol,
                f"${result.last_price:.2f}",
                change_str,
                f"${result.bid:.2f}",
                f"${result.ask:.2f}",
                f"${result.market_cap:.2f}B",
                f"{result.volume:,}",
                ha_signal,
                normal_signal,
                result.scan_time.strftime("%H:%M:%S")
            ))
        
        # Update statistics
        self.stats_label.configure(text=(
            f"Stocks Found: {len(results)}\n"
            f"HA Bullish: {ha_count}\n"
            f"Normal Bullish: {normal_count}\n"
            f"Last Scan: {datetime.now(self.est_tz).strftime('%H:%M:%S')}"
        ))
        
        self.status_label.configure(text=f"Scan complete. Found {len(results)} stocks meeting criteria.")
        
        # Update previous runs
        if self.scanner:
            prev_runs = self.scanner.get_previous_runs()
            if prev_runs:
                runs_text = "\n".join([
                    f"• {run['timestamp'].strftime('%H:%M:%S')} - {run['parameters']} ({len(run['results'])} stocks)"
                    for run in prev_runs[-5:]  # Show last 5 runs
                ])
                self.prev_runs_label.configure(text=runs_text)
