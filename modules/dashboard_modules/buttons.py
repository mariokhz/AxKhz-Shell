from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import GLib
import modules.icons as icons

class Buttons(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="buttons",
            spacing=4,
            h_align="center",
            v_align="start",
            h_expand=True,
            v_expand=True,
            visible=True,
            all_visible=True,
        )

        self.notch = kwargs["notch"]

        self.network_status_button = Button(
            name="network-status-button",
            h_expand=True,
            child=Box(
                h_align="start",
                v_align="center",
                spacing=10,
                children=[
                    Label(
                        name="network-icon",
                        markup=icons.wifi,
                    ),
                    Box(
                        name="network-text",
                        orientation="v",
                        h_align="start",
                        v_align="center",
                        children=[
                            Box(
                                children=[
                                    Label(
                                        name="network-label",
                                        label="Wi-Fi",
                                        justification="left",
                                    ),
                                    Box(h_expand=True),
                                ]
                            ),
                            Box(
                                children=[
                                    Label(
                                        name="network-ssid",
                                        label="ARGOS_5GHz",
                                        justification="left",
                                    ),
                                    Box(h_expand=True),
                                ]
                            ),
                        ]
                    ),
                ],
            )
        )

        self.network_menu_button = Button(
            name="network-menu-button",
            child=Label(
                name="network-menu-label",
                markup=icons.chevron_right,
            ),
        )

        self.network_button = Box(
            name="network-button",
            orientation="h",
            h_align="fill",
            v_align="center",
            h_expand=True,
            v_expand=True,
            children=[
                self.network_status_button,
                self.network_menu_button,
            ],
        )

        self.bluetooth_status_button = Button(
            name="bluetooth-status-button",
            h_expand=True,
            child=Box(
                h_align="start",
                v_align="center",
                spacing=10,
                children=[
                    Label(
                        name="bluetooth-icon",
                        markup=icons.bluetooth,
                    ),
                    Box(
                        orientation="v",
                        h_align="start",
                        v_align="center",
                        children=[
                            Box(
                                children=[
                                    Label(
                                        name="bluetooth-label",
                                        label="Bluetooth",
                                        justification="left",
                                    ),
                                    Box(h_expand=True),
                                ]
                            ),
                            Box(
                                children=[
                                    Label(
                                        name="bluetooth-status",
                                        label="Connected",
                                        justification="left",
                                    ),
                                    Box(h_expand=True),
                                ]
                            ),
                        ]
                    ),
                ],
            )
        )

        self.bluetooth_menu_button = Button(
            name="bluetooth-menu-button",
            on_clicked=lambda *_: self.notch.open_notch("bluetooth"),
            child=Label(
                name="bluetooth-menu-label",
                markup=icons.chevron_right,
            ),
        )

        self.bluetooth_button = Box(
            name="bluetooth-button",
            orientation="h",
            h_align="fill",
            v_align="center",
            h_expand=True,
            v_expand=True,
            children=[
                self.bluetooth_status_button,
                self.bluetooth_menu_button,
            ],
        )

        self.night_mode_button = Button(
            name="night-mode-button",
            child=Box(
                h_align="start",
                v_align="center",
                spacing=10,
                children=[
                    Label(
                        name="night-mode-icon",
                        markup=icons.night,
                    ),
                    Box(
                        name="night-mode-text",
                        orientation="v",
                        h_align="start",
                        v_align="center",
                        children=[
                            Box(
                                children=[
                                    Label(
                                        name="night-mode-label",
                                        label="Night Mode",
                                        justification="left",
                                    ),
                                    Box(h_expand=True),
                                ]
                            ),
                            Box(
                                children=[
                                    Label(
                                        name="night-mode-status",
                                        label="Enabled",
                                        justification="left",
                                    ),
                                    Box(h_expand=True),
                                ]
                            ),
                        ]
                    )
                ],
            )
        )

        self.caffeine_button = Button(
            name="caffeine-button",
            child=Box(
 h_align="start",
                v_align="center",
                spacing=10,
                children=[
                    Label(
                        name="caffeine-icon",
                        markup=icons.coffee,
                    ),
                    Box(
                        name="caffeine-text",
                        orientation="v",
                        h_align="start",
                        v_align="center",
                        children=[
                            Box(
                                children=[
                                    Label(
                                        name="caffeine-label",
                                        label="Caffeine",
                                        justification="left",
                                    ),
                                    Box(h_expand=True),
                                ]
                            ),
                            Box(
                                children=[
                                    Label(
                                        name="caffeine-status",
                                        label="Enabled",
                                        justification="left",
                                    ),
                                    Box(h_expand=True),
                                ]
                            ),
                        ]
                    )
                ],
            )
        )

        self.add(self.network_button)
        self.add(self.bluetooth_button)
        self.add(self.night_mode_button)
        self.add(self.caffeine_button)

        self.show_all()
