# view.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import logging # Import logging

# No longer need threading for animation
# import threading


# --- HomeView ---
class HomeView(ctk.CTk):
    """The main application window with options to order or login."""
    def __init__(self, on_order, on_admin_login):
        super().__init__()
        self.title("Welcome to Coded Restaurant")
        self.geometry("400x300")
        self.resizable(False, False) # Explicitly make window non-resizable
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        try:
            # Adjusted image size to match window size
            bg_image = Image.open("Images/bg.png").resize((400,300), Image.Resampling.LANCZOS)
            bg_ctk = ctk.CTkImage(light_image=bg_image, dark_image=bg_image, size=(400,300))
            bg_label = ctk.CTkLabel(self, image=bg_ctk, text="")
            bg_label.image = bg_ctk # Keep a reference
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        except FileNotFoundError:
            logging.warning("HomeView background image not found at Images/bg.png. Using default background.")
            # Fallback if image fails
            self.configure(fg_color="gray20")
        except Exception as e:
            logging.error(f"HomeView background image error: {e}")
            # Fallback if image fails
            self.configure(fg_color="gray20")


        welcome_label = ctk.CTkLabel(self, text="Welcome to Coded Restaurant", font=("Helvetica Bold-Oblique", 22))
        welcome_label.pack(pady=20)

        order_button = ctk.CTkButton(self, text="Place Order", font=("Helvetica", 16),
                                      command=on_order, fg_color="#2980b9", hover_color="#3498db")
        order_button.pack(pady=10)

        admin_button = ctk.CTkButton(self, text="Admin Login", font=("Helvetica", 16),
                                      command=on_admin_login, fg_color="#2980b9", hover_color="#3498db")
        admin_button.pack(pady=10)

