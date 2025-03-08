import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

# Home view remains largely unchanged.
class HomeView(ctk.CTk):
    def __init__(self, on_order, on_admin_login):
        super().__init__()
        self.title("Welcome to Coded Restaurant_")
        self.geometry("400x300")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

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

# OrderView with order summary, plus buttons, and back button.
class OrderView(ctk.CTkToplevel):
    def __init__(self, menu, on_generate_invoice, on_back):
        super().__init__()
        self.title("Place Order")
        self.geometry("800x600")
        self.menu = menu
        self.on_generate_invoice = on_generate_invoice
        self.on_back = on_back
        self.order_summary = {}  # Mapping (category, item) -> quantity

        # Layout: row0 for order summary, row1 for menu tabs, row2 for buttons.
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Order summary textbox.
        self.summary_textbox = ctk.CTkTextbox(self, wrap="word", font=("Helvetica", 14), height=100)
        self.summary_textbox.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.summary_textbox.configure(state="disabled")

        # Tabview for menu items.
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
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
                
                plus_button = ctk.CTkButton(frame, text="+", width=30, font=label_font,
                                             command=lambda c=category, i=item: self.add_item(c, i))
                plus_button.grid(row=row, column=2, padx=5, pady=5)
                row += 1

        # Bottom button frame with Generate Invoice and Back buttons.
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=2, column=0, pady=10, padx=10, sticky="ew")
        self.button_frame.grid_columnconfigure((0,1), weight=1)
        
        invoice_button = ctk.CTkButton(self.button_frame, text="Generate Invoice", font=("Helvetica", 16),
                                       command=self.generate_invoice)
        invoice_button.grid(row=0, column=0, padx=5, pady=5)
        
        back_button = ctk.CTkButton(self.button_frame, text="Back", font=("Helvetica", 16),
                                    command=self.back)
        back_button.grid(row=0, column=1, padx=5, pady=5)
    
    def add_item(self, category, item):
        key = (category, item)
        self.order_summary[key] = self.order_summary.get(key, 0) + 1
        self.update_summary_display()
    
    def update_summary_display(self):
        self.summary_textbox.configure(state="normal")
        self.summary_textbox.delete("1.0", "end")
        for (cat, item), qty in self.order_summary.items():
            self.summary_textbox.insert("end", f"{item} (x{qty})\n")
        self.summary_textbox.configure(state="disabled")
    
    def generate_invoice(self):
        if not self.order_summary:
            messagebox.showerror("Error", "No items selected.")
            return
        order_details = []
        for (category, item), qty in self.order_summary.items():
            price = self.menu[category][item]
            order_details.append((category, item, qty, price))
        self.withdraw()  # Hide OrderView.
        self.on_generate_invoice(order_details, self)
    
    def back(self):
        self.destroy()
        self.on_back()

# InvoiceView with a back button.
class InvoiceView(ctk.CTkToplevel):
    def __init__(self, order_items, order_time, total, on_back):
        super().__init__()
        self.title("Invoice")
        self.geometry("400x500")
        self.on_back = on_back
        self.create_widgets(order_items, order_time, total)
    
    def create_widgets(self, order_items, order_time, total):
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.textbox = ctk.CTkTextbox(container, wrap="word", font=("Helvetica", 14))
        self.textbox.pack(side="top", fill="both", expand=True)
        
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
        
        back_button = ctk.CTkButton(self, text="Back", font=("Helvetica", 16), command=self.back)
        back_button.pack(pady=10)
    
    def back(self):
        self.destroy()
        self.on_back()

# LoginView with a back button.
class LoginView(ctk.CTkToplevel):
    def __init__(self, on_login, on_back):
        super().__init__()
        self.title("Admin Login")
        self.geometry("300x250")
        self.on_login = on_login
        self.on_back = on_back
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
        login_button.pack(pady=5)
        
        back_button = ctk.CTkButton(self, text="Back", font=label_font, command=self.back)
        back_button.pack(pady=5)
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return
        self.on_login(username, password)
    
    def back(self):
        self.destroy()
        self.on_back()

# AdminPanelView with a back button.
class AdminPanelView(ctk.CTkToplevel):
    def __init__(self, menu, on_update_price, on_back):
        super().__init__()
        self.title("Admin Panel - Update Prices")
        self.geometry("800x600")
        self.menu = menu
        self.on_update_price = on_update_price
        self.on_back = on_back
        self.entries = {}  # Mapping (category, item) -> entry widget.
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
        
        back_button = ctk.CTkButton(self, text="Back", font=("Helvetica", 16), command=self.back)
        back_button.pack(pady=10)
    
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
    
    def back(self):
        self.destroy()
        self.on_back()