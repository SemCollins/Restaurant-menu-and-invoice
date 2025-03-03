import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from tkinter import *
import datetime

# Home view using customtkinter as the main window.
class HomeView(ctk.CTk):
    def __init__(self, on_order, on_admin_login):
        super().__init__()
        self.title("Welcome to Coded Restaurant")
        self.geometry("400x300")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")         # Options: "System", "Dark", "Light"
        ctk.set_default_color_theme("dark-blue")       # Options: "blue", "green", "dark-blue"

        # Try to load a background image if available.
        try:
            self.bg = tk.PhotoImage(file='Images/bg.png')
            bg_label = ctk.CTkLabel(self, image=self.bg, text="")
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print("Background image not found or failed to load:", e)
        
        welcome_label = ctk.CTkLabel(self, text="Welcome to Coded Restaurant", font=("Helvetica Bold-Oblique", 22))
        welcome_label.pack(pady=20)
        
        order_button = ctk.CTkButton(self, text="Place Order", font=("Helvetica", 16), command=on_order)
        order_button.pack(pady=10)
        
        admin_button = ctk.CTkButton(self, text="Admin Login", font=("Helvetica", 16), command=on_admin_login)
        admin_button.pack(pady=10)


# OrderView uses a CTkToplevel window and a CTkTabview for categories.
class OrderView(ctk.CTkToplevel):
    def __init__(self, menu, on_generate_invoice):
        super().__init__()
        self.title("Place Order")
        self.geometry("800x600")
        self.menu = menu
        self.on_generate_invoice = on_generate_invoice
        self.quantity_vars = {}  # (category, item) -> tk.IntVar()

        # Configure grid layout: row 0 will be the tabview (expandable) and row 1 will be the invoice button.
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Create a CTkTabview and place it in row 0.
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Use a larger font for a professional look.
        label_font = ("Helvetica", 14)
        
        for category, items in self.menu.items():
            self.tabview.add(category)
            frame = self.tabview.tab(category)
            row = 0
            for item, price in items.items():
                label_item = ctk.CTkLabel(frame, text=item, font=label_font)
                label_item.grid(row=row, column=0, sticky="w", padx=5, pady=5)
                
                label_price = ctk.CTkLabel(frame, text=f"GHS {price:.2f}", font=label_font)
                label_price.grid(row=row, column=1, padx=5, pady=5)
                
                try:
                    spin = ctk.CTkSpinbox(frame, from_=0, to=20, width=5, font=label_font)
                except AttributeError:
                    var = tk.IntVar(value=0)
                    spin = tk.Spinbox(frame, from_=0, to=20, textvariable=var, width=5, font=label_font)
                    self.quantity_vars[(category, item)] = var
                    spin.grid(row=row, column=2, padx=5, pady=5)
                    row += 1
                    continue
                
                var = tk.IntVar(value=0)
                spin.configure(textvariable=var)
                self.quantity_vars[(category, item)] = var
                spin.grid(row=row, column=2, padx=5, pady=5)
                row += 1

        # Create the Generate Invoice button in row 1.
        invoice_button = ctk.CTkButton(self, text="Generate Invoice", font=("Helvetica", 16), command=self.generate_invoice)
        invoice_button.grid(row=1, column=0, pady=10)
    
    def generate_invoice(self):
        order_details = []
        for (category, item), var in self.quantity_vars.items():
            try:
                quantity = int(var.get())
            except Exception:
                quantity = 0
            if quantity > 0:
                price = self.menu[category][item]
                order_details.append((category, item, quantity, price))
        if not order_details:
            messagebox.showerror("Error", "No items selected.")
        else:
            self.on_generate_invoice(order_details)
            self.destroy()