# --- OrderView ---
class OrderView(ctk.CTkToplevel):
    """Window for placing customer orders, with categories and item selection."""
    def __init__(self, menu, on_generate_invoice, on_back):
        super().__init__()
        self.title("Place Order")
        self.geometry("800x600")
        self.resizable(False, False) # Explicitly make window non-resizable

        self.menu = menu
        self.on_generate_invoice = on_generate_invoice
        self.on_back = on_back
        self.order_summary = {}

        # Dictionary to store canvas references for each tab to manage scrolling
        self.canvases = {}

        # Bind mousewheel events to the toplevel OrderView window
        # This attempts to capture events if they are not caught by widgets inside.
        # The _on_toplevel_mousewheel method will direct scrolling to the active tab's canvas.
        self.bind("<MouseWheel>", self._on_toplevel_mousewheel) # Windows/macOS
        self.bind("<Button-4>", self._on_toplevel_mousewheel) # Linux scroll up
        self.bind("<Button-5>", self._on_toplevel_mousewheel) # Linux scroll down
        # Add binding for middle mouse button drag as an alternative scrolling method
        self.bind("<B2-Motion>", self._on_toplevel_mousewheel) # Pass event to handler


        # Load plus/minus icons
        try:
            plus_raw = Image.open("Images/plus_icon.png")
            self.plus_img = ctk.CTkImage(light_image=plus_raw, dark_image=plus_raw, size=(30,30))
        except FileNotFoundError:
            logging.warning("plus_icon.png not found at Images/plus_icon.png.")
            self.plus_img = None
        except Exception as e:
            logging.error(f"Error loading plus_icon.png: {e}")
            self.plus_img = None

        try:
            minus_raw = Image.open("Images/minus_icon.png")
            self.minus_img = ctk.CTkImage(light_image=minus_raw, dark_image=minus_raw, size=(30,30))
        except FileNotFoundError:
            logging.warning("minus_icon.png not found at Images/minus_icon.png.")
            self.minus_img = None
        except Exception as e:
            logging.error(f"Error loading minus_icon.png: {e}")
            self.minus_img = None

        # Background images used per tab with the canvas approach
        self.bg_images = {
            "Main Courses": "Images/atseke.png",
            "Drinks": "Images/grand_combi.png",
            "Appetizers": "Images/grand_shrimp.png",
            "Desserts": "Images/jollof_chicken.png",
            "Other": "Images/bg.png" # Use a default if not found
        }


        # Overall grid config
        self.grid_rowconfigure(0, weight=0) # Summary frame row
        self.grid_rowconfigure(1, weight=1) # Tabview row
        self.grid_rowconfigure(2, weight=0) # Button frame row
        self.grid_columnconfigure(0, weight=1)

        # --- Summary Frame ---
        self.summary_frame = ctk.CTkFrame(self, fg_color="gray20") # Frame to hold textbox and scrollbar
        self.summary_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.summary_frame.grid_columnconfigure(0, weight=1) # Allow textbox to expand
        self.summary_frame.grid_rowconfigure(0, weight=1) # Allow textbox to expand


        self.summary_textbox = ctk.CTkTextbox(
            self.summary_frame, # Place textbox inside the frame
            wrap="word",
            font=("Helvetica", 14),
            height=100, # Give it a fixed height in the non-resizable window
            state="normal" # Set to normal to insert text
        )
        self.summary_textbox.grid(row=0, column=0, sticky="nsew")

        summary_scrollbar = ctk.CTkScrollbar(
            self.summary_frame, # Place scrollbar inside the frame
            orientation="vertical",
            command=self.summary_textbox.yview
        )
        summary_scrollbar.grid(row=0, column=1, sticky="ns")
        self.summary_textbox.configure(yscrollcommand=summary_scrollbar.set)
        self.summary_textbox.configure(state="disabled") # Set state back after initial setup


        self.create_widgets() # Call create_widgets here to build the UI


    # Define _on_mousewheel as a class method to handle scrolling for a specific canvas
    def _on_mousewheel(self, event: tk.Event, canvas_widget: tk.Canvas):
        """Handles mousewheel events and scrolls the target canvas."""
        # Use event.delta for Windows/macOS, event.num for Linux scroll buttons, event.ydata for B2-Motion
        if event.delta: # Windows/macOS
            scroll_units = -int(event.delta/120) # Standard conversion
        elif event.num == 4: # Linux scroll up
             scroll_units = -1
        elif event.num == 5: # Linux scroll down
             scroll_units = 1
        elif event.ydata is not None: # Middle mouse button drag
             # Calculate vertical delta based on ydata and initial position
             # This might need fine-tuning for sensitivity
             # Note: yview_scroll expects discrete units, converting motion to units is tricky
             # A simpler approach for B2-Motion is to use event.y (relative y pos)
             # Or just rely on the wheel/buttons primarily. Sticking to unit scrolling.
             # A better B2-Motion handler would calculate pixel delta and convert.
             # For now, rely on standard wheel/button events mainly.
             return # Skip B2-Motion for unit scrolling consistency

        else:
            scroll_units = 0

        if scroll_units != 0:
            canvas_widget.yview_scroll(scroll_units, "units")


    # Define _on_toplevel_mousewheel as a class method to direct toplevel events
    def _on_toplevel_mousewheel(self, event: tk.Event):
        """Handles mousewheel events captured by the toplevel OrderView window."""
        # Determine the currently selected tab
        current_tab_name = self.tabview.get()
        if current_tab_name in self.canvases:
            # Get the canvas for the current tab
            current_canvas = self.canvases[current_tab_name]

            # Call the shared mousewheel handling logic
            self._on_mousewheel(event, current_canvas)


    def create_widgets(self):
        """Creates and lays out the widgets for the Order View."""
        # Ensure canvases dictionary is clean on refresh (if refreshing were used here)
        self.canvases = {}

        # --- Tabview of Menu ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        label_font = ("Helvetica", 14)
        button_font = ("Helvetica", 14)

        # Iterate through sorted menu categories for consistent tab order
        for category in sorted(filter(None, self.menu.keys())):
            # Skip adding a tab if the category name is empty (redundant due to filter but safe)
            if not category:
                continue

            self.tabview.add(category)

            # --- Using tk.Canvas with background image ---
            tab_frame_container = ctk.CTkFrame(self.tabview.tab(category), fg_color="transparent")
            tab_frame_container.pack(fill="both", expand=True)

            canvas = tk.Canvas(tab_frame_container, bd=0, highlightthickness=0)
            canvas.pack(side="left", fill="both", expand=True)
            self.canvases[category] = canvas # Store canvas reference

            v_scroll = tk.Scrollbar(tab_frame_container, orient="vertical", command=canvas.yview)
            v_scroll.pack(side="right", fill="y")
            canvas.configure(yscrollcommand=v_scroll.set)

            # Load and place background image on canvas
            bg_photo = None
            try:
                bg_path = self.bg_images.get(category, "Images/bg.png")
                # Resize image to fit canvas area, considering scrollbar width
                # Need to update idletasks before getting accurate canvas width
                self.update_idletasks()
                canvas_width = canvas.winfo_width()
                 # Fallback if width is not yet determined accurately
                if canvas_width <= 1:
                    container_width = self.winfo_width() - 20 # Estimate container width
                    scrollbar_width = v_scroll.winfo_reqwidth()
                    canvas_width = max(1, container_width - scrollbar_width)


                bg_img = Image.open(bg_path).resize((canvas_width, 400), Image.Resampling.LANCZOS) # Resize image
                bg_photo = ImageTk.PhotoImage(bg_img)
                canvas.bg_photo = bg_photo # Keep a reference
                canvas.create_image(0, 0, image=bg_photo, anchor="nw")
            except FileNotFoundError:
                logging.warning(f"Canvas background image not found for category '{category}' at {self.bg_images.get(category, 'Images/bg.png')}. Using fallback background.")
                canvas.configure(bg=tab_frame_container.cget("fg_color")[0]) # Set fallback background color
            except Exception as e:
                logging.error(f"Error loading canvas background for {category}: {e}")
                canvas.configure(bg=tab_frame_container.cget("fg_color")[0]) # Set fallback background color


            inner_frame = ctk.CTkFrame(canvas, fg_color=("white", "gray10"), corner_radius=15) # Use ctk frame for inner content
            canvas.create_window((0,0), window=inner_frame, anchor="nw")

            # Configure scroll region when inner_frame size changes
            # Use update_idletasks to ensure bbox is accurate after widget placement
            inner_frame.bind("<Configure>", lambda event, c=canvas: c.configure(scrollregion=c.bbox("all")))


            # Apply mousewheel bindings directly to widgets within the loop
            # Ensure the callback correctly targets the canvas widget
            canvas.bind("<Enter>", lambda e: canvas.focus_set()) # Focus canvas on entry
            canvas.bind("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas)) # Windows/macOS
            canvas.bind("<Button-4>", lambda e: self._on_mousewheel(e, canvas)) # Linux scroll up
            canvas.bind("<Button-5>", lambda e: self._on_mousewheel(e, canvas)) # Linux scroll down
            # Add binding for middle mouse button drag as an alternative scrolling method
            # NOTE: B2-Motion scrolling on canvas can be less smooth than native scrollable frames.
            # The _on_mousewheel logic currently treats this like unit scrolling, may need refinement.
            canvas.bind("<B2-Motion>", lambda e: self._on_mousewheel(e, canvas)) # Pass event to handler


            # Add bindings to inner frame and container to capture events over them
            inner_frame.bind("<Enter>", lambda e: canvas.focus_set()) # Also focus canvas when over inner_frame
            inner_frame.bind("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas)) # Windows/macOS
            inner_frame.bind("<Button-4>", lambda e: self._on_mousewheel(e, canvas)) # Linux scroll up
            inner_frame.bind("<Button-5>", lambda e: self._on_mousewheel(e, canvas)) # Linux scroll down
             # Add binding for middle mouse button drag as an alternative scrolling method
            inner_frame.bind("<B2-Motion>", lambda e: self._on_mousewheel(e, canvas)) # Pass event to handler


            tab_frame_container.bind("<Enter>", lambda e: canvas.focus_set()) # Still focus the canvas
            tab_frame_container.bind("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas)) # Windows/macOS
            tab_frame_container.bind("<Button-4>", lambda e: self._on_mousewheel(e, canvas)) # Linux scroll up
            tab_frame_container.bind("<Button-5>", lambda e: self._on_mousewheel(e, canvas)) # Linux scroll down
             # Add binding for middle mouse button drag as an alternative scrolling method
            tab_frame_container.bind("<B2-Motion>", lambda e: self._on_mousewheel(e, canvas)) # Pass event to handler


            # Menu Item Widgets placed directly inside the inner_frame using grid
            row = 0
            # Ensure items are sorted for consistent display
            for item, price in sorted(self.menu.get(category, {}).items()):
                ctk.CTkLabel(inner_frame, text=item, font=label_font)\
                    .grid(row=row, column=0, sticky="w", padx=5, pady=5)
                ctk.CTkLabel(inner_frame, text=f"GHS {price:.2f}", font=label_font)\
                    .grid(row=row, column=1, padx=5, pady=5)
                plus_btn = (
                    ctk.CTkButton(inner_frame, image=self.plus_img, text="",
                                  width=30, command=lambda c=category, i=item: self.add_item(c, i),
                                  fg_color="transparent", hover_color="gray30") # Use transparent/hover color for icon buttons
                    if self.plus_img else
                    ctk.CTkButton(inner_frame, text="+", width=30,
                                  command=lambda c=category, i=item: self.add_item(c, i),
                                  fg_color="#28a745", hover_color="#218838") # Example colors for text buttons
                )
                plus_btn.grid(row=row, column=2, padx=5, pady=5)
                minus_btn = (
                    ctk.CTkButton(inner_frame, image=self.minus_img, text="",
                                  width=30, command=lambda c=category, i=item: self.remove_item(c, i),
                                   fg_color="transparent", hover_color="gray30") # Use transparent/hover color for icon buttons
                    if self.minus_img else
                    ctk.CTkButton(inner_frame, text="–", width=30,
                                  command=lambda c=category, i=item: self.remove_item(c, i),
                                  fg_color="#dc3545", hover_color="#c82333") # Example colors for text buttons
                )
                minus_btn.grid(row=row, column=3, padx=5, pady=5)
                row += 1

            # Ensure the scrollregion is updated after all items are placed
            self.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))


        # --- Bottom Buttons ---
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        # Configure columns to expand proportionally
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)


        ctk.CTkButton(
            self.button_frame, text="Generate Invoice",
            font=("Helvetica", 16), command=self.generate_invoice,
             fg_color="#007bff", hover_color="#0056b3" # Example colors
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew") # Add sticky="ew"

        ctk.CTkButton(
            self.button_frame, text="Clear Orders",
            font=("Helvetica", 16), command=self.clear_orders,
            fg_color="#ffc107", hover_color="#e0a800" # Example colors
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew") # Add sticky="ew"

        ctk.CTkButton(
            self.button_frame, text="Back",
            font=("Helvetica", 16), command=self.back,
            fg_color="#6c757d", hover_color="#5a6268" # Example colors
        ).grid(row=0, column=2, padx=5, pady=5, sticky="ew") # Add sticky="ew"


    # Removed animation method
    # def _animate_summary_frame(self, step):
    #     """Subtle color animation for the summary frame."""
    #     # Colors can be adjusted for a more 'restaurant/food' feel
    #     colors = [("gray20", "gray20"), ("#34495e", "#34495e")] # Darker gray to dark blue/gray
    #     # You can add more colors or use a gradient effect if desired

    #     current_color = colors[step % len(colors)]
    #     self.summary_frame.configure(fg_color=current_color)

    #     # Ensure the animation stops if the window is destroyed
    #     if self.winfo_exists():
    #          self.after(1500, lambda: self._animate_summary_frame(step + 1)) # Longer interval


    def add_item(self, category: str, item: str):
        """Adds an item to the current order summary."""
        key = (category, item)
        self.order_summary[key] = self.order_summary.get(key, 0) + 1
        self.update_summary_display()
        logging.info(f"Added '{item}' to order summary (now x{self.order_summary[key]})")

    def remove_item(self, category: str, item: str):
        """Removes an item from the current order summary."""
        key = (category, item)
        if key in self.order_summary:
            if self.order_summary[key] > 1:
                self.order_summary[key] -= 1
                logging.info(f"Decremented quantity for '{item}' in order summary (now x{self.order_summary[key]})")
            else:
                del self.order_summary[key]
                logging.info(f"Removed '{item}' from order summary.")
            self.update_summary_display()
        else:
             logging.warning(f"Attempted to remove non-existent item from order summary: '{item}'")


    def clear_orders(self):
        """Clears all items from the current order summary."""
        confirm = messagebox.askyesno("Clear Order", "Are you sure you want to clear all items from the order?")
        if confirm:
            self.order_summary.clear()
            self.update_summary_display()
            logging.info("Cleared all items from order summary.")
        else:
            logging.info("Clear order cancelled by user.")


    def update_summary_display(self):
        """Updates the text in the summary textbox."""
        self.summary_textbox.configure(state="normal")
        self.summary_textbox.delete("1.0", "end")
        if not self.order_summary:
             self.summary_textbox.insert("end", "Your order is empty.")
        else:
            # Sort items in the summary display
            for (cat, item), qty in sorted(self.order_summary.items()):
                # Get price from menu, handling potential removal from admin panel
                price = self.menu.get(cat, {}).get(item)
                if price is not None:
                    item_total = round(qty * price, 2) # Use round for currency
                    self.summary_textbox.insert("end", f"{item} (x{qty}) @ GHS {price:.2f} = GHS {item_total:.2f}\n")
                else:
                     # Handle case where item might have been deleted from the menu
                     self.summary_textbox.insert("end", f"{item} (x{qty}) - Item no longer available\n")


        self.summary_textbox.configure(state="disabled")

    def generate_invoice(self):
        """Triggers invoice generation via the controller."""
        if not self.order_summary:
            messagebox.showerror("Error", "No items selected.")
            logging.warning("Attempted to generate invoice with no items selected.")
            return
        # Filter out items that might have been deleted from the menu before sending to controller
        valid_order_details = []
        for (category, item), qty in self.order_summary.items():
            if category in self.menu and item in self.menu[category]:
                 valid_order_details.append((category, item, qty, self.menu[category][item]))
            # else:
                 # logging.warning(f"Item '{item}' in category '{category}' not found in menu, skipping for invoice.")
                 # Removed print statement for cleaner console output


        if not valid_order_details:
             messagebox.showerror("Error", "Selected items are no longer available in the menu.")
             logging.warning("Selected items for invoice no longer found in menu.")
             return

        # Delegate to the controller to generate and show the invoice
        logging.info("Calling controller to generate invoice.")
        self.on_generate_invoice(valid_order_details, self) # Pass self so controller can deiconify this window later


    def back(self):
        """Closes the Order View and returns to the previous view."""
        logging.info("Closing Order View.")
        self.destroy()
        self.on_back()

# --- InvoiceView ---
class InvoiceView(ctk.CTkToplevel):
    """Window displaying the generated invoice."""
    def __init__(self, invoice_text: str, on_back):
        super().__init__()
        self.title("Invoice")
        self.geometry("400x500")
        self.resizable(False, False) # Explicitly make window non-resizable
        self.on_back = on_back
        self.create_widgets(invoice_text)
        # protocol is set by the controller now for modal behavior
        # self.protocol("WM_DELETE_WINDOW", self.on_back)

    def create_widgets(self, invoice_text: str):
        """Creates and lays out the widgets for the Invoice View."""
        label_font = ("Helvetica", 14)
        button_font = ("Helvetica", 16) # Button font slightly larger


        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Place background image (This InvoiceView keeps its background image)
        try:
            bg_img = Image.open("Images/grand_crab.png").resize((400,500), Image.Resampling.LANCZOS) # Use Resampling.LANCZOS
            bg_ctk = ctk.CTkImage(light_image=bg_img, dark_image=bg_img, size=(400,500))
            bg_label = ctk.CTkLabel(container, image=bg_ctk, text="")
            bg_label.image = bg_ctk # Keep a reference
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
            bg_label.lower() # Ensure background is behind other widgets
        except FileNotFoundError:
             logging.warning("Invoice background image not found at Images/grand_crab.png. Using default background.")
             # Fallback if image fails
             container.configure(fg_color="gray15") # Dark background
        except Exception as e:
            logging.error(f"Invoice background image error: {e}")
             # Fallback if image fails
            container.configure(fg_color="gray15") # Dark background


        self.textbox = ctk.CTkTextbox(container, wrap="word", font=("Helvetica", 14), state="normal") # Set state to normal initially to insert text
        self.textbox.pack(side="left", fill="both", expand=True) # Pack textbox on the left

        scrollbar = ctk.CTkScrollbar(container, orientation="vertical", command=self.textbox.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 0), pady=0) # Pack scrollbar on the right, adjust padding
        self.textbox.configure(yscrollcommand=scrollbar.set)

        self.textbox.insert("0.0", invoice_text)
        self.textbox.configure(state="disabled") # Set state back after inserting

        # Added explicit padding and sticky to back button
        back_button = ctk.CTkButton(self, text="Back", font=button_font, command=self.back,
                                    fg_color="#6c757d", hover_color="#5a6268") # Example colors
        back_button.pack(pady=(10, 10), padx=10, fill="x") # Added padx, fill="x"


    def back(self):
        """Closes the Invoice View and returns to the previous view (OrderView)."""
        logging.info("Closing Invoice View.")
        self.destroy()
        self.on_back()

# --- LoginView ---
class LoginView(ctk.CTkToplevel):
    """Window for admin user login."""
    def __init__(self, on_login, on_back):
        super().__init__()
        self.title("Admin Login")
        self.geometry("300x250")
        self.resizable(False, False) # Explicitly make window non-resizable
        self.on_login = on_login
        self.on_back = on_back
        self.create_widgets()
        # protocol is set by the controller now for modal behavior
        # self.protocol("WM_DELETE_WINDOW", self.back)
        self.focus_force()

    def create_widgets(self):
        """Creates and lays out the widgets for the Login View."""
        label_font = ("Helvetica", 14)
        entry_font = ("Helvetica", 14)
        button_font = ("Helvetica", 14)


        ctk.CTkLabel(self, text="Username:", font=label_font).pack(pady=(10,0)) # Added top padding
        self.username_entry = ctk.CTkEntry(self, font=entry_font, width=200) # Added width
        self.username_entry.pack(pady=(0,10), padx=20) # Added padding

        ctk.CTkLabel(self, text="Password:", font=label_font).pack(pady=(0,0)) # Added top padding
        self.password_entry = ctk.CTkEntry(self, show="*", font=entry_font, width=200) # Added width
        self.password_entry.pack(pady=(0,10), padx=20) # Added padding

        login_button = ctk.CTkButton(
            self, text="Login", font=button_font, width=150, # Added width
            command=self._perform_login,
             fg_color="#007bff", hover_color="#0056b3" # Example colors
        )
        login_button.pack(pady=10)

        back_button = ctk.CTkButton(self, text="Back", font=button_font, width=150, # Added width
                                    command=self.back,
                                    fg_color="#6c757d", hover_color="#5a6268") # Example colors
        back_button.pack(pady=(0, 10)) # Added bottom padding


    def _perform_login(self):
        """Helper method to get values and call the login function."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        # print("Login pressed") # Keep print for debugging if needed
        self.on_login(username, password)


    def back(self):
        """Closes the Login View and returns to the Home View."""
        logging.info("Closing Login View.")
        self.destroy()
        self.on_back()

# --- AdminPanelView and Related Edit Views ---
class AdminPanelView(ctk.CTkToplevel):
    """Window for managing menu items and prices."""
    def __init__(self, menu_model, controller, on_back):
        super().__init__()
        self.title("Admin Panel - Manage Menu") # Updated title
        self.geometry("800x600")
        self.resizable(False, False) # Explicitly make window non-resizable
        self.menu_model = menu_model
        self.controller = controller
        self.on_back = on_back
        self.entries = {} # Dictionary to hold price entry widgets
        # Removed tab_frames dictionary as we don't need explicit references for this refactor
        # self.tab_frames = {}
        self.create_widgets()
        # protocol is set by the controller now for modal behavior
        # self.protocol("WM_DELETE_WINDOW", self.back)
        self.focus_force()

    def create_widgets(self):
        """Creates and lays out the widgets for the Admin Panel View."""
        # Clear existing widgets if refreshing
        for widget in self.winfo_children():
            widget.destroy()

        self.entries = {} # Reset entries dictionary
        # Removed tab_frames dictionary reset
        # self.tab_frames = {}

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        label_font = ("Helvetica", 14)
        entry_font = ("Helvetica", 14)
        button_font = ("Helvetica", 14)


        menu_data = self.menu_model.get_menu()
        # Iterate through sorted category keys, filtering out any potential empty strings
        for category in sorted(filter(None, menu_data.keys())):
            # The code block for each tab starts here, correctly indented
            self.tabview.add(category)

            # --- Using CTkScrollableFrame for improved scrolling in Admin Panel Tabs ---
            # This works well here as no per-tab background images are needed.
            scrollable_frame = ctk.CTkScrollableFrame(self.tabview.tab(category), fg_color="transparent") # Use transparent or desired background
            scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5) # Add padding to scrollable frame

            # Admin Panel Item Widgets placed directly inside the scrollable_frame using grid
            row = 0
            # Ensure items are sorted for consistent display
            for item, price in sorted(menu_data[category].items()):
                ctk.CTkLabel(scrollable_frame, text=item, font=label_font)\
                    .grid(row=row, column=0, sticky="w", padx=5, pady=5)
                ctk.CTkLabel(scrollable_frame, text="Current Price:", font=label_font)\
                    .grid(row=row, column=1, padx=5, pady=5)
                ctk.CTkLabel(scrollable_frame, text=f"GHS {price:.2f}", font=label_font)\
                    .grid(row=row, column=2, padx=5, pady=5)
                ctk.CTkLabel(scrollable_frame, text="New Price:", font=label_font).grid(row=row, column=3, padx=5, pady=5)

                entry = ctk.CTkEntry(scrollable_frame, width=100, font=entry_font) # Give entry a width
                entry.grid(row=row, column=4, padx=5, pady=5)
                self.entries[(category, item)] = entry

                # Pass the entry widget to the update function
                update_button = ctk.CTkButton(
                    scrollable_frame, text="Update Price", font=button_font, width=100,
                    command=lambda c=category, i=item, e=entry: self.update_price_command(c, i, e),
                     fg_color="#28a745", hover_color="#218838" # Example colors
                )
                update_button.grid(row=row, column=5, padx=5, pady=5)

                edit_button = ctk.CTkButton(
                     scrollable_frame, text="Edit Details", font=button_font, width=100, # Renamed text, adjusted width
                     command=lambda c=category, i=item: self.open_edit_window(c, i),
                      fg_color="#ffc107", hover_color="#e0a800" # Example colors
                )
                edit_button.grid(row=row, column=6, padx=5, pady=5)
                row += 1

            # Configure columns within the scrollable frame to expand
            scrollable_frame.grid_columnconfigure(0, weight=1) # Item name takes up space
            # Add weight to other columns to distribute space if needed
            scrollable_frame.grid_columnconfigure(1, weight=0)
            scrollable_frame.grid_columnconfigure(2, weight=0)
            scrollable_frame.grid_columnconfigure(3, weight=0)
            scrollable_frame.grid_columnconfigure(4, weight=0)
            scrollable_frame.grid_columnconfigure(5, weight=0)
            scrollable_frame.grid_columnconfigure(6, weight=0)

            # CTkScrollableFrame handles its own scrollregion and bindings


        # Add major edit button outside the tabview
        ctk.CTkButton(self, text="Major Edit Options", font=("Helvetica", 16),
                      command=self.open_major_edit_window,
                       fg_color="#007bff", hover_color="#0056b3").pack(pady=(10,5)) # Added padding


        # Add back button outside the tabview
        ctk.CTkButton(self, text="Back", font=("Helvetica", 16), command=self.back,
                      fg_color="#6c757d", hover_color="#5a6268").pack(pady=(0,10)) # Added padding


    def update_price_command(self, category: str, item: str, entry_widget: ctk.CTkEntry):
        """Handles the update button click in Admin Panel."""
        new_price = entry_widget.get()
        if not new_price:
            messagebox.showerror("Input Error", "Please enter a new price.") # More specific title
            return
        try:
            new_price_float = float(new_price)
            if new_price_float < 0: # Add basic validation
                 messagebox.showerror("Input Error", "Price cannot be negative.")
                 return
        except ValueError:
            messagebox.showerror("Input Error", "Invalid price. Please enter a valid number (e.g., 12.50).") # More specific error
            return

        # Call the controller method to update the price in the model
        success = self.controller.update_menu_price(category, item, new_price_float)

        if success:
            # messagebox.showinfo("Success", f"Price for '{item}' updated successfully.") # Removed verbose success message
            # Refresh the display is handled by the controller upon model success
            pass
        else:
            messagebox.showerror("Update Failed", f"Failed to update price for '{item}'. Item might not exist.") # More specific title

    def open_edit_window(self, category: str, item: str):
        """Opens the product edit window for a specific item."""
        # Get the current price dynamically from the menu model
        current_price = self.menu_model.get_menu().get(category, {}).get(item)
        if current_price is None:
             messagebox.showerror("Error", "Could not find item details.")
             return
        # Create ProductEditView, passing self (AdminPanelView) as parent
        # Parent argument is implicitly handled by CTkToplevel passing master
        ProductEditView(self, category, item, current_price, self.controller)


    def open_major_edit_window(self):
        """Opens the major edit options window."""
        # Reuse existing major edit view if open
        if hasattr(self.controller, 'major_edit_view') and self.controller.major_edit_view is not None and self.controller.major_edit_view.winfo_exists():
             self.controller.major_edit_view.lift()
             self.controller.major_edit_view.focus_force() # Ensure focus
             return
        # Create and store reference in the controller
        self.controller.major_edit_view = MajorEditView(self, self.controller)
        self.controller.major_edit_view.transient(self) # Make modal to AdminPanel
        self.controller.major_edit_view.grab_set() # Grab focus

    def back(self):
        """Closes the Admin Panel View and returns to the Home View."""
        # Closing the AdminPanelView is handled in the Controller's on_admin_panel_view_close method
        # which destroys associated sub-windows and deiconifies the main view.
        # Just destroy the AdminPanelView itself here.
        logging.info("Closing Admin Panel View from Back button.")
        self.destroy()
        # The on_back callback (controller.on_admin_panel_view_close) will handle the rest.


    def refresh_display(self):
        """Refreshes the content of the Admin Panel tabs."""
        # Destroy existing tabview and recreate it
        # Check if the window still exists before trying to destroy/create
        if self.winfo_exists():
             logging.info("Refreshing Admin Panel display.")
             self.tabview.destroy()
             self.create_widgets() # Recreate all widgets

# New view to remove a category (Defined before MajorEditView as requested)
class RemoveCategoryView(ctk.CTkToplevel):
    """Window for removing an existing menu category."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Remove Category")
        self.geometry("300x200")
        self.resizable(False, False) # Explicitly make window non-resizable
        self.controller = controller
        self.menu_model = controller.menu_model
        # self.parent = parent # Parent reference is implicitly handled by CTkToplevel
        self.create_widgets()
         # protocol is handled by default for toplevels or can be set by controller
        # self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    def create_widgets(self):
        """Creates and lays out the widgets for the Remove Category View."""
        label_font = ("Helvetica", 14)
        button_font = ("Helvetica", 14)

        ctk.CTkLabel(self, text="Select Category to Remove:", font=label_font).pack(pady=(10,5))

        self.selected_category = tk.StringVar(self)
        # Filter out empty strings and sort categories for the dropdown
        categories = sorted(filter(None, self.menu_model.get_menu().keys()))

        if categories:
            self.selected_category.set(categories[0])
        else:
             self.selected_category.set("No categories available") # Handle empty menu case
             categories = ["No categories available"] # Ensure dropdown is not empty


        self.category_menu = ctk.CTkOptionMenu(self, values=categories, variable=self.selected_category, width=250) # Added width
        self.category_menu.pack(pady=(0,10), padx=20)

        ctk.CTkButton(self, text="Remove Category", font=button_font, command=self.remove_category,
                       fg_color="#dc3545", hover_color="#c82333").pack(pady=10)

    def remove_category(self):
        """Handles removing the selected category."""
        category = self.selected_category.get()

        if category == "No categories available" or not category:
            messagebox.showerror("Selection Error", "No category selected or available.")
            return

        # Confirm with the user before deleting a category and its contents
        confirm = messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove the category '{category}' and all its items? This cannot be undone.")
        if not confirm:
            return

        # Call controller method to remove category
        success = self.controller.remove_menu_category(category)

        if success:
            # messagebox.showinfo("Success", f"Category '{category}' removed.") # Removed verbose success
            # Refresh is handled by the controller
            logging.info(f"Removed category '{category}'.")
            self.destroy()
        else:
            messagebox.showerror("Removal Failed", "Failed to remove category.")


