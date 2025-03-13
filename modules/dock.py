import json
from gi.repository import GLib, Gtk, Gdk, Gio
from utils.icon_resolver import IconResolver
from utils.occlusion import check_occlusion
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.image import Image
from fabric.widgets.eventbox import EventBox
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.hyprland.widgets import get_hyprland_connection
from fabric.utils import exec_shell_command, exec_shell_command_async, idle_add, remove_handler, get_relative_path
from fabric.utils.helpers import get_desktop_applications

import config.data as data
import logging

def read_config():
    """Read and return the full configuration from the JSON file, handling missing file."""
    config_path = get_relative_path("../config/dock.json")
    try:
        with open(config_path, "r") as file:
            data = json.load(file)
            
        # Migration: Convert old format (simple string array) to new format (array of objects with full app data)
        if "pinned_apps" in data and data["pinned_apps"] and isinstance(data["pinned_apps"][0], str):
            # Get all desktop apps for lookup during migration
            all_apps = get_desktop_applications()
            app_map = {app.name: app for app in all_apps if app.name}
            
            # This is the old format - convert it with full app data
            old_pinned = data["pinned_apps"]
            data["pinned_apps"] = []
            
            for app_id in old_pinned:
                # Try to find the app by name
                app = app_map.get(app_id)
                if app:
                    # Create comprehensive app data
                    app_data = {
                        "name": app.name,
                        "display_name": app.display_name,
                        "window_class": app.window_class,
                        "executable": app.executable,
                        "command_line": app.command_line
                    }
                    data["pinned_apps"].append(app_data)
                else:
                    # Fallback to just the name if app not found
                    data["pinned_apps"].append({"name": app_id})
                
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"pinned_apps": []}  # Default to empty pinned apps
    return data

