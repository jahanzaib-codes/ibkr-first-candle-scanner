import sys
import os

# Add src folder to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import customtkinter as ctk
from datetime import datetime
import logging

from gui import ScannerGUI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the IBKR First Candle Market Scanner."""
    
    # Set appearance mode and default color theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create main application window
    app = ScannerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
