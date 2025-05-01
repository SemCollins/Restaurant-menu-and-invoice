# view.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# --- HomeView ---
class HomeView(ctk.CTk):
    def __init__(self, on_order, on_admin_login):
        super().__init__()
        self.title("Welcome to Coded Restaurant")
        self.geometry("400x300")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        try:
            bg = Image.open("Images/bg.png").resize((400,300), Image.Resampling.LANCZOS)
            img = ctk.CTkImage(light_image=bg, dark_image=bg, size=(400,300))
            lbl = ctk.CTkLabel(self, image=img, text="")
            lbl.image = img
            lbl.place(relx=0, rely=0, relwidth=1, relheight=1)
        except Exception as e:
            print("HomeView background image error:", e)
            self.configure(fg_color="gray20")
        ctk.CTkLabel(
            self, text="Welcome to Coded Restaurant",
            font=("Helvetica Bold-Oblique", 22)
        ).pack(pady=20)
        ctk.CTkButton(
            self, text="Place Order", font=("Helvetica", 16),
            command=on_order, fg_color="#2980b9"
        ).pack(pady=10)
        ctk.CTkButton(
            self, text="Admin Login", font=("Helvetica", 16),
            command=on_admin_login, fg_color="#2980b9"
        ).pack(pady=10)


# --- OrderView ---
class OrderView(ctk.CTkToplevel):
    def __init__(self, menu, on_generate_invoice, on_back):
        super().__init__()
        self.title("Place Order")
        self.geometry("800x600")
        self.resizable(False, False)
        self.menu = menu
        self.on_generate_invoice = on_generate_invoice
        self.on_back = on_back
        self.order_summary = {}

        # Load plus/minus icons
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

        # Background images per category
        self.bg_images = {
            "Main Courses": "Images/atseke.png",
            "Drinks": "Images/grand_combi.png",
            "Appetizers": "Images/grand_shrimp.png",
            "Desserts": "Images/jollof_chicken.png",
            "Other": "Images/bg.png"
        }

        # Layout configuration
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Summary frame
        sf = ctk.CTkFrame(self, fg_color="gray20")
        sf.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        sf.grid_columnconfigure(0, weight=1)
        sf.grid_rowconfigure(0, weight=1)
        self.summary_textbox = ctk.CTkTextbox(sf, wrap="word", font=("Helvetica",14), height=100)
        self.summary_textbox.grid(row=0, column=0, sticky="nsew")
        sb = ctk.CTkScrollbar(sf, orientation="vertical", command=self.summary_textbox.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.summary_textbox.configure(yscrollcommand=sb.set, state="disabled")

        # Tabview for menu
        tv = ctk.CTkTabview(self)
        tv.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        for category in sorted(self.menu.keys()):
            if not category:
                continue
            tv.add(category)
            container = ctk.CTkFrame(tv.tab(category), fg_color="transparent")
            container.pack(fill="both", expand=True)
            canvas = tk.Canvas(container, bd=0, highlightthickness=0)
            canvas.pack(side="left", fill="both", expand=True)
            vs = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
            vs.pack(side="right", fill="y")
            canvas.configure(yscrollcommand=vs.set)

            # Canvas background
            try:
                path = self.bg_images.get(category, "Images/bg.png")
                img = Image.open(path).resize((750-vs.winfo_reqwidth(),400), Image.Resampling.LANCZOS)
                bgp = ImageTk.PhotoImage(img)
                canvas.bgp = bgp
                canvas.create_image(0,0,image=bgp,anchor="nw")
            except Exception:
                canvas.configure(bg=container.cget("fg_color"))

            inner = ctk.CTkFrame(canvas, fg_color=("white","gray10"), corner_radius=15)
            canvas.create_window((0,0), window=inner, anchor="nw")
            inner.bind(
                "<Configure>",
                lambda e, c=canvas: c.configure(scrollregion=c.bbox("all"))
            )
            canvas.bind("<Enter>", lambda e: canvas.focus_set())
            canvas.bind("<MouseWheel>", lambda e, c=canvas: c.yview_scroll(-int(e.delta/120),"units"))
            canvas.bind("<Button-4>", lambda e, c=canvas: c.yview_scroll(-1,"units"))
            canvas.bind("<Button-5>", lambda e, c=canvas: c.yview_scroll(1,"units"))

            row = 0
            for item, price in sorted(self.menu[category].items()):
                ctk.CTkLabel(inner, text=item, font=("Helvetica",14))\
                    .grid(row=row, column=0, sticky="w", padx=5, pady=5)
                ctk.CTkLabel(inner, text=f"GHS {price:.2f}", font=("Helvetica",14))\
                    .grid(row=row, column=1, padx=5, pady=5)
                plus = ctk.CTkButton(inner,
                                     image=self.plus_img, text="", width=30,
                                     command=lambda c=category, i=item: self.add_item(c, i))
                if not self.plus_img:
                    plus.configure(text="+")
                plus.grid(row=row, column=2, padx=5, pady=5)
                minus = ctk.CTkButton(inner,
                                      image=self.minus_img, text="", width=30,
                                      command=lambda c=category, i=item: self.remove_item(c, i))
                if not self.minus_img:
                    minus.configure(text="–")
                minus.grid(row=row, column=3, padx=5, pady=5)
                row += 1

        # Bottom buttons
        bf = ctk.CTkFrame(self)
        bf.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        bf.grid_columnconfigure((0,1,2), weight=1)
        ctk.CTkButton(bf, text="Generate Invoice", font=("Helvetica",16),
                      command=self.generate_invoice)\
            .grid(row=0, column=0, sticky="ew", padx=5)
        ctk.CTkButton(bf, text="Clear Orders", font=("Helvetica",16),
                      command=self.clear_orders)\
            .grid(row=0, column=1, sticky="ew", padx=5)
        ctk.CTkButton(bf, text="Back", font=("Helvetica",16),
                      command=self.back)\
            .grid(row=0, column=2, sticky="ew", padx=5)

    def add_item(self, category, item):
        self.order_summary[(category,item)] = self.order_summary.get((category,item), 0) + 1
        self.update_summary_display()

    def remove_item(self, category, item):
        key = (category,item)
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
        if not self.order_summary:
            self.summary_textbox.insert("end", "Your order is empty.")
        else:
            for (cat,item),qty in sorted(self.order_summary.items()):
                price = self.menu.get(cat, {}).get(item)
                if price is not None:
                    total = qty * price
                    self.summary_textbox.insert(
                        "end",
                        f"{item} (x{qty}) @ GHS {price:.2f} = GHS {total:.2f}\n"
                    )
                else:
                    self.summary_textbox.insert(
                        "end",
                        f"{item} (x{qty}) - Item no longer available\n"
                    )
        self.summary_textbox.configure(state="disabled")

    def generate_invoice(self):
        if not self.order_summary:
            messagebox.showerror("Error", "No items selected.")
            return
        details = []
        for (cat,item),qty in self.order_summary.items():
            if cat in self.menu and item in self.menu[cat]:
                details.append((cat, item, qty, self.menu[cat][item]))
        if not details:
            messagebox.showerror("Error", "Selected items are no longer available.")
            return
        self.withdraw()
        self.on_generate_invoice(details, self)

    def back(self):
        self.destroy()
        self.on_back()


# --- InvoiceView ---
class InvoiceView(ctk.CTkToplevel):
    def __init__(self, invoice_text, on_back):
        super().__init__()
        self.title("Invoice")
        self.geometry("400x500")
        self.resizable(False, False)
        self.on_back = on_back
        self.create_widgets(invoice_text)

    def create_widgets(self, txt):
        ctr = ctk.CTkFrame(self, fg_color="transparent")
        ctr.pack(fill="both", expand=True, padx=10, pady=10)
        try:
            bg = Image.open("Images/grand_crab.png").resize((400,500), Image.Resampling.LANCZOS)
            img = ctk.CTkImage(light_image=bg, dark_image=bg, size=(400,500))
            lbl = ctk.CTkLabel(ctr, image=img, text="")
            lbl.image = img
            lbl.place(relx=0, rely=0, relwidth=1, relheight=1)
            lbl.lower()
        except Exception as e:
            print("Invoice background image error:", e)
            ctr.configure(fg_color="gray15")
        tb = ctk.CTkTextbox(ctr, wrap="word", font=("Helvetica",14))
        tb.pack(side="left", fill="both", expand=True)
        sb = ctk.CTkScrollbar(ctr, orientation="vertical", command=tb.yview)
        sb.pack(side="right", fill="y")
        tb.configure(yscrollcommand=sb.set)
        tb.insert("0.0", txt)
        tb.configure(state="disabled")
        ctk.CTkButton(self, text="Back", font=("Helvetica",16),
                      command=self.back).pack(pady=10)

    def back(self):
        self.destroy()
        self.on_back()


# --- LoginView ---
class LoginView(ctk.CTkToplevel):
    def __init__(self, on_login, on_back):
        super().__init__()
        self.title("Admin Login")
        self.geometry("300x250")
        self.resizable(False, False)
        self.on_login = on_login
        self.on_back = on_back
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.back)
        self.focus_force()

    def create_widgets(self):
        f = ("Helvetica",14)
        ctk.CTkLabel(self, text="Username:", font=f).pack(pady=5)
        self.username_entry = ctk.CTkEntry(self, font=f)
        self.username_entry.pack(pady=5)
        ctk.CTkLabel(self, text="Password:", font=f).pack(pady=5)
        self.password_entry = ctk.CTkEntry(self, show="*", font=f)
        self.password_entry.pack(pady=5)
        ctk.CTkButton(self, text="Login", font=f, command=self._perform_login).pack(pady=5)
        ctk.CTkButton(self, text="Back", font=f, command=self.back).pack(pady=5)

    def _perform_login(self):
        self.on_login(self.username_entry.get(), self.password_entry.get())

    def back(self):
        self.destroy()
        self.on_back()


