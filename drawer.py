import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
from datetime import datetime
import screeninfo
import requests
from mapper import get_fig

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

path_to_af = __file__[:-len(__file__.split('/')[-1])]


def click_update_tle():
    len = sum(1 for line in open(path_to_af + 'tle/tle_sites.txt', 'r'))  # number of satellites
    data = open(path_to_af + 'tle/tle_data.txt', 'w')  # file with previous TLE data
    time = datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S")  # current time to record
    data.write("# last update : " + time + " UTC\n")

    with open(path_to_af + 'tle/tle_sites.txt', 'r') as file:  # reading sites from file with links
        for count, line in enumerate(file):
            f = requests.get(line)
            data.write(f.text)
            data.write('\n')
            bar['value'] = int(100 * count / (len - 1))  # update progress bar
            sty.configure("LabeledProgressbar", text="TLE for " + f.text[:13] + " successfully updated!")
            win.update()

    data.close()
    sty.configure("LabeledProgressbar", text="Last update of TLE : " + time + " UTC")  # update text on progress bar
    win.update()


def click_select():
    ftypes = (('OpenCPN files', '*.kml'), ('All files', '*.*'))
    fname = fd.askopenfilename(title='Select a file', initialdir=__file__, filetypes=ftypes)

    ttk.Label(sel_fr_u, text=fname).pack(side='left', padx=10)
    ttk.Label(sel_fr_d, text='Average speed').pack(side='left', padx=5)
    sp_en = ttk.Entry(sel_fr_d, width=4)
    sp_en.pack(side='left')
    ttk.Label(sel_fr_d, text='kn').pack(side='left', padx=10)

    ttk.Label(sel_fr_d, text='Start date').pack(side='left', padx=5)
    dt_en = ttk.Entry(sel_fr_d, width=14)
    dt_en.insert(0, "dd/mm/yy hh:mm")
    dt_en.pack(side='left')
    ttk.Button(sel_fr_u, text="Calculate file!", command=lambda: calc_file(fname, sp_en, dt_en, km_en)).pack(
        side='right', padx=5)


def add_row_to_column():
    for col in range(4):
        en = ttk.Entry(line_fr[col], width=int(win_x * 0.008))

        if len(ent_arr[-1]) != 0:
            if ent_arr[col][-1].get() != "":
                en.insert(0, ent_arr[col][-1].get())
        en.pack()
        ent_arr[col].append(en)



win = tk.Tk()
win.title("AltiFore")
monitor = screeninfo.get_monitors()[0]

win_x = int(monitor.width * 0.7)
win_y = int(monitor.height * 0.7)
center_x = int(0.5 * (monitor.width - win_x))
center_y = int(0.5 * (monitor.height - win_y))
win.geometry(f'{win_x}x{win_y}+{center_x}+{center_y}')
win.iconbitmap('@' + path_to_af + '/altifore.xbm')

sty = ttk.Style(win)
sty.layout("LabeledProgressbar", [('LabeledProgressbar.trough', {
    'children': [('LabeledProgressbar.pbar', {'side': 'left', 'sticky': 'ns'}),
                 ("LabeledProgressbar.label", {"sticky": ""})], 'sticky': 'nswe'})])

left_frame = tk.Frame(win)
left_frame.pack(side='left')
ttk.Label(left_frame,
          text="Welcome to AltiFore! Here you can prognose altimeters tracks. \n"
               "Select a .KML file or enter your vessel track manually. \n\n"
               "After calculation, you will receive a .PNG map with marked altitracks,\n a .XLSX with a daily schedule and .TXT with description of each span. \n\n"
               "In any unclear situation, please restart the app.", justify='center').pack(side='top')

map_frame = tk.Frame(win)
map_frame.pack(side='left')
# img_map = src.add_img(path_to_af + "test.png", win_x, win_y)
# map_lab = ttk.Label(map_frame, image=img_map)
# map_lab.pack()

### frame for TLE progress bar and update button ###
tle_fr = tk.Frame(left_frame)
tle_fr.pack(side='top', pady=10)

### subframe for progress bar ###
left_fr = tk.Frame(tle_fr)
left_fr.pack(side='left', pady=10, padx=5)
bar = ttk.Progressbar(left_fr, orient="horizontal", length=int(win_x * 0.4), style="LabeledProgressbar")
bar.pack()
tle_date = open("/home/leeiozh/ocean/AltiFore/tle/tle_data.txt", 'r').readline()[16:-1]
sty.configure("LabeledProgressbar", text="Last update of TLE : " + tle_date)

### subframe update TLE button ###
right_fr = tk.Frame(tle_fr)
right_fr.pack(side='right', padx=5, pady=10)
but_up = tk.Button(right_fr, text='Update TLE!', command=click_update_tle, width=10)
but_up.pack()

### frame for distance entry ###
di_fr = tk.Frame(left_frame)
di_fr.pack(side='top', padx=5)
ttk.Label(di_fr, text="Distance between vessel and satellite tracks ").pack(side='left')
km_en = ttk.Entry(di_fr, width=5)
km_en.insert(0, "200")
km_en.pack(side='left')
ttk.Label(di_fr, text="km").pack(side='left')

### frame for selecting a file ###
sel_fr = tk.Frame(left_frame)
sel_fr.pack(side='top', padx=5, pady=10)

### subframe for buttons and path ###
sel_fr_u = ttk.Frame(sel_fr)
sel_fr_u.pack(side='top', pady=5)
but_select = ttk.Button(sel_fr_u, text='Select a file', command=click_select)
but_select.pack(side='left')

### subframe for speed and start_date entries ###
sel_fr_d = ttk.Frame(sel_fr)
sel_fr_d.pack(side='top', pady=5)

### frame for tabular button ###
add_fr = ttk.Frame(left_frame)
add_fr.pack(side='top')

add_row_button = tk.Button(add_fr, text="Add new row", command=add_row_to_column)
add_row_button.pack(pady=10, side='left', padx=5)
# add_row_button = tk.Button(add_fr, text="Calculate table!", command=calculate_tab)
add_row_button.pack(pady=10, side='right', padx=5)

### frame for tabular ###
table_fr = ttk.Frame(left_frame)
table_fr.pack(side='top')

### subframes for tabular ###
line_fr = []
ent_arr = [[] for _ in range(4)]
labels = ["Date (dd/mm/yy)", "Time (hh:mm)", u"Latitude (\u00B1dd mm ss)", u"Longitude (\u00B1dd mm ss)"]
for column in range(4):
    frame = tk.Frame(table_fr)
    frame.pack(side="left", padx=int(win_x * 0.008), pady=10)
    ttk.Label(frame, text=labels[column]).pack(side="top")
    line_fr.append(frame)

fig, ax = get_fig()

canvas = FigureCanvasTkAgg(fig, master=win)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill=tk.BOTH, expand=True)

coord_label = tk.Label(win, text="", padx=10, pady=5)
coord_label.pack(side=tk.BOTTOM)

canvas.mpl_connect('motion_notify_event', display_coords)
win.mainloop()