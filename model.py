# model.py
import datetime
import json
import os
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MenuModel:
    def __init__(self, data_file="menu_data.json"):
        self.data_file = data_file
        self.menu = self._load_data()

    def _load_data(self):
        """Loads menu data from a JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    menu_data = json.load(f)
                    logging.info(f"Menu data loaded from {self.data_file}")
                    return menu_data
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding menu data from {self.data_file}: {e}")
                # Fallback to empty menu if file is corrupted
                return {}
            except Exception as e:
                logging.error(f"An error occurred loading menu data: {e}")
                return {}
        else:
            logging.info(f"No menu data file found at {self.data_file}. Starting with an empty menu.")
            # Return an empty menu if the file doesn't exist
            return {}

    def _save_data(self):
        """Saves current menu data to a JSON file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.menu, f, indent=4)
            logging.info(f"Menu data saved to {self.data_file}")
            return True
        except Exception as e:
            logging.error(f"An error occurred saving menu data to {self.data_file}: {e}")
            return False

    def get_menu(self):
        """Returns the current menu dictionary."""
        return self.menu

    def update_price(self, category: str, item: str, new_price: float) -> bool:
        """Updates the price of an item and saves the menu."""
        if category in self.menu and item in self.menu[category]:
            try:
                self.menu[category][item] = float(new_price)
                self._save_data()
                logging.info(f"Updated price for '{item}' in '{category}' to {new_price}")
                return True
            except ValueError:
                logging.warning(f"Attempted to update price with invalid value: {new_price}")
                return False # Should be handled before calling model, but safe here
        logging.warning(f"Attempted to update price for non-existent item: '{item}' in '{category}'")
        return False

    def add_category(self, category: str) -> bool:
        """Adds a new category and saves the menu."""
        if not category or category.strip() == "":
            logging.warning("Attempted to add category with empty name.")
            return False
        category = category.strip()
        if category in self.menu:
            logging.warning(f"Attempted to add duplicate category: '{category}'")
            return False
        self.menu[category] = {}
        self._save_data()
        logging.info(f"Added new category: '{category}'")
        return True

    def add_item(self, category: str, item: str, price: float) -> bool:
        """Adds a new item to a category and saves the menu."""
        if not category or category not in self.menu:
            logging.warning(f"Attempted to add item to non-existent category: '{category}'")
            return False
        if not item or item.strip() == "":
             logging.warning(f"Attempted to add item with empty name to category: '{category}'")
             return False
        item = item.strip()
        if item in self.menu[category]:
            logging.warning(f"Attempted to add duplicate item: '{item}' in '{category}'")
            return False
        try:
            price = float(price)
        except ValueError:
            logging.warning(f"Attempted to add item with invalid price: {price}")
            return False
        self.menu[category][item] = price
        self._save_data()
        logging.info(f"Added item '{item}' with price {price} to category '{category}'")
        return True

    def remove_item(self, category: str, item: str) -> bool:
        """Removes an item from a category and saves the menu."""
        if category in self.menu and item in self.menu[category]:
            del self.menu[category][item]
            self._save_data()
            logging.info(f"Removed item '{item}' from category '{category}'")
            return True
        logging.warning(f"Attempted to remove non-existent item: '{item}' in '{category}'")
        return False

    def remove_category(self, category: str) -> bool:
        """Removes a category and all its items and saves the menu."""
        if not category or category.strip() == "":
             logging.warning("Attempted to remove category with empty name.")
             return False
        category = category.strip()
        if category in self.menu:
            del self.menu[category]
            self._save_data()
            logging.info(f"Removed category: '{category}'")
            return True
        logging.warning(f"Attempted to remove non-existent category: '{category}'")
        return False

    def update_product(self, category: str, old_item_name: str, new_item_name: str, new_price: float) -> bool:
        """Updates item name and/or price and saves the menu."""
        if category not in self.menu or old_item_name not in self.menu[category]:
             logging.warning(f"Attempted to update non-existent product: '{old_item_name}' in '{category}'")
             return False

        new_item_name = new_item_name.strip()
        if not new_item_name:
             logging.warning("Attempted to update product with empty new name.")
             return False

        try:
            new_price = float(new_price)
        except ValueError:
             logging.warning(f"Attempted to update product '{old_item_name}' with invalid new price: {new_price}")
             return False

        # Check if the new name is a duplicate, unless it's the same as the old name
        if old_item_name != new_item_name and new_item_name in self.menu[category]:
             logging.warning(f"Attempted to rename product '{old_item_name}' to an existing name: '{new_item_name}'")
             return False

        # If the name is changing, add with new name, delete old
        if old_item_name != new_item_name:
            self.menu[category][new_item_name] = new_price
            del self.menu[category][old_item_name]
            logging.info(f"Renamed product from '{old_item_name}' to '{new_item_name}' in '{category}' and set price to {new_price}")
        else: # Only price is changing
            self.menu[category][old_item_name] = new_price
            logging.info(f"Updated price for '{old_item_name}' in '{category}' to {new_price}")

        self._save_data()
        return True


