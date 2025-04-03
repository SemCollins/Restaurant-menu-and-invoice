import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk 

# ---------------- HomeView ----------------
class HomeView(ctk.CTk):
    def __init__(self, on_order, on_admin_login):
        super().__init__()
        self.title("Welcome to Coded Restaurant_")
        self.geometry("400x300")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Load background image using Pillow.
        try:
            bg_image = Image.open('Images/bg.png')
            bg_photo = ImageTk.PhotoImage(bg_image)
            bg_label = ctk.CTkLabel(self, image=bg_photo, text="")
            bg_label.image = bg_photo  # Keep a reference.
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print("Background image not found or failed to load:", e)
        
        welcome_label = ctk.CTkLabel(self, text="Welcome to Coded Restaurant", font=("Helvetica Bold-Oblique", 22))
        welcome_label.pack(pady=20)
        
        # Updated button colors to complement the background.
        order_button = ctk.CTkButton(self, text="Place Order", font=("Helvetica", 16),
                                     command=on_order, fg_color="#1E90FF")
        order_button.pack(pady=10)
        
        admin_button = ctk.CTkButton(self, text="Admin Login", font=("Helvetica", 16),
                                     command=on_admin_login, fg_color="#1E90FF")
        admin_button.pack(pady=10)

# ---------------- OrderView ----------------
class OrderView(ctk.CTkToplevel):
    def __init__(self, menu, on_generate_invoice, on_back):
        super().__init__()
        self.title("Place Order")
        self.geometry("800x600")
        self.menu = menu
        self.on_generate_invoice = on_generate_invoice
        self.on_back = on_back
        self.order_summary = {}  # Mapping (category, item) -> quantity
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Enlarged order summary frame at the top.
        summary_frame = ctk.CTkFrame(self)
        summary_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.summary_textbox = ctk.CTkTextbox(summary_frame, wrap="word", font=("Helvetica", 14), height=150)
        self.summary_textbox.grid(row=0, column=0, sticky="ew")
        
        summary_scrollbar = ctk.CTkScrollbar(summary_frame, orientation="vertical", command=self.summary_textbox.yview)
        summary_scrollbar.grid(row=0, column=1, sticky="ns")
        self.summary_textbox.configure(yscrollcommand=summary_scrollbar.set)
        self.summary_textbox.configure(state="disabled")
        
        # Tabview for menu items.
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        label_font = ("Helvetica", 14)
        # For each category, add a scrollable frame.
        for category, items in self.menu.items():
            self.tabview.add(category)
            tab_frame = self.tabview.tab(category)
            scroll_frame = ctk.CTkScrollableFrame(tab_frame, width=750, height=400)
            scroll_frame.pack(fill="both", expand=True)
            row = 0
            for item, price in items.items():
                label_item = ctk.CTkLabel(scroll_frame, text=item, font=label_font)
                label_item.grid(row=row, column=0, sticky="w", padx=5, pady=5)
                
                label_price = ctk.CTkLabel(scroll_frame, text=f"GHS {price:.2f}", font=label_font)
                label_price.grid(row=row, column=1, padx=5, pady=5)
                
                plus_button = ctk.CTkButton(scroll_frame, text="+", width=30, font=label_font,
                                             command=lambda c=category, i=item: self.add_item(c, i))
                plus_button.grid(row=row, column=2, padx=5, pady=5)
                
                minus_button = ctk.CTkButton(scroll_frame, text="–", width=30, font=label_font,
                                              command=lambda c=category, i=item: self.remove_item(c, i))
                minus_button.grid(row=row, column=3, padx=5, pady=5)
                row += 1

        # Bottom button frame with Generate Invoice, Clear Orders, and Back buttons.
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=2, column=0, pady=10, padx=10, sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        invoice_button = ctk.CTkButton(self.button_frame, text="Generate Invoice", font=("Helvetica", 16),
                                       command=self.generate_invoice)
        invoice_button.grid(row=0, column=0, padx=5, pady=5)
        
        clear_button = ctk.CTkButton(self.button_frame, text="Clear Orders", font=("Helvetica", 16),
                                     command=self.clear_orders)
        clear_button.grid(row=0, column=1, padx=5, pady=5)
        
        back_button = ctk.CTkButton(self.button_frame, text="Back", font=("Helvetica", 16),
                                    command=self.back)
        back_button.grid(row=0, column=2, padx=5, pady=5)
    
    def add_item(self, category, item):
        key = (category, item)
        self.order_summary[key] = self.order_summary.get(key, 0) + 1
        self.update_summary_display()
    
    def remove_item(self, category, item):
        key = (category, item)
        if key in self.order_summary:
            if self.order_summary[key] > 1:
                self.order_summary[key] -= 1
            else:
                del self.order_summary[key]
            self.update_summary_display()
    
    def clear_orders(self):
        self.order_summary.clear()
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

