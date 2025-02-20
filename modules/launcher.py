import operator
from collections.abc import Iterator
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.utils import DesktopApp, get_desktop_applications, idle_add, remove_handler
from fabric.widgets.image import Image
from gi.repository import GLib, Gdk
import modules.icons as icons

class AppLauncher(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="app-launcher",
            visible=False,
            all_visible=False,
            **kwargs,
        )

        self.notch = kwargs["notch"]
        self.selected_index = -1  # Track the selected item index

        self._arranger_handler: int = 0
        self._all_apps = get_desktop_applications()

        self.viewport = Box(name="viewport", spacing=4, orientation="v")
        self.search_entry = Entry(
            name="search-entry",
            placeholder="Search Applications...",
            h_expand=True,
            notify_text=lambda entry, *_: self.arrange_viewport(entry.get_text()),
            on_activate=lambda entry, *_: self.on_search_entry_activate(entry.get_text()),
            on_key_press_event=self.on_search_entry_key_press,  # Handle key presses
        )
        self.search_entry.props.xalign = 0.5
        self.scrolled_window = ScrolledWindow(
            name="scrolled-window",
            spacing=10,
            min_content_size=(450, 105),
            max_content_size=(450, 105),
            child=self.viewport,
        )

        self.header_box = Box(
            name="header_box",
            spacing=10,
            orientation="h",
            children=[
                self.search_entry,
                Button(
                    name="close-button",
                    child=Label(name="close-label", markup=icons.cancel),
                    tooltip_text="Exit",
                    on_clicked=lambda *_: self.close_launcher()
                ),
            ],
        )
        
        self.launcher_box = Box(
            name="launcher-box",
            spacing=10,
            h_expand=True,
            orientation="v",
            children=[
                self.header_box,
                self.scrolled_window,
            ],
        )

        self.resize_viewport()

        self.add(self.launcher_box)
        self.show_all()

    def close_launcher(self):
        self.viewport.children = []
        self.selected_index = -1  # Reset selection
        self.notch.close_notch()

    def open_launcher(self):
        self._all_apps = get_desktop_applications()
        self.arrange_viewport()

    def arrange_viewport(self, query: str = ""):
        remove_handler(self._arranger_handler) if self._arranger_handler else None
        self.viewport.children = []
        self.selected_index = -1  # Clear selection when viewport changes

        filtered_apps_iter = iter(
            sorted(
                [
                    app
                    for app in self._all_apps
                    if query.casefold()
                    in (
                        (app.display_name or "")
                        + (" " + app.name + " ")
                        + (app.generic_name or "")
                    ).casefold()
                ],
                key=lambda app: (app.display_name or "").casefold(),
            )
        )
        should_resize = operator.length_hint(filtered_apps_iter) == len(self._all_apps)

        self._arranger_handler = idle_add(
            lambda apps_iter: self.add_next_application(apps_iter) or self.handle_arrange_complete(should_resize, query),
            filtered_apps_iter,
            pin=True,
        )

    def handle_arrange_complete(self, should_resize, query):
        if should_resize:
            self.resize_viewport()
        # Only auto-select first item if query exists
        if query.strip() != "" and self.viewport.get_children():
            self.update_selection(0)
        return False

    def add_next_application(self, apps_iter: Iterator[DesktopApp]):
        if not (app := next(apps_iter, None)):
            return False
        self.viewport.add(self.bake_application_slot(app))
        return True

    def resize_viewport(self):
        self.scrolled_window.set_min_content_width(
            self.viewport.get_allocation().width  # type: ignore
        )
        return False

    def bake_application_slot(self, app: DesktopApp, **kwargs) -> Button:
        button = Button(
            name="app-slot-button",
            child=Box(
                name="app-slot-box",
                orientation="h",
                spacing=10,
                children=[
                    Image(
                        pixbuf=app.get_icon_pixbuf(size=32),
                        h_align="start",
                        name="launcher-app-icon",
                    ),
                    Label(
                        name="app-label",
                        label=app.display_name or "Unknown",
                        ellipsization="end",
                        v_align="center",
                        h_align="center",
                    ),
                ],
            ),
            tooltip_text=app.description,
            on_clicked=lambda *_: (app.launch(), self.close_launcher()),
            **kwargs,
        )
        return button

    def update_selection(self, new_index: int):
        # Unselect current
        if self.selected_index != -1 and self.selected_index < len(self.viewport.get_children()):
            current_button = self.viewport.get_children()[self.selected_index]
            current_button.get_style_context().remove_class("selected")
        # Select new
        if new_index != -1 and new_index < len(self.viewport.get_children()):
            new_button = self.viewport.get_children()[new_index]
            new_button.get_style_context().add_class("selected")
            self.selected_index = new_index
            self.scroll_to_selected(new_button)
        else:
            self.selected_index = -1

    def scroll_to_selected(self, button):
        def scroll():
            adj = self.scrolled_window.get_vadjustment()
            alloc = button.get_allocation()
            if alloc.height == 0:
                return False  # Retry if allocation isn't ready
            
            y = alloc.y
            height = alloc.height
            page_size = adj.get_page_size()
            current_value = adj.get_value()
            
            # Calculate visible boundaries
            visible_top = current_value
            visible_bottom = current_value + page_size

            if y < visible_top:
                # Item above viewport - align to top
                adj.set_value(y)
            elif y + height > visible_bottom:
                # Item below viewport - align to bottom
                new_value = y + height - page_size
                adj.set_value(new_value)
            # No action if already fully visible
            return False
        GLib.idle_add(scroll)

    def on_search_entry_activate(self, text):
        match text:
            case ":w":
                self.notch.open_notch("wallpapers")
            case ":d":
                self.notch.open_notch("dashboard")
            case ":p":
                self.notch.open_notch("power")
            case _:
                children = self.viewport.get_children()
                if children:
                    # Only activate if we have selection or non-empty query
                    if text.strip() == "" and self.selected_index == -1:
                        return  # Prevent accidental activation when empty
                    selected_index = self.selected_index if self.selected_index != -1 else 0
                    if 0 <= selected_index < len(children):
                        children[selected_index].clicked()

    def on_search_entry_key_press(self, widget, event):
        keyval = event.keyval
        if keyval == Gdk.KEY_Down:
            self.move_selection(1)
            return True
        elif keyval == Gdk.KEY_Up:
            self.move_selection(-1)
            return True
        elif keyval == Gdk.KEY_Escape:
            self.close_launcher()
            return True
        return False

    def move_selection(self, delta: int):
        children = self.viewport.get_children()
        if not children:
            return
        # Allow starting selection from nothing when empty
        if self.selected_index == -1 and delta == 1:
            new_index = 0
        else:
            new_index = self.selected_index + delta
        new_index = max(0, min(new_index, len(children) - 1))
        self.update_selection(new_index)
