import platform


def get_graphics_cards():
    system = platform.system()
    if system == "Windows":
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\OpenGLDrivers",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "Display1")
            return value.split("\\")[-1]
    elif system == "Darwin":
        return platform.mac_ver()[0]
    elif system == "Linux":
        with open("/var/log/Xorg.0.log", "r") as f:
            log = f.read()
            for line in log.split("\n"):
                if "OpenGL vendor string" in line:
                    return line.split(":")[-1].strip()
    else:
        return None


print(get_graphics_cards())
