import tkinter as tk
from tkinter import ttk
from tkinter import TclError
from tkinter import filedialog
import json

# =========================
# PUBLISHER INFO (FIXED AT TOP)
# =========================
PUBLISHER_NAME = "gridform3D"


# =========================
# CONFIGURATION - EDIT ALL SETTINGS HERE
# =========================

# === FORMULAS ===
FILAMENT_GRAMS_PER_SPOOL = 1000  # grams per spool
ELECTRICITY_COST_FORMULA = lambda watts, hours, rate: (watts / 1000) * hours * rate
MATERIAL_COST_FORMULA = lambda cost_per_gram, grams: cost_per_gram * grams
LABOR_COST_FORMULA = lambda hours, rate: hours * rate
MACHINE_COST_FORMULA = lambda hours, cost_per_hour: hours * cost_per_hour
MARGIN_PRICE_FORMULA = lambda base_cost, margin_percent: base_cost / (1 - (margin_percent / 100)) if margin_percent < 100 else float('inf')
GRAND_TOTAL_FORMULA = lambda models_total, labor, packaging, shipping: models_total + labor + packaging + shipping

# === DEFAULT VALUES ===
# Material defaults
DEFAULT_MATERIAL = "PLA"
DEFAULT_MATERIAL_PRICE = "900"
DEFAULT_GRAMS_USED = "0"

# Printer defaults
DEFAULT_PRINTER_TYPE = ""
DEFAULT_PRINTER_WATTAGE = "350"
DEFAULT_PRINT_HOURS = "0"
DEFAULT_ELECTRICITY_RATE = "50"
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


