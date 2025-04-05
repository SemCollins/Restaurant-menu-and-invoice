import tkinter as tk
from tkinter import messagebox
from model import MenuModel, OrderModel, UserModel
from view import HomeView, OrderView, InvoiceView, LoginView, AdminPanelView

class Controller:
    def __init__(self):
        # Instantiate the models.
        self.menu_model = MenuModel()
        self.user_model = UserModel()
        # Window references for managing multiple windows.
        self.order_view = None
        self.login_view = None
        self.admin_panel_view = None

        # Default invoice template.
        self.invoice_template = (
            "Invoice\nOrder Time: {order_time}\n" +
            "-" * 40 + "\n{items}" + "\n" +
            "-" * 40 + "\nTotal: GHS {total:.2f}\n"
        )
        
        # Create the main (home) view. We pass callback functions for actions.
        self.main_view = HomeView(self.open_order_view, self.open_login_view)
    
    def open_order_view(self):
        # Hide the home window.
        self.main_view.withdraw()
        if self.order_view is not None and self.order_view.winfo_exists():
            self.order_view.lift()
            return

        self.order_view = OrderView(self.menu_model.get_menu(), self.generate_invoice, self.on_order_view_close)
        self.order_view.protocol("WM_DELETE_WINDOW", self.on_order_view_close)
    
    def on_order_view_close(self):
        if self.order_view is not None:
            self.order_view.destroy()
            self.order_view = None
        self.main_view.deiconify()
    
    def generate_invoice(self, order_details, order_view):
        order_model = OrderModel()
        for category, item, quantity, price in order_details:
            order_model.add_item(category, item, quantity, price)
        total = order_model.calculate_total()
        order_time = order_model.get_order_time().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build the items string.
        items_str = ""
        for category, item, quantity, price in order_details:
            item_total = quantity * price
            items_str += f"{item} x {quantity} @ GHS {price:.2f} = GHS {item_total:.2f}\n"
        
        invoice_str = self.invoice_template.format(order_time=order_time, items=items_str, total=total)
        # Pass the formatted invoice string to InvoiceView.
        InvoiceView(invoice_str, on_back=lambda: order_view.deiconify())
    
    def open_login_view(self):
        self.main_view.withdraw()
        if self.login_view is not None and self.login_view.winfo_exists():
            self.login_view.lift()
            return
        self.login_view = LoginView(self.process_login, self.on_login_view_close)
        self.login_view.protocol("WM_DELETE_WINDOW", self.on_login_view_close)
    
    def on_login_view_close(self):
        if self.login_view is not None:
            self.login_view.destroy()
            self.login_view = None
        self.main_view.deiconify()
    
    def process_login(self, username, password):
        role = self.user_model.validate_user(username, password)
        if role == "admin":
            # Open the admin panel for an admin user.
            self.open_admin_panel_view()
            if self.login_view is not None:
                self.login_view.destroy()
                self.login_view = None
        else:
            messagebox.showerror("Login Failed", "Invalid credentials or insufficient privileges.")
    
    def open_admin_panel_view(self):
        self.main_view.withdraw()
        if self.admin_panel_view is not None and self.admin_panel_view.winfo_exists():
            self.admin_panel_view.lift()
            return
        # Pass both the MenuModel and the controller (self) so the admin panel can update data.
        self.admin_panel_view = AdminPanelView(self.menu_model, self, self.on_admin_panel_view_close)
        self.admin_panel_view.protocol("WM_DELETE_WINDOW", self.on_admin_panel_view_close)
    
    def on_admin_panel_view_close(self):
        if self.admin_panel_view is not None:
            self.admin_panel_view.destroy()
            self.admin_panel_view = None
        self.main_view.deiconify()
    
    def update_menu_price(self, category, item, new_price):
        success = self.menu_model.update_price(category, item, new_price)
        return success
    
    def run(self):
        self.main_view.mainloop()

if __name__ == "__main__":
    app = Controller()
    app.run()
