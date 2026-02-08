"""Model Frame component for individual 3D print models"""

import tkinter as tk
from tkinter import ttk
from tkinter import TclError

from config import (
    FILAMENT_GRAMS_PER_SPOOL,
    ELECTRICITY_COST_FORMULA,
    MATERIAL_COST_FORMULA,
    MACHINE_COST_FORMULA,
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


class ModelFrame(ttk.LabelFrame):
    """Frame for managing a single 3D print model with all its parameters"""
    
    @staticmethod
    def add_numeric_validation(entry_widget, var, allow_float=True):
        """Attach validation to an Entry widget to ensure only numbers are allowed. Highlights red if invalid."""
        def validate_number(*args):
            value = var.get()
            try:
                if allow_float:
                    if value.strip() == "":
                        entry_widget.configure(background="white")
                        return
                    float(value)
                else:
                    if value.strip() == "":
                        entry_widget.configure(background="white")
                        return
                    int(value)
                entry_widget.configure(background="white")
            except ValueError:
                entry_widget.configure(background="#ffcccc")  # light red
        var.trace_add("write", validate_number)
    
    @staticmethod
    def bind_select_all_on_focus(entry_widget):
        """Select all text in the entry when focused."""
        def on_focus_in(event):
            entry_widget.select_range(0, tk.END)
            entry_widget.icursor(tk.END)
        entry_widget.bind("<FocusIn>", on_focus_in)
    
    def __init__(self, parent, index, app_reference=None):
        super().__init__(parent, text=f"Model {index}", relief="raised", borderwidth=2)
        self.index = index
        self.app_reference = app_reference
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

    def create_fields(self):
        """Create all input fields for the model"""
        self.vars = {}
        self.entries = {}  # Store entry widgets for validation
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
        quantity_entry = tk.Entry(self, textvariable=self.quantity_var)
        quantity_entry.grid(row=row, column=1, sticky="ew", padx=5)
        self.bind_select_all_on_focus(quantity_entry)
        self.add_numeric_validation(quantity_entry, self.quantity_var, allow_float=False)
        self.vars["Quantity"] = self.quantity_var
        row += 1

        ttk.Separator(self, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        row += 1

        # MATERIAL SECTION
        ttk.Label(self, text="━━━ MATERIAL ━━━", font=('TkDefaultFont', 9, 'bold')).grid(
            row=row, column=0, columnspan=2, pady=(5, 2))
        row += 1

        material_fields = [
            ("Material", DEFAULT_MATERIAL, False),
            ("Material Price", DEFAULT_MATERIAL_PRICE, True),
            ("Cost per Gram", "", True),
            ("Grams Used", DEFAULT_GRAMS_USED, True),
        ]

        for label, default, is_number in material_fields:
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            var = tk.StringVar(value=default)
            var.trace_add("write", lambda *args: self.auto_calculate())
            if label == "Material":
                def force_uppercase(*args, v=var):
                    value = v.get()
                    if value != value.upper():
                        v.set(value.upper())
                var.trace_add("write", force_uppercase)
                entry = ttk.Entry(self, textvariable=var)
            elif is_number and label != "Cost per Gram":
                entry = tk.Entry(self, textvariable=var)
                self.add_numeric_validation(entry, var, allow_float=True)
            else:
                entry = ttk.Entry(self, textvariable=var)
                if label == "Cost per Gram":
                    entry.state(["readonly"])
            entry.grid(row=row, column=1, sticky="ew", padx=5)
            self.bind_select_all_on_focus(entry)
            self.vars[label] = var
            if label == "Grams Used":
                self.entries[label] = entry
            row += 1

        # Material cost output
        self.material_cost_label = ttk.Label(self, text="Total Material Cost: ₱0.00", foreground="blue")
        self.material_cost_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(2, 5))
        row += 1
        
        # PRINTER/ELECTRICITY SECTION
        ttk.Separator(self, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        row += 1
        ttk.Label(self, text="━━━ PRINTER & ELECTRICITY ━━━", font=('TkDefaultFont', 9, 'bold')).grid(
            row=row, column=0, columnspan=2, pady=(5, 2))
        row += 1
        
        # Printer Type dropdown
        ttk.Label(self, text="Printer Type").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.printer_type_var = tk.StringVar(value=DEFAULT_PRINTER_TYPE)
        printer_combo = ttk.Combobox(self, textvariable=self.printer_type_var, state="readonly", height=10)
        
        # Load printer options
        printer_configs = load_printer_configs()
        printer_combo['values'] = sorted(list(printer_configs.keys()))
        printer_combo.grid(row=row, column=1, sticky="ew", padx=5)
        self.entries["Printer Type"] = printer_combo
        
        # Bind selection event to auto-populate wattage
        def on_printer_selected(event):
            selected = self.printer_type_var.get()
            if selected and selected in printer_configs:
                self.vars["Printer Wattage"].set(str(printer_configs[selected]['wattage']))
        
        printer_combo.bind('<<ComboboxSelected>>', on_printer_selected)
        self.vars["Printer Type"] = self.printer_type_var
        row += 1
        
        printer_fields = [
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
                entry_days = tk.Entry(print_time_frame, textvariable=self.print_days_var, width=8)
                entry_days.grid(row=0, column=1, sticky="ew", padx=5)
                self.bind_select_all_on_focus(entry_days)
                self.add_numeric_validation(entry_days, self.print_days_var, allow_float=True)
                self.vars["Print Days"] = self.print_days_var

                ttk.Label(print_time_frame, text="Print Hours").grid(row=1, column=0, sticky="w", padx=5, pady=2)
                self.print_hours_var = tk.StringVar(value=DEFAULT_PRINT_HOURS)
                self.print_hours_var.trace_add("write", lambda *args: self.auto_calculate())
                entry_hours = tk.Entry(print_time_frame, textvariable=self.print_hours_var, width=8)
                entry_hours.grid(row=1, column=1, sticky="ew", padx=5)
                self.bind_select_all_on_focus(entry_hours)
                self.add_numeric_validation(entry_hours, self.print_hours_var, allow_float=True)
                self.vars["Print Hours"] = self.print_hours_var

                ttk.Label(print_time_frame, text="Print Minutes").grid(row=2, column=0, sticky="w", padx=5, pady=2)
                self.print_minutes_var = tk.StringVar(value="0")
                self.print_minutes_var.trace_add("write", lambda *args: self.auto_calculate())
                entry_minutes = tk.Entry(print_time_frame, textvariable=self.print_minutes_var, width=8)
                entry_minutes.grid(row=2, column=1, sticky="ew", padx=5)
                self.bind_select_all_on_focus(entry_minutes)
                self.add_numeric_validation(entry_minutes, self.print_minutes_var, allow_float=True)
                self.vars["Print Minutes"] = self.print_minutes_var

                row += 1

            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            var = tk.StringVar(value=default)
            var.trace_add("write", lambda *args: self.auto_calculate())
            
            # Make Printer Wattage read-only (only editable via Configure Printers)
            if label == "Printer Wattage":
                entry = tk.Entry(self, textvariable=var, state='readonly')
            else:
                entry = tk.Entry(self, textvariable=var)
                self.add_numeric_validation(entry, var, allow_float=True)
                self.bind_select_all_on_focus(entry)
            
            entry.grid(row=row, column=1, sticky="ew", padx=5)
            self.vars[label] = var
            if label == "Machine Cost / Hour":
                self.entries[label] = entry
            row += 1
        
        # Electricity cost output
        self.electricity_cost_label = ttk.Label(self, text="Total Electricity Cost: ₱0.00", foreground="blue")
        self.electricity_cost_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(2, 5))
        row += 1
        
        # Machine cost output
        self.machine_cost_label = ttk.Label(self, text="Total Machine Cost: ₱0.00", foreground="blue")
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
            self.material_cost_label.config(text=f"Total Material Cost: ₱{material_cost:.2f}")

            # Electricity costs
            watts = float(self.vars["Printer Wattage"].get() or 0)
            days = float(self.vars["Print Days"].get() or 0)
            hours = float(self.vars["Print Hours"].get() or 0)
            minutes = float(self.vars["Print Minutes"].get() or 0)
            total_hours = (days * 24) + hours + (minutes / 60)
            rate = float(self.vars["Electricity Rate / kWh"].get() or 0)
            electricity_cost = ELECTRICITY_COST_FORMULA(watts, total_hours, rate) * quantity
            self.electricity_cost_label.config(text=f"Total Electricity Cost: ₱{electricity_cost:.2f}")

            # Machine costs
            machine_cost_per_hour = float(self.vars["Machine Cost / Hour"].get() or 0)
            machine_cost = MACHINE_COST_FORMULA(total_hours, machine_cost_per_hour) * quantity
            self.machine_cost_label.config(text=f"Total Machine Cost: ₱{machine_cost:.2f}")

            # Total cost (without margin, labor, packaging, and shipping)
            total = material_cost + electricity_cost + machine_cost
            self.total_label.config(text=f"Total Cost: ₱{total:.2f}")
        except (ValueError, TclError):
            # Handle invalid input gracefully
            pass

    def create_totals(self):
        """Create the totals display at the bottom of the frame"""
        # Add separator and total at the end
        ttk.Separator(self, orient='horizontal').grid(row=99, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.total_label = ttk.Label(self, text="Total Cost: ₱0.00", 
                                     font=('Segoe UI', 11, 'bold'), foreground="#2D6A4F")
        self.total_label.grid(row=100, column=0, columnspan=2, pady=10)

    def calculate(self):
        """Calculate all costs and return a summary dictionary"""
        # Material costs
        material_price = float(self.vars["Material Price"].get())
        grams_used = float(self.vars["Grams Used"].get())
        quantity = int(self.vars["Quantity"].get() or 1)

        cost_per_gram = material_price / FILAMENT_GRAMS_PER_SPOOL
        self.vars["Cost per Gram"].set(f"{cost_per_gram:.4f}")

        material_cost = MATERIAL_COST_FORMULA(cost_per_gram, grams_used) * quantity
        self.material_cost_label.config(text=f"Total Material Cost: ₱{material_cost:.2f}")

        # Electricity costs
        watts = float(self.vars["Printer Wattage"].get())
        days = float(self.vars["Print Days"].get())
        hours = float(self.vars["Print Hours"].get())
        minutes = float(self.vars["Print Minutes"].get())
        total_hours = (days * 24) + hours + (minutes / 60)
        rate = float(self.vars["Electricity Rate / kWh"].get())
        electricity_cost = ELECTRICITY_COST_FORMULA(watts, total_hours, rate) * quantity
        self.electricity_cost_label.config(text=f"Total Electricity Cost: ₱{electricity_cost:.2f}")

        # Machine costs
        machine_cost_per_hour = float(self.vars["Machine Cost / Hour"].get())
        machine_cost = MACHINE_COST_FORMULA(total_hours, machine_cost_per_hour) * quantity
        self.machine_cost_label.config(text=f"Total Machine Cost: ₱{machine_cost:.2f}")

        # Total cost (without margin, labor, packaging, and shipping)
        total = material_cost + electricity_cost + machine_cost
        self.total_label.config(text=f"Total Cost: ₱{total:.2f}")

        return {
            "total": total,
            "material": material_cost,
            "electricity": electricity_cost,
            "machine": machine_cost
        }
    
    def validate_required_fields(self):
        """Validate that required fields (Grams Used, Printer Type, Machine Cost / Hour) are filled. Highlight in red if empty. Return False if any are empty."""
        all_valid = True
        
        # Check Grams Used
        if "Grams Used" in self.vars and "Grams Used" in self.entries:
            grams_value = self.vars["Grams Used"].get().strip()
            if grams_value == "" or grams_value == "0":
                self.entries["Grams Used"].configure(background="#ffcccc")
                all_valid = False
            else:
                try:
                    float(grams_value)
                    self.entries["Grams Used"].configure(background="white")
                except ValueError:
                    self.entries["Grams Used"].configure(background="#ffcccc")
                    all_valid = False
        
        # Check Printer Type
        if "Printer Type" in self.vars and "Printer Type" in self.entries:
            printer_value = self.vars["Printer Type"].get().strip()
            combo = self.entries["Printer Type"]
            if printer_value == "":
                # For ttk.Combobox, we need to use configure with a style or fieldbackground
                try:
                    combo.configure(fieldbackground="#ffcccc")
                except:
                    pass
                all_valid = False
            else:
                try:
                    combo.configure(fieldbackground="white")
                except:
                    pass
        
        # Check Machine Cost / Hour
        if "Machine Cost / Hour" in self.vars and "Machine Cost / Hour" in self.entries:
            machine_value = self.vars["Machine Cost / Hour"].get().strip()
            if machine_value == "" or machine_value == "0":
                self.entries["Machine Cost / Hour"].configure(background="#ffcccc")
                all_valid = False
            else:
                try:
                    float(machine_value)
                    self.entries["Machine Cost / Hour"].configure(background="white")
                except ValueError:
                    self.entries["Machine Cost / Hour"].configure(background="#ffcccc")
                    all_valid = False
        
        return all_valid
