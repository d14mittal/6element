#!/usr/bin/python

from multiprocessing import Pool
from opening_hours import OpeningHours
import datetime
import dateutil.parser
import json
import math
import os
import pandas as pd
import pytz
import sys

# Help message
if (len(sys.argv) == 1 or sys.argv[1] == "-h") and 0 == 1:
    print "Usage: " + sys.argv[0] + " json_output [csv_output]"
    print
    print " `-> Print the analysis as json into the json_output file, and,"
    print "     if another file is given, write as CSV the informations concerning"
    print "     the maximum amount of WiFi devices measured by day, by sensor, into"
    print "     the csv_output file."
    print
    exit()

def json_from_file(relative_path):
    with open(os.path.dirname(os.path.abspath(__file__)) + "/" + relative_path) as fs:
        return json.load(fs)

# Loading all sensors' datas
weather_forecast = json_from_file('../sensors/weather.json')
places = json_from_file("/../sensors/all_places_infos.json")
opening_hours = {}
for place in places:
    opening_hours[str(place["id"])] = OpeningHours(json_from_file("../sensors/opening_hours-" + str(place["id"]) + ".json")[0]['opening_hours'])

allsensors = []
base = datetime.datetime.today()
week_day = {"Mon": 0,
        "Tue": 1,
        "Wed": 2,
        "Thu": 3,
        "Fri": 4,
        "Sat": 5,
        "Sun": 6}

# Initializing timezone
paris = pytz.timezone('Europe/Paris')
utc = pytz.utc

# Analyzing dates up to 300 days back
date_list = {}
for x in range(0, 300):
    date_list[(base - datetime.timedelta(days = x)).strftime("%Y-%m-%d")] = []

   #if (month > 3) or (month == 3 and day > 27):

def retrieve_hour(measure):
    date = dateutil.parser.parse(measure["date"])
    date = date - datetime.timedelta(minutes = date.minute % 30, seconds = date.second, microseconds = date.microsecond)
    return date

def retrieve_nb_measured(measure):
    return len(measure["value"])

def get_level(median, nb):
    if (nb <= median):
        return (0)
    if (nb <= 2 * median):
        return (1)
    return (2)

def get_prev(df, date):
    date = date - datetime.timedelta(hours = 1)
    if (date in df.index):
        return df.loc[date]["Nb_measured"]
    return 0

# Processing statistics from the JSON got from the API
def process_sensor(sensor, measures):

    # If no measures were retrieved
    if (len(measures) == 0):
        print "No measures acquired for " + sensor["name"].encode("utf-8") + ", aborting process for the sensor..."
        return (None)

    print "Processing sensor: \"" + sensor["name"].encode("utf-8") + "\"..."

    # Building dataset
    df = pd.DataFrame(data = list(zip(map(retrieve_hour, measures), map(retrieve_nb_measured, measures))), columns = ["Date", "Nb_measured"])
    df["is_open"] = df.apply(lambda row: opening_hours[str(sensor["id"])].is_open(row["Date"].astimezone(paris)), axis = 1)

    median = math.ceil(df[df["is_open"] == 1]["Nb_measured"].median() + 0.01)

    # Grouping duplicates:
    df = df.groupby("Date").mean()


    # Adding features

    df["Previous"]            = df.apply(lambda row: get_prev(df, row.name), axis = 1)
    df["Day_of_week"]         = df.apply(lambda row: week_day[row.name.strftime("%a")], axis = 1)
    df["Hour_of_day"]         = df.apply(lambda row: row.name.hour, axis = 1)
    df["Month"]               = df.apply(lambda row: row.name.month, axis = 1)

    df["Weather"]             = df.apply(lambda row: int(weather_forecast[str(row.name.year)][str(row.name.month)][str(row.name.day)]["weather"][str(row.name.hour - 1 if row.name.hour else 0)]), axis = 1)

    # Additionnal features (disabled by default due to decreasing of accuracy):

    #df["Weather_Quality"]     = df.apply(lambda row: int(weather_forecast[str(row.name.year)][str(row.name.month)][str(row.name.day)]["weather_quality"][str(row.name.hour - 1)]), axis = 1)
    #df["Weather_Type"]        = df.apply(lambda row: int(weather_forecast[str(row.name.year)][str(row.name.month)][str(row.name.day)]["weather_type"][str(row.name.hour - 1)]), axis = 1)
    #df["Weather_Temperature"] = df.apply(lambda row: int(weather_forecast[str(row.name.year)][str(row.name.month)][str(row.name.day)]["temperature"][str(row.name.hour - 1)] / 10), axis = 1)


    # Get the level of the number of people measured, depending on the median of the list
    #  - The first one set the lower level to each measures got on closed hours of the place
    #  - The second one set the level for each hours including closed ones
    #
    # Please comment out the method you want to use

    df["Level"]               = df.apply(lambda row: (get_level(median, row["Nb_measured"]) if (row["is_open"]) else 0), axis = 1)
    #df["Level"]               = df.apply(lambda row: (get_level(median, row["Nb_measured"])), axis = 1)


    # Removing measures on closed hours:

    #df = df[df["is_open"] == 1]
    #del df["is_open"]


    # Output the mean number of people spotted by hour:
    df.to_csv("dataset_sensor-" + str(sensor["id"]) + ".csv")

    return (df)

# This function will be given as parameter to the thread pool
def parallelize(sensor):
    return process_sensor(sensor, json_from_file("../sensors/sensor-" + str(sensor["id"]) + "_wifi.json"))

# Processing datas in multithread
Pool(len(places) / 2).map(parallelize, places)