# =========================
# MODEL FRAME
# =========================
class ModelFrame(ttk.LabelFrame):
    def __init__(self, parent, index):
        super().__init__(parent, text=f"Model {index}", relief="raised", borderwidth=2)
        self.index = index
        self.grid_columnconfigure(1, weight=1)

        self.create_fields()
        self.create_totals()
    
    def update_title(self):
        """Update the frame title with the model name"""
        self.config(text=self.model_name_var.get())
    
    def request_remove(self):
        """Request removal of this model from parent"""
        if hasattr(self, 'on_remove'):
            self.on_remove(self)
    
    def bind_clear_on_focus(self, entry_widget, variable):
        """Clear the field when focused (select all text)"""
        def on_focus_in(event):
            entry_widget.select_range(0, tk.END)
            entry_widget.icursor(tk.END)
        entry_widget.bind("<FocusIn>", on_focus_in)

    def create_fields(self):
        self.vars = {}
        row = 0

        # MODEL NAME and REMOVE BUTTON
        name_frame = ttk.Frame(self)
        name_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        name_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(name_frame, text="Model Name:", font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=0, sticky="w")
        self.model_name_var = tk.StringVar(value=f"Model {self.index}")
        name_entry = ttk.Entry(name_frame, textvariable=self.model_name_var, font=('TkDefaultFont', 10, 'bold'))
        name_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.model_name_var.trace_add("write", lambda *args: self.update_title())

        # Remove button
        self.remove_btn = ttk.Button(name_frame, text="✕ Remove", command=self.request_remove)
        self.remove_btn.grid(row=0, column=2, padx=5)

        row += 1

        # Quantity field
        ttk.Label(self, text="Quantity").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.quantity_var = tk.StringVar(value="1")
        self.quantity_var.trace_add("write", lambda *args: self.auto_calculate())
        quantity_entry = ttk.Entry(self, textvariable=self.quantity_var)
        quantity_entry.grid(row=row, column=1, sticky="ew", padx=5)
        self.bind_clear_on_focus(quantity_entry, self.quantity_var)
        self.vars["Quantity"] = self.quantity_var
        row += 1

        ttk.Separator(self, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        row += 1

        # MATERIAL SECTION
        ttk.Label(self, text="━━━ MATERIAL ━━━", font=('TkDefaultFont', 9, 'bold')).grid(
            row=row, column=0, columnspan=2, pady=(5, 2))
        row += 1

        material_fields = [
            ("Material", DEFAULT_MATERIAL),
            ("Material Price", DEFAULT_MATERIAL_PRICE),
            ("Cost per Gram", ""),
            ("Grams Used", DEFAULT_GRAMS_USED),
        ]

        for label, default in material_fields:
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            var = tk.StringVar(value=default)
            var.trace_add("write", lambda *args: self.auto_calculate())
            entry = ttk.Entry(self, textvariable=var)
            entry.grid(row=row, column=1, sticky="ew", padx=5)
            if label == "Cost per Gram":
                entry.state(["readonly"])
            else:
                self.bind_clear_on_focus(entry, var)
            self.vars[label] = var
            row += 1

        # Material cost output
        self.material_cost_label = ttk.Label(self, text="Total Material Cost: 0.00", foreground="blue")
        self.material_cost_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(2, 5))
        row += 1
        
        # PRINTER/ELECTRICITY SECTION
        ttk.Separator(self, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        row += 1
        ttk.Label(self, text="━━━ PRINTER & ELECTRICITY ━━━", font=('TkDefaultFont', 9, 'bold')).grid(
            row=row, column=0, columnspan=2, pady=(5, 2))
        row += 1
        
        printer_fields = [
            ("Printer Type", DEFAULT_PRINTER_TYPE),
            ("Printer Wattage", DEFAULT_PRINTER_WATTAGE),
            ("Electricity Rate / kWh", DEFAULT_ELECTRICITY_RATE),
            ("Machine Cost / Hour", DEFAULT_MACHINE_COST_PER_HOUR),
        ]

        for idx, (label, default) in enumerate(printer_fields):
            if idx == 2:  # Before "Electricity Rate / kWh"
                # Highlighted box for Print Time
                print_time_frame = ttk.LabelFrame(self, text="Print Time", padding=6)
                print_time_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=(2, 8))

                ttk.Label(print_time_frame, text="Print Days").grid(row=0, column=0, sticky="w", padx=5, pady=2)
                self.print_days_var = tk.StringVar(value="0")
                self.print_days_var.trace_add("write", lambda *args: self.auto_calculate())
                entry_days = ttk.Entry(print_time_frame, textvariable=self.print_days_var, width=8)
                entry_days.grid(row=0, column=1, sticky="ew", padx=5)
                self.bind_clear_on_focus(entry_days, self.print_days_var)
                self.vars["Print Days"] = self.print_days_var

                ttk.Label(print_time_frame, text="Print Hours").grid(row=1, column=0, sticky="w", padx=5, pady=2)
                self.print_hours_var = tk.StringVar(value=DEFAULT_PRINT_HOURS)
                self.print_hours_var.trace_add("write", lambda *args: self.auto_calculate())
                entry_hours = ttk.Entry(print_time_frame, textvariable=self.print_hours_var, width=8)
                entry_hours.grid(row=1, column=1, sticky="ew", padx=5)
                self.bind_clear_on_focus(entry_hours, self.print_hours_var)
                self.vars["Print Hours"] = self.print_hours_var

                ttk.Label(print_time_frame, text="Print Minutes").grid(row=2, column=0, sticky="w", padx=5, pady=2)
                self.print_minutes_var = tk.StringVar(value="0")
                self.print_minutes_var.trace_add("write", lambda *args: self.auto_calculate())
                entry_minutes = ttk.Entry(print_time_frame, textvariable=self.print_minutes_var, width=8)
                entry_minutes.grid(row=2, column=1, sticky="ew", padx=5)
                self.bind_clear_on_focus(entry_minutes, self.print_minutes_var)
                self.vars["Print Minutes"] = self.print_minutes_var

                row += 1

            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            var = tk.StringVar(value=default)
            var.trace_add("write", lambda *args: self.auto_calculate())
            entry = ttk.Entry(self, textvariable=var)
            entry.grid(row=row, column=1, sticky="ew", padx=5)
            self.bind_clear_on_focus(entry, var)
            self.vars[label] = var
            row += 1
        
        # Electricity cost output
        self.electricity_cost_label = ttk.Label(self, text="Total Electricity Cost: 0.00", foreground="blue")
        self.electricity_cost_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(2, 5))
        row += 1
        
        # Machine cost output
        self.machine_cost_label = ttk.Label(self, text="Total Machine Cost: 0.00", foreground="blue")
        self.machine_cost_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(2, 5))
        row += 1


    
    def auto_calculate(self):
        """Automatically calculate and update all cost labels in real-time"""
        try:
            # Material costs
            material_price = float(self.vars["Material Price"].get() or 0)
            grams_used = float(self.vars["Grams Used"].get() or 0)
            quantity = int(self.vars["Quantity"].get() or 1)

            cost_per_gram = material_price / FILAMENT_GRAMS_PER_SPOOL
            self.vars["Cost per Gram"].set(f"{cost_per_gram:.4f}")

            material_cost = MATERIAL_COST_FORMULA(cost_per_gram, grams_used) * quantity
            self.material_cost_label.config(text=f"Total Material Cost: {material_cost:.2f}")

            # Electricity costs
            watts = float(self.vars["Printer Wattage"].get() or 0)
            days = float(self.vars["Print Days"].get() or 0)
            hours = float(self.vars["Print Hours"].get() or 0)
            minutes = float(self.vars["Print Minutes"].get() or 0)
            total_hours = (days * 24) + hours + (minutes / 60)
            rate = float(self.vars["Electricity Rate / kWh"].get() or 0)
            electricity_cost = ELECTRICITY_COST_FORMULA(watts, total_hours, rate) * quantity
            self.electricity_cost_label.config(text=f"Total Electricity Cost: {electricity_cost:.2f}")

            # Machine costs
            machine_cost_per_hour = float(self.vars["Machine Cost / Hour"].get() or 0)
            machine_cost = MACHINE_COST_FORMULA(total_hours, machine_cost_per_hour) * quantity
            self.machine_cost_label.config(text=f"Total Machine Cost: {machine_cost:.2f}")

            # Total cost (without margin, labor, packaging, and shipping)
            total = material_cost + electricity_cost + machine_cost
            self.total_label.config(text=f"Total Cost: {total:.2f}")
        except (ValueError, TclError):
            # Handle invalid input gracefully
            pass

    def create_totals(self):
        # Add separator and total at the end
        ttk.Separator(self, orient='horizontal').grid(row=99, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.total_label = ttk.Label(self, text="Total Cost: 0.00", 
                                     font=('Segoe UI', 11, 'bold'), foreground="#2D6A4F")
        self.total_label.grid(row=100, column=0, columnspan=2, pady=10)

    def calculate(self):
        # Material costs
        material_price = float(self.vars["Material Price"].get())
        grams_used = float(self.vars["Grams Used"].get())
        quantity = int(self.vars["Quantity"].get() or 1)

        cost_per_gram = material_price / FILAMENT_GRAMS_PER_SPOOL
        self.vars["Cost per Gram"].set(f"{cost_per_gram:.4f}")

        material_cost = MATERIAL_COST_FORMULA(cost_per_gram, grams_used) * quantity
        self.material_cost_label.config(text=f"Total Material Cost: {material_cost:.2f}")

        # Electricity costs
        watts = float(self.vars["Printer Wattage"].get())
        days = float(self.vars["Print Days"].get())
        hours = float(self.vars["Print Hours"].get())
        minutes = float(self.vars["Print Minutes"].get())
        total_hours = (days * 24) + hours + (minutes / 60)
        rate = float(self.vars["Electricity Rate / kWh"].get())
        electricity_cost = ELECTRICITY_COST_FORMULA(watts, total_hours, rate) * quantity
        self.electricity_cost_label.config(text=f"Total Electricity Cost: {electricity_cost:.2f}")

        # Machine costs
        machine_cost_per_hour = float(self.vars["Machine Cost / Hour"].get())
        machine_cost = MACHINE_COST_FORMULA(total_hours, machine_cost_per_hour) * quantity
        self.machine_cost_label.config(text=f"Total Machine Cost: {machine_cost:.2f}")

        # Total cost (without margin, labor, packaging, and shipping)
        total = material_cost + electricity_cost + machine_cost
        self.total_label.config(text=f"Total Cost: {total:.2f}")

        return {
            "total": total,
            "material": material_cost,
            "electricity": electricity_cost,
            "machine": machine_cost
        }


# =========================
# MAIN APP
# =========================
class CostCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("3D Printing Cost Calculator")

        # Set initial window size (width x height)
        self.root.geometry("900x700")

        # Fullscreen state
        self.is_fullscreen = False
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)

        self.models = []
        self.addons = []


        # Top bar frame for publisher (right) and project name (left)
        topbar_frame = ttk.Frame(root)
        topbar_frame.pack(pady=(10, 0), padx=20, fill="x")

        # Project name (left)
        ttk.Label(topbar_frame, text="Project Name:", font=('TkDefaultFont', 10, 'bold')).pack(side="left", padx=5)
        self.project_name_var = tk.StringVar(value=DEFAULT_PROJECT_NAME)
        project_entry = ttk.Entry(topbar_frame, textvariable=self.project_name_var, font=('TkDefaultFont', 10), width=40)
        project_entry.pack(side="left", padx=5)

        # Publisher label (right, smaller)
        publisher_label = ttk.Label(topbar_frame, text=f"Created by {PUBLISHER_NAME}", font=("Arial", 9))
        publisher_label.pack(side="right", padx=5)

        # Select all text when clicked
        project_entry.bind("<FocusIn>", lambda e: (project_entry.select_range(0, tk.END), project_entry.icursor(tk.END)))

        # Button frame below project name
        button_frame = ttk.Frame(root)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="New Project", command=self.new_project).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Add Model", command=self.add_model).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Calculate All", command=self.calculate_all).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save Project", command=self.save_project).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Load Project", command=self.load_project).pack(side="left", padx=5)

        # Labor, Markup, and Discount inputs (applies to overall total only)
        inputs_frame = ttk.LabelFrame(root, text="Overall Labor, Markup & Discount", padding=10)
        inputs_frame.pack(pady=5, padx=20, fill="x")

        ttk.Label(inputs_frame, text="Labor Hours:").grid(row=0, column=0, sticky="w", padx=5)
        self.labor_hours_var = tk.StringVar(value=DEFAULT_LABOR_HOURS)
        labor_hours_entry = ttk.Entry(inputs_frame, textvariable=self.labor_hours_var, width=15)
        labor_hours_entry.grid(row=0, column=1, padx=5)
        labor_hours_entry.bind("<FocusIn>", lambda e: (labor_hours_entry.select_range(0, tk.END), labor_hours_entry.icursor(tk.END)))

        ttk.Label(inputs_frame, text="Labor Rate:").grid(row=0, column=2, sticky="w", padx=5)
        self.labor_rate_var = tk.StringVar(value=DEFAULT_LABOR_RATE)
        labor_rate_entry = ttk.Entry(inputs_frame, textvariable=self.labor_rate_var, width=15)
        labor_rate_entry.grid(row=0, column=3, padx=5)
        labor_rate_entry.bind("<FocusIn>", lambda e: (labor_rate_entry.select_range(0, tk.END), labor_rate_entry.icursor(tk.END)))

        ttk.Label(inputs_frame, text="Margin %:").grid(row=0, column=4, sticky="w", padx=5)
        self.margin_percent_var = tk.StringVar(value=DEFAULT_MARGIN_PERCENT)
        margin_entry = ttk.Entry(inputs_frame, textvariable=self.margin_percent_var, width=15)
        margin_entry.grid(row=0, column=5, padx=5)
        margin_entry.bind("<FocusIn>", lambda e: (margin_entry.select_range(0, tk.END), margin_entry.icursor(tk.END)))

        ttk.Label(inputs_frame, text="Discount %:").grid(row=1, column=0, sticky="w", padx=5)
        self.discount_var = tk.StringVar(value="0")
        discount_entry = ttk.Entry(inputs_frame, textvariable=self.discount_var, width=15)
        discount_entry.grid(row=1, column=1, padx=5)
        discount_entry.bind("<FocusIn>", lambda e: (discount_entry.select_range(0, tk.END), discount_entry.icursor(tk.END)))

        ttk.Label(inputs_frame, text="Packaging:").grid(row=1, column=2, sticky="w", padx=5)
        self.packaging_var = tk.StringVar(value=DEFAULT_PACKAGING)
        packaging_entry = ttk.Entry(inputs_frame, textvariable=self.packaging_var, width=15)
        packaging_entry.grid(row=1, column=3, padx=5)
        packaging_entry.bind("<FocusIn>", lambda e: (packaging_entry.select_range(0, tk.END), packaging_entry.icursor(tk.END)))

        ttk.Label(inputs_frame, text="Shipping:").grid(row=1, column=4, sticky="w", padx=5)
        self.shipping_var = tk.StringVar(value=DEFAULT_SHIPPING)
        shipping_entry = ttk.Entry(inputs_frame, textvariable=self.shipping_var, width=15)
        shipping_entry.grid(row=1, column=5, padx=5)
        shipping_entry.bind("<FocusIn>", lambda e: (shipping_entry.select_range(0, tk.END), shipping_entry.icursor(tk.END)))

        # Main container for models and overall totals
        main_container = ttk.Frame(root)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left side: scrollable models
        models_container = ttk.Frame(main_container)
        models_container.pack(side="left", fill="both", expand=True)

        # Create scrollable canvas
        canvas_frame = ttk.Frame(models_container)
        canvas_frame.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", height=50)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.update_scrollbars()
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # Store scrollbar references
        self.h_scrollbar = h_scrollbar
        self.v_scrollbar = v_scrollbar
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        # v_scrollbar will be shown/hidden dynamically
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Store canvas_frame for scrollbar management
        self.canvas_frame = canvas_frame
        
        # Enable mouse wheel scrolling
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_h_mousewheel)
        self.canvas.bind_all("<MouseWheel>", self._on_v_mousewheel)

        # Right side: Container for addons and overall totals
        right_container = ttk.Frame(main_container, width=350)
        right_container.pack(side="right", fill="y", padx=(10, 0))
        right_container.pack_propagate(False)
        
        # Add-ons section (top of right side) - fixed height
        addons_outer_frame = ttk.LabelFrame(right_container, text="━━━ ADDITIONAL MATERIALS ━━━", padding=10, height=200)
        addons_outer_frame.pack(fill="x", pady=(0, 10))
        addons_outer_frame.pack_propagate(False)
        
        # Header row (fixed, not scrollable)
        header_frame = ttk.Frame(addons_outer_frame)
        header_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(header_frame, text="Name", font=('TkDefaultFont', 8, 'bold')).grid(row=0, column=0, padx=2, pady=2, sticky="w")
        ttk.Label(header_frame, text="Qty", font=('TkDefaultFont', 8, 'bold')).grid(row=0, column=1, padx=2, pady=2, sticky="w")
        ttk.Label(header_frame, text="Price", font=('TkDefaultFont', 8, 'bold')).grid(row=0, column=2, padx=2, pady=2, sticky="w")
        ttk.Label(header_frame, text="Total", font=('TkDefaultFont', 8, 'bold')).grid(row=0, column=3, padx=2, pady=2, sticky="w")
        
        ttk.Button(header_frame, text="+", command=self.add_addon, width=3).grid(row=0, column=4, padx=2, pady=2)
        
        # Scrollable container for addons
        canvas_container = ttk.Frame(addons_outer_frame)
        canvas_container.pack(fill="both", expand=True)
        
        addons_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical")
        addons_scrollbar.pack(side="right", fill="y")
        
        self.addons_canvas = tk.Canvas(canvas_container, bg="white", highlightthickness=1, highlightbackground="#cccccc", yscrollcommand=addons_scrollbar.set)
        self.addons_canvas.pack(side="left", fill="both", expand=True)
        
        addons_scrollbar.config(command=self.addons_canvas.yview)
        
        self.addons_scrollable_frame = tk.Frame(self.addons_canvas, bg="white")
        
        self.addons_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.addons_canvas.configure(scrollregion=self.addons_canvas.bbox("all"))
        )
        
        self.addons_canvas.create_window((0, 0), window=self.addons_scrollable_frame, anchor="nw")
        
        # Enable mouse wheel scrolling for addons
        self.addons_canvas.bind_all("<MouseWheel>", self._on_addons_mousewheel)
        
        self.addons_frame = self.addons_scrollable_frame

        # Overall totals section (bottom of right side)
        overall_frame = ttk.LabelFrame(right_container, text="━━━ OVERALL TOTALS ━━━", padding=5)
        overall_frame.pack(fill="both", expand=True)
        
        label_font = ('Segoe UI', 9)
        
        self.overall_material = ttk.Label(overall_frame, text="Total Material Cost: 0.00", 
                                         font=label_font, foreground="#2E86AB")
        self.overall_material.pack(anchor="w", pady=1)
        
        self.overall_electricity = ttk.Label(overall_frame, text="Total Electricity Cost: 0.00", 
                                            font=label_font, foreground="#A23B72")
        self.overall_electricity.pack(anchor="w", pady=1)
        
        self.overall_machine = ttk.Label(overall_frame, text="Total Machine Cost: 0.00", 
                                        font=label_font, foreground="#8B4513")
        self.overall_machine.pack(anchor="w", pady=1)
        
        self.overall_labor = ttk.Label(overall_frame, text="Total Labor Cost: 0.00", 
                                      font=label_font, foreground="#F18F01")
        self.overall_labor.pack(anchor="w", pady=1)
        
        self.overall_addons = ttk.Label(overall_frame, text="Total Add-ons Cost: 0.00", 
                                       font=label_font, foreground="#C73E1D")
        self.overall_addons.pack(anchor="w", pady=1)
        
        self.overall_packaging_shipping = ttk.Label(overall_frame, text="Packaging & Shipping: 0.00", 
                                                   font=label_font, foreground="#6A4C93")
        self.overall_packaging_shipping.pack(anchor="w", pady=1)
        
        ttk.Separator(overall_frame, orient='horizontal').pack(fill="x", pady=5)

        # Summary at the bottom
        self.overall_subtotal = ttk.Label(overall_frame, text="SUBTOTAL (Cost): 0.00", 
                                font=('Segoe UI', 10, 'bold'), foreground="#555555")
        self.overall_subtotal.pack(anchor="w", pady=1)
        
        self.summary = ttk.Label(overall_frame, text="PRICE (with margin): 0.00", 
                    font=('Segoe UI', 11, 'bold'), foreground="#2D6A4F")
        self.summary.pack(anchor="w", pady=2)

        # Divider before price after discount
        ttk.Separator(overall_frame, orient='horizontal').pack(fill="x", pady=5)

        self.price_after_discount = ttk.Label(overall_frame, text="PRICE AFTER DISCOUNT: 0.00", 
                font=('Segoe UI', 11, 'bold'), foreground="#A23B72")
        self.price_after_discount.pack(anchor="w", pady=(2,0))

        self.discount_display = ttk.Label(overall_frame, text="Discount: 0.00", font=('Segoe UI', 8), foreground="#555555")
        self.discount_display.pack(anchor="w", pady=(0,4))
        
        # Create one model frame at startup
        self.add_model()
    
    def _on_h_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    def _on_v_mousewheel(self, event):
        # Only scroll if vertical scrollbar is visible
        if self.v_scrollbar.winfo_ismapped():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _on_addons_mousewheel(self, event):
    
        # Check if mouse is over the addons canvas
        try:
            widget = event.widget.winfo_containing(event.x_root, event.y_root)
            if widget and (widget == self.addons_canvas or self.addons_canvas in str(widget)):
                self.addons_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except:
            pass

    def update_scrollbars(self):
        """Update scrollregion and show/hide vertical scrollbar based on content size"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # If there are models, expand canvas to fill space, otherwise keep it minimal
        if self.models:
            self.canvas.config(height=0)  # Let it expand naturally
        else:
            self.canvas.config(height=50)  # Keep it small when empty
        
        # Check if vertical scrolling is needed
        bbox = self.canvas.bbox("all")
        if bbox:
            content_height = bbox[3] - bbox[1]
            canvas_height = self.canvas.winfo_height()
            
            # Show vertical scrollbar only if content is taller than canvas
            if content_height > canvas_height:
                self.v_scrollbar.grid(row=0, column=1, sticky="ns")
            else:
                self.v_scrollbar.grid_forget()

    def toggle_fullscreen(self, event):
        """Toggle fullscreen mode"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        if not self.is_fullscreen:
            self.root.geometry("900x700")
        return "break"
    
    def exit_fullscreen(self, event):
        """Exit fullscreen mode"""
        self.is_fullscreen = False
        self.root.attributes("-fullscreen", False)
        self.root.geometry("900x700")
        return "break"
    
    def add_addon(self):
        row = len(self.addons)
        name = tk.StringVar()
        quantity = tk.DoubleVar(value=DEFAULT_ADDON_QUANTITY)
        price_per_unit = tk.DoubleVar(value=DEFAULT_ADDON_PRICE)
        
        # Calculate total when quantity or price changes
        def update_addon_total(*args):
            try:
                total = quantity.get() * price_per_unit.get()
                total_label.config(text=f"{total:.2f}")
            except:
                pass
        
        quantity.trace_add("write", update_addon_total)
        price_per_unit.trace_add("write", update_addon_total)

        # Configure column widths to match header
        self.addons_frame.grid_columnconfigure(0, minsize=80)
        self.addons_frame.grid_columnconfigure(1, minsize=50)
        self.addons_frame.grid_columnconfigure(2, minsize=60)
        self.addons_frame.grid_columnconfigure(3, minsize=60)
        
        # Name entry
        name_entry = ttk.Entry(self.addons_frame, textvariable=name, width=12)
        name_entry.grid(row=row, column=0, padx=2, pady=2, sticky="ew")
        
        # Quantity entry
        qty_entry = ttk.Entry(self.addons_frame, textvariable=quantity, width=6)
        qty_entry.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
        qty_entry.bind("<FocusIn>", lambda e: (qty_entry.select_range(0, tk.END), qty_entry.icursor(tk.END)))
        
        # Price per unit entry
        price_entry = ttk.Entry(self.addons_frame, textvariable=price_per_unit, width=8)
        price_entry.grid(row=row, column=2, padx=2, pady=2, sticky="ew")
        price_entry.bind("<FocusIn>", lambda e: (price_entry.select_range(0, tk.END), price_entry.icursor(tk.END)))
        
        # Total label (calculated)
        total_label = ttk.Label(self.addons_frame, text="0.00", width=8, foreground="blue")
        total_label.grid(row=row, column=3, padx=2, pady=2, sticky="w")
        
        # Remove button
        remove_btn = ttk.Button(
            self.addons_frame,
            text="✕",
            width=3,
            command=lambda: self.remove_addon(row, name_entry, qty_entry, price_entry, total_label, remove_btn, quantity, price_per_unit, name)
        )
        remove_btn.grid(row=row, column=4, padx=2, pady=2)

        self.addons.append((name, quantity, price_per_unit))
    
    def remove_addon(self, row, name_entry, qty_entry, price_entry, total_label, remove_btn, quantity_var, price_var, name_var):
        # Remove the widgets
        name_entry.destroy()
        qty_entry.destroy()
        price_entry.destroy()
        total_label.destroy()
        remove_btn.destroy()
        
        # Remove from the addons list
        addon_tuple = (name_var, quantity_var, price_var)
        if addon_tuple in self.addons:
            self.addons.remove(addon_tuple)
        
        # Force canvas to update its scroll region
        self.addons_canvas.update_idletasks()
        self.addons_canvas.configure(scrollregion=self.addons_canvas.bbox("all"))
    
    def add_model(self):
        model = ModelFrame(self.scrollable_frame, len(self.models) + 1)
        model.on_remove = self.remove_model  # Bind the remove callback
        model.pack(side="left", fill="y", padx=20, pady=5)
        self.models.append(model)
    
    def remove_model(self, model):
        """Remove a model from the list and destroy its widget"""
        if model in self.models:
            self.models.remove(model)
            model.destroy()
    
    def new_project(self):
        """Clear all data and start a new project"""
        # Clear all models
        for model in self.models[:]:
            model.destroy()
        self.models.clear()
        
        # Clear all addons
        for name_var, qty_var, price_var in self.addons[:]:
            # Find and destroy addon widgets
            pass  # Widgets are already destroyed when we clear the frame children
        self.addons.clear()
        
        # Destroy addon widgets (except header row)
        for child in self.addons_frame.grid_slaves():
            info = child.grid_info()
            if info and info.get('row', 0) > 0:
                child.destroy()
        
        # Destroy all remaining children in scrollable_frame
        for child in self.scrollable_frame.winfo_children():
            child.destroy()
        
        # Reset project name
        self.project_name_var.set(DEFAULT_PROJECT_NAME)
        
        # Reset overall inputs to defaults
        self.labor_hours_var.set(DEFAULT_LABOR_HOURS)
        self.labor_rate_var.set(DEFAULT_LABOR_RATE)
        self.margin_percent_var.set(DEFAULT_MARGIN_PERCENT)
        self.packaging_var.set(DEFAULT_PACKAGING)
        self.shipping_var.set(DEFAULT_SHIPPING)
        
        # Reset overall totals display
        self.overall_material.config(text="Total Material Cost: 0.00")
        self.overall_electricity.config(text="Total Electricity Cost: 0.00")
        self.overall_machine.config(text="Total Machine Cost: 0.00")
        self.overall_labor.config(text="Total Labor Cost: 0.00")
        self.overall_addons.config(text="Total Add-ons Cost: 0.00")
        self.overall_packaging_shipping.config(text="Packaging & Shipping: 0.00")
        self.overall_subtotal.config(text="SUBTOTAL (Cost): 0.00")
        self.summary.config(text="PRICE (with margin): 0.00")
        
        # Reset canvas to minimal height when empty
        self.canvas.config(height=50)
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.canvas.configure(scrollregion=(0, 0, 1, 1))
        self.v_scrollbar.grid_forget()
        self.canvas.update()
        
        # Create one model frame for the new project
        self.add_model()
        
        # Reset the frame size back to natural
        self.scrollable_frame.config(width=0, height=0)

    def save_project(self):
        """Save all project data to a JSON file"""
        # Use project name as default filename
        default_name = self.project_name_var.get().strip() or "project"
        # Remove invalid filename characters
        default_name = "".join(c for c in default_name if c.isalnum() or c in (' ', '-', '_')).strip()
        default_name = default_name.replace(' ', '_')
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Project",
            initialfile=f"{default_name}.json"
        )
        
        if not file_path:
            return
        
        # Collect all data
        project_data = {
            "project_name": self.project_name_var.get(),
            "overall": {
                "labor_hours": self.labor_hours_var.get(),
                "labor_rate": self.labor_rate_var.get(),
                "margin_percent": self.margin_percent_var.get(),
                "packaging": self.packaging_var.get(),
                "shipping": self.shipping_var.get()
            },
            "addons": [],
            "models": []
        }

        
        # Save add-ons data (project level)
        for name_var, qty_var, price_var in self.addons:
            project_data["addons"].append({
                "name": name_var.get(),
                "quantity": qty_var.get(),
                "price_per_unit": price_var.get()
            })
        
        # Save each model's data
        for model in self.models:
            model_data = {
                "name": model.model_name_var.get(),
                "material": model.vars["Material"].get(),
                "material_price": model.vars["Material Price"].get(),
                "grams_used": model.vars["Grams Used"].get(),
                "printer_type": model.vars["Printer Type"].get(),
                "printer_wattage": model.vars["Printer Wattage"].get(),
                "print_hours": model.vars["Print Hours"].get(),
                "electricity_rate": model.vars["Electricity Rate / kWh"].get(),
                "machine_cost_per_hour": model.vars["Machine Cost / Hour"].get()
            }
            
            project_data["models"].append(model_data)
        
        # Save to file
        try:
            with open(file_path, 'w') as f:
                json.dump(project_data, f, indent=2)
            print(f"Project saved to {file_path}")
        except Exception as e:
            print(f"Error saving project: {e}")
    
    def load_project(self):
        """Load project data from a JSON file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Project"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                project_data = json.load(f)
            
            # Clear existing models
            for model in self.models[:]:
                model.destroy()
            self.models.clear()
            
            # Clear existing addons
            for child in self.addons_frame.grid_slaves():
                info = child.grid_info()
                if info and info.get('row', 0) > 0:
                    child.destroy()
            self.addons.clear()
            
            # Load project name
            self.project_name_var.set(project_data.get("project_name", DEFAULT_PROJECT_NAME))
            
            # Load overall settings
            overall = project_data.get("overall", {})
            self.labor_hours_var.set(overall.get("labor_hours", DEFAULT_LABOR_HOURS))
            self.labor_rate_var.set(overall.get("labor_rate", DEFAULT_LABOR_RATE))
            self.margin_percent_var.set(overall.get("margin_percent", overall.get("markup_percent", DEFAULT_MARGIN_PERCENT)))
            self.packaging_var.set(overall.get("packaging", DEFAULT_PACKAGING))
            self.shipping_var.set(overall.get("shipping", DEFAULT_SHIPPING))
            
            # Load add-ons
            for addon_data in project_data.get("addons", []):
                self.add_addon()
                if self.addons:
                    name_var, qty_var, price_var = self.addons[-1]
                    name_var.set(addon_data.get("name", ""))
                    qty_var.set(addon_data.get("quantity", 0))
                    price_var.set(addon_data.get("price_per_unit", 0))
            
            # Load models
            for model_data in project_data.get("models", []):
                # Create new model
                model = ModelFrame(self.scrollable_frame, len(self.models) + 1)
                model.on_remove = self.remove_model
                model.pack(side="left", fill="y", padx=20, pady=5)
                self.models.append(model)
                
                # Set model data
                model.model_name_var.set(model_data.get("name", f"Model {len(self.models)}"))
                model.vars["Material"].set(model_data.get("material", DEFAULT_MATERIAL))
                model.vars["Material Price"].set(model_data.get("material_price", DEFAULT_MATERIAL_PRICE))
                model.vars["Grams Used"].set(model_data.get("grams_used", DEFAULT_GRAMS_USED))
                model.vars["Printer Type"].set(model_data.get("printer_type", DEFAULT_PRINTER_TYPE))
                model.vars["Printer Wattage"].set(model_data.get("printer_wattage", DEFAULT_PRINTER_WATTAGE))
                model.vars["Print Hours"].set(model_data.get("print_hours", DEFAULT_PRINT_HOURS))
                model.vars["Electricity Rate / kWh"].set(model_data.get("electricity_rate", DEFAULT_ELECTRICITY_RATE))
                model.vars["Machine Cost / Hour"].set(model_data.get("machine_cost_per_hour", DEFAULT_MACHINE_COST_PER_HOUR))
                
                # Trigger auto-calculation
                model.auto_calculate()
            
            print(f"Project loaded from {file_path}")
        except Exception as e:
            print(f"Error loading project: {e}")
            import traceback
            traceback.print_exc()
    
    def calculate_all(self):
        # Calculate totals from all models
        models_total = 0
        total_material = 0
        total_electricity = 0
        total_machine = 0

        for model in self.models:
            result = model.calculate()
            models_total += result["total"]
            total_material += result["material"]
            total_electricity += result["electricity"]
            total_machine += result["machine"]

        # Calculate overall add-ons cost
        total_addons = sum(qty.get() * price.get() for name, qty, price in self.addons)

        # Apply labor (overall only)
        labor_hours = float(self.labor_hours_var.get() or 0)
        labor_rate = float(self.labor_rate_var.get() or 0)
        total_labor = LABOR_COST_FORMULA(labor_hours, labor_rate)

        # Apply packaging and shipping (overall only)
        packaging = float(self.packaging_var.get() or 0)
        shipping = float(self.shipping_var.get() or 0)

        # Calculate subtotal (total cost)
        subtotal = GRAND_TOTAL_FORMULA(models_total, total_labor, packaging, shipping)

        # Apply margin pricing formula
        margin_percent = float(self.margin_percent_var.get() or 0)
        final_price = MARGIN_PRICE_FORMULA(subtotal, margin_percent)

        # Apply discount (after margin)
        discount_percent = float(self.discount_var.get() or 0)
        discount_amount = final_price * (discount_percent / 100)
        final_price_after_discount = max(0, final_price - discount_amount)

        self.overall_material.config(text=f"Total Material Cost: {total_material:.2f}")
        self.overall_electricity.config(text=f"Total Electricity Cost: {total_electricity:.2f}")
        self.overall_machine.config(text=f"Total Machine Cost: {total_machine:.2f}")
        self.overall_labor.config(text=f"Total Labor Cost: {total_labor:.2f}")
        self.overall_addons.config(text=f"Total Add-ons Cost: {total_addons:.2f}")
        self.overall_packaging_shipping.config(text=f"Packaging & Shipping: {packaging + shipping:.2f}")
        self.overall_subtotal.config(text=f"SUBTOTAL (Cost): {subtotal:.2f}")
        self.summary.config(text=f"PRICE (with {margin_percent:.0f}% margin): {final_price:.2f}")
        self.price_after_discount.config(text=f"PRICE AFTER DISCOUNT: {final_price_after_discount:.2f}")
        self.discount_display.config(text=f"Discount: {discount_amount:.2f}")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = CostCalculatorApp(root)
        root.mainloop()
    except Exception as e:
        pass
