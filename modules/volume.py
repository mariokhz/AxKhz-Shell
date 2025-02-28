from fabric.widgets.overlay import Overlay
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from gi.repository import Gdk
from fabric.widgets.eventbox import EventBox
from fabric.widgets.circularprogressbar import CircularProgressBar
from fabric.audio.service import Audio
import modules.icons as icons

class VolumeWidget(Box):
    def __init__(self, **kwargs):
        super().__init__(name="button-bar", spacing=5, **kwargs)
        self.audio = Audio()
        self.last_speaker_volume = 100

        self.speaker_progress_bar = CircularProgressBar(
            name="button-volume", pie=False, size=28, start_angle = 120, end_angle = 60+360, line_width=3,
        )

        self.volume_label = Label(
            name="volume-icon-label",
            markup=icons.vol_high,
        )

        self.speaker_event_box = EventBox(
#            name="button-bar-vol",
            events=["scroll", "smooth-scroll", "button-press"],
            child=Overlay(
                child=self.speaker_progress_bar,
                overlays=self.volume_label,
            ),
        )

        self.microphone_progress_bar = CircularProgressBar(
            name="button-volume", pie=False, size=28, start_angle = 120, end_angle = 60+360, line_width=3,
        )

        self.microphone_label = Label(
            name="microphone-icon-label",
            markup=icons.mic,
        )

        self.microphone_event_box = EventBox(
            name="button-bar",
            events=["scroll", "smooth-scroll", "button-press"],
            child=Overlay(
                child=self.microphone_progress_bar,
                overlays=self.microphone_label,
            ),
        )

        self.audio.connect("notify::speaker", self.on_speaker_changed)
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)
        self.audio.connect("notify::microphone", self.on_microphone_changed)
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)
        self.speaker_event_box.connect("scroll-event", self.on_speaker_scroll)
        self.speaker_event_box.connect("button-press-event", self.on_speaker_button_press)
        self.microphone_event_box.connect("scroll-event", self.on_microphone_scroll)
        self.microphone_event_box.connect("button-press-event", self.on_microphone_button_press)
        self.add(self.speaker_event_box)
        self.add(self.microphone_event_box)

    def on_microphone_scroll(self, _, event):
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if abs(event.delta_y) > 0:
                self.audio.microphone.volume += event.delta_y
            if abs(event.delta_x) > 0:
                self.audio.microphone.volume -= event.delta_x

        match event.direction:
            case 0:
                self.audio.microphone.volume += 2
            case 1:
                self.audio.microphone.volume -= 2

        self.update_microphone_label()
        return

    def on_speaker_scroll(self, _, event):
        
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if abs(event.delta_y) > 0:
                self.audio.speaker.volume += event.delta_y
            if abs(event.delta_x) > 0:
                self.audio.speaker.volume -= event.delta_x

            

        match event.direction:
            case 0:
                self.audio.speaker.volume += 2
            case 1:
                self.audio.speaker.volume -= 2
            

        self.update_speaker_label()
        return
    
    def on_speaker_button_press(self, *_):
        
        if self.audio.speaker.volume == 0:
            self.audio.speaker.volume = self.last_speaker_volume
            self.update_speaker_label()
        else:
            self.last_speaker_volume = self.audio.speaker.volume
            self.audio.speaker.volume = 0
            self.update_speaker_label()
        
        return


    def on_speaker_changed(self, *_):
        self.update_speaker_label()
        if not self.audio.speaker:
            return
        self.speaker_progress_bar.value = self.audio.speaker.volume / 100
        self.audio.speaker.bind(
            "volume", "value", self.speaker_progress_bar, lambda _, v: v / 100
        )
        return
    
    def update_speaker_label(self):
        
        if self.audio.speaker.volume == 0:
            self.volume_label.add_style_class("zero")
            self.speaker_progress_bar.add_style_class("zero")

        if "bluetooth" not in self.audio.speaker.icon_name:
            if self.audio.speaker.muted:
                self.volume_label.markup = icons.vol_off
            elif self.audio.speaker.volume > 65:
                self.speaker_progress_bar.remove_style_class("zero")
                self.volume_label.remove_style_class("zero")
                self.volume_label.set_markup(icons.vol_high)
            elif self.audio.speaker.volume > 10:
                self.speaker_progress_bar.remove_style_class("zero")
                self.volume_label.remove_style_class("zero")
                self.volume_label.set_markup(icons.vol_medium)
            elif self.audio.speaker.volume > 0:
                self.speaker_progress_bar.remove_style_class("zero")
                self.volume_label.remove_style_class("zero")
            elif self.audio.speaker.volume < 5:
                #self.speaker_progress_bar.remove_style_class("zero")
                self.volume_label.set_markup(icons.vol_mute)
            
                
        else:
            if self.audio.speaker.volume == 0:
                self.volume_label.set_markup(icons.bluetooth_disconnected)
            else:
                self.speaker_progress_bar.remove_style_class("zero")
                self.volume_label.remove_style_class("zero")
                self.volume_label.set_markup(icons.bluetooth_connected)
        return
    
    def on_microphone_changed(self, *_):
        if not self.audio.microphone:
            return
        self.microphone_progress_bar.value = self.audio.microphone.volume / 100
        self.audio.microphone.bind(
            "volume", "value", self.microphone_progress_bar, lambda _, v: v / 100
        )
        return
    
    def on_microphone_button_press(self, *_):
        
        if self.audio.microphone.volume == 0:
            self.audio.microphone.volume = 100
            self.update_microphone_label()
        else:
            self.audio.microphone.volume = 0
            self.update_microphone_label()
        
        return
    
    def update_microphone_label(self):
        if self.audio.microphone.volume == 0:
            self.microphone_label.set_markup(icons.mic_off)
            self.microphone_progress_bar.add_style_class("zero")
            self.microphone_label.add_style_class("zero")
        else:
            self.microphone_label.set_markup(icons.mic)
            self.microphone_progress_bar.remove_style_class("zero")
            self.microphone_label.remove_style_class("zero")
        return
