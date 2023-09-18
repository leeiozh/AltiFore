import screeninfo
from drawer import *

if __name__ == "__main__":
    monitor = screeninfo.get_monitors()[0]
    window = MainWindow(monitor_size=(monitor.width, monitor.height))
    window.run()