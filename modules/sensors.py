import psutil
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.widgets.overlay import Overlay
from fabric.widgets.revealer import Revealer
from fabric.utils import invoke_repeater, exec_shell_command_async
from fabric.widgets.circularprogressbar import CircularProgressBar
import subprocess
import time

import modules.icons as icons
from services.network import NetworkClient

class BatteryBox(Box):
    def __init__(self, **kwargs):
        super().__init__(name="button-bar-vol", **kwargs)

        self.icon_label = Label(
            name="button-bar-label",
            markup = icons.battery
        )

        self.battery_percentage_label = Label(
            name="battery-percentage-label",
            markup = ""
        )
        #self.pack_end(self.battery_percentage_label, True, True, 0)


        self.progress_bar = CircularProgressBar(
            name="button-volume", pie=False, size=30, start_angle = 90, end_angle= 90+360, line_width=3,
        )

        self.battery_button = Button()
        self.battery_button_connected = False
        


        self.overlay = Overlay()
        self.overlay.add_overlay(self.icon_label)
        self.overlay.add(self.progress_bar)
        self.overlay.add_overlay(self.battery_button)
        self.pack_end(self.overlay, True, True, 0)

        self.battery_lowest_percentage = 4
        invoke_repeater(500, self.update_label)

    def update_label(self):
        battery = psutil.sensors_battery()
        secsleft = battery.secsleft

        if secsleft == psutil.POWER_TIME_UNLIMITED or secsleft < 0:
            time_str = "∞"

        else:
            hours = secsleft // 3600
            minutes = (secsleft % 3600) // 60
            seconds = secsleft % 60
            if hours:
                time_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes:
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = f"{seconds}s"

        percentage = int(battery.percent)
        self.percentage = percentage
        plugged = battery.power_plugged
        secsleft = time_str
        self.secsleft = secsleft
        self.battery_button.set_tooltip_text(f"Batería: {percentage}% \nTiempo restante: {secsleft}")
        self.progress_bar.value = percentage / 100
        if self.battery_button_connected == False:
            self.battery_button.connect("clicked", self.notify)
            self.battery_button_connected = True




        if plugged or plugged is None:
            self.icon_label.set_markup(icons.battery_charging)
            self.battery_percentage_label.set_markup(f"{percentage}%")

        else:
            if percentage > 75:
                self.icon_label.set_markup(icons.battery_100)
            elif percentage > 50:
                self.icon_label.set_markup(icons.battery_75)
            elif percentage > 25:
                self.icon_label.set_markup(icons.battery_50)
            else:
                self.icon_label.set_markup(icons.battery_25)
            self.battery_percentage_label.set_markup(f"{percentage}%")

            if percentage <= 10:
                percentage -= self.battery_lowest_percentage - 1
                self.notify_critical()

        return True
    
    def notify_critical(self):
        exec_shell_command_async(f"notify-send '{self.percentage}% útil' '{self.secsleft} restantes' -u critical -a 'Batería crítica'")

    def notify(self, *args):
        exec_shell_command_async(f"notify-send '{self.percentage}%' '{self.secsleft} segundos restantes' -a 'Batería'")
  
