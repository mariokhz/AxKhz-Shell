import os
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.stack import Stack
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import GLib, Gtk, Vte, Pango
import modules.icons as icons
from modules.dashboard_modules.buttons import Buttons
from modules.dashboard_modules.widgets import Widgets
from modules.pins import Pins
from modules.calendar import Calendar
from modules.kanban import Kanban

class Dashboard(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="dashboard",
            orientation="v",
            spacing=8,
            h_align="center",
            v_align="start",
            h_expand=True,
            # v_expand=True,
            visible=True,
            all_visible=True,
        )

        self.notch = kwargs["notch"]

        self.widgets = Widgets(notch=self.notch)
        self.pins = Pins()
        self.kanban = Kanban()
        self.calendar = Calendar()

        self.stack = Stack(
            name="stack",
            transition_type="slide-left-right",
            transition_duration=500,
        )

        self.switcher = Gtk.StackSwitcher(
            name="switcher",
            spacing=8,
        )

        self.label_1 = Label(
            name="label-1",
            label="Widgets",
        )

        self.label_2 = Label(
            name="label-2",
            label="Pins",
        )

        self.label_3 = Label(
            name="label-3",
            label="Kanban",
        )

        self.label_4 = Label(
            name="label-4",
            label="Calendar",
        )

        self.terminal = Vte.Terminal()
        user_shell = os.environ.get("SHELL", "/bin/bash")
        self.terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,                  # Flags
            os.path.expanduser("~"),               # Directorio de trabajo
            [user_shell],                          # Comando (shell del usuario)
            None,                                  # Variables de entorno
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,     # Spawn flags
            None,                                  # Función de configuración (opcional)
            None,                                  # Datos adicionales para la función (opcional)
            -1,                                    # Timeout
            None,                                  # GLib.Cancellable
            None                                   # Callback de finalización
        )
        self.terminal.set_font(Pango.FontDescription("ZedMono Nerd Font"))

        self.stack.add_titled(self.widgets, "widgets", "Widgets")
        self.stack.add_titled(self.pins, "pins", "Pins")
        self.stack.add_titled(self.kanban, "kanban", "Kanban")
        self.stack.add_titled(self.calendar, "calendar", "Calendar")
        self.stack.add_titled(self.terminal, "terminal", "Terminal")

        self.switcher.set_stack(self.stack)
        self.switcher.set_hexpand(True)
        self.switcher.set_homogeneous(True)
        self.switcher.set_can_focus(True)

        self.add(self.switcher)
        self.add(self.stack)

        self.show_all()

    def go_to_next_child(self):
        children = self.stack.get_children()
        current_index = self.get_current_index(children)
        next_index = (current_index + 1) % len(children)
        self.stack.set_visible_child(children[next_index])

    def go_to_previous_child(self):
        children = self.stack.get_children()
        current_index = self.get_current_index(children)
        previous_index = (current_index - 1 + len(children)) % len(children)
        self.stack.set_visible_child(children[previous_index])

    def get_current_index(self, children):
        current_child = self.stack.get_visible_child()
        return children.index(current_child) if current_child in children else -1
