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
        try:
            bg_image = Image.open("Images/bg.png")
            bg_ctk = ctk.CTkImage(light_image=bg_image, dark_image=bg_image, size=(400,300))
            bg_label = ctk.CTkLabel(self, image=bg_ctk, text="")
            bg_label.image = bg_ctk
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        except Exception as e:
            print("HomeView background image error:", e)
        welcome_label = ctk.CTkLabel(self, text="Welcome to Coded Restaurant", font=("Helvetica Bold-Oblique", 22))
        welcome_label.pack(pady=20)
        order_button = ctk.CTkButton(self, text="Place Order", font=("Helvetica", 16),
                                     command=on_order, fg_color="#2980b9")
        order_button.pack(pady=10)
        admin_button = ctk.CTkButton(self, text="Admin Login", font=("Helvetica", 16),
                                     command=on_admin_login, fg_color="#2980b9")
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
        self.order_summary = {}
        try:
            plus_raw = Image.open("Images/plus_icon.png")
            self.plus_img = ctk.CTkImage(light_image=plus_raw, dark_image=plus_raw, size=(30,30))
        except Exception as e:
            print("Error loading plus_icon.png:", e)
            self.plus_img = None
        try:
            minus_raw = Image.open("Images/minus_icon.png")
            self.minus_img = ctk.CTkImage(light_image=minus_raw, dark_image=minus_raw, size=(30,30))
        except Exception as e:
            print("Error loading minus_icon.png:", e)
            self.minus_img = None

        self.bg_images = {
            "Main Courses": "Images/atseke.png",
            "Drinks": "Images/grand_combi.png",
            "Appetizers": "Images/grand_shrimp.png",
            "Desserts": "Images/jollof_chicken.png",
            "Other": "Images/bg.png"
        }
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        summary_frame = ctk.CTkFrame(self)
        summary_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.summary_textbox = ctk.CTkTextbox(summary_frame, wrap="word", font=("Helvetica", 14), height=250)
        self.summary_textbox.grid(row=0, column=0, sticky="ew")
        summary_scrollbar = ctk.CTkScrollbar(summary_frame, orientation="vertical", command=self.summary_textbox.yview)
        summary_scrollbar.grid(row=0, column=1, sticky="ns")
        self.summary_textbox.configure(yscrollcommand=summary_scrollbar.set)
        self.summary_textbox.configure(state="disabled")
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        label_font = ("Helvetica", 14)
        for category, items in self.menu.items():
            self.tabview.add(category)
            tab_frame = self.tabview.tab(category)
            container = tk.Frame(tab_frame)
            container.pack(fill="both", expand=True)
            canvas = tk.Canvas(container, width=750, height=400, bd=0, highlightthickness=0)
            canvas.pack(side="left", fill="both", expand=True)
            v_scroll = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
            v_scroll.pack(side="right", fill="y")
            canvas.configure(yscrollcommand=v_scroll.set)
            try:
                bg_path = self.bg_images.get(category, "Images/bg.png")
                bg_img = Image.open(bg_path).resize((750,400), Image.LANCZOS)
                bg_photo = ImageTk.PhotoImage(bg_img)
                canvas.bg_photo = bg_photo
                canvas.create_image(0, 0, image=bg_photo, anchor="nw")
            except Exception as e:
                print("Error loading canvas background for", category, e)
            inner_frame = tk.Frame(canvas)
            canvas.create_window((0,0), window=inner_frame, anchor="nw")
            inner_frame.bind("<Configure>", lambda event, c=canvas: c.configure(scrollregion=c.bbox("all")))
            try:
                overlay_bg_img = Image.open(self.bg_images.get(category, "Images/bg.png")).resize((730,380), Image.LANCZOS)
                overlay_bg_photo = ImageTk.PhotoImage(overlay_bg_img)
            except Exception as e:
                print("Error loading overlay background for", category, e)
                overlay_bg_photo = None
            # Improved touchpad scrolling: scroll one unit for any nonzero delta.
            def _on_mousewheel(event, canvas=canvas):
                if event.delta:
                    scroll_units = -1 if event.delta > 0 else 1
                    canvas.yview_scroll(scroll_units, "units")
            canvas.bind("<Enter>", lambda e: canvas.focus_set())
            canvas.bind("<MouseWheel>", _on_mousewheel)
            canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
            overlay = ctk.CTkFrame(inner_frame, width=730, height=380, corner_radius=15, fg_color=("white","gray10"))
            overlay.pack(padx=10, pady=10)
            if overlay_bg_photo is not None:
                overlay_bg_label = tk.Label(overlay, image=overlay_bg_photo, bd=0)
                overlay_bg_label.image = overlay_bg_photo
                overlay_bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
                overlay_bg_label.lower()
            self.animate_overlay(overlay, 0)
            row = 0
            for item, price in items.items():
                label_item = ctk.CTkLabel(overlay, text=item, font=label_font)
                label_item.grid(row=row, column=0, sticky="w", padx=5, pady=5)
                label_price = ctk.CTkLabel(overlay, text=f"GHS {price:.2f}", font=label_font)
                label_price.grid(row=row, column=1, padx=5, pady=5)
                if self.plus_img:
                    plus_button = ctk.CTkButton(overlay, image=self.plus_img, text="",
                                                width=30, command=lambda c=category, i=item: self.add_item(c, i))
                else:
                    plus_button = ctk.CTkButton(overlay, text="+", width=30,
                                                command=lambda c=category, i=item: self.add_item(c, i))
                plus_button.grid(row=row, column=2, padx=5, pady=5)
                if self.minus_img:
                    minus_button = ctk.CTkButton(overlay, image=self.minus_img, text="",
                                                 width=30, command=lambda c=category, i=item: self.remove_item(c, i))
                else:
                    minus_button = ctk.CTkButton(overlay, text="–", width=30,
                                                 command=lambda c=category, i=item: self.remove_item(c, i))
                minus_button.grid(row=row, column=3, padx=5, pady=5)
                row += 1
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
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
    
    def animate_overlay(self, widget, step):
        colors = [("orange", "gray10"), ("lightgray", "gray20")]
        widget.configure(fg_color=colors[step % len(colors)])
        widget.after(1000, lambda: self.animate_overlay(widget, step + 1))
    
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
        self.withdraw()
        self.on_generate_invoice(order_details, self)
    
    def back(self):
        self.destroy()
        self.on_back()

