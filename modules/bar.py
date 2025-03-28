from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.datetime import DateTime
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.button import Button
from fabric.utils.helpers import FormattedString
from fabric.widgets.revealer import Revealer
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.hyprland.widgets import Workspaces, WorkspaceButton, Language, get_hyprland_connection
from fabric.hyprland.service import HyprlandEvent
from fabric.utils.helpers import get_relative_path, exec_shell_command_async
from gi.repository import Gdk
from modules.systemtray import SystemTray
import modules.icons as icons
import modules.data as data
from modules.metrics import MetricsSmall, Battery, NetworkApplet
from modules.controls import ControlSmall


from modules.battery import Battery

from modules.updates import UpdatesWidget
from modules.weather import Weather

class Bar(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="bar",
            layer="top",
            anchor="left top right",
            margin="-8px -4px -8px -4px",
            exclusivity="auto",
            visible=True,
            all_visible=True,
        )

        self.notch = kwargs.get("notch", None)

        self.network_applet = NetworkApplet()
        
        self.workspaces = Workspaces(
            name="workspaces",
            invert_scroll=True,
            empty_scroll=True,
            v_align="fill",
            orientation="h",
            spacing=10,
            buttons=[WorkspaceButton(id=i, label="") for i in range(1, 11)],
        )
        self.ignored_workspaces = [-99, -98]
        self.hide_ignored_workspaces()
        self.workspaces.connection.connect("event::workspacev2", self.hide_ignored_workspaces)
        self.workspaces.connection.connect("event::createworkspacev2", self.hide_ignored_workspaces)
        self.workspaces.connection.connect("event::urgent", self.hide_ignored_workspaces)
        
        self.button_tools = Button(
            name="button-bar",
            on_clicked=lambda *_: self.tools_menu(),
            child=Label(
                name="button-bar-label",
                markup=icons.toolbox
            )
        )

        self.connection = get_hyprland_connection()
        self.button_tools.connect("enter_notify_event", self.on_button_enter)
        self.button_tools.connect("leave_notify_event", self.on_button_leave)

        self.systray = SystemTray()
        self.weather = Weather()
        self.network = NetworkApplet()
        # self.systray = SystemTray(name="systray", spacing=8, icon_size=20)

        self.language = Language(name="language", h_align="center", v_align="center")
        self.switch_on_start()
        self.connection.connect("event::activelayout", self.on_language_switch)

        self.date_time = DateTime(name="date-time", formatters=["%H:%M"], h_align="center", v_align="center")
      
        self.updates = UpdatesWidget()
        self.updates.connect("enter-notify-event", self.on_button_enter)
        self.updates.connect("leave-notify-event", self.on_button_leave)

        self.battery = Battery()

        self.button_apps = Button(
            name="button-bar",
            on_clicked=lambda *_: self.search_apps(),
            child=Label(
                name="button-bar-label",
                markup=icons.apps
            )
        )
        self.button_apps.connect("enter_notify_event", self.on_button_enter)
        self.button_apps.connect("leave_notify_event", self.on_button_leave)

        self.button_power = Button(
            name="button-bar",
            on_clicked=lambda *_: self.power_menu(),
            child=Label(
                name="button-bar-label",
                markup=icons.shutdown
            )
        )
        self.button_power.connect("enter_notify_event", self.on_button_enter)
        self.button_power.connect("leave_notify_event", self.on_button_leave)

        self.button_overview = Button(
            name="button-bar",
            on_clicked=lambda *_: self.overview(),
            child=Label(
                name="button-bar-label",
                markup=icons.windows
            )
        )
        self.button_overview.connect("enter_notify_event", self.on_button_enter)
        self.button_overview.connect("leave_notify_event", self.on_button_leave)


        self.control = ControlSmall()
        self.metrics = MetricsSmall()
        self.battery = Battery()

        self.revealer_right = Revealer(
            name="bar-revealer",
            transition_type="slide-left",
            child_revealed=True,
            child=Box(
                name="bar-revealer-box",
                orientation="h",
                spacing=4,
                children=[
                    self.metrics,
                    self.control
                    
                ],
            ),
        )

        self.boxed_revealer_right = Box(
            name="boxed-revealer",
            children=[
                self.revealer_right,
            ],
        )

        self.revealer_left = Revealer(
            name="bar-revealer",
            transition_type="slide-right",
            child_revealed=True,
            child=Box(
                name="bar-revealer-box",
                orientation="h",
                spacing=4,
                children=[
                    self.date_time,
                    self.weather,
                    self.network,
                ],
            ),
        )

        self.boxed_revealer_left = Box(
            name="boxed-revealer",
            children=[
                self.revealer_left,
            ],
        )

        self.bar_inner = CenterBox(
            name="bar-inner",
            orientation="h",
            h_align="fill",
            v_align="center",
            start_children=Box(
                name="start-container",
                spacing=4,
                orientation="h",
                children=[
                    self.button_apps,
                    Box(name="workspaces-container", children=[self.workspaces]),
                    self.button_overview,
                    self.boxed_revealer_left,
                ]
            ),
            end_children=Box(
                name="end-container",
                spacing=4,
                orientation="h",
                children=[
                    self.battery,
                    self.boxed_revealer_right,
                    
                    #self.updates,
                    self.systray,
                    self.button_tools,
                    #self.language,
                    self.date_time,
                    self.button_power,
                ],
            ),
        )

        self.children = self.bar_inner

        self.hidden = False

        # self.show_all()
        self.systray._update_visibility()

    def on_button_enter(self, widget, event):
        window = widget.get_window()
        if window:
            window.set_cursor(Gdk.Cursor(Gdk.CursorType.HAND2))

    def on_button_leave(self, widget, event):
        window = widget.get_window()
        if window:
            window.set_cursor(None)

    def on_button_clicked(self, *args):
        # Ejecuta notify-send cuando se hace clic en el botón
        exec_shell_command_async("notify-send 'Botón presionado' '¡Funciona!'")

    def search_apps(self):
        self.notch.open_notch("launcher")

    def overview(self):
        self.notch.open_notch("overview")

    def power_menu(self):
        self.notch.open_notch("power")
    def tools_menu(self):
        self.notch.open_notch("tools")

    def on_language_switch(self, _, event: HyprlandEvent):
        self.language.set_label(self.language.get_label()[0:3].upper())

    def switch_on_start(self):
        self.language.set_label(self.language.get_label()[0:3].upper())

    def toggle_hidden(self):
        self.hidden = not self.hidden
        if self.hidden:
            self.bar_inner.add_style_class("hidden")
        else:
            self.bar_inner.remove_style_class("hidden")

    def hide_ignored_workspaces(self, *args):
        for button in self.workspaces.get_child():
            if button.id in self.ignored_workspaces:
                self.workspaces.remove_button(button)
        
