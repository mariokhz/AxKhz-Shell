import json

from fabric.utils import exec_shell_command_async, get_relative_path, invoke_repeater
from fabric.widgets.box import Box
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.label import Label
from fabric.widgets.revealer import Revealer
from fabric.widgets.stack import Stack
import modules.icons as icons
from loguru import logger

from gi.repository import Gtk
from fabric.widgets.button import Button


class UpdatesWidget(Button):
    """A widget to display the number of available updates."""

    def __init__(
        self,
        **kwargs,
    ):
        # Initialize the EventBox with specific name and style
        super().__init__(name="button-bar", **kwargs)
        

        self.script_file = get_relative_path("../scripts/systemupdates.sh")

        self.update_level_label = Label(
            name="battery-percentage-label",
            label="0",
            visible=False, 
        )

        self.update_icon = Label(name="battery-icon-label", markup=icons.update)
        self.updated_icon = Label(name="button-icon-label", markup=icons.updated)

        self.update_box = CenterBox(
            center_children=(self.update_icon, self.update_level_label),
        )

        self.updated_box = CenterBox(
            center_children=(self.updated_icon),
        )

        self.stack = Stack()
        self.stack.add_named(self.update_box, "update_box")
        self.stack.add_named(self.updated_box, "updated_box")
        self.stack.set_visible_child_name("update_box")

        self.children = Box(
            children=self.stack,
        )

        # Ensure the stack resizes to the current visible child
        self.stack.set_homogeneous(False)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        # Show initial value of 0 if label is enabled

        self.connect("button-press-event", self.on_button_press)

        # Set up a repeater to call the update method at specified intervals
        invoke_repeater(600000, self.update, initial_call=True)

    def update_values(self, value: str):
        # Parse the JSON value
        value = json.loads(value)

        # Update the label if enabled
        self.update_level_label.set_label(value["total"])

        if value["total"] == "0":
            self.stack.set_visible_child_name("updated_box")
        else:
            self.stack.set_visible_child_name("update_box")

        # Update the tooltip if enabled
        self.set_tooltip_text(value["tooltip"])
        return True

    def on_button_press(self, _, event):
        if event.button == 1:
            exec_shell_command_async(
                f"{self.script_file} -arch -up",
                lambda _: None,
            )
            self.update()
            return True
        else:
            self.update()

    def update(self):
        logger.info("[Updates] Checking for updates...")

        # Execute the update script asynchronously and update values
        exec_shell_command_async(
            f"{self.script_file} -arch",
            lambda output: self.update_values(output),
        )

        return True