class ProductEditView(ctk.CTkToplevel):
    """Window for editing a specific product's name and price."""
    def __init__(self, parent, category: str, item: str, current_price: float, controller):
        super().__init__(parent)
        self.title(f"Edit Product: {item}")
        self.geometry("400x300")
        self.resizable(False, False) # Explicitly make window non-resizable
        self.category = category
        self.item = item
        self.current_price = current_price
        self.controller = controller
        # self.parent = parent # Parent reference is implicitly handled by CTkToplevel
        self.create_widgets()
        # protocol is handled by default for toplevels or can be set by controller
        # self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    def create_widgets(self):
        """Creates and lays out the widgets for the Product Edit View."""
        label_font = ("Helvetica", 14)
        entry_font = ("Helvetica", 14)
        button_font = ("Helvetica", 14)


        ctk.CTkLabel(self, text="Product Name:", font=label_font).pack(pady=(10,0))
        self.name_entry = ctk.CTkEntry(self, font=entry_font, width=250)
        self.name_entry.insert(0, self.item)
        self.name_entry.pack(pady=(0,10), padx=20)

        ctk.CTkLabel(self, text="Price:", font=label_font).pack(pady=(0,0))
        self.price_entry = ctk.CTkEntry(self, font=entry_font, width=250)
        self.price_entry.insert(0, f"{self.current_price:.2f}")
        self.price_entry.pack(pady=(0,10), padx=20)

        ctk.CTkButton(self, text="Save Changes", font=button_font, command=self.save_changes,
                       fg_color="#28a745", hover_color="#218838").pack(pady=10)

    def save_changes(self):
        """Handles saving changes to the product details."""
        new_name = self.name_entry.get().strip()
        new_price = self.price_entry.get().strip()

        if not new_name: # Allow price to be empty, validation happens in controller/model
            messagebox.showerror("Input Error", "Product name cannot be empty.")
            return
        if not new_price:
             messagebox.showerror("Input Error", "Price cannot be empty.")
             return

        try:
            new_price_float = float(new_price)
            if new_price_float < 0: # Add basic validation
                 messagebox.showerror("Input Error", "Price cannot be negative.")
                 return
        except ValueError:
            messagebox.showerror("Input Error", "Invalid price. Please enter a valid number.")
            return


        # Call the controller method to update the product details
        updated = self.controller.update_product_details(self.category, self.item, new_name, new_price_float)

        if updated:
            # messagebox.showinfo("Success", f"Product '{new_name}' updated successfully.") # Removed verbose success
            # Refresh is handled by the controller
            logging.info(f"Product details saved for '{new_name}'.")
            self.destroy()
        else:
            messagebox.showerror("Update Failed", "Update failed. Check if the new name already exists or if the item was removed.")

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image
import logging