# ---------------- InvoiceView ----------------
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

# ---------------- LoginView ----------------
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

# ---------------- AdminPanelView ----------------
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
                
                edit_button = ctk.CTkButton(frame, text="Edit", font=label_font, 
                                            command=lambda c=category, i=item, p=price: self.open_edit_window(c, i, p))
                edit_button.grid(row=row, column=6, padx=5, pady=5)
                row += 1
        
        main_edit_button = ctk.CTkButton(self, text="Main Edit", font=("Helvetica", 16),
                                         command=self.open_major_edit_window)
        main_edit_button.pack(pady=10)
        
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
    
    def open_edit_window(self, category, item, current_price):
        ProductEditView(self, category, item, current_price)
    
    def open_major_edit_window(self):
        MajorEditView(self)
    
    def back(self):
        self.destroy()
        self.on_back()

# ---------------- ProductEditView ----------------
class ProductEditView(ctk.CTkToplevel):
    def __init__(self, parent, category, item, current_price):
        super().__init__(parent)
        self.title(f"Edit Product: {item}")
        self.geometry("400x300")
        self.category = category
        self.item = item
        self.current_price = current_price
        self.create_widgets()
    
    def create_widgets(self):
        label_font = ("Helvetica", 14)
        
        name_label = ctk.CTkLabel(self, text="Product Name:", font=label_font)
        name_label.pack(pady=5)
        self.name_entry = ctk.CTkEntry(self, font=label_font)
        self.name_entry.insert(0, self.item)
        self.name_entry.pack(pady=5)
        
        price_label = ctk.CTkLabel(self, text="Price:", font=label_font)
        price_label.pack(pady=5)
        self.price_entry = ctk.CTkEntry(self, font=label_font)
        self.price_entry.insert(0, f"{self.current_price:.2f}")
        self.price_entry.pack(pady=5)
        
        # Additional fields (e.g., quantity, description) can be added here.
        
        save_button = ctk.CTkButton(self, text="Save Changes", font=label_font, command=self.save_changes)
        save_button.pack(pady=10)
    
    def save_changes(self):
        new_name = self.name_entry.get()
        new_price = self.price_entry.get()
        # Implement saving logic as needed.
        messagebox.showinfo("Saved", f"Changes saved for product '{new_name}'.")
        self.destroy()

# ---------------- MajorEditView ----------------
class MajorEditView(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Major Edit Options")
        self.geometry("400x400")
        self.grab_set()     # Make this window modal.
        self.focus_set()
        self.create_widgets()
    
    def create_widgets(self):
        label_font = ("Helvetica", 14)
        label = ctk.CTkLabel(self, text="Major Edit Options", font=label_font)
        label.pack(pady=10)
        
        add_category_button = ctk.CTkButton(self, text="Add Category", font=label_font, command=self.add_category)
        add_category_button.pack(pady=5)
        
        add_item_button = ctk.CTkButton(self, text="Add Item", font=label_font, command=self.add_item)
        add_item_button.pack(pady=5)
        
        remove_item_button = ctk.CTkButton(self, text="Remove Item", font=label_font, command=self.remove_item)
        remove_item_button.pack(pady=5)
        
        edit_invoice_button = ctk.CTkButton(self, text="Edit Invoice Format", font=label_font, command=self.edit_invoice)
        edit_invoice_button.pack(pady=5)
    
    def add_category(self):
        messagebox.showinfo("Add Category", "Add Category functionality not implemented yet.")
    
    def add_item(self):
        messagebox.showinfo("Add Item", "Add Item functionality not implemented yet.")
    
    def remove_item(self):
        messagebox.showinfo("Remove Item", "Remove Item functionality not implemented yet.")
    
    def edit_invoice(self):
        messagebox.showinfo("Edit Invoice", "Edit Invoice Format functionality not implemented yet.")