class NetworkApplet(Button):
    def __init__(self, **kwargs):
        super().__init__(name="button-bar", **kwargs)
        self.download_label = Label(name="download-label", markup="Download: 0 B/s")
        self.network_client = NetworkClient()
        self.upload_label = Label(name="upload-label", markup="Upload: 0 B/s")
        self.wifi_label = Label(name="icon-label", markup="WiFi: Unknown")

        self.is_mouse_over = False

        self.download_icon = Label(name="download-icon-label", markup=icons.download)
        self.upload_icon = Label(name="upload-icon-label", markup=icons.upload)

        self.download_box = Box(
            children=[self.download_icon, self.download_label],
        )

        self.upload_box = Box(
            children=[self.upload_label, self.upload_icon],
        )

        self.download_revealer = Revealer(child=self.download_box, transition_type = "slide-right", child_revealed=False)
        self.upload_revealer = Revealer(child=self.upload_box, transition_type="slide-left" ,child_revealed=False)
        

        self.children = Box(
            children=[self.upload_revealer, self.wifi_label, self.download_revealer],
        )
        self.last_counters = psutil.net_io_counters()
        self.last_time = time.time()
        invoke_repeater(1000, self.update_network)

        self.connect("enter-notify-event", self.on_mouse_enter)
        self.connect("leave-notify-event", self.on_mouse_leave)

    def update_network(self):
        current_time = time.time()
        elapsed = current_time - self.last_time
        current_counters = psutil.net_io_counters()
        download_speed = (current_counters.bytes_recv - self.last_counters.bytes_recv) / elapsed
        upload_speed = (current_counters.bytes_sent - self.last_counters.bytes_sent) / elapsed
        self.download_label.set_markup(self.format_speed(download_speed))
        self.upload_label.set_markup(self.format_speed(upload_speed))

        self.downloading = (download_speed >= 20e6)
        self.uploading = (upload_speed >= 2e6)

        if self.downloading and not self.is_mouse_over:
            self.download_urgent()
        if self.uploading and not self.is_mouse_over:
            self.upload_urgent()

        self.download_revealer.set_reveal_child(self.downloading or self.is_mouse_over)
        self.upload_revealer.set_reveal_child(self.uploading or self.is_mouse_over)

        if not self.downloading and not self.uploading:
            self.remove_urgent()

        # Verificar el wifi utilizando el NetworkClient con la propiedad strength
        if self.network_client and self.network_client.wifi_device:
            if self.network_client.wifi_device.ssid != "Disconnected":
                strength = self.network_client.wifi_device.strength
                # Si la intensidad es mayor o igual a 50 usamos wifi_1, de lo contrario wifi_0
                if strength >= 75:
                    self.wifi_label.set_markup(icons.wifi)
                elif strength >= 50:
                    self.wifi_label.set_markup(icons.wifi_2)
                elif strength >= 25:
                    self.wifi_label.set_markup(icons.wifi_1)
                else:
                    self.wifi_label.set_markup(icons.wifi_0)

                self.set_tooltip_text(self.network_client.wifi_device.ssid)

            else:
                self.wifi_label.set_markup(icons.network_off)
                self.set_tooltip_text("Disconnected")
        else:
            self.wifi_label.set_markup(icons.network_off)
            self.set_tooltip_text("Disconnected")

        

        self.last_counters = current_counters
        self.last_time = current_time
        return True

    def format_speed(self, speed):
        if speed < 1024:
            return f"{speed:.0f} B/s"
        elif speed < 1024 * 1024:
            return f"{speed / 1024:.1f} KB/s"
        else:
            return f"{speed / (1024 * 1024):.1f} MB/s"
        
    def on_mouse_enter(self, *_):
        self.is_mouse_over = True
        self.remove_urgent()
        self.download_revealer.set_reveal_child(True)
        self.upload_revealer.set_reveal_child(True)
        return
    
    def on_mouse_leave(self, *_):
        self.is_mouse_over = False
        self.remove_urgent()
        self.download_revealer.set_reveal_child(False)
        self.upload_revealer.set_reveal_child(False)
        return

    def upload_urgent(self):
        self.add_style_class("upload")
        self.wifi_label.add_style_class("urgent")
        self.upload_label.add_style_class("urgent")
        self.upload_icon.add_style_class("urgent")
        self.download_icon.add_style_class("urgent")
        self.upload_revealer.set_reveal_child(True)
        self.download_revealer.set_reveal_child(self.downloading)
        return
    
    def download_urgent(self):
        self.add_style_class("download")
        self.wifi_label.add_style_class("urgent")
        self.download_label.add_style_class("urgent")
        self.download_icon.add_style_class("urgent")
        self.upload_icon.add_style_class("urgent")
        self.download_revealer.set_reveal_child(True)
        self.upload_revealer.set_reveal_child(self.uploading)
        return
    
    def remove_urgent(self):
        self.remove_style_class("download")
        self.remove_style_class("upload")
        self.wifi_label.remove_style_class("urgent")
        self.download_label.remove_style_class("urgent")
        self.upload_label.remove_style_class("urgent")
        self.download_icon.remove_style_class("urgent")
        self.upload_icon.remove_style_class("urgent")
        return