# --- OrderView ---
class OrderView(ctk.CTkToplevel):
    """Window for placing customer orders."""
    def __init__(self, menu, controller, on_generate_invoice, on_back):
        super().__init__()
        self.title("Place Order")
        self.geometry("800x600")
        self.resizable(False, False)
        self.menu = menu
        self.controller = controller
        self.on_generate_invoice = on_generate_invoice
        self.on_back = on_back
        self.order_summary = {}
        # Attempt to load plus/minus icons
        try:
            plus_img = Image.open("Images/plus.png")
            minus_img = Image.open("Images/minus.png")
            self.plus_img = ctk.CTkImage(plus_img, size=(20, 20))
            self.minus_img = ctk.CTkImage(minus_img, size=(20, 20))
        except Exception:
            self.plus_img = None
            self.minus_img = None
        self.create_widgets()

    def create_widgets(self):
        # --- Scrollable menu list ---
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        inner_frame = container

        row = 0
        for category, items in self.menu.items():
            ctk.CTkLabel(inner_frame, text=category, font=("Helvetica", 18, "bold"))\
                .grid(row=row, column=0, columnspan=4, pady=(10, 5), sticky="w")
            row += 1
            for item, price in sorted(items.items()):
                ctk.CTkLabel(inner_frame, text=item, font=("Helvetica", 14))\
                    .grid(row=row, column=0, sticky="w", padx=5, pady=5)
                ctk.CTkLabel(inner_frame, text=f"GHS {price:.2f}", font=("Helvetica", 14))\
                    .grid(row=row, column=1, padx=5, pady=5)

                plus_btn = (
                    ctk.CTkButton(
                        inner_frame,
                        image=self.plus_img, text="",
                        width=30,
                        command=lambda c=category, i=item: self.add_item(c, i),
                        fg_color="transparent", hover_color="gray30"
                    )
                    if self.plus_img
                    else
                    ctk.CTkButton(
                        inner_frame,
                        text="+", width=30,
                        command=lambda c=category, i=item: self.add_item(c, i),
                        fg_color="#28a745", hover_color="#218838"
                    )
                )
                plus_btn.grid(row=row, column=2, padx=5, pady=5)

                minus_btn = (
                    ctk.CTkButton(
                        inner_frame,
                        image=self.minus_img, text="",
                        width=30,
                        command=lambda c=category, i=item: self.remove_item(c, i),
                        fg_color="transparent", hover_color="gray30"
                    )
                    if self.minus_img
                    else
                    ctk.CTkButton(
                        inner_frame,
                        text="–", width=30,
                        command=lambda c=category, i=item: self.remove_item(c, i),
                        fg_color="#dc3545", hover_color="#c82333"
                    )
                )
                minus_btn.grid(row=row, column=3, padx=5, pady=5)
                row += 1

        # --- Bottom Buttons ---
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            button_frame, text="Generate Invoice",
            font=("Helvetica", 16), command=self.generate_invoice,
            fg_color="#007bff", hover_color="#0056b3"
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            button_frame, text="Clear Orders",
            font=("Helvetica", 16), command=self.clear_orders,
            fg_color="#ffc107", hover_color="#e0a800"
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            button_frame, text="Back",
            font=("Helvetica", 16), command=self.back,
            fg_color="#6c757d", hover_color="#5a6268"
        ).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

    def add_item(self, category: str, item: str):
        key = (category, item)
        self.order_summary[key] = self.order_summary.get(key, 0) + 1
        self.update_summary_display()
        logging.info(f"Added '{item}' to order (now x{self.order_summary[key]})")

    def remove_item(self, category: str, item: str):
        key = (category, item)
        if key in self.order_summary:
            if self.order_summary[key] > 1:
                self.order_summary[key] -= 1
                logging.info(f"Decremented '{item}' (now x{self.order_summary[key]})")
            else:
                del self.order_summary[key]
                logging.info(f"Removed '{item}' from order.")
            self.update_summary_display()
        else:
            logging.warning(f"Tried to remove non-existent '{item}'")

    def clear_orders(self):
        if messagebox.askyesno("Clear Order", "Clear all items?"):
            self.order_summary.clear()
            self.update_summary_display()
            logging.info("Cleared all orders.")
        else:
            logging.info("Clear cancelled.")

    def update_summary_display(self):
        # Assume you have a CTkTextbox named self.summary_textbox
        self.summary_textbox.configure(state="normal")
        self.summary_textbox.delete("1.0", "end")
        if not self.order_summary:
            self.summary_textbox.insert("end", "Your order is empty.")
        else:
            for (cat, item), qty in sorted(self.order_summary.items()):
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
                        f"{item} (x{qty}) — no longer available\n"
                    )
        self.summary_textbox.configure(state="disabled")

    def generate_invoice(self):
        if not self.order_summary:
            messagebox.showerror("Error", "No items selected.")
            return
        details = []
        for (cat, item), qty in self.order_summary.items():
            price = self.menu.get(cat, {}).get(item)
            if price is not None:
                details.append((cat, item, qty, price))
        if not details:
            messagebox.showerror("Error", "Selected items unavailable.")
            return
        self.on_generate_invoice(details, self)

    def back(self):
        self.destroy()
        self.on_back()


