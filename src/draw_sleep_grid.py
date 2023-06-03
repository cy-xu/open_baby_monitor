"""
when called, read the recent 7 days' sleep data from csv file
each line is like "2023-05-26,17:15,0,0" but many lines are missing
second to last element, 0: not in crib, 1: in crib
last element, 0: no movement, 1: baby_moving
each hour is split into 5-minute slots
first build a placeholder 2d array of 7*(24*12) elements
then read the real data from csv file to match existing slots
for missing slots, fill with -1
return a 2d array of 7*(24*12) elements
CY Xu, 2021-06-02
"""

import pandas as pd
import datetime
import numpy as np


def get_sleep_data():
    # get the current date
    today = datetime.date.today()
    # get the date of 6 days ago, then it's a week of data
    six_days_ago = today - datetime.timedelta(days=6)
    # read the csv file
    df = pd.read_csv("baby_sleep_data.csv", header=None)
    # convert the first column to a date object
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], format="%Y-%m-%d").dt.date
    # filter the data by date range
    df = df[df.iloc[:, 0] >= six_days_ago]
    # create a placeholder 2D array
    sleep_data = [[-1] * (24 * 12) for _ in range(7)]

    # fill in the array with real data
    for _, row in df.iterrows():
        date, time_str, in_crib, moving = row

        time = datetime.datetime.strptime(time_str, "%H:%M").time()
        slot = (time.hour * 12) + (time.minute // 5)
        day_offset = (date - six_days_ago).days
        assert day_offset < 7

        if in_crib == 1:
            if moving == 1:
                sleep_data[day_offset][slot] = 2
            else:
                sleep_data[day_offset][slot] = 1
        else:
            sleep_data[day_offset][slot] = 0

    # return the sleep data array
    sleep_data = np.array(sleep_data).flatten().tolist()
    return sleep_data


if __name__ == "__main__":
    get_sleep_data()
