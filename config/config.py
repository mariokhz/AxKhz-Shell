import os
import shutil
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import toml
from PIL import Image
import subprocess
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from config.data import (
    APP_NAME, APP_NAME_CAP, CONFIG_DIR, HOME_DIR, WALLPAPERS_DIR_DEFAULT
)
from fabric.utils.helpers import get_relative_path
from gi.repository import GdkPixbuf

SOURCE_STRING = f"""
# {APP_NAME_CAP}
source = ~/.config/{APP_NAME_CAP}/config/hypr/{APP_NAME}.conf
"""

# Initialize bind_vars with default values
DEFAULTS = {
    'prefix_restart': "SUPER ALT",
    'suffix_restart': "B",
    'prefix_axmsg': "SUPER",
    'suffix_axmsg': "A",
    'prefix_dash': "SUPER",
    'suffix_dash': "D",
    'prefix_bluetooth': "SUPER",
    'suffix_bluetooth': "B",
    'prefix_pins': "SUPER",
    'suffix_pins': "Q",
    'prefix_kanban': "SUPER",
    'suffix_kanban': "N",
    'prefix_launcher': "SUPER",
    'suffix_launcher': "R",
    'prefix_tmux': "SUPER",
    'suffix_tmux': "T",
    'prefix_toolbox': "SUPER",
    'suffix_toolbox': "S",
    'prefix_overview': "SUPER",
    'suffix_overview': "TAB",
    'prefix_wallpapers': "SUPER",
    'suffix_wallpapers': "COMMA",
    'prefix_emoji': "SUPER",
    'suffix_emoji': "PERIOD",
    'prefix_power': "SUPER",
    'suffix_power': "ESCAPE",
    'prefix_toggle': "SUPER CTRL",
    'suffix_toggle': "B",
    'prefix_css': "SUPER SHIFT",
    'suffix_css': "B",
    'wallpapers_dir': WALLPAPERS_DIR_DEFAULT,
    'prefix_restart_inspector': "SUPER CTRL ALT",
    'suffix_restart_inspector': "B",
    'vertical': False,  # New default for vertical layout
    'centered_bar': False,  # New default for centered bar option
    'terminal_command': "kitty -e",  # Default terminal command for tmux
    'dock_enabled': True,  # Default value for dock visibility
    'dock_icon_size': 28,  # Default dock icon size
}

bind_vars = DEFAULTS.copy()


def deep_update(target: dict, update: dict) -> dict:
    """
    Recursively update a nested dictionary with values from another dictionary.
    """
    for key, value in update.items():
        if isinstance(value, dict):
            target[key] = deep_update(target.get(key, {}), value)
        else:
            target[key] = value
    return target


def ensure_matugen_config():
    """
    Ensure that the matugen configuration file exists and is updated
    with the expected settings.
    """
    expected_config = {
        'config': {
            'reload_apps': True,
            'wallpaper': {
                'command': 'swww',
                'arguments': [
                    'img', '-t', 'outer',
                    '--transition-duration', '1.5',
                    '--transition-step', '255',
                    '--transition-fps', '60',
                    '-f', 'Nearest'
                ],
                'set': True
            },
            'custom_colors': {
                'red': {
                    'color': "#FF0000",
                    'blend': True
                },
                'green': {
                    'color': "#00FF00",
                    'blend': True
                },
                'yellow': {
                    'color': "#FFFF00",
                    'blend': True
                },
                'blue': {
                    'color': "#0000FF",
                    'blend': True
                },
                'magenta': {
                    'color': "#FF00FF",
                    'blend': True
                },
                'cyan': {
                    'color': "#00FFFF",
                    'blend': True
                },
                'white': {
                    'color': "#FFFFFF",
                    'blend': True
                }
            }
        },
        'templates': {
            'hyprland': {
                'input_path': f'~/.config/{APP_NAME_CAP}/config/matugen/templates/hyprland-colors.conf',
                'output_path': f'~/.config/{APP_NAME_CAP}/config/hypr/colors.conf'
            },
            f'{APP_NAME}': {
                'input_path': f'~/.config/{APP_NAME_CAP}/config/matugen/templates/{APP_NAME}.css',
                'output_path': f'~/.config/{APP_NAME_CAP}/styles/colors.css',
                'post_hook': f"fabric-cli exec {APP_NAME} 'app.set_css()' &"
            }
        }
    }

    config_path = os.path.expanduser('~/.config/matugen/config.toml')
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    # Load any existing configuration
    existing_config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            existing_config = toml.load(f)
        # Backup existing configuration
        shutil.copyfile(config_path, config_path + '.bak')

    # Merge configurations
    merged_config = deep_update(existing_config, expected_config)
    with open(config_path, 'w') as f:
        toml.dump(merged_config, f)

    # Expand paths for checking
    current_wall = os.path.expanduser("~/.current.wall")
    hypr_colors = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/config/hypr/colors.conf")
    css_colors = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/styles/colors.css")
    
    # Check if any of the required files are missing
    if not os.path.exists(current_wall) or not os.path.exists(hypr_colors) or not os.path.exists(css_colors):
        # Ensure the directories exist
        os.makedirs(os.path.dirname(hypr_colors), exist_ok=True)
        os.makedirs(os.path.dirname(css_colors), exist_ok=True)
        
        # Use the example wallpaper if no current wallpaper
        if not os.path.exists(current_wall):
            image_path = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/assets/wallpapers_example/example-1.jpg")
            # Create symlink to the example wallpaper if it doesn't exist already
            if os.path.exists(image_path) and not os.path.exists(current_wall):
                try:
                    os.symlink(image_path, current_wall)
                except FileExistsError:
                    os.remove(current_wall)
                    os.symlink(image_path, current_wall)
        else:
            # Use the existing wallpaper
            image_path = os.path.realpath(current_wall) if os.path.islink(current_wall) else current_wall
        
        # Run matugen to generate the color files
        print(f"Generating color theme from wallpaper: {image_path}")
        try:
            subprocess.run(["matugen", "image", image_path], check=True)
            print("Color theme generated successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error generating color theme: {e}")
        except FileNotFoundError:
            print("Error: matugen command not found. Please install matugen.")


