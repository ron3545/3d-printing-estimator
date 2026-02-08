"""Printer Configuration Dialog for managing 3D printer types and specifications"""

import tkinter as tk
from tkinter import ttk, messagebox

from config import load_printer_configs, save_printer_configs


class PrinterConfigDialog:
    """Dialog for configuring 3D printer types with wattage and lifetime specifications"""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configure 3D Printers")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.configs = load_printer_configs()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        ttk.Label(main_frame, text="3D Printer Configurations", 
                  font=('TkDefaultFont', 12, 'bold')).pack(pady=(0, 10))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.printer_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                          font=('TkDefaultFont', 10))
        self.printer_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.printer_listbox.yview)
        
        self.refresh_list()
        
        # Entry fields frame
        entry_frame = ttk.LabelFrame(main_frame, text="Printer Details", padding=10)
        entry_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(entry_frame, text="Printer Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.name_var = tk.StringVar()
        self.name_combo = ttk.Combobox(entry_frame, textvariable=self.name_var, width=28)
        self.name_combo.grid(row=0, column=1, padx=5, pady=5)
        self.update_printer_dropdown()
        
        ttk.Label(entry_frame, text="Wattage (W):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.wattage_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.wattage_var, width=30).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(entry_frame, text="Lifetime (hours):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.lifetime_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.lifetime_var, width=30).grid(row=2, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="Add/Update", command=self.add_or_update).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete", command=self.delete_printer).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Load from List", command=self.load_selected).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save & Close", command=self.save_and_close).pack(side="right", padx=5)
        
        self.printer_listbox.bind('<<ListboxSelect>>', lambda e: self.load_selected())
    
    def refresh_list(self):
        """Refresh the printer listbox with current configurations"""
        self.printer_listbox.delete(0, tk.END)
        for name, details in sorted(self.configs.items()):
            self.printer_listbox.insert(tk.END, 
                f"{name} - {details['wattage']}W - {details['lifetime_hours']}h")
    
    def update_printer_dropdown(self):
        """Update the printer name dropdown with available printer names"""
        self.name_combo['values'] = sorted(list(self.configs.keys()))
    
    def load_selected(self):
        """Load the selected printer's details into the entry fields"""
        selection = self.printer_listbox.curselection()
        if selection:
            idx = selection[0]
            printer_name = list(sorted(self.configs.keys()))[idx]
            details = self.configs[printer_name]
            self.name_var.set(printer_name)
            self.wattage_var.set(str(details['wattage']))
            self.lifetime_var.set(str(details['lifetime_hours']))
    
    def add_or_update(self):
        """Add a new printer or update an existing one"""
        name = self.name_var.get().strip()
        wattage = self.wattage_var.get().strip()
        lifetime = self.lifetime_var.get().strip()
        
        if not name or not wattage or not lifetime:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        try:
            wattage_val = float(wattage)
            lifetime_val = float(lifetime)
            
            self.configs[name] = {
                "wattage": wattage_val,
                "lifetime_hours": lifetime_val
            }
            
            self.refresh_list()
            self.update_printer_dropdown()
            messagebox.showinfo("Success", f"Printer '{name}' added/updated")
        except ValueError:
            messagebox.showerror("Error", "Wattage and Lifetime must be numbers")
    
    def delete_printer(self):
        """Delete the selected printer configuration"""
        selection = self.printer_listbox.curselection()
        if selection:
            idx = selection[0]
            printer_name = list(sorted(self.configs.keys()))[idx]
            
            if messagebox.askyesno("Confirm Delete", f"Delete printer '{printer_name}'?"):
                del self.configs[printer_name]
                self.refresh_list()
                self.update_printer_dropdown()
                self.name_var.set("")
                self.wattage_var.set("")
                self.lifetime_var.set("")
    
    def save_and_close(self):
        """Save the printer configurations and close the dialog"""
        if save_printer_configs(self.configs):
            messagebox.showinfo("Success", "Printer configurations saved")
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", "Failed to save printer configurations")
