# Parameters
font_family: str = 'tabler-icons'
font_weight: str = 'normal'

span: str = f"<span font-family='{font_family}' font-weight='{font_weight}'>"

#Panels
apps: str = "&#xf1fd;"
dashboard: str = "&#xea87;"
chat: str = "&#xf59f;"
wallpapers: str = "&#xeb01;"
windows: str = "&#xefe6;"

# Bar
colorpicker: str = "&#xebe6;"
media: str = "&#xf00d;"

# Circles
temp: str = "&#xeb38;"
disk: str = "&#xea88;"
battery: str = "&#xea38;"
memory: str = "&#xfa97;"
cpu: str = "&#xef8e;"

# AIchat
reload: str = "&#xf3ae;"
detach: str = "&#xea99;"

# Wallpapers
add: str = "&#xeb0b;"
sort: str = "&#xeb5a;"
circle: str = "&#xf671;"

# Chevrons
chevron_up: str = "&#xea62;"
chevron_down: str = "&#xea5f;"
chevron_left: str = "&#xea60;"
chevron_right: str = "&#xea61;"

# Power
lock: str = "&#xeae2;"
suspend: str = "&#xece7;"
logout: str = "&#xeba8;"
reboot: str = "&#xeb13;"
shutdown: str = "&#xeb0d;"

# Power Manager
power_saving: str = "&#xed4f;"
power_balanced: str = "&#xfa77;"
power_performance: str = "&#xec45;"
charging: str = "&#x10063;"
discharging: str = "&#x1006a;"
alert: str = "&#xefb4;"

# Sensors
battery_25: str = "&#xea2f;"
battery_50: str = "&#xea30;"
battery_75: str = "&#xea31;"
battery_100: str = "&#xea32;"
battery_charging: str = "&#xea33;"

update: str = "&#xfa0a;"
updated: str = "&#xf704;"

# Applets
wifi: str = "&#xeb52;"
bluetooth: str = "&#xea37;"
night: str = "&#xeaf8;"
coffee: str = "&#xef0e;"
dnd: str = "&#xea35;"

wifi_off: str = "&#xecfa;"
bluetooth_off: str = "&#xeceb;"
night_off: str = "&#xf162;"
dnd_off: str = "&#xece9;"

# Network
wifi_0: str = "&#xeba3;"
wifi_1: str = "&#xeba4;"
wifi_2: str = "&#xeba5;"
download: str = "&#xea96;"
upload: str = "&#xeb47;"
# Bluetooth
bluetooth_connected: str = "&#xecea;"
bluetooth_disconnected: str = "&#xf081;"

# Player
pause: str = "&#xf690;"
play: str = "&#xf691;"
stop: str = "&#xf695;"
skip_back: str = "&#xf693;"
skip_forward: str = "&#xf694;"
prev: str = "&#xf697;"
next: str = "&#xf696;"
shuffle: str = "&#xf000;"
repeat: str = "&#xeb72;"
music: str = "&#xeafc;"
rewind_backward_5: str = "&#xfabf;"
rewind_forward_5: str = "&#xfac7;"

# Volume
vol_off: str = "&#xf1c3;"
vol_mute: str = "&#xeb50;"
vol_medium: str = "&#xeb4f;"
vol_high: str = "&#xeb51;"

# Overview
circle_plus: str = "&#xea69;"

# Pins
copy_plus: str = "&#xfdae;"
paperclip: str = "&#xeb02;"

# Confirm
accept: str = "&#xea5e;"
cancel: str = "&#xeb55;"
trash: str = "&#xeb41;"

# Config
config: str = "&#xeb20;"

# Icons
desktop: str = "&#xea89;"
firefox: str = "&#xecfd;"
chromium: str = "&#xec18;"
spotify: str = "&#xfe86;"
code: str = "&#xf3a0;"
discord: str = "&#xece3;"
obsidian: str = "&#xeff5;"
anytype: str = "&#xf495;"
safari: str = "&#xec23;"
obs: str = "&#xef70;"
ghost: str = "&#xfc13;"
appstore: str = "&#xebb6;"

writing: str = "&#xef08;"
brush: str = "&#xebb8;"

apple: str = "&#xec17;"
mobile: str = "&#xea8a;"

finder: str = "&#xf218;"
folder: str = "&#xeaad;"
zip: str = "&#xed4e;"

terminal: str = "&#xebef;"


disc: str = "&#x1003e;"
disc_off: str = "&#xf118;"

# Misc
dot: str = "&#xf698;"

exceptions: list[str] = ['font_family', 'font_weight', 'span']

def apply_span() -> None:
    global_dict = globals()
    for key in global_dict:
        if key not in exceptions and not key.startswith('__'):
            global_dict[key] = f"{span}{global_dict[key]}</span>"

apply_span()

def get_class_icon(win_class):
    icon = ghost
    if win_class == "unknown":
        icon = desktop
    if win_class == "firefox":
        icon = firefox
    elif win_class == "org.kde.dolphin":
        icon = finder
    elif win_class == "chromium":
        icon = chromium
    elif win_class == "Spotify":
        icon = spotify
    elif win_class == "code":
        icon = code
    elif win_class == "com.discordapp.Discord":
        icon = discord
    elif win_class == "kitty":
        icon = terminal
    elif win_class == "obsidian":
        icon = obsidian
    elif win_class == "anytype":
        icon = anytype
    elif win_class == "zen":
        icon = safari
    elif win_class == "com.obsproject.Studio":
        icon = obs
    elif win_class == "GStreamer":
        icon = mobile
    elif win_class == "org.kde.discover":
        icon = appstore
    elif win_class == "org.pulseaudio.pavucontrol":
        icon = vol_high
    elif win_class == "com.github.flxzt.rnote" or win_class == "com.github.xournalpp.xournalpp":
        icon = writing
    elif win_class == "krita":
        icon = brush
    elif win_class == "org.kde.ark":
        icon = zip
    return icon
