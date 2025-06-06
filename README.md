<p align="center">
  <img src="assets/cover.png">
</p>

<p align="center"><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Telegram-Animated-Emojis/main/Activity/Sparkles.webp" alt="Sparkles" width="25" height="25" /> <sup>A ʜᴀᴄᴋᴀʙʟᴇ sʜᴇʟʟ ꜰᴏʀ Hʏᴘʀʟᴀɴᴅ, ᴘᴏᴡᴇʀᴇᴅ ʙʏ <a href="https://github.com/Fabric-Development/fabric/">Fᴀʙʀɪᴄ</a>. </sup><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Telegram-Animated-Emojis/main/Activity/Sparkles.webp" alt="Sparkles" width="25" height="25" /></p>

## AxKhz-Shell vs Ax-Shell
Here is a quick comparison with Ax-Shell. I am in direct contact with the original developer, and the plan is to progressively adjust and integrate these new widgets into the main repository.

### Cavalcade | Merged to Ax-Shell ✅
- [x] Merged

<p align="center">
  <img src="assets/screenshots/cavalcade.png">
</p>

### Network speed | Merged to Ax-Shell ✅
- [x] Merged
<p align="center">
  <img src="assets/screenshots/default-wifi.png">
  <img src="assets/screenshots/hover.png">
  <img src="assets/screenshots/download.png">
  <img src="assets/screenshots/upload.png">
</p>

## Personal changes in branch dev2 (old)

### Window Title 
<p align="center">
  <img src="assets/screenshots/windowtitle.png">
</p>
I use win_class for the icons, and win_title as the text

### Battery
- Battery monitoring implemented with ```psutil``` library instead of ```acpi``` commands
- Maintains Axenide's ```auto-cpufreq``` control buttons for power management
<p align="center">
  <img src="assets/screenshots/battery.png">
</p>


### Icons in launcher
<p align="center">
  <img src="assets/screenshots/launcher.png">
</p>

<h2><sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Camera%20with%20Flash.png" alt="Camera with Flash" width="25" height="25" /></sub> Screenshots</h2>
<table align="center">
  <tr>
    <td colspan="4"><img src="assets/screenshots/1.png"></td>
  </tr>
  <tr>
    <td colspan="1"><img src="assets/screenshots/2.png"></td>
    <td colspan="1"><img src="assets/screenshots/3.png"></td>
    <td colspan="1" align="center"><img src="assets/screenshots/4.png"></td>
    <td colspan="1" align="center"><img src="assets/screenshots/5.png"></td>
  </tr>
</table>

<h2><sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Package.png" alt="Package" width="25" height="25" /></sub> Installation</h2>

> [!NOTE]
> You need a functioning Hyprland installation.

### Arch Linux

> [!TIP]
> This command also works for updating an existing installation!


```bash
curl -fsSL https://raw.githubusercontent.com/Axenide/Ax-Shell/main/install.sh | bash
```

### Manual Installation
1. Install dependencies:
    - [Fabric](https://github.com/Fabric-Development/fabric)
    - [fabric-cli](https://github.com/Fabric-Development/fabric-cli)
    - [Gray](https://github.com/Fabric-Development/gray)
    - [Matugen](https://github.com/InioX/matugen)
    - `brightnessctl`
    - `cava`
    - `gnome-bluetooth-3.0`
    - `gobject-introspection`
    - `gpu-screen-recorder`
    - `grimblast`
    - `hypridle`
    - `hyprlock`
    - `hyprpicker`
    - `hyprsunset`
    - `imagemagick`
    - `libnotify`
    - `noto-fonts-emoji`
    - `playerctl`
    - `swappy`
    - `swww`
    - `tesseract`
    - `uwsm`
    - `wl-clipboard`
    - `wlinhibit`
    - Python dependencies:
        - ijson
        - pillow
        - psutil
        - requests
        - setproctitle
        - toml
        - watchdog
    - Fonts (automated on first run):
        - Zed Sans
        - Tabler Icons

2. Download and run Ax-Shell:
    ```bash
    git clone https://github.com/Axenide/Ax-Shell.git ~/.config/Ax-Shell
    uwsm -- app python ~/.config/Ax-Shell/main.py > /dev/null 2>&1 & disown
    ```

<h2><sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Rocket.png" alt="Rocket" width="25" height="25" /></sub> Roadmap</h2>

- [x] App Launcher
- [x] Calculator
- [x] Power Menu
- [x] Dock
- [x] Emoji Picker
- [x] Wallpaper Selector
- [x] System Tray
- [x] Notifications
- [x] Terminal
- [x] Pins
- [x] Kanban Board
- [x] Calendar
- [x] Color Picker
- [x] Dashboard
- [x] Bluetooth Manager
- [x] Power Manager
- [x] Settings
- [x] Screenshot
- [x] Screen Recorder
- [x] OCR
- [x] Workspaces Overview
- [ ] Network Manager
- [ ] Clipboard Manager
- [ ] Multimodal AI Assistant
- [ ] Vertical Layout
- [ ] Multi-monitor support

---

<table align="center">
  <tr>
    <td align="center"><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Telegram-Animated-Emojis/main/Activity/Sparkles.webp" alt="Sparkles" width="16" height="16" /><sup> sᴜᴘᴘᴏʀᴛ ᴛʜᴇ ᴘʀᴏᴊᴇᴄᴛ </sup><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Telegram-Animated-Emojis/main/Activity/Sparkles.webp" alt="Sparkles" width="16" height="16" /></td>
  </tr>
  <tr>
    <td align="center">
      <a href='https://ko-fi.com/Axenide' target='_blank'>
        <img style='border:0px;height:128px;'
             src='https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExc3N4NzlvZWs2Z2tsaGx4aHgwa3UzMWVpcmNwZTNraTM2NW84ZDlqbiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/PaF9a1MpqDzovyqVKj/giphy.gif'
             border='0' alt='Support me on Ko-fi!' />
      </a>
    </td>
  </tr>
</table>
