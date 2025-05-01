# model.py
import datetime

class MenuModel:
    def __init__(self):
        self.menu = {
            "Appetizers": {
                "Spring Rolls (Small)": 25,
                "Spring Rolls (Medium)": 38,
                "Spring Rolls (Large)": 53,
                "Samosas (3 pieces)": 20,
                "Kelete (Plantain Chips)": 15,
                "Chicken Wings (6 pieces)": 38,
                "Pepper Soup (small)": 33,
                "Asanka Local Salad": 28,
            },
            "Main Courses": {
                "Banku & Tilapia": 50,
                "Tilapia": 30,
                "Banku": 20,
                "Fufu & Groundnut Soup": 65,
                "Fufu & Light Soup": 60,
                "Jollof Rice with Fish": 58,
                "Jollof Rice with Chicken": 55,
                "Fried Rice with Chicken": 53,
                "Waakye": 40,
                "Kenkey & Fried Fish and Pepper Sauce": 45,
                "Pounded Fufu & Goat Light Soup": 75,
                "Pizza (Small)": 65,
                "Pizza (Medium)": 100,
                "Pizza (Large)": 150,
                "Burger (Single)": 50,
                "Burger (Double)": 70,
                "Spaghetti": 40,
            },
            "Desserts": {
                "Fruit Salad": 28,
                "Ice Cream (scoop)": 20,
                "Cake Slice": 28,
                "Waffles": 40,
                "Assorted jollof": 50,
            },
            "Drinks": {
                "Soft Drinks (Coca-Cola, Fanta, Sprite)": 20,
                "Juices (Mango, Pineapple, Orange)": 28,
                "Water (Bottled)": 13,
                "Beer (Local)": 25,
                "Beer (Imported)": 40,
                "Local Gin (small)": 20,
                "Local Gin (large)": 40,
                "Palm wine (small)": 15,
                "Palm wine (large)": 25,
            },
            "Other": {
                "Tissues (per pack)": 8,
                "Takeaway Containers": 8,
            },
        }

    def get_menu(self):
        return self.menu

    def update_price(self, category, item, new_price):
        if category in self.menu and item in self.menu[category]:
            try:
                self.menu[category][item] = float(new_price)
                return True
            except ValueError:
                return False
        return False

    def add_category(self, category):
        if not category or category in self.menu:
            return False
        self.menu[category] = {}
        return True

    def add_item(self, category, item, price):
        if not category or category not in self.menu:
            return False
        if not item or item in self.menu[category]:
            return False
        try:
            self.menu[category][item] = float(price)
            return True
        except ValueError:
            return False

    def remove_item(self, category, item):
        if category in self.menu and item in self.menu[category]:
            del self.menu[category][item]
            return True
        return False

    def remove_category(self, category):
        if not category or category not in self.menu:
            return False
        del self.menu[category]
        return True

    def update_product(self, category, old_name, new_name, new_price):
        if category in self.menu and old_name in self.menu[category]:
            try:
                price = float(new_price)
                if old_name != new_name:
                    if new_name in self.menu[category]:
                        return False
                    self.menu[category][new_name] = price
                    del self.menu[category][old_name]
                else:
                    self.menu[category][old_name] = price
                return True
            except ValueError:
                return False
        return False

class OrderModel:
    def __init__(self):
        self.order_items = []
        self.order_time = datetime.datetime.now()

    def add_item(self, category, item, quantity, unit_price):
        if quantity <= 0:
            return
        for oi in self.order_items:
            if oi["category"] == category and oi["item"] == item:
                oi["quantity"] += quantity
                oi["total_price"] = oi["quantity"] * oi["unit_price"]
                return
        self.order_items.append({
            "category": category,
            "item": item,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": quantity * unit_price
        })

    def get_order(self):
        return self.order_items

    def get_order_time(self):
        return self.order_time

    def calculate_total(self):
        return sum(i["total_price"] for i in self.order_items)

class UserModel:
    def __init__(self):
        self.users = {
            "admin": {"password": "admin123", "role": "admin"},
            "cashier": {"password": "cashier123", "role": "cashier"}
        }

    def validate_user(self, username, password):
        u = self.users.get(username)
        if u and u["password"] == password:
            return u["role"]
        return None
