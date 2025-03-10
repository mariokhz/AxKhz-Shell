import json
from gi.repository import GLib, Gtk, Gdk
from utils.icon_resolver import IconResolver
from utils.occlusion import check_occlusion
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.image import Image
from fabric.widgets.eventbox import EventBox
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.hyprland.widgets import get_hyprland_connection
from fabric.utils import exec_shell_command, exec_shell_command_async, idle_add, remove_handler, get_relative_path

import config.data as data

def read_config():
    """Read and return the full configuration from the JSON file."""
    config_path = get_relative_path("../config/dock.json")
    with open(config_path, "r") as file:
        data = json.load(file)
    return data

class Dock(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="dock-window",
            layer="top",
            anchor="bottom center",
            margin="0 0 -4px 0",
            exclusivity="none",
            **kwargs,
        )
        self.config = read_config()
        self.conn = get_hyprland_connection()
        self.icon = IconResolver()
        self.pinned = self.config.get("pinned_apps", [])
        self.is_hidden = False
        self.hide_id = None
        self._arranger_handler = None
        self.is_hovered = False

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

        # Drag-and-drop setup
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
        if check_occlusion(occlusion_region):
            self.wrapper.add_style_class("occluded")
        return True

    # Add this new method to handle child widget hover
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
        """Refresh dock contents"""
        arranger_handler = getattr(self, "_arranger_handler", None)
        if arranger_handler:
            remove_handler(arranger_handler)
        clients = self.get_clients()
        running = {}
        for c in clients:
            key = c["initialClass"].lower()
            running.setdefault(key, []).append(c)
        pinned_buttons = [
            self.create_button(app, running.get(app.lower(), [])) for app in self.pinned
        ]
        open_buttons = [
            self.create_button(
                c["initialClass"], running.get(c["initialClass"].lower(), [])
            )
            for group in running.values()
            for c in group
            if c["initialClass"].lower() not in [p.lower() for p in self.pinned]
        ]
        children = pinned_buttons
        if pinned_buttons and open_buttons:
            children += [Box(orientation="v", v_expand=True, name="dock-separator")]
        children += open_buttons
        self.view.children = children
        idle_add(self._update_size)

    def _update_size(self):
        """Update window size based on content"""
        width, _ = self.view.get_preferred_width()
        self.set_size_request(width, -1)
        return False

    def create_button(self, app, instances):
        """Create dock application button"""
        icon_img = self.icon.get_icon_pixbuf(
            app.lower(), 36
        ) or self.icon.get_icon_pixbuf("image-missing", 36)
        items = [Image(pixbuf=icon_img)]
        
        button = Button(
            child=Box(
                name="dock-icon",
                orientation="v",
                h_align="center",
                children=items,
            ),
            on_clicked=lambda *a: self.handle_app(app, instances),
            tooltip_text=instances[0]["title"] if instances else app,
            name="dock-app-button",
        )
        
        if instances:
            button.add_style_class("instance")

        # Enable DnD for pinned apps
        if app.lower() in [p.lower() for p in self.pinned]:
            button.drag_source_set(
                Gdk.ModifierType.BUTTON1_MASK,
                [Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP, 0)],
                Gdk.DragAction.MOVE
            )
            button.drag_dest_set(
                Gtk.DestDefaults.ALL,
                [Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP, 0)],
                Gdk.DragAction.MOVE
            )
            button.connect("drag-data-get", self.on_drag_data_get)
            button.connect("drag-data-received", self.on_drag_data_received)
        
        button.connect("enter-notify-event", self._on_child_enter)
        return button

    def handle_app(self, app, instances):
        """Handle application button clicks"""
        if not instances:
            exec_shell_command_async(f"nohup {app}")
        else:
            focused = self.get_focused()
            idx = next(
                (i for i, inst in enumerate(instances) if inst["address"] == focused),
                -1,
            )
            next_inst = instances[(idx + 1) % len(instances)]
            exec_shell_command(
                f"hyprctl dispatch focuswindow address:{next_inst['address']}"
            )

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
        if self.is_hovered:
            return True  # Skip if hovered
        occlusion_region = (0, data.CURRENT_HEIGHT - 80, data.CURRENT_WIDTH, 80)
        if check_occlusion(occlusion_region):
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
            self.view.children = children
            self.update_pinned_apps()

    def update_pinned_apps(self):
        """Update pinned apps configuration"""
        self.config["pinned_apps"] = [
            child.get_tooltip_text() for child in self.view.get_children() if child.get_tooltip_text() in self.pinned
        ]
        config_path = get_relative_path("../config/dock.json")
        with open(config_path, "w") as file:
            json.dump(self.config, file, indent=4)
