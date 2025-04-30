# controller.py

import tkinter as tk
from tkinter import messagebox
import logging
import json
import os

# Import models and views
from model import MenuModel, OrderModel, UserModel
from view import (
    HomeView, OrderView, InvoiceView, LoginView,
    AdminPanelView, InvoiceFormatEditView, AddCategoryView,
    AddItemView, RemoveItemView, ProductEditView,
    MajorEditView, RemoveCategoryView
)

# Ensure logging is configured only once
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Controller:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self._load_config()

        # Models
        self.menu_model   = MenuModel(data_file="menu_data.json")
        self.user_model   = UserModel(data_file="user_data.json")
        self.order_model  = OrderModel()

        # View references
        self.main_view           = HomeView(self.open_order_view, self.open_login_view)
        self.order_view          = None
        self.login_view          = None
        self.admin_panel_view    = None
        self.major_edit_view     = None
        self.invoice_format_view = None
        self.add_category_view   = None
        self.add_item_view       = None
        self.remove_item_view    = None
        self.remove_category_view= None

        # Invoice template
        self.invoice_template = self.config.get(
            "invoice_template",
            "Invoice\n{items}\nTotal: GHS {total:.2f}\n"
        )

        logging.info("Application started. Home view created.")

    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    logging.info(f"Configuration loaded from {self.config_file}")
                    return data
            except Exception as e:
                logging.error(f"Error loading config: {e}")
                messagebox.showerror("Configuration Error", str(e))
        else:
            logging.warning(f"No config at {self.config_file}. Using defaults.")
        return {}

    def run(self):
        self.main_view.mainloop()

    def open_order_view(self):
        logging.info("Opening Order View.")
        self.main_view.withdraw()

        if self.order_view and self.order_view.winfo_exists():
            self.order_view.lift()
            return

        # Pass four args: menu, controller (self), on_generate_invoice, on_back
        self.order_view = OrderView(
            self.menu_model.get_menu(),
            self,                        # controller
            self.generate_invoice,       # on_generate_invoice
            self.on_order_view_close     # on_back
        )
        self.order_view.protocol("WM_DELETE_WINDOW", self.on_order_view_close)
        self.order_view.transient(self.main_view)
        self.order_view.grab_set()
        logging.info("Order View created.")

    def on_order_view_close(self):
        logging.info("Closing Order View.")
        if self.order_view and self.order_view.winfo_exists():
            self.order_view.destroy()
        self.order_view = None
        self.main_view.deiconify()

    def generate_invoice(self, order_details, order_view):
        logging.info("Generating invoice.")
        if not order_details:
            messagebox.showerror("Error", "No items to invoice.")
            return

        temp_model = OrderModel()
        for cat, item, qty, price in order_details:
            temp_model.add_item(cat, item, qty, price)

        total = temp_model.calculate_total()
        order_time = temp_model.get_order_time().strftime("%Y-%m-%d %H:%M:%S")

        items_str = ""
        for oi in temp_model.get_order():
            items_str += (
                f"{oi['item']} x {oi['quantity']} "
                f"@ GHS {oi['unit_price']:.2f} = GHS {oi['total_price']:.2f}\n"
            )

        try:
            invoice_str = self.invoice_template.format(
                order_time=order_time,
                items=items_str,
                total=total
            )
        except KeyError as e:
            logging.error(f"Template error: {e}")
            messagebox.showerror("Invoice Error", f"Missing key: {e}")
            invoice_str = f"{items_str}\nTotal: GHS {total:.2f}"

        inv_win = InvoiceView(invoice_str, on_back=lambda: order_view.deiconify())
        inv_win.protocol("WM_DELETE_WINDOW", lambda: order_view.deiconify())
        inv_win.transient(order_view)
        inv_win.grab_set()
        order_view.withdraw()

    def open_login_view(self):
        logging.info("Opening Login View.")
        self.main_view.withdraw()

        if self.login_view and self.login_view.winfo_exists():
            self.login_view.lift()
            return

        self.login_view = LoginView(self.process_login, self.on_login_view_close)
        self.login_view.protocol("WM_DELETE_WINDOW", self.on_login_view_close)
        self.login_view.transient(self.main_view)
        self.login_view.grab_set()

    def on_login_view_close(self):
        logging.info("Closing Login View.")
        if self.login_view and self.login_view.winfo_exists():
            self.login_view.destroy()
        self.login_view = None
        self.main_view.deiconify()

    def process_login(self, username, password):
        role = self.user_model.validate_user(username, password)
        if role == "admin":
            logging.info("Admin logged in.")
            if self.login_view:
                self.login_view.destroy()
                self.login_view = None
            self.open_admin_panel_view()
        else:
            logging.warning("Login failed.")
            messagebox.showerror("Login Failed", "Invalid credentials.")

    def open_admin_panel_view(self):
        logging.info("Opening Admin Panel View.")
        self.main_view.withdraw()

        if self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.lift()
            return

        self.admin_panel_view = AdminPanelView(
            self.menu_model, self, self.on_admin_panel_view_close
        )
        self.admin_panel_view.protocol(
            "WM_DELETE_WINDOW", self.on_admin_panel_view_close
        )
        self.admin_panel_view.transient(self.main_view)
        self.admin_panel_view.grab_set()

    def on_admin_panel_view_close(self):
        logging.info("Closing Admin Panel View.")
        for attr in [
            'major_edit_view', 'invoice_format_view', 'add_category_view',
            'add_item_view', 'remove_item_view', 'remove_category_view'
        ]:
            win = getattr(self, attr)
            if win and win.winfo_exists():
                win.destroy()
            setattr(self, attr, None)

        if self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.destroy()
        self.admin_panel_view = None
        self.main_view.deiconify()

    # --- Admin operations ---
    def update_menu_price(self, category, item, new_price):
        ok = self.menu_model.update_price(category, item, new_price)
        if ok and self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.refresh_display()
        return ok

    def add_menu_category(self, category):
        ok = self.menu_model.add_category(category)
        if ok and self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.refresh_display()
        return ok

    def add_menu_item(self, category, item, price):
        ok = self.menu_model.add_item(category, item, price)
        if ok and self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.refresh_display()
        return ok

    def remove_menu_item(self, category, item):
        ok = self.menu_model.remove_item(category, item)
        if ok and self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.refresh_display()
        return ok

    def remove_menu_category(self, category):
        ok = self.menu_model.remove_category(category)
        if ok and self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.refresh_display()
        return ok

    def update_product_details(self, category, old_name, new_name, new_price):
        ok = self.menu_model.update_product(
            category, old_name, new_name, new_price
        )
        if ok and self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.refresh_display()
        return ok

    def get_invoice_template(self):
        return self.invoice_template

    def set_invoice_template(self, new_template):
        self.invoice_template = new_template
        self.config["invoice_template"] = new_template
        self._save_config()

    def _save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logging.info(f"Config saved to {self.config_file}")
        except Exception as e:
            logging.error(f"Error saving config: {e}")
            messagebox.showerror("Configuration Error", str(e))

if __name__ == "__main__":
    Controller().run()