# ---------------- InvoiceView ----------------
class InvoiceView(ctk.CTkToplevel):
    def __init__(self, invoice_text, on_back):
        super().__init__()
        self.title("Invoice")
        self.geometry("400x500")
        self.on_back = on_back
        self.create_widgets(invoice_text)
    
    def create_widgets(self, invoice_text):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        try:
            bg_img = Image.open("Images/grand_crab.png").resize((400,500), Image.LANCZOS)
            bg_ctk = ctk.CTkImage(light_image=bg_img, dark_image=bg_img, size=(400,500))
            bg_label = ctk.CTkLabel(container, image=bg_ctk, text="")
            bg_label.image = bg_ctk
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
            bg_label.lower()
        except Exception as e:
            print("Invoice background image error:", e)
        self.textbox = ctk.CTkTextbox(container, wrap="word", font=("Helvetica", 14))
        self.textbox.pack(side="top", fill="both", expand=True)
        scrollbar = ctk.CTkScrollbar(container, orientation="vertical", command=self.textbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.textbox.configure(yscrollcommand=scrollbar.set)
        self.textbox.insert("0.0", invoice_text)
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
        self.attributes("-topmost", True)
        self.title("Admin Login")
        self.geometry("300x250")
        self.on_login = on_login
        self.on_back = on_back
        self.create_widgets()
        self.focus_force()
    
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
        login_button = ctk.CTkButton(self, text="Login", font=label_font, command=lambda: (print("Login pressed"), self.on_login(self.username_entry.get(), self.password_entry.get())))
        login_button.pack(pady=5)
        back_button = ctk.CTkButton(self, text="Back", font=label_font, command=self.back)
        back_button.pack(pady=5)
    
    def back(self):
        self.destroy()
        self.on_back()

# ---------------- AdminPanelView and Related Edit Views ----------------
class AdminPanelView(ctk.CTkToplevel):
    def __init__(self, menu_model, controller, on_back):
        super().__init__()
        self.attributes("-topmost", True)
        self.title("Admin Panel - Update Prices")
        self.geometry("800x600")
        self.menu_model = menu_model
        self.controller = controller
        self.on_back = on_back
        self.entries = {}
        self.create_widgets()
        self.major_edit_view = None
        self.focus_force()
    
    def create_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        label_font = ("Helvetica", 14)
        for category, items in self.menu_model.get_menu().items():
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
        success = self.menu_model.update_price(category, item, new_price_float)
        if success:
            messagebox.showinfo("Success", f"Price for '{item}' updated successfully.")
            entry_widget.delete(0, tk.END)
        else:
            messagebox.showerror("Error", f"Failed to update price for '{item}'.")
    
    def open_edit_window(self, category, item, current_price):
        ProductEditView(self, category, item, current_price, self.controller)
    
    def open_major_edit_window(self):
        if self.major_edit_view is not None and self.major_edit_view.winfo_exists():
            self.major_edit_view.lift()
            return
        self.major_edit_view = MajorEditView(self, self.controller)
    
    def back(self):
        self.destroy()
        self.on_back()

class ProductEditView(ctk.CTkToplevel):
    def __init__(self, parent, category, item, current_price, controller):
        super().__init__(parent)
        self.attributes("-topmost", True)
        self.title(f"Edit Product: {item}")
        self.geometry("400x300")
        self.category = category
        self.item = item  # old item name
        self.current_price = current_price
        self.controller = controller
        self.create_widgets()
        self.focus_force()
    
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
        save_button = ctk.CTkButton(self, text="Save Changes", font=label_font, command=self.save_changes)
        save_button.pack(pady=10)
    
    def save_changes(self):
        new_name = self.name_entry.get().strip()
        new_price = self.price_entry.get().strip()
        if not new_name or not new_price:
            messagebox.showerror("Error", "Product name and price cannot be empty.")
            return
        try:
            new_price_float = float(new_price)
        except ValueError:
            messagebox.showerror("Error", "Invalid price. Please enter a valid number.")
            return
        updated = self.controller.menu_model.update_product(self.category, self.item, new_name, new_price_float)
        if updated:
            messagebox.showinfo("Success", f"Product '{new_name}' updated successfully.")
        else:
            messagebox.showerror("Error", "Update failed. Check that the product exists and try again.")
        self.destroy()

class MajorEditView(ctk.CTkToplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.attributes("-topmost", True)
        self.title("Major Edit Options")
        self.geometry("400x400")
        # Uncomment the following line if you want modal behavior.
        # self.grab_set()
        self.controller = controller
        self.parent = parent
        self.create_widgets()
        self.add_category_view = None
        self.add_item_view = None
        self.remove_item_view = None
        self.invoice_format_view = None
        self.focus_force()
    
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
        print("Add Category button pressed")
        if self.add_category_view is not None and self.add_category_view.winfo_exists():
            self.add_category_view.lift()
            return
        self.add_category_view = AddCategoryView(self, self.controller)
    
    def add_item(self):
        print("Add Item button pressed")
        if self.add_item_view is not None and self.add_item_view.winfo_exists():
            self.add_item_view.lift()
            return
        self.add_item_view = AddItemView(self, self.controller)
    
    def remove_item(self):
        print("Remove Item button pressed")
        if self.remove_item_view is not None and self.remove_item_view.winfo_exists():
            self.remove_item_view.lift()
            return
        self.remove_item_view = RemoveItemView(self, self.controller)
    
    def edit_invoice(self):
        print("Edit Invoice Format button pressed")
        if self.invoice_format_view is not None and self.invoice_format_view.winfo_exists():
            self.invoice_format_view.lift()
            return
        self.invoice_format_view = InvoiceFormatEditView(self, self.controller)

class AddCategoryView(ctk.CTkToplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.attributes("-topmost", True)
        self.title("Add New Category")
        self.geometry("300x200")
        self.controller = controller
        self.create_widgets()
        self.focus_force()
    
    def create_widgets(self):
        label_font = ("Helvetica", 14)
        label = ctk.CTkLabel(self, text="Category Name:", font=label_font)
        label.pack(pady=10)
        self.category_entry = ctk.CTkEntry(self, font=label_font)
        self.category_entry.pack(pady=5)
        add_button = ctk.CTkButton(self, text="Add Category", font=label_font, command=self.add_category)
        add_button.pack(pady=10)
    
    def add_category(self):
        category = self.category_entry.get().strip()
        if not category:
            messagebox.showerror("Error", "Please enter a category name.")
            return
        success = self.controller.menu_model.add_category(category)
        print("Attempting to add category:", category, "Success:", success)
        if success:
            messagebox.showinfo("Success", f"Category '{category}' added.")
            self.destroy()
        else:
            messagebox.showerror("Error", f"Category '{category}' already exists.")

class AddItemView(ctk.CTkToplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.attributes("-topmost", True)
        self.title("Add New Item")
        self.geometry("300x300")
        self.controller = controller
        self.menu_model = controller.menu_model
        self.create_widgets()
        self.focus_force()
    
    def create_widgets(self):
        label_font = ("Helvetica", 14)
        tk.Label(self, text="Select Category:", font=label_font).pack(pady=5)
        self.selected_category = tk.StringVar(self)
        categories = list(self.menu_model.get_menu().keys())
        if categories:
            self.selected_category.set(categories[0])
        self.category_menu = ctk.CTkOptionMenu(self, values=categories, variable=self.selected_category)
        self.category_menu.pack(pady=5)
        tk.Label(self, text="Item Name:", font=label_font).pack(pady=5)
        self.item_entry = ctk.CTkEntry(self, font=label_font)
        self.item_entry.pack(pady=5)
        tk.Label(self, text="Price:", font=label_font).pack(pady=5)
        self.price_entry = ctk.CTkEntry(self, font=label_font)
        self.price_entry.pack(pady=5)
        add_button = ctk.CTkButton(self, text="Add Item", font=label_font, command=self.add_item)
        add_button.pack(pady=10)
    
    def add_item(self):
        category = self.selected_category.get()
        item = self.item_entry.get().strip()
        price = self.price_entry.get().strip()
        if not item or not price:
            messagebox.showerror("Error", "Please enter both item name and price.")
            return
        success = self.menu_model.add_item(category, item, price)
        print("Attempting to add item:", item, "in category:", category, "Success:", success)
        if success:
            messagebox.showinfo("Success", f"Item '{item}' added to category '{category}'.")
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to add item. It may already exist or price is invalid.")

class RemoveItemView(ctk.CTkToplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.attributes("-topmost", True)
        self.title("Remove Item")
        self.geometry("300x300")
        self.controller = controller
        self.menu_model = controller.menu_model
        self.create_widgets()
        self.focus_force()
    
    def create_widgets(self):
        label_font = ("Helvetica", 14)
        tk.Label(self, text="Select Category:", font=label_font).pack(pady=5)
        self.selected_category = tk.StringVar(self)
        categories = list(self.menu_model.get_menu().keys())
        if categories:
            self.selected_category.set(categories[0])
        self.category_menu = ctk.CTkOptionMenu(self, values=categories, variable=self.selected_category, command=self.update_items)
        self.category_menu.pack(pady=5)
        tk.Label(self, text="Select Item:", font=label_font).pack(pady=5)
        self.selected_item = tk.StringVar(self)
        first_category_items = list(self.menu_model.get_menu().get(self.selected_category.get(), {}).keys())
        if first_category_items:
            self.selected_item.set(first_category_items[0])
        self.item_menu = ctk.CTkOptionMenu(self, values=first_category_items, variable=self.selected_item)
        self.item_menu.pack(pady=5)
        remove_button = ctk.CTkButton(self, text="Remove Item", font=label_font, command=self.remove_item)
        remove_button.pack(pady=10)
    
    def update_items(self, _):
        items = list(self.menu_model.get_menu().get(self.selected_category.get(), {}).keys())
        if items:
            self.selected_item.set(items[0])
        else:
            self.selected_item.set("")
        self.item_menu.configure(values=items)
    
    def remove_item(self):
        category = self.selected_category.get()
        item = self.selected_item.get()
        if not item:
            messagebox.showerror("Error", "No item selected.")
            return
        success = self.menu_model.remove_item(category, item)
        print("Attempting to remove item:", item, "from category:", category, "Success:", success)
        if success:
            messagebox.showinfo("Success", f"Item '{item}' removed from category '{category}'.")
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to remove item.")

class InvoiceFormatEditView(ctk.CTkToplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.attributes("-topmost", True)
        self.title("Edit Invoice Format")
        self.geometry("500x400")
        self.controller = controller
        self.create_widgets()
        self.focus_force()
    
    def create_widgets(self):
        label_font = ("Helvetica", 14)
        label = ctk.CTkLabel(self, text="Edit Invoice Template:", font=label_font)
        label.pack(pady=10)
        self.textbox = ctk.CTkTextbox(self, wrap="word", font=label_font)
        self.textbox.insert("0.0", self.controller.invoice_template)
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        save_button = ctk.CTkButton(self, text="Save Template", font=label_font, command=self.save_template)
        save_button.pack(pady=10)
    
    def save_template(self):
        new_template = self.textbox.get("0.0", "end").strip()
        if new_template:
            self.controller.invoice_template = new_template
            messagebox.showinfo("Success", "Invoice template updated.")
            self.destroy()
        else:
            messagebox.showerror("Error", "Template cannot be empty.")
