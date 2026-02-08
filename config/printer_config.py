"""Printer configuration management using ConfigParser (INI format)"""

import os
import configparser
from .constants import PRINTER_CONFIG_FILE, DEFAULT_PRINTERS


def load_printer_configs():
    """Load printer configurations from file, or return defaults if file doesn't exist"""
    if os.path.exists(PRINTER_CONFIG_FILE):
        try:
            config = configparser.ConfigParser()
            config.read(PRINTER_CONFIG_FILE)
            printers = {}
            for section in config.sections():
                printers[section] = {
                    "wattage": int(float(config.get(section, "wattage")))
                }
            return printers
        except Exception as e:
            print(f"Error loading printer config: {e}")
            return DEFAULT_PRINTERS.copy()
    return DEFAULT_PRINTERS.copy()


def save_printer_configs(configs):
    """Save printer configurations to file"""
    try:
        config = configparser.ConfigParser()
        for printer_name, details in configs.items():
            config[printer_name] = {
                "wattage": str(details["wattage"])
            }
        with open(PRINTER_CONFIG_FILE, 'w') as f:
            config.write(f)
        return True
    except Exception as e:
        print(f"Error saving printer config: {e}")
        return False
