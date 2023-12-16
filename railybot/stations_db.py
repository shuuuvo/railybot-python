import pandas as pd
import difflib


def get_db():
    return pd.read_csv('_db/station_code.csv')


def get_delay_db():
    return pd.read_csv('_db/delay_stations.csv')


def get_closest_city(text, list):
    closest = difflib.get_close_matches(text, list, cutoff=0.75)
    if len(closest) > 0:
        values = [get_difference(text, x) for x in closest]
        return closest[values.index(max(values))]
    else:
        return None


def get_difference(text, ref):
    count = 0
    for _ in difflib.ndiff(list(text.lower()), list(ref.lower())):
        if _[0] != '+' and _[0] != '-':
            count += 1
    return count / max(len(text), len(ref))
