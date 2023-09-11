import screeninfo
from drawer import *

path_to_af = __file__[:-len(__file__.split('/')[-1])]
colors = ['yellow', 'red', 'orange', 'green', 'blue', 'purple', 'pink', 'grey']
color_rgd = ['FFFF00', 'FF0000', 'FF8000', '009900', '0080FF', '7F00FF', 'FFCCFF', 'C0C0C0']

if __name__ == "__main__":
    monitor = screeninfo.get_monitors()[0]
    window = MainWindow(monitor_size=(monitor.width, monitor.height))
    window.run()
