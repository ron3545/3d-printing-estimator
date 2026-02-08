"""
3D Printing Cost Calculator
Entry point for the application

This application helps calculate the total cost of 3D printing projects,
including materials, electricity, machine wear, labor, and additional materials.
"""

import tkinter as tk
from ui import CostCalculatorApp


def main():
    """Initialize and run the application"""
    try:
        root = tk.Tk()
        app = CostCalculatorApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
