import screeninfo
from drawer import MainWindow

if __name__ == "__main__":
    monitor = screeninfo.get_monitors()[0]  # for using with several monitors
    window = MainWindow(monitor_size=(monitor.width, monitor.height))
    window.run()
