"""Main application class for 3D Printing Cost Calculator"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json

from config import (
    PUBLISHER_NAME,
    LABOR_COST_FORMULA,
    MARGIN_PRICE_FORMULA,
    GRAND_TOTAL_FORMULA,
    DEFAULT_PROJECT_NAME,
    DEFAULT_LABOR_HOURS,
    DEFAULT_LABOR_RATE,
    DEFAULT_MARGIN_PERCENT,
    DEFAULT_PACKAGING,
    DEFAULT_SHIPPING,
    DEFAULT_ADDON_QUANTITY,
    DEFAULT_ADDON_PRICE,
    DEFAULT_MATERIAL,
    DEFAULT_MATERIAL_PRICE,
    DEFAULT_GRAMS_USED,
    DEFAULT_PRINTER_TYPE,
    DEFAULT_PRINTER_WATTAGE,
    DEFAULT_PRINT_HOURS,
    DEFAULT_ELECTRICITY_RATE,
    DEFAULT_MACHINE_COST_PER_HOUR,
    load_printer_configs
)
from .model_frame import ModelFrame
from .printer_config_dialog import PrinterConfigDialog


class CostCalculatorApp:
    """Main application window for the 3D Printing Cost Calculator"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("3D Printing Cost Calculator")

        # Set initial window size (width x height)
        self.root.geometry("900x700")

        # Maximize window on startup (keeps window buttons visible)
        self.root.state('zoomed')
        
        # Keep fullscreen toggle available with F11
        self.is_fullscreen = False
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.handle_escape)

        self.models = []
        self.addons = []
        self.breakdown_data = None
        self.breakdown_window = None

        self._create_ui()
    
    def _create_ui(self):
        """Create the user interface"""
        # Top bar frame for publisher (right) and project name (left)
        topbar_frame = ttk.Frame(self.root)
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
        ModelFrame.bind_select_all_on_focus(project_entry)

        # Button frame below project name
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="New Project", command=self.new_project).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Add Model", command=self.add_model).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Configure Printers", command=self.open_printer_config).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save Project", command=self.save_project).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Load Project", command=self.load_project).pack(side="left", padx=5)

        # Labor and Markup inputs (applies to overall total only)
        self._create_overall_inputs()
        
        # Main container for models and overall totals
        self._create_main_container()
        
        # Create one model frame at startup
        self.add_model()
    
    def _create_overall_inputs(self):
        """Create overall labor and markup inputs"""
        inputs_frame = ttk.LabelFrame(self.root, text="Overall Labor & Markup", padding=10)
        inputs_frame.pack(pady=5, padx=20, fill="x")

        ttk.Label(inputs_frame, text="Labor Hours:").grid(row=0, column=0, sticky="w", padx=5)
        self.labor_hours_var = tk.StringVar(value=DEFAULT_LABOR_HOURS)
        labor_hours_entry = tk.Entry(inputs_frame, textvariable=self.labor_hours_var, width=15)
        labor_hours_entry.grid(row=0, column=1, padx=5)
        ModelFrame.bind_select_all_on_focus(labor_hours_entry)
        ModelFrame.add_numeric_validation(labor_hours_entry, self.labor_hours_var, allow_float=True)

        ttk.Label(inputs_frame, text="Labor Rate:").grid(row=0, column=2, sticky="w", padx=5)
        self.labor_rate_var = tk.StringVar(value=DEFAULT_LABOR_RATE)
        labor_rate_entry = tk.Entry(inputs_frame, textvariable=self.labor_rate_var, width=15)
        labor_rate_entry.grid(row=0, column=3, padx=5)
        ModelFrame.bind_select_all_on_focus(labor_rate_entry)
        ModelFrame.add_numeric_validation(labor_rate_entry, self.labor_rate_var, allow_float=True)

        ttk.Label(inputs_frame, text="Margin %:").grid(row=0, column=4, sticky="w", padx=5)
        self.margin_percent_var = tk.StringVar(value=DEFAULT_MARGIN_PERCENT)
        margin_entry = tk.Entry(inputs_frame, textvariable=self.margin_percent_var, width=15)
        margin_entry.grid(row=0, column=5, padx=5)
        ModelFrame.bind_select_all_on_focus(margin_entry)
        ModelFrame.add_numeric_validation(margin_entry, self.margin_percent_var, allow_float=True)

        ttk.Label(inputs_frame, text="Packaging:").grid(row=1, column=0, sticky="w", padx=5)
        self.packaging_var = tk.StringVar(value=DEFAULT_PACKAGING)
        packaging_entry = tk.Entry(inputs_frame, textvariable=self.packaging_var, width=15)
        packaging_entry.grid(row=1, column=1, padx=5)
        ModelFrame.bind_select_all_on_focus(packaging_entry)
        ModelFrame.add_numeric_validation(packaging_entry, self.packaging_var, allow_float=True)

        ttk.Label(inputs_frame, text="Shipping:").grid(row=1, column=2, sticky="w", padx=5)
        self.shipping_var = tk.StringVar(value=DEFAULT_SHIPPING)
        shipping_entry = tk.Entry(inputs_frame, textvariable=self.shipping_var, width=15)
        shipping_entry.grid(row=1, column=3, padx=5)
        ModelFrame.bind_select_all_on_focus(shipping_entry)
        ModelFrame.add_numeric_validation(shipping_entry, self.shipping_var, allow_float=True)
    
    def _create_main_container(self):
        """Create the main container with models and totals"""
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left side: scrollable models
        self._create_models_container(main_container)
        
        # Right side: Container for addons and overall totals
        self._create_right_container(main_container)
    
    def _create_models_container(self, parent):
        """Create the scrollable models container"""
        models_container = ttk.Frame(parent)
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
    
    def _create_right_container(self, parent):
        """Create the right container with addons and totals"""
        right_container = ttk.Frame(parent, width=350)
        right_container.pack(side="right", fill="y", padx=(10, 0))
        right_container.pack_propagate(False)
        
        # Add-ons section (top of right side) - fixed height
        self._create_addons_section(right_container)
        
        # Overall totals section (bottom of right side)
        self._create_totals_section(right_container)
    
    def _create_addons_section(self, parent):
        """Create the addons section"""
        addons_outer_frame = ttk.LabelFrame(parent, text="━━━ ADDITIONAL MATERIALS ━━━", padding=10, height=200)
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
        
        self.addons_canvas = tk.Canvas(canvas_container, bg="white", highlightthickness=1, 
                                       highlightbackground="#cccccc", yscrollcommand=addons_scrollbar.set)
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
    
    def _create_totals_section(self, parent):
        """Create the overall totals section"""
        overall_frame = ttk.LabelFrame(parent, text="━━━ OVERALL TOTALS ━━━", padding=5)
        overall_frame.pack(fill="both", expand=True)
        
        label_font = ('Segoe UI', 9)
        
        self.overall_material = ttk.Label(overall_frame, text="Total Material Cost: ₱0.00", 
                                         font=label_font, foreground="#2E86AB")
        self.overall_material.pack(anchor="w", pady=1)
        
        self.overall_electricity = ttk.Label(overall_frame, text="Total Electricity Cost: ₱0.00", 
                                            font=label_font, foreground="#A23B72")
        self.overall_electricity.pack(anchor="w", pady=1)
        
        self.overall_machine = ttk.Label(overall_frame, text="Total Machine Cost: ₱0.00", 
                                        font=label_font, foreground="#8B4513")
        self.overall_machine.pack(anchor="w", pady=1)
        
        self.overall_labor = ttk.Label(overall_frame, text="Total Labor Cost: ₱0.00", 
                                      font=label_font, foreground="#F18F01")
        self.overall_labor.pack(anchor="w", pady=1)
        
        self.overall_addons = ttk.Label(overall_frame, text="Total Add-ons Cost: ₱0.00", 
                                       font=label_font, foreground="#C73E1D")
        self.overall_addons.pack(anchor="w", pady=1)
        
        self.overall_packaging_shipping = ttk.Label(overall_frame, text="Packaging & Shipping: ₱0.00", 
                                                   font=label_font, foreground="#6A4C93")
        self.overall_packaging_shipping.pack(anchor="w", pady=1)
        
        ttk.Separator(overall_frame, orient='horizontal').pack(fill="x", pady=5)

        # Final price display (simplified)
        self.summary = ttk.Label(overall_frame, text="TOTAL PRICE: ₱0.00", 
                    font=('Segoe UI', 14, 'bold'), foreground="#2D6A4F")
        self.summary.pack(anchor="w", pady=10)
        
        # Buttons
        ttk.Separator(overall_frame, orient='horizontal').pack(fill="x", pady=5)
        
        button_container = ttk.Frame(overall_frame)
        button_container.pack(fill="x", pady=5)
        
        ttk.Button(button_container, text="Calculate All", command=self.calculate_all).pack(fill="x", pady=(0, 5))
        ttk.Button(button_container, text="Show Breakdown", command=self.show_breakdown).pack(fill="x")
    
    def _on_h_mousewheel(self, event):
        """Handle horizontal mouse wheel scrolling"""
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    def _on_v_mousewheel(self, event):
        """Handle vertical mouse wheel scrolling"""
        # Only scroll if vertical scrollbar is visible
        if self.v_scrollbar.winfo_ismapped():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _on_addons_mousewheel(self, event):
        """Handle mouse wheel scrolling for addons"""
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
    
    def handle_escape(self, event):
        """Handle Escape key: close breakdown window if open, otherwise exit fullscreen"""
        if self.breakdown_window and self.breakdown_window.winfo_exists():
            self.breakdown_window.destroy()
            self.breakdown_window = None
        else:
            self.exit_fullscreen(event)
    
    def add_addon(self):
        """Add a new addon row"""
        row = len(self.addons)
        name = tk.StringVar()
        quantity = tk.StringVar(value=str(DEFAULT_ADDON_QUANTITY))
        price_per_unit = tk.StringVar(value=str(DEFAULT_ADDON_PRICE))
        
        # Calculate total when quantity or price changes
        def update_addon_total(*args):
            try:
                q = float(quantity.get()) if quantity.get().strip() != '' else 0
                p = float(price_per_unit.get()) if price_per_unit.get().strip() != '' else 0
                total = q * p
                total_label.config(text=f"{total:.2f}")
            except Exception:
                total_label.config(text="0.00")
        
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
        qty_entry = tk.Entry(self.addons_frame, textvariable=quantity, width=6)
        qty_entry.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
        qty_entry.bind("<FocusIn>", lambda e: (qty_entry.select_range(0, tk.END), qty_entry.icursor(tk.END)))
        ModelFrame.add_numeric_validation(qty_entry, quantity, allow_float=True)

        # Price per unit entry
        price_entry = tk.Entry(self.addons_frame, textvariable=price_per_unit, width=8)
        price_entry.grid(row=row, column=2, padx=2, pady=2, sticky="ew")
        price_entry.bind("<FocusIn>", lambda e: (price_entry.select_range(0, tk.END), price_entry.icursor(tk.END)))
        ModelFrame.add_numeric_validation(price_entry, price_per_unit, allow_float=True)
        
        # Total label (calculated)
        total_label = ttk.Label(self.addons_frame, text="0.00", width=8, foreground="blue")
        total_label.grid(row=row, column=3, padx=2, pady=2, sticky="w")
        
        # Remove button
        remove_btn = ttk.Button(
            self.addons_frame,
            text="✕",
            width=3,
            command=lambda: self.remove_addon(row, name_entry, qty_entry, price_entry, total_label, 
                                             remove_btn, quantity, price_per_unit, name)
        )
        remove_btn.grid(row=row, column=4, padx=2, pady=2)

        self.addons.append((name, quantity, price_per_unit))
    
    def remove_addon(self, row, name_entry, qty_entry, price_entry, total_label, remove_btn, 
                     quantity_var, price_var, name_var):
        """Remove an addon row"""
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
    
    def open_printer_config(self):
        """Open the printer configuration dialog"""
        dialog = PrinterConfigDialog(self.root)
        # Wait for the dialog to close before refreshing
        self.root.wait_window(dialog.dialog)
        # Refresh all model printer dropdowns after closing config
        for model in self.models:
            self.refresh_model_printer_dropdown(model)
    
    def refresh_model_printer_dropdown(self, model):
        """Refresh the printer type dropdown in a model"""
        printer_configs = load_printer_configs()
        
        # Check if model has the printer type combobox stored
        if hasattr(model, 'entries') and "Printer Type" in model.entries:
            combo = model.entries["Printer Type"]
            current_value = model.printer_type_var.get()
            combo['values'] = sorted(list(printer_configs.keys()))
            # Restore previous selection if still valid
            if current_value and current_value not in printer_configs:
                model.printer_type_var.set("")
        else:
            # Fallback: Find the combobox widget
            for child in model.winfo_children():
                if isinstance(child, ttk.Combobox) and child.cget('textvariable') == str(model.printer_type_var):
                    current_value = model.printer_type_var.get()
                    child['values'] = sorted(list(printer_configs.keys()))
                    # Restore previous selection if still valid
                    if current_value and current_value not in printer_configs:
                        model.printer_type_var.set("")
                    break
    
    def add_model(self):
        """Add a new model frame"""
        model = ModelFrame(self.scrollable_frame, len(self.models) + 1, app_reference=self)
        model.on_remove = self.remove_model  # Bind the remove callback
        model.pack(side="left", fill="y", padx=20, pady=5)
        self.models.append(model)
        # Scroll to the far right to show the newly added model
        self.canvas.update_idletasks()
        self.canvas.xview_moveto(1.0)
    
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
        
        # Clear all addons (additional materials)
        for child in self.addons_frame.grid_slaves():
            child.destroy()
        self.addons.clear()
        
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
        self.overall_material.config(text="Total Material Cost: ₱0.00")
        self.overall_electricity.config(text="Total Electricity Cost: ₱0.00")
        self.overall_machine.config(text="Total Machine Cost: ₱0.00")
        self.overall_labor.config(text="Total Labor Cost: ₱0.00")
        self.overall_addons.config(text="Total Add-ons Cost: ₱0.00")
        self.overall_packaging_shipping.config(text="Packaging & Shipping: ₱0.00")
        self.summary.config(text="TOTAL PRICE: ₱0.00")
        
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
                "printer_lifetime": model.vars.get("Printer Lifetime (hours)", tk.StringVar(value="5000")).get(),
                "print_days": model.vars["Print Days"].get() if "Print Days" in model.vars else "0",
                "print_hours": model.vars["Print Hours"].get() if "Print Hours" in model.vars else "0",
                "print_minutes": model.vars["Print Minutes"].get() if "Print Minutes" in model.vars else "0",
                "electricity_rate": model.vars["Electricity Rate / kWh"].get(),
                "machine_cost_per_hour": model.vars["Machine Cost / Hour"].get()
            }
            # Save any additional fields present in model.vars
            for key, var in model.vars.items():
                if key not in model_data and hasattr(var, 'get'):
                    model_data[key] = var.get()
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
            
            # Set project name to the filename (without extension)
            base_name = os.path.basename(file_path)
            project_name = os.path.splitext(base_name)[0]
            self.project_name_var.set(project_name)
            print(f"Loaded project name (from filename): {project_name}")
            
            # Load overall settings
            overall = project_data.get("overall", {})
            self.labor_hours_var.set(overall.get("labor_hours", DEFAULT_LABOR_HOURS))
            self.labor_rate_var.set(overall.get("labor_rate", DEFAULT_LABOR_RATE))
            self.margin_percent_var.set(overall.get("margin_percent", 
                                        overall.get("markup_percent", DEFAULT_MARGIN_PERCENT)))
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
                model = ModelFrame(self.scrollable_frame, len(self.models) + 1, app_reference=self)
                model.on_remove = self.remove_model
                model.pack(side="left", fill="y", padx=20, pady=5)
                self.models.append(model)

                # Set model data for all known fields
                model.model_name_var.set(model_data.get("name", f"Model {len(self.models)}"))
                model.vars["Material"].set(model_data.get("material", DEFAULT_MATERIAL))
                model.vars["Material Price"].set(model_data.get("material_price", DEFAULT_MATERIAL_PRICE))
                model.vars["Grams Used"].set(model_data.get("grams_used", DEFAULT_GRAMS_USED))
                model.vars["Printer Type"].set(model_data.get("printer_type", DEFAULT_PRINTER_TYPE))
                model.vars["Printer Wattage"].set(model_data.get("printer_wattage", DEFAULT_PRINTER_WATTAGE))
                model.vars["Printer Lifetime (hours)"].set(model_data.get("printer_lifetime", "5000"))
                model.vars["Print Days"].set(model_data.get("print_days", "0"))
                model.vars["Print Hours"].set(model_data.get("print_hours", DEFAULT_PRINT_HOURS))
                model.vars["Print Minutes"].set(model_data.get("print_minutes", "0"))
                model.vars["Electricity Rate / kWh"].set(model_data.get("electricity_rate", DEFAULT_ELECTRICITY_RATE))
                model.vars["Machine Cost / Hour"].set(model_data.get("machine_cost_per_hour", DEFAULT_MACHINE_COST_PER_HOUR))

                # Set any additional fields that exist in both model.vars and model_data
                for key, var in model.vars.items():
                    if key in model_data and hasattr(var, 'set'):
                        var.set(model_data[key])

                # Trigger auto-calculation
                model.auto_calculate()
            
            print(f"Project loaded from {file_path}")
        except Exception as e:
            print(f"Error loading project: {e}")
            import traceback
            traceback.print_exc()
    
    def validate_all_numeric_fields(self):
        """Check all numeric fields in project, models, and addons. Highlight invalid and return False if any invalid."""
        invalid_fields = []
        
        # Project-level fields
        project_fields = [
            (getattr(self, 'labor_hours_var', None), None),
            (getattr(self, 'labor_rate_var', None), None),
            (getattr(self, 'margin_percent_var', None), None),
            (getattr(self, 'packaging_var', None), None),
            (getattr(self, 'shipping_var', None), None),
        ]
        
        # Find corresponding Entry widgets for project fields
        entry_map = {}
        for child in self.root.winfo_children():
            if isinstance(child, ttk.LabelFrame) and 'Overall Labor' in str(child):
                for sub in child.winfo_children():
                    if isinstance(sub, tk.Entry):
                        entry_map[sub.cget('textvariable')] = sub
        
        for var, _ in project_fields:
            if var is not None:
                value = var.get()
                entry = None
                for k, v in entry_map.items():
                    if k == str(var):
                        entry = v
                        break
                try:
                    float(value)
                    if entry:
                        entry.configure(background="white")
                except Exception:
                    if entry:
                        entry.configure(background="#ffcccc")
                    invalid_fields.append(entry)
        
        # Addon fields
        for i, (name_var, qty_var, price_var) in enumerate(self.addons):
            # Find the corresponding Entry widgets
            row_widgets = self.addons_frame.grid_slaves(row=i)
            qty_entry = None
            price_entry = None
            for w in row_widgets:
                if isinstance(w, tk.Entry):
                    if w.cget('textvariable') == str(qty_var):
                        qty_entry = w
                    elif w.cget('textvariable') == str(price_var):
                        price_entry = w
            for var, entry in [(qty_var, qty_entry), (price_var, price_entry)]:
                try:
                    float(var.get())
                    if entry:
                        entry.configure(background="white")
                except Exception:
                    if entry:
                        entry.configure(background="#ffcccc")
                    invalid_fields.append(entry)
        
        # Model fields
        for model in self.models:
            for label, var in model.vars.items():
                # Only check fields that are numbers (skip model name, printer type, etc)
                if label in ["Material Price", "Grams Used", "Quantity", "Print Days", "Print Hours", 
                            "Print Minutes", "Printer Wattage", "Printer Lifetime (hours)", 
                            "Electricity Rate / kWh", "Machine Cost / Hour"]:
                    # Find the entry widget
                    entry = None
                    for child in model.winfo_children():
                        if isinstance(child, tk.Entry) and child.cget('textvariable') == str(var):
                            entry = child
                            break
                        # Also check inside frames (like Print Time)
                        if isinstance(child, ttk.LabelFrame):
                            for sub in child.winfo_children():
                                if isinstance(sub, tk.Entry) and sub.cget('textvariable') == str(var):
                                    entry = sub
                                    break
                    try:
                        float(var.get())
                        if entry:
                            entry.configure(background="white")
                    except Exception:
                        if entry:
                            entry.configure(background="#ffcccc")
                        invalid_fields.append(entry)
        
        return len(invalid_fields) == 0
    
    def calculate_all(self):
        """Calculate totals for all models and overall project"""
        # Validate all numeric fields before calculation
        if not self.validate_all_numeric_fields():
            messagebox.showerror("Invalid Input", 
                               "Some fields require a valid number. Please correct highlighted fields.")
            return
        
        # Validate required fields in all models
        for model in self.models:
            if not model.validate_required_fields():
                messagebox.showerror("Missing Required Fields", 
                                   "Please fill in all required fields (Grams Used, Printer Type, Machine Cost / Hour) highlighted in red.")
                return
        
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
        def safe_float(val):
            try:
                return float(val)
            except Exception:
                return 0.0
        
        total_addons = sum(safe_float(qty.get()) * safe_float(price.get()) 
                          for name, qty, price in self.addons)

        # Apply labor (overall only)
        labor_hours = float(self.labor_hours_var.get() or 0)
        labor_rate = float(self.labor_rate_var.get() or 0)
        total_labor = LABOR_COST_FORMULA(labor_hours, labor_rate)

        # Apply packaging and shipping (overall only)
        packaging = float(self.packaging_var.get() or 0)
        shipping = float(self.shipping_var.get() or 0)

        # Calculate subtotal (total cost) - including addons
        subtotal = GRAND_TOTAL_FORMULA(models_total, total_labor, packaging, shipping) + total_addons

        # Apply margin pricing formula
        margin_percent = float(self.margin_percent_var.get() or 0)
        final_price = MARGIN_PRICE_FORMULA(subtotal, margin_percent)

        # Store breakdown data for the breakdown window
        self.breakdown_data = {
            'material': total_material,
            'electricity': total_electricity,
            'machine': total_machine,
            'labor': total_labor,
            'addons': total_addons,
            'packaging': packaging,
            'shipping': shipping,
            'subtotal': subtotal,
            'margin_percent': margin_percent,
            'final_price': final_price
        }

        # Update display (simplified - only show final price)
        self.overall_material.config(text=f"Total Material Cost: ₱{total_material:.2f}")
        self.overall_electricity.config(text=f"Total Electricity Cost: ₱{total_electricity:.2f}")
        self.overall_machine.config(text=f"Total Machine Cost: ₱{total_machine:.2f}")
        self.overall_labor.config(text=f"Total Labor Cost: ₱{total_labor:.2f}")
        self.overall_addons.config(text=f"Total Add-ons Cost: ₱{total_addons:.2f}")
        self.overall_packaging_shipping.config(text=f"Packaging & Shipping: ₱{packaging + shipping:.2f}")
        self.summary.config(text=f"TOTAL PRICE: ₱{final_price:.2f}")
    
    def show_breakdown(self):
        """Show detailed price breakdown in a new window"""
        # Check if breakdown data exists
        if not hasattr(self, 'breakdown_data') or not self.breakdown_data:
            messagebox.showinfo("No Data", "Please calculate the totals first by clicking 'Calculate All'.")
            return
        
        # Create a new window
        self.breakdown_window = tk.Toplevel(self.root)
        self.breakdown_window.title("Price Breakdown")
        self.breakdown_window.geometry("500x600")
        
        # Bind Escape key to close window and clear reference on close
        self.breakdown_window.bind("<Escape>", lambda e: self.breakdown_window.destroy())
        self.breakdown_window.protocol("WM_DELETE_WINDOW", lambda: self._close_breakdown())
        
        # Create a frame with padding
        main_frame = ttk.Frame(self.breakdown_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Complete Price Breakdown", 
                               font=('Segoe UI', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Get breakdown data
        data = self.breakdown_data
        
        # Cost breakdown section
        costs_frame = ttk.LabelFrame(main_frame, text="Cost Components", padding=15)
        costs_frame.pack(fill="x", pady=(0, 10))
        
        cost_font = ('Segoe UI', 10)
        
        ttk.Label(costs_frame, text=f"Material Cost:", font=cost_font).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Label(costs_frame, text=f"₱{data['material']:.2f}", font=cost_font, foreground="#2E86AB").grid(row=0, column=1, sticky="e", pady=3)
        
        ttk.Label(costs_frame, text=f"Electricity Cost:", font=cost_font).grid(row=1, column=0, sticky="w", pady=3)
        ttk.Label(costs_frame, text=f"₱{data['electricity']:.2f}", font=cost_font, foreground="#A23B72").grid(row=1, column=1, sticky="e", pady=3)
        
        ttk.Label(costs_frame, text=f"Machine Wear Cost:", font=cost_font).grid(row=2, column=0, sticky="w", pady=3)
        ttk.Label(costs_frame, text=f"₱{data['machine']:.2f}", font=cost_font, foreground="#8B4513").grid(row=2, column=1, sticky="e", pady=3)
        
        ttk.Label(costs_frame, text=f"Labor Cost:", font=cost_font).grid(row=3, column=0, sticky="w", pady=3)
        ttk.Label(costs_frame, text=f"₱{data['labor']:.2f}", font=cost_font, foreground="#F18F01").grid(row=3, column=1, sticky="e", pady=3)
        
        ttk.Label(costs_frame, text=f"Add-ons Cost:", font=cost_font).grid(row=4, column=0, sticky="w", pady=3)
        ttk.Label(costs_frame, text=f"₱{data['addons']:.2f}", font=cost_font, foreground="#C73E1D").grid(row=4, column=1, sticky="e", pady=3)
        
        ttk.Label(costs_frame, text=f"Packaging:", font=cost_font).grid(row=5, column=0, sticky="w", pady=3)
        ttk.Label(costs_frame, text=f"₱{data['packaging']:.2f}", font=cost_font, foreground="#6A4C93").grid(row=5, column=1, sticky="e", pady=3)
        
        ttk.Label(costs_frame, text=f"Shipping:", font=cost_font).grid(row=6, column=0, sticky="w", pady=3)
        ttk.Label(costs_frame, text=f"₱{data['shipping']:.2f}", font=cost_font, foreground="#6A4C93").grid(row=6, column=1, sticky="e", pady=3)
        
        # Configure column weights
        costs_frame.columnconfigure(0, weight=1)
        costs_frame.columnconfigure(1, weight=1)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill="x", pady=10)
        
        # Subtotal section
        subtotal_frame = ttk.Frame(main_frame)
        subtotal_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(subtotal_frame, text="SUBTOTAL (Cost):", 
                 font=('Segoe UI', 11, 'bold')).pack(side="left")
        ttk.Label(subtotal_frame, text=f"₱{data['subtotal']:.2f}", 
                 font=('Segoe UI', 11, 'bold'), foreground="#555555").pack(side="right")
        
        # Margin section
        margin_frame = ttk.LabelFrame(main_frame, text="Margin Applied", padding=15)
        margin_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(margin_frame, text=f"Margin Percentage:", font=cost_font).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Label(margin_frame, text=f"{data['margin_percent']:.1f}%", font=cost_font, foreground="#2D6A4F").grid(row=0, column=1, sticky="e", pady=3)
        
        margin_amount = data['final_price'] - data['subtotal']
        ttk.Label(margin_frame, text=f"Margin Amount:", font=cost_font).grid(row=1, column=0, sticky="w", pady=3)
        ttk.Label(margin_frame, text=f"₱{margin_amount:.2f}", font=cost_font, foreground="#2D6A4F").grid(row=1, column=1, sticky="e", pady=3)
        
        margin_frame.columnconfigure(0, weight=1)
        margin_frame.columnconfigure(1, weight=1)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill="x", pady=15)
        
        # Final price section
        final_frame = ttk.Frame(main_frame)
        final_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(final_frame, text="TOTAL PRICE:", 
                 font=('Segoe UI', 14, 'bold')).pack(side="left")
        ttk.Label(final_frame, text=f"₱{data['final_price']:.2f}", 
                 font=('Segoe UI', 14, 'bold'), foreground="#2D6A4F").pack(side="right")
        
        # Close button
        ttk.Button(main_frame, text="Close", command=self._close_breakdown).pack(pady=(20, 0))
    
    def _close_breakdown(self):
        """Close the breakdown window and clear reference"""
        if self.breakdown_window:
            self.breakdown_window.destroy()
            self.breakdown_window = None
