import numpy as np  # conda install -c conda-forge numpy
from skyfield.api import load, wgs84, utc  # conda install -c conda-forge skyfield
import geopy.distance as dist  # conda install -c conda-forge geopy
import datetime as dt
import fiona  # conda install -c conda-forge fiona
import geopandas as gpd  # conda install -c conda-forge geopandas
import pandas as pd  # conda install -c conda-forge pandas
from const import *
from pyproj import Geod
import math

geod = Geod(ellps="WGS84")

ts = load.timescale()


def calc_track(lat, lon, start, speed):
    new_lats = [lat[0]]
    new_lons = [lon[0]]
    new_times = [start]

    for i in range(1, len(lat)):
        azimuth, _, distance = geod.inv(lon[i - 1], lat[i - 1], lon[i], lat[i])

        time_interval = distance / (speed * 0.51444)
        current_time = new_times[-1]
        num_intervals = int(time_interval // int(GAP * 3600))
        for j in range(1, num_intervals + 1):
            fraction = j * int(GAP * 3600) / time_interval
            inter_lon, inter_lat, _ = geod.fwd(lon[i - 1], lat[i - 1], azimuth, fraction * distance)
            new_lats.append(inter_lat)
            new_lons.append(inter_lon)
            new_times.append(current_time + dt.timedelta(seconds=j * int(GAP * 3600)))

        new_lats.append(lat[i])
        new_lons.append(lon[i])
        new_times.append(current_time + dt.timedelta(seconds=time_interval))

    return new_lats, new_lons, new_times


# def calc_time(track, start, speed):
#     """
#     calculating time of track points if we suppose constant speed
#     :param track: array of track points
#     :param start: datetime of start point
#     :param speed: constant speed
#     :return: array of times
#     """
#     res = np.ndarray(track.shape[0] - 1, dtype=dt.datetime)
#     res[0] = start
#
#     for i in range(res.shape[0] - 1):
#         res[i + 1] = res[i] + dt.timedelta(
#             hours=(dist.geodesic((track[i + 1].y, track[i + 1].x), (track[i].y, track[i].x)).nm / speed))
#     res = [r.replace(tzinfo=utc) for r in res]
#     return res


def calc_alt(distance):
    """
    very stupid method for calculation sat altitude where its gets into the {distance} radius circle
    :param distance: radius of circle
    :return: array of sat altitudes
    """
    phi = distance / 6371
    s = 6371 * np.sin(phi)
    alph = np.arctan2(s, 6371 * (1 - np.cos(phi)) + SAT_HEIGHTS)
    return 90 - (phi + alph) / np.pi * 180.


def calc(distance, lats, lons, times, save_name):
    """
    main calculation
    :return: list for creating a table and array for drawing
    """
    path_to_save = save_name.get()
    try:
        ofile = open(path_to_save + ".txt", "w")  # output file
    except:
        return -1, -1

    sats = load.tle_file(path_to_af + 'tle/tle_data.txt')

    try:
        sat_data = [{sat.name: sat for sat in sats}[name] for name in SAT_NAMES]

        for s in sat_data:
            vec = s.at(ts.from_datetime(times[0])).position.km
            SAT_HEIGHTS.append(np.linalg.norm(np.array(vec)) - 6371)

    except KeyError:
        return [], []

    res_list = []  # list of results with dicts {sat_name, date, time, dist, color} for schedule
    arr_for_draw = []  # list of coordinates and colors for drawing s map
    alt = calc_alt(distance)  # critical altitude of sat

    for n in range(len(times)):  # loop for periods between neighbors times

        res_list.append([])
        time1 = ts.from_datetime(times[n])

        if n == (len(times) - 1):
            time2 = ts.from_datetime(times[n] + dt.timedelta(hours=6))  # add 6 hours to last point
        else:
            if times[n] > times[n + 1]:  # input data must be sorted
                ofile.close()
                return [], []
            time2 = ts.from_datetime(times[n + 1])

        for i in range(len(SAT_NAMES)):

            # magic function which returns times of flights
            res_sat = sat_data[i].find_events(wgs84.latlon(lats[n], lons[n]), time1, time2, altitude_degrees=alt[i])

            if len(res_sat[0]) > 0:
                for t in res_sat[0]:
                    ll = wgs84.latlon_of(sat_data[i].at(t))  # obtain sat coordinates at res_sat time
                    if len(res_sat[0]) == 3:  # if ok, there is 3 points: enter and exit from circle and culmination
                        dist_km = dist.geodesic((ll[0].degrees, ll[1].degrees), (lats[n], lons[n])).km
                        arr_for_draw.append(
                            [ll[1].degrees, ll[0].degrees, i, round(dist_km), t.utc_datetime().timestamp(), lats[n],
                             lons[n], n])

                        if t == res_sat[0][1]:  # save only central point of flight where sat the closest to us
                            res_list[n].append(
                                {'sat_name': SAT_NAMES[i], 'date': t.utc_datetime().date().strftime("%d/%m/%Y"),
                                 'time': t.utc_datetime().time().strftime("%H:%M"),
                                 'dist': round(dist_km, 2), 'color': color_rgd[i], 'lat': lats[n], 'lon': lons[n]})

                            ofile.write(str(SAT_NAMES[i]) + " ")
                            ofile.write(
                                str(t.utc_datetime().date()) + " " + str(t.utc_datetime().time().strftime("%H:%M")))
                            ofile.write(f"\nlat {round(ll[0].degrees, 3)}, lon {round(ll[1].degrees, 3)}, "
                                        f"dist {round(dist_km, 2)} km\n\n")

        res_list[n] = sorted(res_list[n], key=lambda x: x['time'])  # sorted by time (but sometimes it does not work)
    ofile.close()
    return res_list, np.array(arr_for_draw)


def calc_from_file(name, distance, start_date, speed, save_name):
    if name[-3:] == "kml":
        # reading kml file
        fiona.drvsupport.supported_drivers['KML'] = 'rw'
        geo_df = gpd.read_file(name, driver='KML')
        track_df = pd.DataFrame(geo_df)["geometry"]

        # preparing data for calculation
        lat = [track_df[i].y for i in range(track_df.shape[0] - 1)]
        lon = [track_df[i].x for i in range(track_df.shape[0] - 1)]
        lat, lon, track_time = calc_track(lat, lon, start_date, speed)
        return calc(distance, lat, lon, track_time, save_name), track_time[-1], lat, lon


def calc_sun(latitude, longitude, day_of_year, hour_minute):
    g = (360 / 365.25) * (day_of_year + hour_minute / 24)
    g_rad = math.radians(g)
    decl = 0.396372 - 22.91327 * math.cos(g_rad) + 4.02543 * math.sin(g_rad) - 0.387205 * math.cos(2 * g_rad) \
           + 0.051967 * math.sin(2 * g_rad) - 0.154527 * math.cos(3 * g_rad) + 0.084798 * math.sin(3 * g_rad)
    time_corr = 0.004297 + 0.107029 * math.cos(g_rad) - 1.837877 * math.sin(g_rad) - 0.837378 * math.cos(2 * g_rad) \
                - 2.340475 * math.sin(2 * g_rad)
    SHA = (hour_minute - 12) * 15 + longitude + time_corr

    lat_rad = math.radians(latitude)
    d_rad = math.radians(decl)
    SHA_rad = math.radians(SHA)
    SZA_rad = math.acos(math.sin(lat_rad) * math.sin(d_rad) + math.cos(lat_rad) * math.cos(d_rad) * math.cos(SHA_rad))

    return 90 - math.degrees(SZA_rad)


def calc_sunset_sunrise(latitude, longitude, day_of_year):
    hour_minute = np.linspace(0, 24, 24 * 60)
    func = np.vectorize(calc_sun)
    elev = func(latitude, longitude, day_of_year, hour_minute)

    if np.all(elev > 0):
        return -1, 1
    elif np.all(elev < 0):
        return -1, -1
    else:
        rise = np.argmax(elev > 0)  # first positive element
        set = len(elev) - np.argmax(elev[::-1] > 0)  # last positive element
        if rise == 0:  # if sunrise was tomorrow
            elev = elev[::-1]  # mirror array
            rise = len(elev) - np.argmax(elev < 0)
            set = np.argmax(elev[::-1] < 0)

    return rise / hour_minute.shape[0] * 24, set / hour_minute.shape[0] * 24