# --- InvoiceView ---
class InvoiceView(ctk.CTkToplevel):
    """Window displaying the generated invoice."""
    def __init__(self, invoice_text: str, on_back):
        super().__init__()
        self.title("Invoice")
        self.geometry("400x500")
        self.resizable(False, False)
        self.on_back = on_back
        self.create_widgets(invoice_text)

    def create_widgets(self, invoice_text: str):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        try:
            bg = Image.open("Images/grand_crab.png").resize((400, 500), Image.Resampling.LANCZOS)
            img = ctk.CTkImage(light_image=bg, dark_image=bg, size=(400, 500))
            lbl = ctk.CTkLabel(container, image=img, text="")
            lbl.image = img
            lbl.place(relwidth=1, relheight=1)
            lbl.lower()
        except Exception:
            container.configure(fg_color="gray15")

        self.textbox = ctk.CTkTextbox(container, wrap="word", font=("Helvetica", 14))
        self.textbox.pack(side="left", fill="both", expand=True)
        scrollbar = ctk.CTkScrollbar(container, orientation="vertical", command=self.textbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.textbox.configure(yscrollcommand=scrollbar.set)
        self.textbox.insert("0.0", invoice_text)
        self.textbox.configure(state="disabled")

        ctk.CTkButton(
            self, text="Back", font=("Helvetica", 16),
            fg_color="#6c757d", hover_color="#5a6268",
            command=self.back
        ).pack(fill="x", padx=10, pady=10)

    def back(self):
        self.destroy()
        self.on_back()


# --- LoginView ---
class LoginView(ctk.CTkToplevel):
    """Window for admin login."""
    def __init__(self, on_login, on_back):
        super().__init__()
        self.title("Admin Login")
        self.geometry("300x250")
        self.resizable(False, False)
        self.on_login = on_login
        self.on_back = on_back
        self.create_widgets()
        self.focus_force()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Username:", font=("Helvetica", 14)).pack(pady=(10, 0))
        self.username_entry = ctk.CTkEntry(self, width=200)
        self.username_entry.pack(pady=(0, 10), padx=20)
        ctk.CTkLabel(self, text="Password:", font=("Helvetica", 14)).pack()
        self.password_entry = ctk.CTkEntry(self, show="*", width=200)
        self.password_entry.pack(pady=(0, 10), padx=20)
        ctk.CTkButton(
            self, text="Login", width=150,
            fg_color="#007bff", hover_color="#0056b3",
            command=self._perform_login
        ).pack(pady=10)
        ctk.CTkButton(
            self, text="Back", width=150,
            fg_color="#6c757d", hover_color="#5a6268",
            command=self.back
        ).pack()

    def _perform_login(self):
        self.on_login(self.username_entry.get(), self.password_entry.get())

    def back(self):
        self.destroy()
        self.on_back()


# --- AdminPanelView ---
class AdminPanelView(ctk.CTkToplevel):
    """Window for managing menu items/prices."""
    def __init__(self, menu_model, controller, on_back):
        super().__init__()
        self.title("Admin Panel - Manage Menu")
        self.geometry("800x600")
        self.resizable(False, False)
        self.menu_model = menu_model
        self.controller = controller
        self.on_back = on_back
        self.entries = {}
        self.create_widgets()
        self.focus_force()

    def create_widgets(self):
        for w in self.winfo_children():
            w.destroy()
        self.entries.clear()

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        label_font = ("Helvetica", 14)
        entry_font = ("Helvetica", 14)
        button_font = ("Helvetica", 14)

        menu_data = self.menu_model.get_menu()
        for category in sorted(filter(None, menu_data.keys())):
            self.tabview.add(category)
            frame = ctk.CTkScrollableFrame(self.tabview.tab(category), fg_color="transparent")
            frame.pack(fill="both", expand=True, padx=5, pady=5)
            frame.grid_columnconfigure(0, weight=1)

            row = 0
            for item, price in sorted(menu_data[category].items()):
                ctk.CTkLabel(frame, text=item, font=label_font).grid(row=row, column=0, sticky="w", padx=5, pady=5)
                ctk.CTkLabel(frame, text=f"GHS {price:.2f}", font=label_font).grid(row=row, column=1, padx=5, pady=5)
                ctk.CTkLabel(frame, text="New Price:", font=label_font).grid(row=row, column=2, padx=5, pady=5)
                entry = ctk.CTkEntry(frame, width=100, font=entry_font)
                entry.grid(row=row, column=3, padx=5, pady=5)
                self.entries[(category, item)] = entry

                ctk.CTkButton(
                    frame, text="Update Price", font=button_font, width=100,
                    fg_color="#28a745", hover_color="#218838",
                    command=lambda c=category, i=item, e=entry: self.update_price_command(c, i, e)
                ).grid(row=row, column=4, padx=5, pady=5)

                ctk.CTkButton(
                    frame, text="Edit Details", font=button_font, width=100,
                    fg_color="#ffc107", hover_color="#e0a800",
                    command=lambda c=category, i=item: self.open_edit_window(c, i)
                ).grid(row=row, column=5, padx=5, pady=5)
                row += 1

        ctk.CTkButton(
            self, text="Major Edit Options", font=("Helvetica", 16),
            fg_color="#007bff", hover_color="#0056b3",
            command=self.open_major_edit_window
        ).pack(pady=(10, 5))

        ctk.CTkButton(
            self, text="Back", font=("Helvetica", 16),
            fg_color="#6c757d", hover_color="#5a6268",
            command=self.back
        ).pack(pady=(0, 10))

    def update_price_command(self, category: str, item: str, entry_widget: ctk.CTkEntry):
        new_price = entry_widget.get()
        if not new_price:
            messagebox.showerror("Input Error", "Please enter a new price.")
            return
        try:
            val = float(new_price)
            if val < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Invalid price.")
            return
        self.controller.update_menu_price(category, item, val)

    def open_edit_window(self, category: str, item: str):
        current_price = self.menu_model.get_menu().get(category, {}).get(item)
        if current_price is None:
            messagebox.showerror("Error", "Item not found.")
            return
        ProductEditView(self, category, item, current_price, self.controller)

    def open_major_edit_window(self):
        if hasattr(self.controller, 'major_edit_view') and self.controller.major_edit_view and self.controller.major_edit_view.winfo_exists():
            self.controller.major_edit_view.lift()
            self.controller.major_edit_view.focus_force()
            return
        self.controller.major_edit_view = MajorEditView(self, self.controller)
        self.controller.major_edit_view.transient(self)
        self.controller.major_edit_view.grab_set()

    def back(self):
        self.destroy()
        self.on_back()

    def refresh_display(self):
        if self.winfo_exists():
            self.tabview.destroy()
            self.create_widgets()


# --- RemoveCategoryView ---
class RemoveCategoryView(ctk.CTkToplevel):
    """Window for removing an existing menu category."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Remove Category")
        self.geometry("300x200")
        self.resizable(False, False)
        self.controller = controller
        self.menu_model = controller.menu_model
        self.create_widgets()
        self.focus_force()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Select Category to Remove:", font=("Helvetica", 14)).pack(pady=(10, 5))
        self.selected_category = tk.StringVar(self)
        categories = sorted(filter(None, self.menu_model.get_menu().keys()))
        self.selected_category.set(categories[0] if categories else "No categories available")
        ctk.CTkOptionMenu(self, values=categories or ["No categories available"],
                           variable=self.selected_category, width=250).pack(pady=(0, 10), padx=20)
        ctk.CTkButton(
            self, text="Remove Category", font=("Helvetica", 14),
            fg_color="#dc3545", hover_color="#c82333",
            command=self.remove_category
        ).pack(pady=10)

    def remove_category(self):
        category = self.selected_category.get()
        if not category or category == "No categories available":
            messagebox.showerror("Selection Error", "No valid category selected.")
            return
        if not messagebox.askyesno("Confirm", f"Remove '{category}' forever?"):
            return
        self.controller.remove_menu_category(category)
        self.destroy()


# --- ProductEditView ---
class ProductEditView(ctk.CTkToplevel):
    """Window for editing a specific product's name and price."""
    def __init__(self, parent, category: str, item: str, current_price: float, controller):
        super().__init__(parent)
        self.title(f"Edit Product: {item}")
        self.geometry("400x300")
        self.resizable(False, False)
        self.category = category
        self.item = item
        self.current_price = current_price
        self.controller = controller
        self.create_widgets()
        self.focus_force()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Product Name:", font=("Helvetica", 14)).pack(pady=(10, 0))
        self.name_entry = ctk.CTkEntry(self, width=250)
        self.name_entry.insert(0, self.item)
        self.name_entry.pack(pady=(0, 10), padx=20)

        ctk.CTkLabel(self, text="Price:", font=("Helvetica", 14)).pack()
        self.price_entry = ctk.CTkEntry(self, width=250)
        self.price_entry.insert(0, f"{self.current_price:.2f}")
        self.price_entry.pack(pady=(0, 10), padx=20)

        ctk.CTkButton(
            self, text="Save Changes", font=("Helvetica", 14),
            fg_color="#28a745", hover_color="#218838",
            command=self.save_changes
        ).pack(pady=10)

    def save_changes(self):
        new_name = self.name_entry.get().strip()
        new_price = self.price_entry.get().strip()
        if not new_name:
            messagebox.showerror("Input Error", "Name cannot be empty.")
            return
        try:
            price_val = float(new_price)
            if price_val < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Invalid price.")
            return
        self.controller.update_product_details(self.category, self.item, new_name, price_val)
        self.destroy()


# --- MajorEditView ---
class MajorEditView(ctk.CTkToplevel):
    """Window containing major menu editing options."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Major Edit Options")
        self.geometry("400x400")
        self.resizable(False, False)
        self.controller = controller
        self.create_widgets()
        self.focus_force()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Major Edit Options", font=("Helvetica", 16)).pack(pady=(10, 20))
        btn_cfg = {"font": ("Helvetica", 14), "width": 300, "padx": 20, "fill": "x"}
        ctk.CTkButton(
            self, text="Add Category", **btn_cfg,
            fg_color="#28a745", hover_color="#218838",
            command=self.add_category
        ).pack(pady=5)
        ctk.CTkButton(
            self, text="Delete Category", **btn_cfg,
            fg_color="#dc3545", hover_color="#c82333",
            command=self.remove_category
        ).pack(pady=5)
        ctk.CTkButton(
            self, text="Add Item", **btn_cfg,
            fg_color="#28a745", hover_color="#218838",
            command=self.add_item
        ).pack(pady=5)
        ctk.CTkButton(
            self, text="Remove Item", **btn_cfg,
            fg_color="#dc3545", hover_color="#c82333",
            command=self.remove_item
        ).pack(pady=5)
        ctk.CTkButton(
            self, text="Edit Invoice Format", **btn_cfg,
            fg_color="#007bff", hover_color="#0056b3",
            command=self.edit_invoice
        ).pack(pady=(5, 20))

    def add_category(self):
        if hasattr(self.controller, 'add_category_view') and getattr(self.controller, 'add_category_view', None) and self.controller.add_category_view.winfo_exists():
            self.controller.add_category_view.lift()
            self.controller.add_category_view.focus_force()
            return
        self.controller.add_category_view = AddCategoryView(self, self.controller)
        self.controller.add_category_view.transient(self)
        self.controller.add_category_view.grab_set()

    def remove_category(self):
        if hasattr(self.controller, 'remove_category_view') and getattr(self.controller, 'remove_category_view', None) and self.controller.remove_category_view.winfo_exists():
            self.controller.remove_category_view.lift()
            self.controller.remove_category_view.focus_force()
            return
        self.controller.remove_category_view = RemoveCategoryView(self, self.controller)
        self.controller.remove_category_view.transient(self)
        self.controller.remove_category_view.grab_set()

    def add_item(self):
        if hasattr(self.controller, 'add_item_view') and getattr(self.controller, 'add_item_view', None) and self.controller.add_item_view.winfo_exists():
            self.controller.add_item_view.lift()
            self.controller.add_item_view.focus_force()
            return
        self.controller.add_item_view = AddItemView(self, self.controller)
        self.controller.add_item_view.transient(self)
        self.controller.add_item_view.grab_set()

    def remove_item(self):
        if hasattr(self.controller, 'remove_item_view') and getattr(self.controller, 'remove_item_view', None) and self.controller.remove_item_view.winfo_exists():
            self.controller.remove_item_view.lift()
            self.controller.remove_item_view.focus_force()
            return
        self.controller.remove_item_view = RemoveItemView(self, self.controller)
        self.controller.remove_item_view.transient(self)
        self.controller.remove_item_view.grab_set()

    def edit_invoice(self):
        if hasattr(self.controller, 'invoice_format_view') and getattr(self.controller, 'invoice_format_view', None) and self.controller.invoice_format_view.winfo_exists():
            self.controller.invoice_format_view.lift()
            self.controller.invoice_format_view.focus_force()
            return
        self.controller.invoice_format_view = InvoiceFormatEditView(self, self.controller)
        self.controller.invoice_format_view.transient(self)
        self.controller.invoice_format_view.grab_set()


# --- AddCategoryView ---
class AddCategoryView(ctk.CTkToplevel):
    """Window for adding a new menu category."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Add New Category")
        self.geometry("300x200")
        self.resizable(False, False)
        self.controller = controller
        self.create_widgets()
        self.focus_force()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Category Name:", font=("Helvetica", 14)).pack(pady=(10, 0))
        self.category_entry = ctk.CTkEntry(self, width=250)
        self.category_entry.pack(pady=(0, 10), padx=20)
        ctk.CTkButton(
            self, text="Add Category", font=("Helvetica", 14),
            fg_color="#28a745", hover_color="#218838",
            command=self.add_category
        ).pack(pady=10)

    def add_category(self):
        name = self.category_entry.get().strip()
        if not name:
            messagebox.showerror("Input Error", "Please enter a category name.")
            return
        self.controller.add_menu_category(name)
        self.destroy()