# --- AdminPanelView ---
class AdminPanelView(ctk.CTkToplevel):
    def __init__(self, menu_model, controller, on_back):
        super().__init__()
        self.title("Admin Panel - Update Prices")
        self.geometry("800x600")
        self.resizable(False, False)
        self.menu_model = menu_model
        self.controller = controller
        self.on_back = on_back
        self.entries = {}
        self.tab_frames = {}
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.back)
        self.focus_force()

    def create_widgets(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.entries.clear()
        self.tab_frames.clear()

        tv = ctk.CTkTabview(self)
        tv.pack(fill="both", expand=True, padx=10, pady=10)
        f = ("Helvetica",14)
        data = self.menu_model.get_menu()
        for category in sorted(filter(None, data.keys())):
            tv.add(category)
            sf = ctk.CTkScrollableFrame(tv.tab(category), fg_color="transparent")
            sf.pack(fill="both", expand=True, padx=5, pady=5)
            self.tab_frames[category] = sf
            row = 0
            for item, price in sorted(data[category].items()):
                ctk.CTkLabel(sf, text=item, font=f).grid(row=row, column=0, sticky="w", padx=5, pady=5)
                ctk.CTkLabel(sf, text="Current Price:", font=f).grid(row=row, column=1, padx=5, pady=5)
                ctk.CTkLabel(sf, text=f"GHS {price:.2f}", font=f).grid(row=row, column=2, padx=5, pady=5)
                ctk.CTkLabel(sf, text="New Price:", font=f).grid(row=row, column=3, padx=5, pady=5)
                ent = ctk.CTkEntry(sf, width=100, font=f)
                ent.grid(row=row, column=4, padx=5, pady=5)
                self.entries[(category,item)] = ent
                ctk.CTkButton(sf, text="Update Price", font=f, width=100,
                              command=lambda c=category,i=item,e=ent: self.update_price_command(c,i,e))\
                    .grid(row=row, column=5, padx=5, pady=5)
                ctk.CTkButton(sf, text="Edit Item Details", font=f, width=120,
                              command=lambda c=category,i=item: self.open_edit_window(c,i))\
                    .grid(row=row, column=6, padx=5, pady=5)
                row += 1
            for col in range(7):
                sf.grid_columnconfigure(col, weight=0)

        ctk.CTkButton(self, text="Major Edit Options", font=("Helvetica",16),
                      command=self.open_major_edit_window).pack(pady=10)
        ctk.CTkButton(self, text="Back", font=("Helvetica",16),
                      command=self.back).pack(pady=10)

    def update_price_command(self, category, item, entry):
        np = entry.get().strip()
        if not np:
            messagebox.showerror("Error", "Please enter a new price.")
            return
        try:
            npf = float(np)
        except ValueError:
            messagebox.showerror("Error", "Invalid price. Please enter a number.")
            return
        if self.controller.update_menu_price(category, item, npf):
            messagebox.showinfo("Success", f"Price for '{item}' updated.")
            self.refresh_display()
        else:
            messagebox.showerror("Error", f"Failed to update price for '{item}'.")

    def open_edit_window(self, category, item):
        cp = self.menu_model.get_menu().get(category, {}).get(item)
        if cp is None:
            messagebox.showerror("Error", "Item not found.")
            return
        ProductEditView(self, category, item, cp, self.controller)

    def open_major_edit_window(self):
        if getattr(self.controller, 'major_edit_view', None) and self.controller.major_edit_view.winfo_exists():
            self.controller.major_edit_view.lift()
            return
        self.controller.major_edit_view = MajorEditView(self, self.controller)

    def back(self):
        self.destroy()
        self.on_back()

    def refresh_display(self):
        if self.winfo_exists():
            self.create_widgets()


# --- ProductEditView ---
class ProductEditView(ctk.CTkToplevel):
    def __init__(self, parent, category, item, current_price, controller):
        super().__init__(parent)
        self.title(f"Edit Product: {item}")
        self.geometry("400x300")
        self.resizable(False, False)
        self.category = category
        self.item = item
        self.current_price = current_price
        self.controller = controller
        self.parent = parent
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    def create_widgets(self):
        f = ("Helvetica",14)
        ctk.CTkLabel(self, text="Product Name:", font=f).pack(pady=5)
        self.name_entry = ctk.CTkEntry(self, font=f)
        self.name_entry.insert(0, self.item)
        self.name_entry.pack(pady=5)
        ctk.CTkLabel(self, text="Price:", font=f).pack(pady=5)
        self.price_entry = ctk.CTkEntry(self, font=f)
        self.price_entry.insert(0, f"{self.current_price:.2f}")
        self.price_entry.pack(pady=5)
        ctk.CTkButton(self, text="Save Changes", font=f, command=self.save_changes).pack(pady=10)

    def save_changes(self):
        new_name = self.name_entry.get().strip()
        new_price = self.price_entry.get().strip()
        if not new_name or not new_price:
            messagebox.showerror("Error", "Product name and price cannot be empty.")
            return
        try:
            npf = float(new_price)
        except ValueError:
            messagebox.showerror("Error", "Invalid price. Please enter a number.")
            return
        if self.controller.update_product_details(self.category, self.item, new_name, npf):
            messagebox.showinfo("Success", f"Product '{new_name}' updated.")
            if self.parent and self.parent.winfo_exists():
                self.parent.refresh_display()
            self.destroy()
        else:
            messagebox.showerror("Error", "Update failed. Check for duplicate name or invalid data.")


# --- MajorEditView ---
class MajorEditView(ctk.CTkToplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Major Edit Options")
        self.geometry("400x400")
        self.resizable(False, False)
        self.controller = controller
        self.parent = parent
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    def create_widgets(self):
        f = ("Helvetica",14)
        ctk.CTkLabel(self, text="Major Edit Options", font=f).pack(pady=10)
        ctk.CTkButton(self, text="Add Category", font=f,
                      command=self.add_category).pack(pady=5)
        ctk.CTkButton(self, text="Delete Category", font=f,
                      command=self.remove_category).pack(pady=5)
        ctk.CTkButton(self, text="Add Item", font=f,
                      command=self.add_item).pack(pady=5)
        ctk.CTkButton(self, text="Remove Item", font=f,
                      command=self.remove_item).pack(pady=5)
        ctk.CTkButton(self, text="Edit Invoice Format", font=f,
                      command=self.edit_invoice).pack(pady=5)

    def add_category(self):
        if getattr(self.controller, 'add_category_view', None) and self.controller.add_category_view.winfo_exists():
            self.controller.add_category_view.lift()
            return
        self.controller.add_category_view = AddCategoryView(self, self.controller)

    def remove_category(self):
        if getattr(self.controller, 'remove_category_view', None) and self.controller.remove_category_view.winfo_exists():
            self.controller.remove_category_view.lift()
            return
        self.controller.remove_category_view = RemoveCategoryView(self, self.controller)

    def add_item(self):
        if getattr(self.controller, 'add_item_view', None) and self.controller.add_item_view.winfo_exists():
            self.controller.add_item_view.lift()
            return
        self.controller.add_item_view = AddItemView(self, self.controller)

    def remove_item(self):
        if getattr(self.controller, 'remove_item_view', None) and self.controller.remove_item_view.winfo_exists():
            self.controller.remove_item_view.lift()
            return
        self.controller.remove_item_view = RemoveItemView(self, self.controller)

    def edit_invoice(self):
        if getattr(self.controller, 'invoice_format_view', None) and self.controller.invoice_format_view.winfo_exists():
            self.controller.invoice_format_view.lift()
            return
        self.controller.invoice_format_view = InvoiceFormatEditView(self, self.controller)


# --- AddCategoryView ---
class AddCategoryView(ctk.CTkToplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Add New Category")
        self.geometry("300x200")
        self.resizable(False, False)
        self.controller = controller
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    def create_widgets(self):
        f = ("Helvetica",14)
        ctk.CTkLabel(self, text="Category Name:", font=f).pack(pady=10)
        self.category_entry = ctk.CTkEntry(self, font=f)
        self.category_entry.pack(pady=5)
        ctk.CTkButton(self, text="Add Category", font=f,
                      command=self.add_category).pack(pady=10)

    def add_category(self):
        cat = self.category_entry.get().strip()
        if not cat:
            messagebox.showerror("Error", "Please enter a category name.")
            return
        success = self.controller.add_menu_category(cat)
        if success:
            messagebox.showinfo("Success", f"Category '{cat}' added.")
            if getattr(self.controller, 'admin_panel_view', None):
                self.controller.admin_panel_view.refresh_display()
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to add category.")


# --- RemoveCategoryView ---
class RemoveCategoryView(ctk.CTkToplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Delete Category")
        self.geometry("300x200")
        self.resizable(False, False)
        self.controller = controller
        self.menu_model = controller.menu_model
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    def create_widgets(self):
        f = ("Helvetica",14)
        ctk.CTkLabel(self, text="Select Category to Delete:", font=f).pack(pady=10)
        cats = sorted(self.menu_model.get_menu().keys())
        self.selected = tk.StringVar(value=cats[0] if cats else "")
        self.menu = ctk.CTkOptionMenu(self, values=cats, variable=self.selected)
        self.menu.pack(pady=5)
        ctk.CTkButton(self, text="Delete Category", font=f,
                      command=self.delete_category).pack(pady=10)

    def delete_category(self):
        cat = self.selected.get()
        if not cat:
            messagebox.showerror("Error", "No category selected.")
            return
        if not messagebox.askyesno("Confirm", f"Really delete category '{cat}'?"):
            return
        success = self.controller.remove_menu_category(cat)
        if success:
            messagebox.showinfo("Success", f"Category '{cat}' removed.")
            if getattr(self.controller, 'admin_panel_view', None):
                self.controller.admin_panel_view.refresh_display()
            self.destroy()
        else:
            messagebox.showerror("Error", f"Failed to remove category '{cat}'.")


# --- AddItemView ---
class AddItemView(ctk.CTkToplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Add New Item")
        self.geometry("300x350")
        self.resizable(False, False)
        self.controller = controller
        self.menu_model = controller.menu_model
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    def create_widgets(self):
        f = ("Helvetica",14)
        ctk.CTkLabel(self, text="Select Category:", font=f).pack(pady=5)
        self.selected_category = tk.StringVar(self)
        cats = sorted(filter(None, self.menu_model.get_menu().keys()))
        self.selected_category.set(cats[0] if cats else "No categories available")
        self.category_menu = ctk.CTkOptionMenu(self, values=cats, variable=self.selected_category)
        self.category_menu.pack(pady=5)
        ctk.CTkLabel(self, text="Item Name:", font=f).pack(pady=5)
        self.item_entry = ctk.CTkEntry(self, font=f)
        self.item_entry.pack(pady=5)
        ctk.CTkLabel(self, text="Price:", font=f).pack(pady=5)
        self.price_entry = ctk.CTkEntry(self, font=f)
        self.price_entry.pack(pady=5)
        ctk.CTkButton(self, text="Add Item", font=f,
                      command=self.add_item).pack(pady=10)

    def add_item(self):
        cat = self.selected_category.get()
        item = self.item_entry.get().strip()
        price = self.price_entry.get().strip()
        if cat == "No categories available":
            messagebox.showerror("Error", "Cannot add item, no categories exist.")
            return
        if not item or not price:
            messagebox.showerror("Error", "Please enter both item name and price.")
            return
        success = self.controller.add_menu_item(cat, item, price)
        if success:
            messagebox.showinfo("Success", f"Item '{item}' added to '{cat}'.")
            if getattr(self.controller, 'admin_panel_view', None):
                self.controller.admin_panel_view.refresh_display()
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to add item. It may already exist or price is invalid.")


# --- RemoveItemView ---
class RemoveItemView(ctk.CTkToplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Remove Item")
        self.geometry("300x300")
        self.resizable(False, False)
        self.controller = controller
        self.menu_model = controller.menu_model
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    def create_widgets(self):
        f = ("Helvetica",14)
        ctk.CTkLabel(self, text="Select Category:", font=f).pack(pady=5)
        self.selected_category = tk.StringVar(self)
        cats = sorted(filter(None, self.menu_model.get_menu().keys()))
        self.selected_category.set(cats[0] if cats else "No categories available")
        self.category_menu = ctk.CTkOptionMenu(
            self, values=cats, variable=self.selected_category,
            command=self.update_items
        )
        self.category_menu.pack(pady=5)

        ctk.CTkLabel(self, text="Select Item:", font=f).pack(pady=5)
        self.selected_item = tk.StringVar(self)
        items = sorted(filter(None, self.menu_model.get_menu().get(self.selected_category.get(), {}).keys()))
        self.selected_item.set(items[0] if items else "No items available")
        self.item_menu = ctk.CTkOptionMenu(self, values=items, variable=self.selected_item)
        self.item_menu.pack(pady=5)

        ctk.CTkButton(self, text="Remove Item", font=f,
                      command=self.remove_item).pack(pady=10)

    def update_items(self, new_cat):
        items = sorted(filter(None, self.menu_model.get_menu().get(new_cat, {}).keys()))
        self.selected_item.set(items[0] if items else "No items available")
        self.item_menu.configure(values=items)

    def remove_item(self):
        cat = self.selected_category.get()
        itm = self.selected_item.get()
        if cat == "No categories available":
            messagebox.showerror("Error", "Cannot remove item, no categories exist.")
            return
        if itm == "No items available" or not itm:
            messagebox.showerror("Error", "No item selected.")
            return
        if not messagebox.askyesno("Confirm Removal", f"Really remove '{itm}' from '{cat}'?"):
            return
        success = self.controller.remove_menu_item(cat, itm)
        if success:
            messagebox.showinfo("Success", f"Item '{itm}' removed.")
            if getattr(self.controller, 'admin_panel_view', None):
                self.controller.admin_panel_view.refresh_display()
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to remove item.")


# --- InvoiceFormatEditView ---
class InvoiceFormatEditView(ctk.CTkToplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Edit Invoice Format")
        self.geometry("500x400")
        self.resizable(False, False)
        self.controller = controller
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    def create_widgets(self):
        f = ("Helvetica",14)
        ctk.CTkLabel(self, text="Edit Invoice Template:", font=f).pack(pady=10)
        self.textbox = ctk.CTkTextbox(self, wrap="word", font=f)
        self.textbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        sb = ctk.CTkScrollbar(self, orientation="vertical", command=self.textbox.yview)
        sb.pack(side="right", fill="y", padx=0, pady=10)
        self.textbox.configure(yscrollcommand=sb.set)
        self.textbox.insert("0.0", self.controller.get_invoice_template())
        ctk.CTkButton(self, text="Save Template", font=f,
                      command=self.save_template).pack(pady=10)

    def save_template(self):
        new_tpl = self.textbox.get("0.0", "end").strip()
        if not new_tpl:
            messagebox.showerror("Error", "Template cannot be empty.")
            return
        self.controller.set_invoice_template(new_tpl)
        messagebox.showinfo("Success", "Invoice template updated.")
        self.destroy()
