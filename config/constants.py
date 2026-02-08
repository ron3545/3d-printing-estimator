"""Constants and configuration values for the 3D Printing Cost Calculator"""

# =========================
# PUBLISHER INFO (FIXED AT TOP)
# =========================
PUBLISHER_NAME = "gridform3D"

# =========================
# PRINTER CONFIGURATION FILE
# =========================
PRINTER_CONFIG_FILE = "printer_config.ini"

# Default printer configurations
DEFAULT_PRINTERS = {
    "Ender 3": {"wattage": 350, "lifetime_hours": 5000},
    "Prusa i3 MK3S+": {"wattage": 120, "lifetime_hours": 10000},
    "Anycubic Kobra": {"wattage": 250, "lifetime_hours": 5000},
    "Creality CR-10": {"wattage": 300, "lifetime_hours": 5000},
    "Bambu Lab X1 Carbon": {"wattage": 350, "lifetime_hours": 8000}
}

# =========================
# FORMULAS
# =========================
FILAMENT_GRAMS_PER_SPOOL = 1000  # grams per spool
ELECTRICITY_COST_FORMULA = lambda watts, hours, rate: (watts / 1000) * hours * rate
MATERIAL_COST_FORMULA = lambda cost_per_gram, grams: cost_per_gram * grams
LABOR_COST_FORMULA = lambda hours, rate: hours * rate
MACHINE_COST_FORMULA = lambda hours, cost_per_hour: hours * cost_per_hour
MARGIN_PRICE_FORMULA = lambda base_cost, margin_percent: base_cost / (1 - (margin_percent / 100)) if margin_percent < 100 else float('inf')
GRAND_TOTAL_FORMULA = lambda models_total, labor, packaging, shipping: models_total + labor + packaging + shipping

# =========================
# DEFAULT VALUES
# =========================

# Material defaults
DEFAULT_MATERIAL = "PLA"
DEFAULT_MATERIAL_PRICE = "900"
DEFAULT_GRAMS_USED = "0"

# Printer defaults
DEFAULT_PRINTER_TYPE = ""
DEFAULT_PRINTER_WATTAGE = "350"
DEFAULT_PRINT_HOURS = "0"
DEFAULT_ELECTRICITY_RATE = "18"
DEFAULT_MACHINE_COST_PER_HOUR = "0"

# Overall defaults
DEFAULT_LABOR_HOURS = "0"
DEFAULT_LABOR_RATE = "0"
DEFAULT_MARGIN_PERCENT = "50"
DEFAULT_PACKAGING = "0"
DEFAULT_SHIPPING = "0"

# Project defaults
DEFAULT_PROJECT_NAME = "My Project"

# Add-on defaults
DEFAULT_ADDON_QUANTITY = 0
DEFAULT_ADDON_PRICE = 0
