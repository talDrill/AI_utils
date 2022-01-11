from datetime import datetime, timedelta
import re


def extract_date_hour_from_str(name):
    assert len(name) == 14
    date = "{}-{}-{}".format(name[:4], name[4:6], name[6:8])
    hour = "{}:{}:{}".format(name[8:10], name[10:12], name[12:])
    return date, hour


def parse_hikvision_name(name, camera='hikvision'):
    """extract date and hour from video, based on video name downloading from hikvision"""
    # parsing fits for hikvision cameras, if new videos needs to adapt the code
    matches = re.findall('[0-9]{14}', name)
    start = extract_date_hour_from_str(matches[0])
    # end = extract_date_hour_from_str(matches[1])
    return start


def add_second_to_hour(hour: str, seconds: int):
    """hour == '%H:%M:%S"""
    new_hour = datetime.strptime(hour, '%H:%M:%S') + timedelta(seconds=seconds)
    return new_hour.strftime('%H:%M:%S')