class OrderModel:
    def __init__(self):
        # order_items now stores dicts { "category": ..., "item": ..., "quantity": ..., "unit_price": ..., "total_price": ... }
        self.order_items = []
        self.order_time = datetime.datetime.now()

    def add_item(self, category: str, item: str, quantity: int, unit_price: float):
        """Adds an item to the current order or updates its quantity."""
        if quantity <= 0:
            logging.warning(f"Attempted to add item '{item}' with non-positive quantity: {quantity}")
            return

        # Check if item already exists in order_items, if so, update quantity
        for order_item in self.order_items:
            if order_item["category"] == category and order_item["item"] == item:
                order_item["quantity"] += quantity
                order_item["total_price"] = round(order_item["quantity"] * order_item["unit_price"], 2) # Use round for currency
                logging.info(f"Updated quantity for '{item}' in order to {order_item['quantity']}")
                return
        # If item is not found, add it
        self.order_items.append({
            "category": category,
            "item": item,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": round(quantity * unit_price, 2) # Use round for currency
        })
        logging.info(f"Added new item to order: '{item}' (x{quantity}) @ GHS {unit_price:.2f}")

    def get_order(self):
        """Returns the list of items in the current order."""
        return self.order_items

    def get_order_time(self):
        """Returns the timestamp when the order was initiated."""
        return self.order_time

    def calculate_total(self) -> float:
        """Calculates the total price of the current order."""
        total = sum(item["total_price"] for item in self.order_items)
        return round(total, 2) # Ensure total is rounded for currency

class UserModel:
    def __init__(self, data_file="user_data.json"):
        self.data_file = data_file
        self.users = self._load_data()

    def _load_data(self):
        """Loads user data from a JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    user_data = json.load(f)
                    logging.info(f"User data loaded from {self.data_file}")
                    return user_data
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding user data from {self.data_file}: {e}")
                 # Fallback to a default admin user if file is corrupted
                return {"admin": {"password": "admin123", "role": "admin"}}
            except Exception as e:
                 logging.error(f"An error occurred loading user data: {e}")
                 return {"admin": {"password": "admin123", "role": "admin"}} # Fallback
        else:
            logging.info(f"No user data file found at {self.data_file}. Starting with default admin user.")
            # Return a default admin user if the file doesn't exist
            return {"admin": {"password": "admin123", "role": "admin"}}

    
    def validate_user(self, username: str, password: str) -> str | None:
        """Validates username and password and returns the user's role or None."""
        user = self.users.get(username)
        if user and user["password"] == password:
            logging.info(f"User '{username}' logged in successfully with role '{user['role']}'")
            return user["role"]
        logging.warning(f"Failed login attempt for username: '{username}'")
        return None