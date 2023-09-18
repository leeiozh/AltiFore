from skyfield.api import load, wgs84, utc
import geopy.distance as dist
import datetime as dt
import fiona
import geopandas as gpd
import pandas as pd
from suncalc import get_position, get_times
from const import *

ts = load.timescale()


def calc_time(track, start, speed):
    res = np.ndarray(track.shape[0] - 1, dtype=dt.datetime)
    res[0] = start
    for i in range(res.shape[0] - 1):
        res[i + 1] = res[i] + dt.timedelta(
            hours=(dist.geodesic((track[i + 1].y, track[i + 1].x), (track[i].y, track[i].x)).nm / speed))
    res = [r.replace(tzinfo=utc) for r in res]
    return res


def calc_alt(distance):
    phi = distance / 6371
    s = 6371 * np.sin(phi)
    alph = np.arctan2(s, 6371 * (1 - np.cos(phi)) + SAT_HEIGHTS)
    return 90 - (phi + alph) / np.pi * 180.


def calc(distance, lats, lons, times):
    ofile = open(path_to_af + "test.txt", "w")  # output file

    sats = load.tle_file(path_to_af + 'tle/tle_data.txt')

    try:
        sat_data = [{sat.name: sat for sat in sats}[name] for name in SAT_NAMES]
    except KeyError:
        return [], []

    res_list = []  # list of results with dicts {sat_name, date, time, dist, color} for schedule
    arr_for_draw = []  # list of coordinates and colors for drawing s map
    alt = calc_alt(distance)  # critical altitude of sat

    for n in range(len(times)):  # loop for periods between neighbors times

        res_list.append([])
        time1 = ts.from_datetime(times[n])

        if n == (len(times) - 1):
            time2 = ts.from_datetime(times[n] + dt.timedelta(hours=2))
        else:
            if times[n] > times[n + 1]:
                ofile.close()
                return [], []
            time2 = ts.from_datetime(times[n + 1])

        for i in range(len(SAT_NAMES)):

            res_sat = sat_data[i].find_events(wgs84.latlon(lats[n], lons[n]), time1, time2, altitude_degrees=alt[i])

            if len(res_sat[0]) > 0:
                for t in res_sat[0]:
                    ll = wgs84.latlon_of(sat_data[i].at(t))
                    if len(res_sat[0]) == 3:
                        dist_km = dist.geodesic((ll[0].degrees, ll[1].degrees), (lats[n], lons[n])).km
                        arr_for_draw.append(
                            [ll[1].degrees, ll[0].degrees, i, round(dist_km), t.utc_datetime().timestamp(), lats[n],
                             lons[n], n])

                        if t == res_sat[0][1]:
                            res_list[n].append(
                                {'sat_name': SAT_NAMES[i], 'date': t.utc_datetime().date().strftime("%Y-%m-%d"),
                                 'time': t.utc_datetime().time().strftime("%H:%M"),
                                 'dist': round(dist_km, 2), 'color': color_rgd[i]})

                            ofile.write(str(SAT_NAMES[i]) + " ")
                            ofile.write(
                                str(t.utc_datetime().date()) + " " + str(t.utc_datetime().time().strftime("%H:%M")))
                            ofile.write(f"\nlat {round(ll[0].degrees, 3)}, lon {round(ll[1].degrees, 3)}, "
                                        f"dist {round(dist_km, 2)} km\n\n")

        res_list[n] = sorted(res_list[n], key=lambda x: x['time'])

    ofile.close()

    return res_list, np.array(arr_for_draw)


def calc_from_file(name, distance, start_date, speed):
    fiona.drvsupport.supported_drivers['KML'] = 'rw'
    geo_df = gpd.read_file(name, driver='KML')
    track_df = pd.DataFrame(geo_df)["geometry"]

    track_time = calc_time(track_df, start_date, speed=speed)

    lat = [track_df[i].y for i in range(track_df.shape[0] - 1)]
    lon = [track_df[i].x for i in range(track_df.shape[0] - 1)]

    return calc(distance, lat, lon, track_time), track_time[-1], lat, lon