class Dock(Window):
    # Static registry to track all active dock instances
    _instances = []
    
    def __init__(self, **kwargs):
        super().__init__(
            name="dock-window",
            layer="top",
            anchor="bottom center",
            margin="-8px 0 -4px 0",
            exclusivity="none",
            **kwargs,
        )
        # Add this instance to the registry
        Dock._instances.append(self)
        self.config = read_config()
        self.conn = get_hyprland_connection()
        self.icon = IconResolver()
        self.pinned = self.config.get("pinned_apps", [])
        self.config_path = get_relative_path("../config/dock.json")
        self.app_map = {}  # Initialize the app map
        self._all_apps = get_desktop_applications() # Get all apps for lookup
        # Create app identifiers mapping
        self.app_identifiers = self._build_app_identifiers_map()
        self.is_hidden = False
        self.hide_id = None
        self._arranger_handler = None
        self._drag_in_progress = False  # Drag lock flag
        self.is_hovered = False

        # Common window class aliases for applications with mismatched classes
        self.window_class_aliases = {
            "audacity": ["audacity.bin"],
            "firefox": ["firefox-esr", "firefoxdeveloperedition", "firefox-developer-edition"],
            "libreoffice": ["libreoffice-writer", "libreoffice-calc", "libreoffice-impress", "soffice"],
            "gimp": ["gimp-2.10"],
            "chromium": ["chromium-browser", "chrome"],
            "google-chrome": ["chrome"],
            "steam": ["steam_app_", "steamwebhelper"],
            "code": ["code-oss", "vscodium"],
            "jetbrains-idea": ["jetbrains-idea-ce"],
            "vlc": ["vlc-qt-interface"],
            "krita": ["krita.bin"],
            "blender": ["blender.bin"],
            # Add more common aliases as needed
        }

        # Set up UI containers
        self.view = Box(name="viewport", orientation="h", spacing=8)
        self.wrapper = Box(name="dock", orientation="v", children=[self.view])

        # Main dock container with hover handling
        self.dock_eventbox = EventBox()
        self.dock_eventbox.add(self.wrapper)
        self.dock_eventbox.connect("enter-notify-event", self._on_dock_enter)
        self.dock_eventbox.connect("leave-notify-event", self._on_dock_leave)

        # Bottom hover activation area
        self.hover_activator = EventBox()
        self.hover_activator.set_size_request(-1, 1)
        self.hover_activator.connect("enter-notify-event", self._on_hover_enter)
        self.hover_activator.connect("leave-notify-event", self._on_hover_leave)

        self.main_box = Box(orientation="v", children=[self.dock_eventbox, self.hover_activator])
        self.add(self.main_box)

        # Drag-and-drop setup for the viewport
        self.view.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK,
            [Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP, 0)],
            Gdk.DragAction.MOVE
        )
        self.view.drag_dest_set(
            Gtk.DestDefaults.ALL,
            [Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP, 0)],
            Gdk.DragAction.MOVE
        )
        self.view.connect("drag-data-get", self.on_drag_data_get)
        self.view.connect("drag-data-received", self.on_drag_data_received)
        self.view.connect("drag-begin", self.on_drag_begin)
        self.view.connect("drag-end", self.on_drag_end)

        # Initialization
        if self.conn.ready:
            self.update_dock()
            GLib.timeout_add(500, self.check_hide)
        else:
            self.conn.connect("event::ready", self.update_dock)
            self.conn.connect("event::ready", self.check_hide)

        for ev in ("activewindow", "openwindow", "closewindow", "changefloatingmode"):
            self.conn.connect(f"event::{ev}", self.update_dock)
        self.conn.connect("event::workspace", self.check_hide)

        GLib.timeout_add(250, self.check_occlusion_state)
        # Monitor dock.json for changes
        GLib.timeout_add_seconds(1, self.check_config_change)
        
    def _build_app_identifiers_map(self):
        """Build a mapping of app identifiers (class names, executables, names) to DesktopApp objects"""
        identifiers = {}
        for app in self._all_apps:
            # Map by name (lowercase)
            if app.name:
                identifiers[app.name.lower()] = app
                
            # Map by display name
            if app.display_name:
                identifiers[app.display_name.lower()] = app
                
            # Map by window class if available
            if app.window_class:
                identifiers[app.window_class.lower()] = app
                
            # Map by executable name if available
            if app.executable:
                exe_basename = app.executable.split('/')[-1].lower()
                identifiers[exe_basename] = app
                
            # Map by command line if available (without parameters)
            if app.command_line:
                cmd_base = app.command_line.split()[0].split('/')[-1].lower()
                identifiers[cmd_base] = app
                
        return identifiers

    def _normalize_window_class(self, class_name):
        """Normalize window class by removing common suffixes and lowercase."""
        if not class_name:
            return ""
            
        normalized = class_name.lower()
        
        # Remove common suffixes
        suffixes = [".bin", ".exe", ".so", "-bin", "-gtk"]
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
                
        return normalized
        
    def _classes_match(self, class1, class2):
        """Check if two window class names match accounting for variations."""
        if not class1 or not class2:
            return False
            
        # Normalize both classes
        norm1 = self._normalize_window_class(class1)
        norm2 = self._normalize_window_class(class2)
        
        # Direct match after normalization
        if norm1 == norm2:
            return True
            
        # Check aliases
        for base_class, aliases in self.window_class_aliases.items():
            if norm1 == base_class and norm2 in aliases:
                return True
            if norm2 == base_class and norm1 in aliases:
                return True
                
        # Check if one is contained within the other
        if len(norm1) > 3 and len(norm2) > 3:  # Avoid short class names which could lead to false matches
            if norm1 in norm2 or norm2 in norm1:
                return True
                
        return False

    def on_drag_begin(self, widget, drag_context):
        """Handle drag begin event by setting the drag lock flag."""
        self._drag_in_progress = True

    def _on_hover_enter(self, *args):
        """Handle hover over bottom activation area"""
        self.toggle_dock(show=True)

    def _on_hover_leave(self, *args):
        """Handle leave from bottom activation area"""
        self.delay_hide()

    def _on_dock_enter(self, widget, event):
        """Handle hover over dock content"""
        self.is_hovered = True
        self.wrapper.remove_style_class("occluded")
        # Cancel any pending hide operations
        if self.hide_id:
            GLib.source_remove(self.hide_id)
            self.hide_id = None
        self.toggle_dock(show=True)
        return True  # Important: Stop event propagation

    def _on_dock_leave(self, widget, event):
        """Handle leave from dock content"""
        # Only trigger if mouse actually left the entire dock area
        if event.detail == Gdk.NotifyType.INFERIOR:
            return False  # Ignore child-to-child mouse movements

        self.is_hovered = False
        self.delay_hide()
        # Immediate occlusion check on true leave
        occlusion_region = (0, data.CURRENT_HEIGHT - 70, data.CURRENT_WIDTH, 70)
        # Only add occlusion style if not dragging an icon.
        if not self._drag_in_progress and (check_occlusion(occlusion_region) or not self.view.get_children()):
            self.wrapper.add_style_class("occluded")
        return True

    # Enhanced app lookup methods
    def find_app(self, app_identifier):
        """Return the DesktopApp object by matching any app identifier.
        
        If app_identifier is a dict, it will use all available keys for matching.
        """
        if not app_identifier:
            return None
            
        # If we got a dict object with app data (new format)
        if isinstance(app_identifier, dict):
            # Try to find by all available identifiers in priority order
            for key in ["window_class", "executable", "command_line", "name", "display_name"]:
                if key in app_identifier and app_identifier[key]:
                    app = self.find_app_by_key(app_identifier[key])
                    if app:
                        return app
            return None
            
        # Simple string identifier (backward compatibility)
        return self.find_app_by_key(app_identifier)
    
    def find_app_by_key(self, key_value):
        """Find app by a single identifier value"""
        if not key_value:
            return None
            
        # Try direct lookup in our identifiers map
        normalized_id = str(key_value).lower()
        if normalized_id in self.app_identifiers:
            return self.app_identifiers[normalized_id]
            
        # Try fuzzy matching - find apps where the identifier is part of their names
        for app in self._all_apps:
            if app.name and normalized_id in app.name.lower():
                return app
            if app.display_name and normalized_id in app.display_name.lower():
                return app
            if app.window_class and normalized_id in app.window_class.lower():
                return app
            if app.executable and normalized_id in app.executable.lower():
                return app
            if app.command_line and normalized_id in app.command_line.lower():
                return app
        
        return None

    # Update the dock's app map using DesktopApp objects from the system.
    def update_app_map(self):
        """Updates the mapping of commands to DesktopApp objects."""
        self._all_apps = get_desktop_applications() # Refresh all apps
        self.app_map = {app.name: app for app in self._all_apps if app.name} # Map app names to DesktopApp objects
        self.app_identifiers = self._build_app_identifiers_map()  # Rebuild identifiers map

    def create_button(self, app_identifier, instances):
        """Create dock application button"""
        desktop_app = self.find_app(app_identifier) # Find app by identifier
        icon_img = None
        display_name = None
        
        if desktop_app:
            icon_img = desktop_app.get_icon_pixbuf(size=36)
            display_name = desktop_app.display_name or desktop_app.name
        
        # Extract identifier for fallback
        id_value = app_identifier["name"] if isinstance(app_identifier, dict) else app_identifier
        
        if not icon_img:
            # Fallback to IconResolver with the app command
            icon_img = self.icon.get_icon_pixbuf(id_value, 36) # Use identifier for fallback
        
        if not icon_img: # Double check after exec path try
            # Fallback icon if no DesktopApp is found
            icon_img = self.icon.get_icon_pixbuf("application-x-executable-symbolic", 36)
            # Final fallback
            if not icon_img:
                icon_img = self.icon.get_icon_pixbuf("image-missing", 36)
                
        items = [Image(pixbuf=icon_img)]

        tooltip = display_name or (id_value if isinstance(id_value, str) else "Unknown")
        if not display_name and instances and instances[0].get("title"):
            tooltip = instances[0]["title"]

        button = Button(
            child=Box(
                name="dock-icon",
                orientation="v",
                h_align="center",
                children=items,
            ),
            on_clicked=lambda *a: self.handle_app(app_identifier, instances, desktop_app), # Pass desktop_app as well
            tooltip_text=tooltip,
            name="dock-app-button",
        )

        # Store app data with the button for future reference
        button.app_identifier = app_identifier
        button.desktop_app = desktop_app
        button.instances = instances

        if instances:
            button.add_style_class("instance") # Style running apps

        # Enable DnD for ALL apps
        button.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK,
            [Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP, 0)],
            Gdk.DragAction.MOVE
        )
        button.connect("drag-begin", self.on_drag_begin)
        button.connect("drag-end", self.on_drag_end)  # Connect drag-end to ALL buttons
        
        # Make all buttons drop targets for better reordering
        button.drag_dest_set(
            Gtk.DestDefaults.ALL,
            [Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP, 0)],
            Gdk.DragAction.MOVE
        )
        button.connect("drag-data-get", self.on_drag_data_get)
        button.connect("drag-data-received", self.on_drag_data_received)

        button.connect("enter-notify-event", self._on_child_enter)
        return button

    # Enhanced app launching with multiple fallbacks
    def handle_app(self, app_identifier, instances, desktop_app=None):
        """Handle application button clicks with improved fallbacks"""
        if not instances:
            # Try to launch the app with multiple fallback methods
            if not desktop_app:
                desktop_app = self.find_app(app_identifier)
                
            if desktop_app:
                # Try the standard launch method first
                launch_success = desktop_app.launch()
                
                # If that fails, try command line or executable
                if not launch_success:
                    if desktop_app.command_line:
                        exec_shell_command_async(f"nohup {desktop_app.command_line}")
                    elif desktop_app.executable:
                        exec_shell_command_async(f"nohup {desktop_app.executable}")
            else:
                # No desktop entry found, try direct execution
                if isinstance(app_identifier, dict):
                    # Try command_line first, then executable, then name as last resort
                    if "command_line" in app_identifier and app_identifier["command_line"]:
                        exec_shell_command_async(f"nohup {app_identifier['command_line']}")
                    elif "executable" in app_identifier and app_identifier["executable"]:
                        exec_shell_command_async(f"nohup {app_identifier['executable']}")
                    elif "name" in app_identifier and app_identifier["name"]:
                        exec_shell_command_async(f"nohup {app_identifier['name']}")
                elif isinstance(app_identifier, str):
                    # Try direct execution with the identifier as fallback
                    exec_shell_command_async(f"nohup {app_identifier}")
        else:
            # Handle window switching for running instances
            focused = self.get_focused()
            idx = next(
                (i for i, inst in enumerate(instances) if inst["address"] == focused),
                -1,
            )
            next_inst = instances[(idx + 1) % len(instances)]
            exec_shell_command(
                f"hyprctl dispatch focuswindow address:{next_inst['address']}"
            )

    def _on_child_enter(self, widget, event):
        """Maintain hover state when entering child widgets"""
        self.is_hovered = True
        if self.hide_id:
            GLib.source_remove(self.hide_id)
            self.hide_id = None
        return False  # Continue event propagation

    def toggle_dock(self, show):
        """Show or hide the dock immediately"""
        if show:
            if self.is_hidden:
                self.is_hidden = False
                self.wrapper.add_style_class("show-dock")
                self.wrapper.remove_style_class("hide-dock")
            if self.hide_id:
                GLib.source_remove(self.hide_id)
                self.hide_id = None
        else:
            if not self.is_hidden:
                self.is_hidden = True
                self.wrapper.add_style_class("hide-dock")
                self.wrapper.remove_style_class("show-dock")

    def delay_hide(self):
        """Schedule hiding after short delay"""
        if self.hide_id:
            GLib.source_remove(self.hide_id)
        self.hide_id = GLib.timeout_add(1000, self.hide_dock)

    def hide_dock(self):
        """Finalize hiding procedure"""
        self.toggle_dock(show=False)
        self.hide_id = None
        return False

    def check_hide(self, *args):
        """Determine if dock should auto-hide"""
        clients = self.get_clients()
        current_ws = self.get_workspace()
        ws_clients = [w for w in clients if w["workspace"]["id"] == current_ws]

        if not ws_clients:
            self.toggle_dock(show=True)
        elif any(not w.get("floating") and not w.get("fullscreen") for w in ws_clients):
            self.delay_hide()
        else:
            self.toggle_dock(show=True)

    def update_dock(self, *args):
        """Refresh dock contents and clear drag lock."""
        self.update_app_map()  # Update app map before creating buttons
        arranger_handler = getattr(self, "_arranger_handler", None)
        if arranger_handler:
            remove_handler(arranger_handler)
        clients = self.get_clients()
        
        # Create a mapping of window class to instances
        running_windows = {}
        for c in clients:
            # Try multiple identification methods in order of reliability
            window_id = None
            
            # Try initialClass first (most reliable)
            if class_name := c.get("initialClass", "").lower():
                window_id = class_name
                
            # Try class second (fallback)
            elif class_name := c.get("class", "").lower():
                window_id = class_name
                
            # Use title as last resort if both class identifiers are missing
            elif title := c.get("title", "").lower():
                # Extract app name from title (common format: "App Name - Document")
                possible_name = title.split(" - ")[0].strip()
                if possible_name and len(possible_name) > 1:  # Avoid single letter app names
                    window_id = possible_name
                else:
                    window_id = title  # Use full title if we can't extract a good name
            
            # Use generic identifier as absolute fallback
            if not window_id:
                window_id = "unknown-app"
                
            # Log window for debugging purposes
            logging.debug(f"Window detected: {window_id} (from {c.get('initialClass', '')}/{c.get('class', '')}/{c.get('title', '')})")
                
            # Add to running windows
            running_windows.setdefault(window_id, []).append(c)
        
        # Map pinned apps to their running instances
        pinned_buttons = []
        used_window_classes = set()  # Track which window classes we've already assigned
        
        for app_data in self.pinned:
            app = self.find_app(app_data)
            
            # Try to find running instances for this pinned app
            instances = []
            matched_class = None
            
            if app:
                # Try matching by window class with improved matching
                if app.window_class:
                    app_class = app.window_class.lower()
                    # First try direct match
                    if app_class in running_windows:
                        instances = running_windows[app_class]
                        matched_class = app_class
                    else:
                        # Try matching with window class variations and aliases
                        for class_name in running_windows.keys():
                            if self._classes_match(app_class, class_name):
                                instances = running_windows[class_name]
                                matched_class = class_name
                                break
                
                # If no instances found by window class, try by executable name
                if not instances and app.executable:
                    exe_base = app.executable.split('/')[-1].lower()
                    
                    # Try exact match first
                    for class_key in running_windows.keys():
                        if exe_base == class_key:
                            instances = running_windows[class_key]
                            matched_class = class_key
                            break
                    
                    # Then try fuzzy matching with executable
                    if not instances:
                        for class_key, class_instances in running_windows.items():
                            # Check if executable is a substring of class or vice versa
                            if exe_base in class_key or class_key in exe_base:
                                instances = class_instances
                                matched_class = class_key
                                break
                
                # Try app name as last resort
                if not instances and app.name:
                    app_name = app.name.lower()
                    
                    # Try exact match first
                    if app_name in running_windows:
                        instances = running_windows[app_name]
                        matched_class = app_name
                    else:
                        # Try fuzzy name matching
                        for class_key, class_instances in running_windows.items():
                            if app_name in class_key or class_key in app_name:
                                instances = class_instances
                                matched_class = class_key
                                break
                    
                # If we're using a dict app_data, try matching with its window_class
                if not instances and isinstance(app_data, dict) and "window_class" in app_data and app_data["window_class"] is not None:
                    dict_class = app_data["window_class"].lower()
                    
                    # Try exact match first
                    if dict_class in running_windows:
                        instances = running_windows[dict_class]
                        matched_class = dict_class
                    else:
                        # Try matching with improved window class matching
                        for class_key in running_windows.keys():
                            if self._classes_match(dict_class, class_key):
                                instances = running_windows[class_key]
                                matched_class = class_key
                                break
            
            # Mark the matched class as used
            if matched_class:
                used_window_classes.add(matched_class)
            
            # Create button for this pinned app with any found instances
            pinned_buttons.append(self.create_button(app_data, instances))
        
        # For any remaining window classes that aren't assigned to pinned apps
        open_buttons = []
        for class_name, instances in running_windows.items():
            if class_name not in used_window_classes:
                # Check if this window class matches any known alias
                skip = False
                for base_class, aliases in self.window_class_aliases.items():
                    if class_name in aliases:
                        # Skip if this is an alias that might be handled elsewhere
                        norm_class = self._normalize_window_class(class_name)
                        if norm_class in used_window_classes or base_class in used_window_classes:
                            skip = True
                            break
                            
                if skip:
                    continue
                            
                # Try to find a proper app identifier for this window class
                app = self.app_identifiers.get(class_name)
                identifier = app.name if app else class_name
                open_buttons.append(self.create_button(identifier, instances))

        # Assemble dock layout
        children = pinned_buttons
        if pinned_buttons and open_buttons:
            children += [Box(orientation="v", v_expand=True, name="dock-separator")]
        children += open_buttons
        
        self.view.children = children
        idle_add(self._update_size)
        self._drag_in_progress = False  # Clear the drag lock

    def _update_size(self):
        """Update window size based on content"""
        width, _ = self.view.get_preferred_width()
        self.set_size_request(width, -1)
        return False

    def get_clients(self):
        """Get current client list"""
        try:
            return json.loads(self.conn.send_command("j/clients").reply.decode())
        except json.JSONDecodeError:
            return []

    def get_focused(self):
        """Get focused window address"""
        try:
            return json.loads(
                self.conn.send_command("j/activewindow").reply.decode()
            ).get("address", "")
        except json.JSONDecodeError:
            return ""

    def get_workspace(self):
        """Get current workspace ID"""
        try:
            return json.loads(
                self.conn.send_command("j/activeworkspace").reply.decode()
            ).get("id", 0)
        except json.JSONDecodeError:
            return 0

    def check_occlusion_state(self):
        """Periodic occlusion check"""
        # Skip occlusion check if hovered or dragging an icon
        if self.is_hovered or self._drag_in_progress:
            self.wrapper.remove_style_class("occluded")
            return True
        occlusion_region = (0, data.CURRENT_HEIGHT - 80, data.CURRENT_WIDTH, 80)
        if check_occlusion(occlusion_region) or not self.view.get_children():
            self.wrapper.add_style_class("occluded")
        else:
            self.wrapper.remove_style_class("occluded")
        return True

    def _find_drag_target(self, widget):
        """Find valid drag target in viewport"""
        children = self.view.get_children()
        while widget is not None and widget not in children:
            widget = widget.get_parent() if hasattr(widget, "get_parent") else None
        return widget

    def on_drag_data_get(self, widget, drag_context, data, info, time):
        """Handle drag start"""
        target = self._find_drag_target(widget.get_parent() if isinstance(widget, Box) else widget)
        if target is not None:
            index = self.view.get_children().index(target)
            data.set_text(str(index), -1)

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        """Handle drop event"""
        target = self._find_drag_target(widget.get_parent() if isinstance(widget, Box) else widget)
        if target is None:
            return
        try:
            source_index = int(data.get_text())
        except (TypeError, ValueError):
            return

        children = self.view.get_children()
        try:
            target_index = children.index(target)
        except ValueError:
            return

        if source_index != target_index:
            child = children.pop(source_index)
            children.insert(target_index, child)
            self.view.children = children  # Update view immediately
            self.update_pinned_apps(skip_update=True)  # Skip dock update to avoid recursive updates

    def on_drag_end(self, widget, drag_context):
        """Handles drag end, for unpinning and closing apps."""
        # If a drag is already in progress, ignore duplicate calls.
        if not self._drag_in_progress:
            return

        def process_drag_end():
            """Inner function to handle drag end, safe to call with idle_add."""
            if self.get_mapped():  # Check if the window is mapped
                # Get window geometry *before* any modifications
                display = Gdk.Display.get_default()
                _, x, y, _ = display.get_pointer()  # Get pointer relative to the screen
                window = self.get_window()
                if window:  # Check if we got a window
                    win_x, win_y, width, height = window.get_geometry()
                    if not (win_x <= x <= win_x + width and win_y <= y <= win_y + height):
                        # Drag ended outside the dock - get app data from the button
                        app_id = widget.app_identifier
                        instances = widget.instances
                        
                        # Find this app in pinned list
                        app_index = -1
                        for i, pinned_app in enumerate(self.pinned):
                            # Match by identifier
                            if pinned_app == app_id:
                                app_index = i
                                break
                            # For dict format, match by name
                            elif isinstance(pinned_app, dict) and isinstance(app_id, dict):
                                if pinned_app.get("name") == app_id.get("name"):
                                    app_index = i
                                    break
                                    
                        # If it's a pinned app, remove from pinned
                        if app_index >= 0:
                            self.pinned.pop(app_index)
                            self.config["pinned_apps"] = self.pinned
                            self.update_pinned_apps_file()
                            self.update_dock()  # Update dock after file save
                        elif instances: # Close if running and unpinned
                            # Close running app (if not pinned)
                            address = instances[0].get("address")
                            if address:
                                exec_shell_command(f"hyprctl dispatch closewindow address:{address}")
                                self.update_dock()  # Update dock after closing window
            self._drag_in_progress = False  # Clear the drag lock

        GLib.idle_add(process_drag_end)  # Deferred execution with idle_add

    def check_config_change(self):
        """Check if the config file has been modified."""
        new_config = read_config()
        if new_config.get("pinned_apps", []) != self.config.get("pinned_apps", []):
            self.config = new_config
            self.pinned = self.config.get("pinned_apps", [])
            self.update_app_map()  # Update app_map when config changes
            self.update_dock()
        return True  # Continue the timeout

    def update_pinned_apps_file(self):
        """Writes the updated pinned apps list to dock.json"""
        config_path = get_relative_path("../config/dock.json")
        try:
            with open(config_path, "w") as file:
                json.dump(self.config, file, indent=4)
            return True
        except Exception as e:
            logging.error(f"Failed to write dock config: {e}")
            return False

    def update_pinned_apps(self, skip_update=False):
        """Update pinned apps configuration by collecting all items before the separator"""
        pinned_children = []
        for child in self.view.get_children():
            if child.get_name() == "dock-separator":
                break  # Stop at separator
            
            # Use stored app identifier from the button
            if hasattr(child, "app_identifier"):
                # If the button has a desktop_app, use it to create comprehensive data
                if hasattr(child, "desktop_app") and child.desktop_app:
                    app = child.desktop_app
                    app_data = {
                        "name": app.name,
                        "display_name": app.display_name,
                        "window_class": app.window_class,
                        "executable": app.executable,
                        "command_line": app.command_line
                    }
                    pinned_children.append(app_data)
                else:
                    # Keep existing app_identifier (might be dict or string)
                    pinned_children.append(child.app_identifier)

        # Directly update both config and local pinned list
        self.config["pinned_apps"] = pinned_children
        self.pinned = pinned_children  # Update local state immediately

        # Write to file first to ensure persistence
        file_updated = self.update_pinned_apps_file()
        
        # Only update the dock if needed and file was successfully written
        if file_updated and not skip_update:
            self.update_dock()  # Refresh dock only after file is saved

    # Static method to update all dock instances
    @staticmethod
    def notify_config_change():
        """Notify all dock instances to reload their configuration immediately."""
        for dock in Dock._instances:
            # Use idle_add to avoid potential issues with direct calls
            GLib.idle_add(dock.check_config_change_immediate)
            
    def check_config_change_immediate(self):
        """Immediately check for configuration changes and update if needed."""
        new_config = read_config()
        if new_config.get("pinned_apps", []) != self.config.get("pinned_apps", []):
            self.config = new_config
            self.pinned = self.config.get("pinned_apps", [])
            self.update_app_map()
            self.update_dock()
        return False  # Don't repeat
