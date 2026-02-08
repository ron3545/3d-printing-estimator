"""Configuration package for 3D Printing Cost Calculator"""

from .constants import *
from .printer_config import load_printer_configs, save_printer_configs

__all__ = [
    'PUBLISHER_NAME',
    'PRINTER_CONFIG_FILE',
    'DEFAULT_PRINTERS',
    'FILAMENT_GRAMS_PER_SPOOL',
    'ELECTRICITY_COST_FORMULA',
    'MATERIAL_COST_FORMULA',
    'LABOR_COST_FORMULA',
    'MACHINE_COST_FORMULA',
    'MARGIN_PRICE_FORMULA',
    'GRAND_TOTAL_FORMULA',
    'DEFAULT_MATERIAL',
    'DEFAULT_MATERIAL_PRICE',
    'DEFAULT_GRAMS_USED',
    'DEFAULT_PRINTER_TYPE',
    'DEFAULT_PRINTER_WATTAGE',
    'DEFAULT_PRINT_HOURS',
    'DEFAULT_ELECTRICITY_RATE',
    'DEFAULT_MACHINE_COST_PER_HOUR',
    'DEFAULT_LABOR_HOURS',
    'DEFAULT_LABOR_RATE',
    'DEFAULT_MARGIN_PERCENT',
    'DEFAULT_PACKAGING',
    'DEFAULT_SHIPPING',
    'DEFAULT_PROJECT_NAME',
    'DEFAULT_ADDON_QUANTITY',
    'DEFAULT_ADDON_PRICE',
    'load_printer_configs',
    'save_printer_configs'
]