# --- AddItemView ---
class AddItemView(ctk.CTkToplevel):
    """Window for adding a new item to a menu category."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Add New Item")
        self.geometry("300x350")
        self.resizable(False, False)
        self.controller = controller
        self.menu_model = controller.menu_model
        self.create_widgets()
        self.focus_force()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Select Category:", font=("Helvetica", 14)).pack(pady=(10, 5))
        self.selected_category = tk.StringVar(self)
        cats = sorted(filter(None, self.menu_model.get_menu().keys()))
        self.selected_category.set(cats[0] if cats else "No categories available")
        ctk.CTkOptionMenu(self, values=cats or ["No categories available"],
                           variable=self.selected_category, width=250).pack(pady=(0, 10), padx=20)

        ctk.CTkLabel(self, text="Item Name:", font=("Helvetica", 14)).pack()
        self.item_entry = ctk.CTkEntry(self, width=250)
        self.item_entry.pack(pady=(0, 10), padx=20)

        ctk.CTkLabel(self, text="Price:", font=("Helvetica", 14)).pack()
        self.price_entry = ctk.CTkEntry(self, width=250)
        self.price_entry.pack(pady=(0, 10), padx=20)

        ctk.CTkButton(
            self, text="Add Item", font=("Helvetica", 14),
            fg_color="#28a745", hover_color="#218838",
            command=self.add_item
        ).pack(pady=10)

    def add_item(self):
        cat = self.selected_category.get()
        name = self.item_entry.get().strip()
        val = self.price_entry.get().strip()
        if not name or not val:
            messagebox.showerror("Input Error", "Please fill all fields.")
            return
        try:
            price = float(val)
            if price < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Invalid price.")
            return
        self.controller.add_menu_item(cat, name, price)
        self.destroy()


# --- RemoveItemView ---
class RemoveItemView(ctk.CTkToplevel):
    """Window for removing an item from a menu category."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Remove Item")
        self.geometry("300x300")
        self.resizable(False, False)
        self.controller = controller
        self.menu_model = controller.menu_model
        self.create_widgets()
        self.focus_force()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Select Category:", font=("Helvetica", 14)).pack(pady=(10, 5))
        self.selected_category = tk.StringVar(self)
        cats = sorted(filter(None, self.menu_model.get_menu().keys()))
        self.selected_category.set(cats[0] if cats else "No categories available")
        ctk.CTkOptionMenu(
            self, values=cats or ["No categories available"],
            variable=self.selected_category,
            command=self.update_items,
            width=250
        ).pack(pady=(0, 10), padx=20)

        ctk.CTkLabel(self, text="Select Item:", font=("Helvetica", 14)).pack()
        self.selected_item = tk.StringVar(self)
        items = sorted(self.menu_model.get_menu().get(self.selected_category.get(), {}).keys())
        self.selected_item.set(items[0] if items else "No items available")
        self.item_menu = ctk.CTkOptionMenu(
            self, values=items or ["No items available"], variable=self.selected_item, width=250
        )
        self.item_menu.pack(pady=(0, 10), padx=20)

        ctk.CTkButton(
            self, text="Remove Item", font=("Helvetica", 14),
            fg_color="#dc3545", hover_color="#c82333",
            command=self.remove_item
        ).pack(pady=10)

    def update_items(self, cat):
        items = sorted(self.menu_model.get_menu().get(cat, {}).keys())
        if items:
            self.selected_item.set(items[0])
        else:
            self.selected_item.set("No items available")
            items = ["No items available"]
        self.item_menu.configure(values=items)

    def remove_item(self):
        cat = self.selected_category.get()
        item = self.selected_item.get()
        if not cat or not item or "No" in item:
            messagebox.showerror("Error", "Nothing to remove.")
            return
        if not messagebox.askyesno("Confirm", f"Remove '{item}' from '{cat}'?"):
            return
        self.controller.remove_menu_item(cat, item)
        self.destroy()


