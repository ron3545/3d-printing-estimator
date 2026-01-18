import tkinter as tk
from tkinter import ttk
from tkinter import TclError
from tkinter import filedialog
import json

# =========================
# CONFIGURATION - EDIT ALL SETTINGS HERE
# =========================

# === FORMULAS ===
FILAMENT_GRAMS_PER_SPOOL = 1000  # grams per spool
ELECTRICITY_COST_FORMULA = lambda watts, hours, rate: (watts / 1000) * hours * rate
MATERIAL_COST_FORMULA = lambda cost_per_gram, grams: cost_per_gram * grams
LABOR_COST_FORMULA = lambda hours, rate: hours * rate
CUSTOM_MARKUP_FORMULA = lambda base_cost, markup_percent: base_cost * (markup_percent / 100)
GRAND_TOTAL_FORMULA = lambda models_total, labor, packaging, shipping, markup: models_total + labor + packaging + shipping + markup

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

# Overall defaults
DEFAULT_LABOR_HOURS = "0"
DEFAULT_LABOR_RATE = "0"
DEFAULT_MARKUP_PERCENT = "50"
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

        self.addons = []

        self.create_fields()
        self.create_addons_section()
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
                # Bind clear on focus (select all) for all editable fields
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
            ("Print Hours", DEFAULT_PRINT_HOURS),
            ("Electricity Rate / kWh", DEFAULT_ELECTRICITY_RATE),
        ]
        
        for label, default in printer_fields:
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            var = tk.StringVar(value=default)
            var.trace_add("write", lambda *args: self.auto_calculate())
            entry = ttk.Entry(self, textvariable=var)
            entry.grid(row=row, column=1, sticky="ew", padx=5)
            # Bind clear on focus (select all) for all fields
            self.bind_clear_on_focus(entry, var)
            self.vars[label] = var
            row += 1
        
        # Electricity cost output
        self.electricity_cost_label = ttk.Label(self, text="Total Electricity Cost: 0.00", foreground="blue")
        self.electricity_cost_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(2, 5))
        row += 1
        
        # Add-ons section
        ttk.Separator(self, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        row += 1
        
        self.addon_row = row

    def create_addons_section(self):
        row = self.addon_row
        self.addon_frame = ttk.LabelFrame(self, text="Additional Materials")
        self.addon_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        row += 1

        # Column headers
        ttk.Label(self.addon_frame, text="Name", font=('TkDefaultFont', 8, 'bold')).grid(row=0, column=0, padx=2, pady=2)
        ttk.Label(self.addon_frame, text="Qty", font=('TkDefaultFont', 8, 'bold')).grid(row=0, column=1, padx=2, pady=2)
        ttk.Label(self.addon_frame, text="Price/Unit", font=('TkDefaultFont', 8, 'bold')).grid(row=0, column=2, padx=2, pady=2)
        ttk.Label(self.addon_frame, text="Total", font=('TkDefaultFont', 8, 'bold')).grid(row=0, column=3, padx=2, pady=2)
        
        ttk.Button(
            self.addon_frame,
            text="Add",
            command=self.add_addon
        ).grid(row=0, column=4, padx=2, pady=2)
        
        # Add-ons cost output
        self.addons_cost_label = ttk.Label(self, text="Total Add-ons: 0.00", foreground="blue")
        self.addons_cost_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(2, 5))

    def add_addon(self):
        row = len(self.addons) + 1
        name = tk.StringVar()
        quantity = tk.DoubleVar(value=DEFAULT_ADDON_QUANTITY)
        price_per_unit = tk.DoubleVar(value=DEFAULT_ADDON_PRICE)
        
        # Calculate total when quantity or price changes
        def update_addon_total(*args):
            try:
                total = quantity.get() * price_per_unit.get()
                total_label.config(text=f"{total:.2f}")
                self.auto_calculate()
            except:
                pass
        
        quantity.trace_add("write", update_addon_total)
        price_per_unit.trace_add("write", update_addon_total)

        # Name entry
        name_entry = ttk.Entry(self.addon_frame, textvariable=name, width=15)
        name_entry.grid(row=row, column=0, padx=2, pady=2)
        
        # Quantity entry
        qty_entry = ttk.Entry(self.addon_frame, textvariable=quantity, width=8)
        qty_entry.grid(row=row, column=1, padx=2, pady=2)
        self.bind_clear_on_focus(qty_entry, quantity)
        
        # Price per unit entry
        price_entry = ttk.Entry(self.addon_frame, textvariable=price_per_unit, width=8)
        price_entry.grid(row=row, column=2, padx=2, pady=2)
        self.bind_clear_on_focus(price_entry, price_per_unit)
        
        # Total label (calculated)
        total_label = ttk.Label(self.addon_frame, text="0.00", width=8, foreground="blue")
        total_label.grid(row=row, column=3, padx=2, pady=2)
        
        # Remove button
        remove_btn = ttk.Button(
            self.addon_frame,
            text="Remove",
            command=lambda: self.remove_addon(row, name_entry, qty_entry, price_entry, total_label, remove_btn, quantity, price_per_unit)
        )
        remove_btn.grid(row=row, column=4, padx=2, pady=2)

        self.addons.append((quantity, price_per_unit))
    
    def remove_addon(self, row, name_entry, qty_entry, price_entry, total_label, remove_btn, quantity_var, price_var):
        # Remove the widgets
        name_entry.destroy()
        qty_entry.destroy()
        price_entry.destroy()
        total_label.destroy()
        remove_btn.destroy()
        
        # Remove from the addons list
        addon_tuple = (quantity_var, price_var)
        if addon_tuple in self.addons:
            self.addons.remove(addon_tuple)
        
        self.auto_calculate()
    
    def auto_calculate(self):
        """Automatically calculate and update all cost labels in real-time"""
        try:
            # Material costs
            material_price = float(self.vars["Material Price"].get() or 0)
            grams_used = float(self.vars["Grams Used"].get() or 0)

            cost_per_gram = material_price / FILAMENT_GRAMS_PER_SPOOL
            self.vars["Cost per Gram"].set(f"{cost_per_gram:.4f}")

            material_cost = MATERIAL_COST_FORMULA(cost_per_gram, grams_used)
            self.material_cost_label.config(text=f"Total Material Cost: {material_cost:.2f}")

            # Electricity costs
            watts = float(self.vars["Printer Wattage"].get() or 0)
            hours = float(self.vars["Print Hours"].get() or 0)
            rate = float(self.vars["Electricity Rate / kWh"].get() or 0)
            electricity_cost = ELECTRICITY_COST_FORMULA(watts, hours, rate)
            self.electricity_cost_label.config(text=f"Total Electricity Cost: {electricity_cost:.2f}")

            # Add-ons costs
            addons_cost = sum(qty.get() * price.get() for qty, price in self.addons)
            self.addons_cost_label.config(text=f"Total Add-ons: {addons_cost:.2f}")

            # Total cost (without markup, labor, packaging, and shipping)
            total = material_cost + electricity_cost + addons_cost
            self.total_label.config(text=f"Total Cost: {total:.2f}")
        except (ValueError, TclError):
            # Handle invalid input gracefully
            pass

    def create_totals(self):
        row = self.addon_row + 2  # Place below the addons cost label
        
        self.total_label = ttk.Label(self, text="Total Cost: 0.00", 
                                     font=('Segoe UI', 11, 'bold'), foreground="#2D6A4F")
        self.total_label.grid(row=row, column=0, columnspan=2, pady=10)

    def calculate(self):
        # Material costs
        material_price = float(self.vars["Material Price"].get())
        grams_used = float(self.vars["Grams Used"].get())

        cost_per_gram = material_price / FILAMENT_GRAMS_PER_SPOOL
        self.vars["Cost per Gram"].set(f"{cost_per_gram:.4f}")

        material_cost = MATERIAL_COST_FORMULA(cost_per_gram, grams_used)
        self.material_cost_label.config(text=f"Total Material Cost: {material_cost:.2f}")

        # Electricity costs
        watts = float(self.vars["Printer Wattage"].get())
        hours = float(self.vars["Print Hours"].get())
        rate = float(self.vars["Electricity Rate / kWh"].get())
        electricity_cost = ELECTRICITY_COST_FORMULA(watts, hours, rate)
        self.electricity_cost_label.config(text=f"Total Electricity Cost: {electricity_cost:.2f}")

        # Add-ons costs
        addons_cost = sum(qty.get() * price.get() for qty, price in self.addons)
        self.addons_cost_label.config(text=f"Total Add-ons: {addons_cost:.2f}")

        # Total cost (without markup, labor, packaging, and shipping)
        total = material_cost + electricity_cost + addons_cost
        self.total_label.config(text=f"Total Cost: {total:.2f}")

        return {
            "total": total,
            "material": material_cost,
            "electricity": electricity_cost,
            "addons": addons_cost
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

        # Project name frame at the top
        name_frame = ttk.Frame(root)
        name_frame.pack(pady=(10, 5), padx=20, fill="x")
        ttk.Label(name_frame, text="Project Name:", font=('TkDefaultFont', 10, 'bold')).pack(side="left", padx=5)
        self.project_name_var = tk.StringVar(value=DEFAULT_PROJECT_NAME)
        project_entry = ttk.Entry(name_frame, textvariable=self.project_name_var, font=('TkDefaultFont', 10), width=40)
        project_entry.pack(side="left", padx=5)
        # Select all text when clicked
        project_entry.bind("<FocusIn>", lambda e: (project_entry.select_range(0, tk.END), project_entry.icursor(tk.END)))

        # Button frame at the top
        button_frame = ttk.Frame(root)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="New Project", command=self.new_project).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Add Model", command=self.add_model).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Calculate All", command=self.calculate_all).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save Project", command=self.save_project).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Load Project", command=self.load_project).pack(side="left", padx=5)

        # Labor and Markup inputs (applies to overall total only)
        inputs_frame = ttk.LabelFrame(root, text="Overall Labor & Markup", padding=10)
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
        
        ttk.Label(inputs_frame, text="Markup %:").grid(row=0, column=4, sticky="w", padx=5)
        self.markup_percent_var = tk.StringVar(value=DEFAULT_MARKUP_PERCENT)
        markup_entry = ttk.Entry(inputs_frame, textvariable=self.markup_percent_var, width=15)
        markup_entry.grid(row=0, column=5, padx=5)
        markup_entry.bind("<FocusIn>", lambda e: (markup_entry.select_range(0, tk.END), markup_entry.icursor(tk.END)))
        
        ttk.Label(inputs_frame, text="Packaging:").grid(row=1, column=0, sticky="w", padx=5)
        self.packaging_var = tk.StringVar(value=DEFAULT_PACKAGING)
        packaging_entry = ttk.Entry(inputs_frame, textvariable=self.packaging_var, width=15)
        packaging_entry.grid(row=1, column=1, padx=5)
        packaging_entry.bind("<FocusIn>", lambda e: (packaging_entry.select_range(0, tk.END), packaging_entry.icursor(tk.END)))
        
        ttk.Label(inputs_frame, text="Shipping:").grid(row=1, column=2, sticky="w", padx=5)
        self.shipping_var = tk.StringVar(value=DEFAULT_SHIPPING)
        shipping_entry = ttk.Entry(inputs_frame, textvariable=self.shipping_var, width=15)
        shipping_entry.grid(row=1, column=3, padx=5)
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

        # Right side: Overall totals section (fixed)
        overall_frame = ttk.LabelFrame(main_container, text="━━━ OVERALL TOTALS (ALL MODELS) ━━━", padding=10, width=300)
        overall_frame.pack(side="right", fill="y", padx=(10, 0))
        overall_frame.pack_propagate(False)  # Keep fixed width
        
        label_font = ('Segoe UI', 10)
        
        self.overall_material = ttk.Label(overall_frame, text="Total Material Cost: 0.00", 
                                         font=label_font, foreground="#2E86AB")
        self.overall_material.pack(anchor="w", pady=2)
        
        self.overall_electricity = ttk.Label(overall_frame, text="Total Electricity Cost: 0.00", 
                                            font=label_font, foreground="#A23B72")
        self.overall_electricity.pack(anchor="w", pady=2)
        
        self.overall_labor = ttk.Label(overall_frame, text="Total Labor Cost: 0.00", 
                                      font=label_font, foreground="#F18F01")
        self.overall_labor.pack(anchor="w", pady=2)
        
        self.overall_addons = ttk.Label(overall_frame, text="Total Add-ons Cost: 0.00", 
                                       font=label_font, foreground="#C73E1D")
        self.overall_addons.pack(anchor="w", pady=2)
        
        self.overall_packaging_shipping = ttk.Label(overall_frame, text="Packaging & Shipping: 0.00", 
                                                   font=label_font, foreground="#6A4C93")
        self.overall_packaging_shipping.pack(anchor="w", pady=2)
        
        self.overall_markup = ttk.Label(overall_frame, text="Total Markup: 0.00", 
                                       font=label_font, foreground="#1982C4")
        self.overall_markup.pack(anchor="w", pady=2)
        
        ttk.Separator(overall_frame, orient='horizontal').pack(fill="x", pady=10)

        # Summary at the bottom
        self.summary = ttk.Label(overall_frame, text="GRAND TOTAL: 0.00", 
                                font=('Segoe UI', 13, 'bold'), foreground="#2D6A4F")
        self.summary.pack(anchor="w", pady=5)
        
        # Create one model frame at startup
        self.add_model()
    
    def _on_h_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    def _on_v_mousewheel(self, event):
        # Only scroll if vertical scrollbar is visible
        if self.v_scrollbar.winfo_ismapped():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

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
        
        # Destroy all remaining children in scrollable_frame
        for child in self.scrollable_frame.winfo_children():
            child.destroy()
        
        # Reset project name
        self.project_name_var.set(DEFAULT_PROJECT_NAME)
        
        # Reset overall inputs to defaults
        self.labor_hours_var.set(DEFAULT_LABOR_HOURS)
        self.labor_rate_var.set(DEFAULT_LABOR_RATE)
        self.markup_percent_var.set(DEFAULT_MARKUP_PERCENT)
        self.packaging_var.set(DEFAULT_PACKAGING)
        self.shipping_var.set(DEFAULT_SHIPPING)
        
        # Reset overall totals display
        self.overall_material.config(text="Total Material Cost: 0.00")
        self.overall_electricity.config(text="Total Electricity Cost: 0.00")
        self.overall_labor.config(text="Total Labor Cost: 0.00")
        self.overall_addons.config(text="Total Add-ons Cost: 0.00")
        self.overall_packaging_shipping.config(text="Packaging & Shipping: 0.00")
        self.overall_markup.config(text="Total Markup: 0.00")
        self.summary.config(text="GRAND TOTAL: 0.00")
        
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
                "markup_percent": self.markup_percent_var.get(),
                "packaging": self.packaging_var.get(),
                "shipping": self.shipping_var.get()
            },
            "models": []
        }
        
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
                "addons": []
            }
            
            # Save add-ons data
            for i, (qty_var, price_var) in enumerate(model.addons):
                # Find the name entry widget in the addon_frame
                addon_widgets = model.addon_frame.grid_slaves(row=i+1, column=0)
                name = addon_widgets[0].get() if addon_widgets else ""
                
                model_data["addons"].append({
                    "name": name,
                    "quantity": qty_var.get(),
                    "price_per_unit": price_var.get()
                })
            
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
            
            # Load project name
            self.project_name_var.set(project_data.get("project_name", DEFAULT_PROJECT_NAME))
            
            # Load overall settings
            overall = project_data.get("overall", {})
            self.labor_hours_var.set(overall.get("labor_hours", DEFAULT_LABOR_HOURS))
            self.labor_rate_var.set(overall.get("labor_rate", DEFAULT_LABOR_RATE))
            self.markup_percent_var.set(overall.get("markup_percent", DEFAULT_MARKUP_PERCENT))
            self.packaging_var.set(overall.get("packaging", DEFAULT_PACKAGING))
            self.shipping_var.set(overall.get("shipping", DEFAULT_SHIPPING))
            
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
                
                # Load add-ons
                for addon_data in model_data.get("addons", []):
                    model.add_addon()
                    # Get the last added addon (most recent)
                    if model.addons:
                        qty_var, price_var = model.addons[-1]
                        qty_var.set(addon_data.get("quantity", 0))
                        price_var.set(addon_data.get("price_per_unit", 0))
                        
                        # Set the name in the entry widget
                        row = len(model.addons)
                        name_widgets = model.addon_frame.grid_slaves(row=row, column=0)
                        if name_widgets:
                            name_widgets[0].delete(0, tk.END)
                            name_widgets[0].insert(0, addon_data.get("name", ""))
                
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
        total_addons = 0
        
        for model in self.models:
            result = model.calculate()
            models_total += result["total"]
            total_material += result["material"]
            total_electricity += result["electricity"]
            total_addons += result["addons"]

        # Apply labor (overall only)
        labor_hours = float(self.labor_hours_var.get() or 0)
        labor_rate = float(self.labor_rate_var.get() or 0)
        total_labor = LABOR_COST_FORMULA(labor_hours, labor_rate)
        
        # Apply packaging and shipping (overall only)
        packaging = float(self.packaging_var.get() or 0)
        shipping = float(self.shipping_var.get() or 0)
        
        # Apply markup to models total + labor + packaging + shipping (overall only)
        base_for_markup = models_total + total_labor + packaging + shipping
        markup_percent = float(self.markup_percent_var.get() or 0)
        total_markup = CUSTOM_MARKUP_FORMULA(base_for_markup, markup_percent)
        
        # Calculate grand total
        grand_total = GRAND_TOTAL_FORMULA(models_total, total_labor, packaging, shipping, total_markup)

        self.overall_material.config(text=f"Total Material Cost: {total_material:.2f}")
        self.overall_electricity.config(text=f"Total Electricity Cost: {total_electricity:.2f}")
        self.overall_labor.config(text=f"Total Labor Cost: {total_labor:.2f}")
        self.overall_addons.config(text=f"Total Add-ons Cost: {total_addons:.2f}")
        self.overall_packaging_shipping.config(text=f"Packaging & Shipping: {packaging + shipping:.2f}")
        self.overall_markup.config(text=f"Total Markup: {total_markup:.2f}")
        self.summary.config(text=f"GRAND TOTAL: {grand_total:.2f}")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    try:
        print("Starting application...")
        root = tk.Tk()
        print("Creating app...")
        app = CostCalculatorApp(root)
        print("Window created! If you don't see it, check your taskbar.")
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