def load_bind_vars():
    """
    Load saved key binding variables from JSON, if available.
    """
    config_json = os.path.expanduser(f'~/.config/{APP_NAME_CAP}/config/config.json')
    try:
        with open(config_json, 'r') as f:
            saved_vars = json.load(f)
            bind_vars.update(saved_vars)
    except FileNotFoundError:
        # Use default values if no saved config exists
        pass


def generate_hyprconf() -> str:
    """
    Generate the Hypr configuration string using the current bind_vars.
    """
    home = os.path.expanduser('~')
    return f"""exec-once = uwsm-app $(python {home}/.config/{APP_NAME_CAP}/main.py)
exec = pgrep -x "hypridle" > /dev/null || uwsm-app hypridle
exec = uwsm-app swww-daemon

$fabricSend = fabric-cli exec {APP_NAME}
$axMessage = notify-send "Axenide" "What are you doing?" -i "{home}/.config/{APP_NAME_CAP}/assets/ax.png" -a "Source Code" -A "Be patient. 🍙"

bind = {bind_vars['prefix_restart']}, {bind_vars['suffix_restart']}, exec, killall {APP_NAME}; uwsm-app $(python {home}/.config/{APP_NAME_CAP}/main.py) # Reload {APP_NAME_CAP} | Default: SUPER ALT + B
bind = {bind_vars['prefix_axmsg']}, {bind_vars['suffix_axmsg']}, exec, $axMessage # Message | Default: SUPER + A
bind = {bind_vars['prefix_dash']}, {bind_vars['suffix_dash']}, exec, $fabricSend 'notch.open_notch("dashboard")' # Dashboard | Default: SUPER + D
bind = {bind_vars['prefix_bluetooth']}, {bind_vars['suffix_bluetooth']}, exec, $fabricSend 'notch.open_notch("bluetooth")' # Bluetooth | Default: SUPER + B
bind = {bind_vars['prefix_pins']}, {bind_vars['suffix_pins']}, exec, $fabricSend 'notch.open_notch("pins")' # Pins | Default: SUPER + Q
bind = {bind_vars['prefix_kanban']}, {bind_vars['suffix_kanban']}, exec, $fabricSend 'notch.open_notch("kanban")' # Kanban | Default: SUPER + N
bind = {bind_vars['prefix_launcher']}, {bind_vars['suffix_launcher']}, exec, $fabricSend 'notch.open_notch("launcher")' # App Launcher | Default: SUPER + R
bind = {bind_vars['prefix_tmux']}, {bind_vars['suffix_tmux']}, exec, $fabricSend 'notch.open_notch("tmux")' # App Launcher | Default: SUPER + T
bind = {bind_vars['prefix_toolbox']}, {bind_vars['suffix_toolbox']}, exec, $fabricSend 'notch.open_notch("tools")' # Toolbox | Default: SUPER + S
bind = {bind_vars['prefix_overview']}, {bind_vars['suffix_overview']}, exec, $fabricSend 'notch.open_notch("overview")' # Overview | Default: SUPER + TAB
bind = {bind_vars['prefix_wallpapers']}, {bind_vars['suffix_wallpapers']}, exec, $fabricSend 'notch.open_notch("wallpapers")' # Wallpapers | Default: SUPER + COMMA
bind = {bind_vars['prefix_emoji']}, {bind_vars['suffix_emoji']}, exec, $fabricSend 'notch.open_notch("emoji")' # Emoji | Default: SUPER + PERIOD
bind = {bind_vars['prefix_power']}, {bind_vars['suffix_power']}, exec, $fabricSend 'notch.open_notch("power")' # Power Menu | Default: SUPER + ESCAPE
bind = {bind_vars['prefix_toggle']}, {bind_vars['suffix_toggle']}, exec, $fabricSend 'bar.toggle_hidden()' # Toggle Bar | Default: SUPER CTRL + B
bind = {bind_vars['prefix_toggle']}, {bind_vars['suffix_toggle']}, exec, $fabricSend 'notch.toggle_hidden()' # Toggle Notch | Default: SUPER CTRL + B
bind = {bind_vars['prefix_css']}, {bind_vars['suffix_css']}, exec, $fabricSend 'app.set_css()' # Reload CSS | Default: SUPER SHIFT + B
bind = {bind_vars['prefix_restart_inspector']}, {bind_vars['suffix_restart_inspector']}, exec, killall {APP_NAME}; uwsm-app $(GTK_DEBUG=interactive python {home}/.config/{APP_NAME_CAP}/main.py) # Restart with inspector | Default: SUPER CTRL ALT + B

# Wallpapers directory: {bind_vars['wallpapers_dir']}

source = {home}/.config/{APP_NAME_CAP}/config/hypr/colors.conf

layerrule = noanim, fabric

exec = cp $wallpaper ~/.current.wall

general {{
    col.active_border = 0xff$primary
    col.inactive_border = 0xff$surface
    gaps_in = 2
    gaps_out = 4
    border_size = 2
    layout = dwindle
}}

cursor {{
  no_warps=true
}}

decoration {{
    blur {{
        enabled = yes
        size = 5
        passes = 3
        new_optimizations = yes
        contrast = 1
        brightness = 1
    }}
    rounding = 14
    shadow {{
      enabled = true
      range = 10
      render_power = 2
      color = rgba(0, 0, 0, 0.25)
    }}
}}

animations {{
    enabled = yes
    bezier = myBezier, 0.4, 0, 0.2, 1
    animation = windows, 1, 2.5, myBezier, popin 80%
    animation = border, 1, 2.5, myBezier
    animation = fade, 1, 2.5, myBezier
    animation = workspaces, 1, 2.5, myBezier, {'slidefadevert' if bind_vars['vertical'] else 'slidefade'} 20%
}}
"""


