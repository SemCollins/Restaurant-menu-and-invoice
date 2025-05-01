# controller.py
import tkinter as tk
from tkinter import messagebox
from model import MenuModel, OrderModel, UserModel
from view import (
    HomeView, OrderView, InvoiceView, LoginView, AdminPanelView,
    InvoiceFormatEditView, AddCategoryView, AddItemView,
    RemoveItemView, ProductEditView, MajorEditView, RemoveCategoryView
)

class Controller:
    def __init__(self):
        # Instantiate the models.
        self.menu_model = MenuModel()
        self.user_model = UserModel()
        self.order_model = OrderModel()

        # Window references.
        self.main_view = HomeView(self.open_order_view, self.open_login_view)
        self.order_view = None
        self.login_view = None
        self.admin_panel_view = None
        self.major_edit_view = None
        self.invoice_format_view = None
        self.add_category_view = None
        self.add_item_view = None
        self.remove_item_view = None
        self.remove_category_view = None

        # Default invoice template.
        self.invoice_template = (
            "Invoice\nOrder Time: {order_time}\n" +
            "-" * 40 + "\n{items}" + "\n" +
            "-" * 40 + "\nTotal: GHS {total:.2f}\n"
        )

    def open_order_view(self):
        self.main_view.withdraw()
        if self.order_view and self.order_view.winfo_exists():
            self.order_view.lift()
            return
        self.order_view = OrderView(
            self.menu_model.get_menu(),
            self.generate_invoice,
            self.on_order_view_close
        )
        self.order_view.protocol("WM_DELETE_WINDOW", self.on_order_view_close)
        self.order_view.resizable(False, False)

    def on_order_view_close(self):
        if self.order_view:
            self.order_view.destroy()
            self.order_view = None
        self.main_view.deiconify()

    def generate_invoice(self, order_details, order_view):
        current_order = OrderModel()
        for cat, item, qty, price in order_details:
            current_order.add_item(cat, item, qty, price)
        total = current_order.calculate_total()
        order_time = current_order.get_order_time().strftime("%Y-%m-%d %H:%M:%S")

        items_str = ""
        for d in current_order.get_order():
            items_str += (
                f"{d['item']} x {d['quantity']} @ GHS {d['unit_price']:.2f} "
                f"= GHS {d['total_price']:.2f}\n"
            )

        invoice_str = self.invoice_template.format(
            order_time=order_time,
            items=items_str,
            total=total
        )
        invoice_window = InvoiceView(invoice_str, on_back=lambda: order_view.deiconify())
        invoice_window.resizable(False, False)

    def open_login_view(self):
        self.main_view.withdraw()
        if self.login_view and self.login_view.winfo_exists():
            self.login_view.lift()
            return
        self.login_view = LoginView(self.process_login, self.on_login_view_close)
        self.login_view.protocol("WM_DELETE_WINDOW", self.on_login_view_close)
        self.login_view.resizable(False, False)

    def on_login_view_close(self):
        if self.login_view:
            self.login_view.destroy()
            self.login_view = None
        self.main_view.deiconify()

    def process_login(self, username, password):
        role = self.user_model.validate_user(username, password)
        if role == "admin":
            self.open_admin_panel_view()
            if self.login_view:
                self.login_view.destroy()
                self.login_view = None
        else:
            messagebox.showerror("Login Failed", "Invalid credentials or insufficient privileges.")

    def open_admin_panel_view(self):
        self.main_view.withdraw()
        if self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.lift()
            return
        self.admin_panel_view = AdminPanelView(
            self.menu_model, self, self.on_admin_panel_view_close
        )
        self.admin_panel_view.protocol("WM_DELETE_WINDOW", self.on_admin_panel_view_close)
        self.admin_panel_view.resizable(False, False)

    def on_admin_panel_view_close(self):
        for win in (
            self.admin_panel_view, self.major_edit_view,
            self.invoice_format_view, self.add_category_view,
            self.add_item_view, self.remove_item_view,
            self.remove_category_view
        ):
            if win and win.winfo_exists():
                win.destroy()
        self.admin_panel_view = None
        self.major_edit_view = None
        self.invoice_format_view = None
        self.add_category_view = None
        self.add_item_view = None
        self.remove_item_view = None
        self.remove_category_view = None
        self.main_view.deiconify()

    # --- Model operations ---

    def update_menu_price(self, category, item, new_price):
        success = self.menu_model.update_price(category, item, new_price)
        if success and self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.refresh_display()
        return success

    def add_menu_category(self, category):
        success = self.menu_model.add_category(category)
        if success and self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.refresh_display()
        return success

    def add_menu_item(self, category, item, price):
        success = self.menu_model.add_item(category, item, price)
        if success and self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.refresh_display()
        return success

    def remove_menu_item(self, category, item):
        success = self.menu_model.remove_item(category, item)
        if success and self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.refresh_display()
        return success

    def remove_menu_category(self, category):
        success = self.menu_model.remove_category(category)
        if success and self.admin_panel_view and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.refresh_display()
        return success

    def update_product_details(self, category, old_item, new_item, new_price):
        return self.menu_model.update_product(category, old_item, new_item, new_price)

    def get_invoice_template(self):
        return self.invoice_template

    def set_invoice_template(self, new_template):
        self.invoice_template = new_template

    def run(self):
        self.main_view.mainloop()

if __name__ == "__main__":
    Controller().run()