# --- InvoiceFormatEditView ---
class InvoiceFormatEditView(ctk.CTkToplevel):
    """Window for editing the invoice template string."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Edit Invoice Template")
        self.geometry("500x400")
        self.resizable(False, False)
        self.controller = controller
        self.create_widgets()
        self.focus_force()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Invoice Template:", font=("Helvetica", 14)).pack(pady=(10, 5))
        ctk.CTkLabel(
            self,
            text="Use {order_time}, {items}, {total:.2f} as placeholders.",
            font=("Helvetica", 10)
        ).pack(pady=(0, 5))

        self.textbox = ctk.CTkTextbox(self, wrap="word", font=("Courier New", 12))
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("0.0", self.controller.get_invoice_template())
        self.textbox.configure(state="normal")

        scrollbar = ctk.CTkScrollbar(self, command=self.textbox.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self.textbox.configure(yscrollcommand=scrollbar.set)

        ctk.CTkButton(
            self, text="Save Template", font=("Helvetica", 14),
            fg_color="#28a745", hover_color="#218838",
            command=self.save_template
        ).pack(fill="x", padx=10, pady=(0, 10))

    def save_template(self):
        self.textbox.configure(state="normal")
        new = self.textbox.get("0.0", "end").strip()
        if not new:
            messagebox.showerror("Input Error", "Template cannot be empty.")
            return
        self.controller.set_invoice_template(new)
        self.destroy()