def ensure_face_icon():
    """
    Ensure the face icon exists. If not, copy the default icon.
    """
    face_icon_path = os.path.expanduser("~/.face.icon")
    default_icon_path = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/assets/default.png")
    if not os.path.exists(face_icon_path) and os.path.exists(default_icon_path):
        shutil.copy(default_icon_path, face_icon_path)


def backup_and_replace(src: str, dest: str, config_name: str):
    """
    Backup the existing configuration file and replace it with a new one.
    """
    if os.path.exists(dest):
        backup_path = dest + ".bak"
        shutil.copy(dest, backup_path)
        print(f"{config_name} config backed up to {backup_path}")
    shutil.copy(src, dest)
    print(f"{config_name} config replaced from {src}")


class HyprConfGUI(Gtk.Window):
    def __init__(self, show_lock_checkbox: bool, show_idle_checkbox: bool):
        super().__init__(title="Ax-Shell Settings")
        self.set_border_width(10)
        self.set_default_size(500, 550)
        self.set_resizable(False)

        self.selected_face_icon = None
        self.show_lock_checkbox = show_lock_checkbox
        self.show_idle_checkbox = show_idle_checkbox

        # Main vertical box to contain the notebook and buttons
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)

        # Create notebook for tabs
        notebook = Gtk.Notebook()
        notebook.set_margin_top(5)
        notebook.set_margin_bottom(10)
        main_box.pack_start(notebook, True, True, 0)

        # Create tabs
        key_bindings_tab = self.create_key_bindings_tab()
        notebook.append_page(key_bindings_tab, Gtk.Label(label="Key Bindings"))

        appearance_tab = self.create_appearance_tab()
        notebook.append_page(appearance_tab, Gtk.Label(label="Appearance"))

        system_tab = self.create_system_tab()
        notebook.append_page(system_tab, Gtk.Label(label="System"))

        # Button box for Close and Accept buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)

        reset_btn = Gtk.Button(label="Reset to Defaults")
        reset_btn.connect("clicked", self.on_reset)
        button_box.pack_start(reset_btn, False, False, 0)

        cancel_btn = Gtk.Button(label="Close")
        cancel_btn.connect("clicked", self.on_cancel)
        button_box.pack_start(cancel_btn, False, False, 0)

        accept_btn = Gtk.Button(label="Accept")
        accept_btn.connect("clicked", self.on_accept)
        button_box.pack_start(accept_btn, False, False, 0)

        main_box.pack_start(button_box, False, False, 0)

    def create_key_bindings_tab(self):
        """Create tab for key bindings configuration."""
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_start(15)
        grid.set_margin_end(15)
        scrolled_window.add(grid)

        # Create labels for columns
        action_label = Gtk.Label()
        action_label.set_markup("<b>Action</b>")
        action_label.set_halign(Gtk.Align.START)
        action_label.set_margin_bottom(5)
        action_label.get_style_context().add_class("heading")

        modifier_label = Gtk.Label()
        modifier_label.set_markup("<b>Modifier</b>")
        modifier_label.set_halign(Gtk.Align.START)
        modifier_label.set_margin_bottom(5)
        modifier_label.get_style_context().add_class("heading")

        key_label = Gtk.Label()
        key_label.set_markup("<b>Key</b>")
        key_label.set_halign(Gtk.Align.START)
        key_label.set_margin_bottom(5)
        key_label.get_style_context().add_class("heading")

        grid.attach(action_label, 0, 1, 1, 1)
        grid.attach(modifier_label, 1, 1, 1, 1) 
        grid.attach(key_label, 3, 1, 1, 1)

        self.entries = []
        bindings = [
            (f"Reload {APP_NAME_CAP}", 'prefix_restart', 'suffix_restart'),
            ("Message", 'prefix_axmsg', 'suffix_axmsg'),
            ("Dashboard", 'prefix_dash', 'suffix_dash'),
            ("Bluetooth", 'prefix_bluetooth', 'suffix_bluetooth'),
            ("Pins", 'prefix_pins', 'suffix_pins'),
            ("Kanban", 'prefix_kanban', 'suffix_kanban'),
            ("App Launcher", 'prefix_launcher', 'suffix_launcher'),
            ("Tmux", 'prefix_tmux', 'suffix_tmux'),
            ("Toolbox", 'prefix_toolbox', 'suffix_toolbox'),
            ("Overview", 'prefix_overview', 'suffix_overview'),
            ("Wallpapers", 'prefix_wallpapers', 'suffix_wallpapers'),
            ("Emoji Picker", 'prefix_emoji', 'suffix_emoji'),
            ("Power Menu", 'prefix_power', 'suffix_power'),
            ("Toggle Bar and Notch", 'prefix_toggle', 'suffix_toggle'),
            ("Reload CSS", 'prefix_css', 'suffix_css'),
            ("Restart with inspector", 'prefix_restart_inspector', 'suffix_restart_inspector'),
        ]

        # Populate grid with key binding rows, starting at row 2
        row = 2
        for label_text, prefix_key, suffix_key in bindings:
            # Binding description
            binding_label = Gtk.Label(label=label_text)
            binding_label.set_halign(Gtk.Align.START)
            grid.attach(binding_label, 0, row, 1, 1)

            # Prefix entry
            prefix_entry = Gtk.Entry()
            prefix_entry.set_text(bind_vars[prefix_key])
            grid.attach(prefix_entry, 1, row, 1, 1)

            # Plus label between entries
            plus_label = Gtk.Label(label=" + ")
            grid.attach(plus_label, 2, row, 1, 1)

            # Suffix entry
            suffix_entry = Gtk.Entry()
            suffix_entry.set_text(bind_vars[suffix_key])
            grid.attach(suffix_entry, 3, row, 1, 1)

            self.entries.append((prefix_key, suffix_key, prefix_entry, suffix_entry))
            row += 1

        return scrolled_window

    def create_appearance_tab(self):
        """Create tab for appearance settings with a compact grid layout."""
        # Create a scrolled window container
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Create a grid for more efficient space usage
        grid = Gtk.Grid()
        grid.set_column_spacing(20)
        grid.set_row_spacing(15)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_start(15)
        grid.set_margin_end(15)
        
        # Current row for positioning
        row = 0
        
        # === WALLPAPERS SECTION (LEFT COLUMN) ===
        wall_header = Gtk.Label()
        wall_header.set_markup("<b>Wallpapers</b>")
        wall_header.set_halign(Gtk.Align.START)
        grid.attach(wall_header, 0, row, 1, 1)
        
        # === PROFILE ICON SECTION (RIGHT COLUMN) ===
        face_header = Gtk.Label()
        face_header.set_markup("<b>Profile Icon</b>")
        face_header.set_halign(Gtk.Align.START)
        grid.attach(face_header, 1, row, 1, 1)
        row += 1
        
        # Wallpaper directory selection
        wall_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        wall_box.set_margin_start(10)
        wall_box.set_margin_top(5)
        
        wall_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        wall_label = Gtk.Label(label="Directory:")
        wall_label.set_halign(Gtk.Align.START)
        self.wall_dir_chooser = Gtk.FileChooserButton(
            title="Select a folder",
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        self.wall_dir_chooser.set_tooltip_text("Select the directory containing your wallpaper images")
        self.wall_dir_chooser.set_filename(bind_vars['wallpapers_dir'])
        wall_hbox.pack_start(wall_label, False, False, 0)
        wall_hbox.pack_start(self.wall_dir_chooser, True, True, 0)
        wall_box.pack_start(wall_hbox, False, False, 0)
        
        grid.attach(wall_box, 0, row, 1, 1)
        
        # Profile icon selection
        face_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        face_box.set_margin_start(10)
        face_box.set_margin_top(5)
        
        # Current icon display and selection in horizontal layout
        face_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Current icon display
        current_face = os.path.expanduser("~/.face.icon")
        face_image_frame = Gtk.Frame()
        face_image_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        face_image = Gtk.Image()
        try:
            if (os.path.exists(current_face)):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(current_face)
                pixbuf = pixbuf.scale_simple(64, 64, GdkPixbuf.InterpType.BILINEAR)  # Smaller icon
            else:
                pixbuf = Gtk.IconTheme.get_default().load_icon("user-info", 64, 0)  # Smaller icon
            face_image.set_from_pixbuf(pixbuf)
        except Exception:
            face_image.set_from_icon_name("user-info", Gtk.IconSize.DIALOG)
        
        face_image_frame.add(face_image)
        face_hbox.pack_start(face_image_frame, False, False, 0)
        
        # Selection button alongside the image
        face_controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        face_btn = Gtk.Button(label="Browse...")
        face_btn.set_tooltip_text("Select a square image for your profile icon")
        face_btn.connect("clicked", self.on_select_face_icon)
        face_controls.pack_start(face_btn, False, False, 0)
        
        self.face_status_label = Gtk.Label(label="")
        self.face_status_label.set_halign(Gtk.Align.START)
        face_controls.pack_start(self.face_status_label, False, False, 0)
        
        face_hbox.pack_start(face_controls, True, True, 10)
        face_box.pack_start(face_hbox, False, False, 0)
        
        grid.attach(face_box, 1, row, 1, 1)
        row += 1
        
        # === LAYOUT OPTIONS SECTION ===
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(5)
        separator.set_margin_bottom(5)
        grid.attach(separator, 0, row, 2, 1)  # Span both columns
        row += 1
        
        layout_header = Gtk.Label()
        layout_header.set_markup("<b>Layout Options</b>")
        layout_header.set_halign(Gtk.Align.START)
        grid.attach(layout_header, 0, row, 2, 1)  # Span both columns
        row += 1
        
        # Create a 2-column grid for the layout options
        layout_grid = Gtk.Grid()
        layout_grid.set_column_spacing(20)
        layout_grid.set_row_spacing(10)
        layout_grid.set_margin_start(10)
        
        # Vertical layout (left column)
        vertical_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vertical_label = Gtk.Label(label="Vertical Layout")
        vertical_label.set_halign(Gtk.Align.START)
        self.vertical_switch = Gtk.Switch()
        self.vertical_switch.set_active(bind_vars.get('vertical', False))
        self.vertical_switch.connect("notify::active", self.on_vertical_changed)
        vertical_box.pack_start(vertical_label, True, True, 0)
        vertical_box.pack_end(self.vertical_switch, False, False, 0)
        layout_grid.attach(vertical_box, 0, 0, 1, 1)
        
        # Centered bar (right column)
        centered_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        centered_label = Gtk.Label(label="Centered Bar (Vertical Only)")
        centered_label.set_halign(Gtk.Align.START)
        self.centered_switch = Gtk.Switch()
        self.centered_switch.set_active(bind_vars.get('centered_bar', False))
        self.centered_switch.set_sensitive(self.vertical_switch.get_active())
        centered_box.pack_start(centered_label, True, True, 0)
        centered_box.pack_end(self.centered_switch, False, False, 0)
        layout_grid.attach(centered_box, 1, 0, 1, 1)
        
        # Show dock (left column, second row)
        dock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dock_label = Gtk.Label(label="Show Dock")
        dock_label.set_halign(Gtk.Align.START)
        self.dock_switch = Gtk.Switch()
        self.dock_switch.set_active(bind_vars.get('dock_enabled', True))
        self.dock_switch.connect("notify::active", self.on_dock_enabled_changed)
        dock_box.pack_start(dock_label, True, True, 0)
        dock_box.pack_end(self.dock_switch, False, False, 0)
        layout_grid.attach(dock_box, 0, 1, 1, 1)
        
        # Dock always occluded (show on hover only) (right column, second row)
        dock_hover_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dock_hover_label = Gtk.Label(label="Show Dock Only on Hover")
        dock_hover_label.set_halign(Gtk.Align.START)
        self.dock_hover_switch = Gtk.Switch()
        self.dock_hover_switch.set_active(bind_vars.get('dock_always_occluded', False))
        self.dock_hover_switch.set_sensitive(self.dock_switch.get_active())
        dock_hover_box.pack_start(dock_hover_label, True, True, 0)
        dock_hover_box.pack_end(self.dock_hover_switch, False, False, 0)
        layout_grid.attach(dock_hover_box, 1, 1, 1, 1)
        
        # Add dock icon size slider (new)
        dock_size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dock_size_label = Gtk.Label(label="Dock Icon Size")
        dock_size_label.set_halign(Gtk.Align.START)
        
        # Create a scale/slider for icon size
        self.dock_size_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 16, 48, 2)
        self.dock_size_scale.set_value(bind_vars.get('dock_icon_size', 28))
        self.dock_size_scale.set_draw_value(True)
        self.dock_size_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.dock_size_scale.set_size_request(100, -1)
        
        dock_size_box.pack_start(dock_size_label, True, True, 0)
        dock_size_box.pack_end(self.dock_size_scale, True, True, 0)
        layout_grid.attach(dock_size_box, 0, 2, 2, 1)  # Span both columns
        
        grid.attach(layout_grid, 0, row, 2, 1)  # Span both columns
        row += 1
        
        # === BAR COMPONENTS SECTION ===
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator2.set_margin_top(5)
        separator2.set_margin_bottom(5)
        grid.attach(separator2, 0, row, 2, 1)  # Span both columns
        row += 1
        
        # Use an expander to save vertical space
        components_expander = Gtk.Expander(label="Bar Components")
        components_expander.set_expanded(False)  # Collapsed by default
        
        components_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        components_box.set_margin_start(10)
        components_box.set_margin_top(5)
        
        # Create switches for each component using a grid to save space
        self.component_switches = {}
        component_display_names = {
            'button_apps': "App Launcher Button",
            'systray': "System Tray",
            'control': "Control Panel",
            'network': "Network Applet",
            'button_tools': "Toolbox Button",
            'button_overview': "Overview Button",
            'ws_container': "Workspaces",
            'weather': "Weather Widget",
            'battery': "Battery Indicator",
            'metrics': "System Metrics",
            'language': "Language Indicator",
            'date_time': "Date & Time",
            'button_power': "Power Button",
        }
        
        # Create a grid for component switches - 2 columns
        comp_grid = Gtk.Grid()
        comp_grid.set_column_spacing(20)
        comp_grid.set_row_spacing(8)
        
        # Split the components into left and right columns
        components_list = list(component_display_names.items())
        left_components = components_list[:len(components_list)//2 + len(components_list)%2]
        right_components = components_list[len(components_list)//2 + len(components_list)%2:]
        
        # Add components to left column
        for i, (component_name, display_name) in enumerate(left_components):
            component_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            component_label = Gtk.Label(label=display_name)
            component_label.set_halign(Gtk.Align.START)
            component_switch = Gtk.Switch()
            config_key = f'bar_{component_name}_visible'
            component_switch.set_active(bind_vars.get(config_key, True))
            component_box.pack_start(component_label, True, True, 0)
            component_box.pack_end(component_switch, False, False, 0)
            comp_grid.attach(component_box, 0, i, 1, 1)
            self.component_switches[component_name] = component_switch
            
        # Add components to right column
        for i, (component_name, display_name) in enumerate(right_components):
            component_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            component_label = Gtk.Label(label=display_name)
            component_label.set_halign(Gtk.Align.START)
            component_switch = Gtk.Switch()
            config_key = f'bar_{component_name}_visible'
            component_switch.set_active(bind_vars.get(config_key, True))
            component_box.pack_start(component_label, True, True, 0)
            component_box.pack_end(component_switch, False, False, 0)
            comp_grid.attach(component_box, 1, i, 1, 1)
            self.component_switches[component_name] = component_switch
        
        components_box.pack_start(comp_grid, True, True, 0)
        components_expander.add(components_box)
        grid.attach(components_expander, 0, row, 2, 1)  # Span both columns
        
        scrolled_window.add(grid)
        return scrolled_window

    def on_vertical_changed(self, switch, gparam):
        """Update centered_bar sensitivity based on vertical mode"""
        self.centered_switch.set_sensitive(switch.get_active())
        if not switch.get_active():
            self.centered_switch.set_active(False)  # Turn off centered_bar if vertical is disabled

    def on_dock_enabled_changed(self, switch, gparam):
        """Update dock hover switch sensitivity based on dock enabled state"""
        self.dock_hover_switch.set_sensitive(switch.get_active())
        if not switch.get_active():
            self.dock_hover_switch.set_active(False)  # Turn off hover-only if dock is disabled

    def create_system_tab(self):
        """Create tab for system configurations with a more compact layout."""
        # Create a grid layout instead of vertical box
        grid = Gtk.Grid()
        grid.set_column_spacing(20)
        grid.set_row_spacing(15)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_start(15)
        grid.set_margin_end(15)
        
        # Current row for positioning
        row = 0
        
        # === TERMINAL SETTINGS (LEFT COLUMN) ===
        terminal_header = Gtk.Label()
        terminal_header.set_markup("<b>Terminal Settings</b>")
        terminal_header.set_halign(Gtk.Align.START)
        grid.attach(terminal_header, 0, row, 1, 1)
        row += 1
        
        terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        terminal_box.set_margin_start(10)
        terminal_box.set_margin_top(5)
        
        terminal_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        terminal_label = Gtk.Label(label="Command:")
        terminal_label.set_halign(Gtk.Align.START)
        self.terminal_entry = Gtk.Entry()
        self.terminal_entry.set_text(bind_vars['terminal_command'])
        self.terminal_entry.set_tooltip_text("Command used to launch terminal apps (e.g., 'kitty -e')")
        terminal_hbox.pack_start(terminal_label, False, False, 0)
        terminal_hbox.pack_start(self.terminal_entry, True, True, 0)
        terminal_box.pack_start(terminal_hbox, False, False, 0)
        
        hint_label = Gtk.Label()
        hint_label.set_markup("<small>Examples: 'kitty -e', 'alacritty -e', 'foot -e'</small>")
        hint_label.set_halign(Gtk.Align.START)
        terminal_box.pack_start(hint_label, False, False, 5)
        
        grid.attach(terminal_box, 0, row, 1, 1)
        
        # === HYPRLAND INTEGRATION (RIGHT COLUMN) ===
        hypr_header = Gtk.Label()
        hypr_header.set_markup("<b>Hyprland Integration</b>")
        hypr_header.set_halign(Gtk.Align.START)
        grid.attach(hypr_header, 1, row - 1, 1, 1)  # Same row as Terminal header
        
        hypr_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        hypr_box.set_margin_start(10)
        hypr_box.set_margin_top(5)
        
        # Hyprland locks and idle settings
        if self.show_lock_checkbox:
            lock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            lock_label = Gtk.Label(label="Replace Hyprlock config")
            lock_label.set_halign(Gtk.Align.START)
            self.lock_switch = Gtk.Switch()
            self.lock_switch.set_tooltip_text("Replace Hyprlock configuration with Ax-Shell's custom config")
            lock_box.pack_start(lock_label, True, True, 0)
            lock_box.pack_end(self.lock_switch, False, False, 0)
            hypr_box.pack_start(lock_box, False, False, 0)
        else:
            self.lock_switch = None

        if self.show_idle_checkbox:
            idle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            idle_label = Gtk.Label(label="Replace Hypridle config")
            idle_label.set_halign(Gtk.Align.START)
            self.idle_switch = Gtk.Switch()
            self.idle_switch.set_tooltip_text("Replace Hypridle configuration with Ax-Shell's custom config")
            idle_box.pack_start(idle_label, True, True, 0)
            idle_box.pack_end(self.idle_switch, False, False, 0)
            hypr_box.pack_start(idle_box, False, False, 0)
        else:
            self.idle_switch = None
            
        # Add note about config replacement if applicable
        if self.show_lock_checkbox or self.show_idle_checkbox:
            note_label = Gtk.Label()
            note_label.set_markup("<small>Existing configs will be backed up</small>")
            note_label.set_halign(Gtk.Align.START)
            hypr_box.pack_start(note_label, False, False, 0)

        grid.attach(hypr_box, 1, row, 1, 1)
        row += 1
        
        # === SUPPORT INFO ===
        support_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        support_box.set_margin_top(15)
        
        support_icon = Gtk.Image.new_from_icon_name("help-about", Gtk.IconSize.MENU)
        support_label = Gtk.Label()
        support_label.set_markup("<small>For help or to report issues, visit the <a href='https://github.com/Axenide/Ax-Shell'>GitHub repository</a></small>")
        support_box.pack_start(support_icon, False, False, 0)
        support_box.pack_start(support_label, False, False, 0)
        
        grid.attach(support_box, 0, row, 2, 1)  # Span both columns
        
        # Create a scrolled window to contain the grid
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(grid)
        
        return scrolled_window
    
    def on_select_face_icon(self, widget):
        """
        Open a file chooser dialog for selecting a new face icon image.
        """
        dialog = Gtk.FileChooserDialog(
            title="Select Face Icon",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
        )

        # Filter to allow image files only
        image_filter = Gtk.FileFilter()
        image_filter.set_name("Image files")
        image_filter.add_mime_type("image/png")
        image_filter.add_mime_type("image/jpeg")
        image_filter.add_pattern("*.png")
        image_filter.add_pattern("*.jpg")
        image_filter.add_pattern("*.jpeg")
        dialog.add_filter(image_filter)

        if dialog.run() == Gtk.ResponseType.OK:
            self.selected_face_icon = dialog.get_filename()
            self.face_status_label.set_text(f"Selected: {os.path.basename(self.selected_face_icon)}")
        dialog.destroy()

    def on_accept(self, widget):
        """
        Save the configuration and update the necessary files without closing the window.
        """
        # Update bind_vars from user inputs
        for prefix_key, suffix_key, prefix_entry, suffix_entry in self.entries:
            bind_vars[prefix_key] = prefix_entry.get_text()
            bind_vars[suffix_key] = suffix_entry.get_text()

        # Update wallpaper directory
        bind_vars['wallpapers_dir'] = self.wall_dir_chooser.get_filename()

        # Update vertical setting from the new switch
        bind_vars['vertical'] = self.vertical_switch.get_active()
        bind_vars['centered_bar'] = self.centered_switch.get_active()
        bind_vars['dock_enabled'] = self.dock_switch.get_active()
        bind_vars['dock_always_occluded'] = self.dock_hover_switch.get_active()
        bind_vars['dock_icon_size'] = int(self.dock_size_scale.get_value())
        
        # Update terminal command
        bind_vars['terminal_command'] = self.terminal_entry.get_text()
        
        # Update component visibility settings
        for component_name, switch in self.component_switches.items():
            config_key = f'bar_{component_name}_visible'
            bind_vars[config_key] = switch.get_active()

        # Save the updated bind_vars to a JSON file
        config_json = os.path.expanduser(f'~/.config/{APP_NAME_CAP}/config/config.json')
        os.makedirs(os.path.dirname(config_json), exist_ok=True)
        with open(config_json, 'w') as f:
            json.dump(bind_vars, f)

        # Process face icon if one was selected
        if self.selected_face_icon:
            try:
                img = Image.open(self.selected_face_icon)
                side = min(img.size)
                left = (img.width - side) / 2
                top = (img.height - side) / 2
                cropped_img = img.crop((left, top, left + side, top + side))
                cropped_img.save(os.path.expanduser("~/.face.icon"), format='PNG')
                print("Face icon saved.")
            except Exception as e:
                print("Error processing face icon:", e)

        # Replace hyprlock config if requested using the new switch
        if self.lock_switch and self.lock_switch.get_active():
            src_lock = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/config/hypr/hyprlock.conf")
            dest_lock = os.path.expanduser("~/.config/hypr/hyprlock.conf")
            backup_and_replace(src_lock, dest_lock, "Hyprlock")

        # Replace hypridle config if requested using the new switch
        if self.idle_switch and self.idle_switch.get_active():
            src_idle = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/config/hypr/hypridle.conf")
            dest_idle = os.path.expanduser("~/.config/hypr/hypridle.conf")
            backup_and_replace(src_idle, dest_idle, "Hypridle")

        # Append the source string to the Hyprland config if not present
        hyprland_config_path = os.path.expanduser("~/.config/hypr/hyprland.conf")
        with open(hyprland_config_path, "r") as f:
            content = f.read()
        if (SOURCE_STRING not in content):
            with open(hyprland_config_path, "a") as f:
                f.write(SOURCE_STRING)

        # Update configuration
        start_config()
        
        # First prepare the restart command to be executed in background
        restart_script = f"""#!/bin/bash
killall {APP_NAME} 2>/dev/null
python_output=$(python {os.path.expanduser(f"~/.config/{APP_NAME_CAP}/main.py")})
uwsm-app "$python_output" &
"""
        
        # Create a temporary script file
        restart_path = "/tmp/ax_shell_restart.sh"
        with open(restart_path, "w") as f:
            f.write(restart_script)
        os.chmod(restart_path, 0o755)
        
        # Start the script in the background
        subprocess.Popen(["/bin/bash", restart_path], 
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True)
        
        # Removed confirmation dialog to make the interface cleaner
        
        # The window remains open - don't call Gtk.main_quit()

    def on_reset(self, widget):
        """
        Reset all settings to default values.
        """
        # Ask for confirmation
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Reset all settings to defaults?"
        )
        dialog.format_secondary_text("This will reset all keybindings and other settings to their default values.")
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Reset bind_vars to default values
            global bind_vars
            bind_vars = DEFAULTS.copy()
            
            # Update UI elements
            # Update key binding entries
            for prefix_key, suffix_key, prefix_entry, suffix_entry in self.entries:
                prefix_entry.set_text(bind_vars[prefix_key])
                suffix_entry.set_text(bind_vars[suffix_key])
            
            # Update wallpaper directory chooser
            self.wall_dir_chooser.set_filename(bind_vars['wallpapers_dir'])
            
            # Update vertical switch
            self.vertical_switch.set_active(bind_vars.get('vertical', False))
            self.centered_switch.set_active(bind_vars.get('centered_bar', False))
            self.centered_switch.set_sensitive(self.vertical_switch.get_active())
            self.dock_switch.set_active(bind_vars.get('dock_enabled', True))
            self.dock_hover_switch.set_active(bind_vars.get('dock_always_occluded', False))
            self.dock_hover_switch.set_sensitive(self.dock_switch.get_active())
            self.dock_size_scale.set_value(bind_vars.get('dock_icon_size', 28))
            
            # Update terminal command entry
            self.terminal_entry.set_text(bind_vars['terminal_command'])
            
            # Clear face icon selection status
            self.selected_face_icon = None
            self.face_status_label.set_text("")

    def on_cancel(self, widget):
        self.destroy()


def start_config():
    """
    Run final configuration steps: ensure necessary configs, write the hyprconf, and reload.
    """
    ensure_matugen_config()
    ensure_face_icon()

    # Write the generated hypr configuration to file
    hypr_config_dir = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/config/hypr/")
    os.makedirs(hypr_config_dir, exist_ok=True)
    hypr_conf_path = os.path.join(hypr_config_dir, f"{APP_NAME}.conf")
    with open(hypr_conf_path, "w") as f:
        f.write(generate_hyprconf())

    # Reload Hyprland configuration using subprocess.run instead of os.system
    subprocess.run(["hyprctl", "reload"])


def open_config():
    """
    Entry point for opening the configuration GUI.
    """
    load_bind_vars()

    # Check and copy hyprlock config if needed
    dest_lock = os.path.expanduser("~/.config/hypr/hyprlock.conf")
    src_lock = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/config/hypr/hyprlock.conf")
    os.makedirs(os.path.dirname(dest_lock), exist_ok=True)
    show_lock_checkbox = True
    if not os.path.exists(dest_lock):
        shutil.copy(src_lock, dest_lock)
        show_lock_checkbox = False

    # Check and copy hypridle config if needed
    dest_idle = os.path.expanduser("~/.config/hypr/hypridle.conf")
    src_idle = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/config/hypr/hypridle.conf")
    show_idle_checkbox = True
    if not os.path.exists(dest_idle):
        shutil.copy(src_idle, dest_idle)
        show_idle_checkbox = False

    # Create and run the GUI
    window = HyprConfGUI(show_lock_checkbox, show_idle_checkbox)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    open_config()