# InvoiceView uses a CTkToplevel and a CTkTextbox with an attached scrollbar to display the invoice.
class InvoiceView(ctk.CTkToplevel):
    def __init__(self, order_items, order_time, total):
        super().__init__()
        self.title("Invoice")
        self.geometry("400x500")
        self.create_widgets(order_items, order_time, total)
    
    def create_widgets(self, order_items, order_time, total):
        # Create a frame to hold the textbox and scrollbar.
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create the textbox with a larger font.
        self.textbox = ctk.CTkTextbox(container, wrap="word", font=("Helvetica", 14))
        self.textbox.pack(side="left", fill="both", expand=True)
        
        # Create and attach a vertical scrollbar.
        scrollbar = ctk.CTkScrollbar(container, orientation="vertical", command=self.textbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.textbox.configure(yscrollcommand=scrollbar.set)
        
        invoice_str = f"Invoice\nOrder Time: {order_time}\n"
        invoice_str += "-" * 40 + "\n"
        for category, item, quantity, price in order_items:
            item_total = quantity * price
            invoice_str += f"{item} x {quantity} @ GHS {price:.2f} = GHS {item_total:.2f}\n"
        invoice_str += "-" * 40 + "\n"
        invoice_str += f"Total: GHS {total:.2f}\n"
        
        self.textbox.insert("0.0", invoice_str)
        self.textbox.configure(state="disabled")


# LoginView for admin login using customtkinter.
class LoginView(ctk.CTkToplevel):
    def __init__(self, on_login):
        super().__init__()
        self.title("Admin Login")
        self.geometry("300x200")
        self.on_login = on_login
        self.create_widgets()
    
    def create_widgets(self):
        label_font = ("Helvetica", 14)
        label_username = ctk.CTkLabel(self, text="Username:", font=label_font)
        label_username.pack(pady=5)
        
        self.username_entry = ctk.CTkEntry(self, font=label_font)
        self.username_entry.pack(pady=5)
        
        label_password = ctk.CTkLabel(self, text="Password:", font=label_font)
        label_password.pack(pady=5)
        
        self.password_entry = ctk.CTkEntry(self, show="*", font=label_font)
        self.password_entry.pack(pady=5)
        
        login_button = ctk.CTkButton(self, text="Login", font=label_font, command=self.login)
        login_button.pack(pady=10)
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return
        self.on_login(username, password)


# AdminPanelView to update menu prices using a CTkTabview.
class AdminPanelView(ctk.CTkToplevel):
    def __init__(self, menu, on_update_price):
        super().__init__()
        self.title("Admin Panel - Update Prices")
        self.geometry("800x600")
        self.menu = menu
        self.on_update_price = on_update_price
        self.entries = {}  # (category, item) -> entry widget
        self.create_widgets()
    
    def create_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        label_font = ("Helvetica", 14)
        
        for category, items in self.menu.items():
            self.tabview.add(category)
            frame = self.tabview.tab(category)
            row = 0
            for item, price in items.items():
                label_item = ctk.CTkLabel(frame, text=item, font=label_font)
                label_item.grid(row=row, column=0, sticky="w", padx=5, pady=5)
                
                label_current = ctk.CTkLabel(frame, text="Current Price:", font=label_font)
                label_current.grid(row=row, column=1, padx=5, pady=5)
                
                price_label = ctk.CTkLabel(frame, text=f"GHS {price:.2f}", font=label_font)
                price_label.grid(row=row, column=2, padx=5, pady=5)
                
                label_new = ctk.CTkLabel(frame, text="New Price:", font=label_font)
                label_new.grid(row=row, column=3, padx=5, pady=5)
                
                entry = ctk.CTkEntry(frame, width=10, font=label_font)
                entry.grid(row=row, column=4, padx=5, pady=5)
                self.entries[(category, item)] = entry
                
                update_button = ctk.CTkButton(frame, text="Update", font=label_font, 
                                              command=lambda c=category, i=item, e=entry: self.update_price(c, i, e))
                update_button.grid(row=row, column=5, padx=5, pady=5)
                row += 1
    
    def update_price(self, category, item, entry_widget):
        new_price = entry_widget.get()
        if not new_price:
            messagebox.showerror("Error", "Please enter a new price.")
            return
        try:
            new_price_float = float(new_price)
        except ValueError:
            messagebox.showerror("Error", "Invalid price. Please enter a valid number.")
            return
        success = self.on_update_price(category, item, new_price_float)
        if success:
            messagebox.showinfo("Success", f"Price for '{item}' updated successfully.")
            entry_widget.delete(0, tk.END)
        else:
            messagebox.showerror("Error", f"Failed to update price for '{item}'.")