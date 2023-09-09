import matplotlib.pyplot as plt
from calculator import *
import src
from drawer import *
from tabber import *
from mapper import *
import cartopy.crs as ccrs

path_to_af = __file__[:-len(__file__.split('/')[-1])]
colors = ['yellow', 'red', 'orange', 'green', 'blue', 'purple', 'pink', 'grey']
color_rgd = ['FFFF00', 'FF0000', 'FF8000', '009900', '0080FF', '7F00FF', 'FFCCFF', 'C0C0C0']

res_list = []


def calc_file(filename, sp_en, dt_en, km_en):
    try:
        speed = float(sp_en.get())
    except ValueError:
        messagebox.showerror('Altifore Error', 'Check speed field!')
        return 0

    try:
        start_date = datetime.strptime(dt_en.get(), '%d/%m/%y %H:%M').replace(tzinfo=utc)
    except ValueError:
        messagebox.showerror('Altifore Error', 'Check start date field!')
        return 0

    try:
        distance = float(km_en.get())
    except ValueError:
        messagebox.showerror('Altifore Error', 'Check distance field!')
        return 0

    result_list, arr_for_draw, last_date, tr_lat, tr_lon = calc_from_file(filename, distance, start_date, speed)

    if len(result_list == 0):
        messagebox.showerror('No flights!')
        return 0

    draw_map(arr_for_draw, tr_lat, tr_lon)

    num_of_days = (last_date - start_date).days + 2
    res_sheet = prepare_sheet(start_date, num_of_days)
    convert_list(path_to_af + "test.xlsx", res_sheet, res_list)





"""
def calculate_tab():
    station_pos_lat = np.zeros(shape=(len(ent_arr[0], )))
    station_pos_lon = np.zeros(shape=(len(ent_arr[0], )))
    times = []
    for i in range(len(ent_arr[0])):
        lat_str = list(map(int, ent_arr[2][i].get().split()))
        lat = np.sign(lat_str[0]) * (np.abs(lat_str[0]) + (lat_str[1] + lat_str[2] / 60.) / 60.)
        lon_str = list(map(int, ent_arr[3][i].get().split()))
        lon = np.sign(lon_str[0]) * (np.abs(lon_str[0]) + (lon_str[1] + lon_str[2] / 60.) / 60.)
        station_pos_lat[i] = lat
        station_pos_lon[i] = lon
        times.append(
            datetime.strptime(ent_arr[0][i].get() + " " + ent_arr[1][i].get(), '%d/%m/%y %H:%M').replace(tzinfo=utc))

    station_pos_ll = [wgs84.latlon(station_pos_lat[i], station_pos_lon[i]) for i in range(len(ent_arr[0]))]
    distance = float(km_en.get())

    sats = load.tle_file(path_to_af + 'tle/tle_data.txt')
    sat_names = {sat.name: sat for sat in sats}
    sat_data = [sat_names[name] for name in names]

    alt = 90 - src.calc_alt(distance, height) / np.pi * 180

    lat_min = int(np.min(station_pos_lat)) - 5
    lat_max = int(np.max(station_pos_lat)) + 5
    lon_min = int(np.min(station_pos_lon)) - 5
    lon_max = int(np.max(station_pos_lon)) + 5
    st_lo = int((lon_max - lon_min) / 10)
    st_lat = int((lat_max - lat_min) / 10)

    plt.figure(figsize=(5, 5), dpi=700)
    ax = plt.axes(projection=ccrs.PlateCarree())
    src.make_map(ax, left=lon_min, right=lon_max, up=lat_max, down=lat_min, step_lon=st_lo, step_lat=st_lat)
    ax.scatter(station_pos_lon, station_pos_lat, zorder=10, marker='+', color='black')
    f = open(path_to_af + "test.txt", "w")

    for n in range(len(station_pos_ll) - 1):

        res_list.append([])
        time1 = ts.from_datetime(times[n])
        time2 = ts.from_datetime(times[n + 1])

        for i in range(len(names)):

            res_sat = sat_data[i].find_events(station_pos_ll[n], time1, time2, altitude_degrees=alt[i])

            if len(res_sat[0]) > 0:
                for t in res_sat[0]:
                    ll = wgs84.latlon_of(sat_data[i].at(t))
                    if len(res_sat[0]) == 3 and t == res_sat[0][1]:
                        dist_km = dist.geodesic((ll[0].degrees, ll[1].degrees),
                                                (station_pos_lat[n], station_pos_lon[n])).km

                        res_list[n].append(
                            {'sat_name': names[i], 'date': t.utc_datetime().date().strftime("%Y-%m-%d"),
                             'time': t.utc_datetime().time().strftime("%H:%M"),
                             'dist': dist_km, 'color': color_rgd[i]})

                        f.write(str(names[i]) + " ")
                        f.write(str(t.utc_datetime().date()) + " " + str(t.utc_datetime().time().strftime("%H:%M")))
                        f.write(
                            f"\nlat {round(ll[0].degrees, 3)}, lon {round(ll[1].degrees, 3)}, dist {round(dist_km, 2)} km\n\n")

                    ax.scatter(ll[1].degrees, ll[0].degrees, color=colors[i], alpha=1, s=10)

        res_list[n] = sorted(res_list[n], key=lambda x: x['time'])

    f.close()
    num_of_days = (times[-1] - times[0]).days + 2
    res_sheet = src.prepare_sheet(times[0], num_of_days)

    if not src.convert_list(path_to_af + "test.xlsx", res_sheet, res_list):
        messagebox.showerror('Altifore Error', 'No flights in the selected date range!')

    else:
        for i in range(len(sat_names)):
            plt.scatter([0], [0], color=colors[i], label=names[i])
        plt.legend(loc='best', fontsize="6")
        plt.savefig(path_to_af + "test.png", dpi=700, bbox_inches='tight')
        img_new = src.add_img(path_to_af + "test.png", win_x, win_y)
        map_lab.configure(image=img_new)
        map_lab.image = img_new
        win.update()
"""

win.mainloop()
