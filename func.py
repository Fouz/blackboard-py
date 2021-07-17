import datetime
from datetime import timedelta
import pandas as pd
from datetime import date


def check_session(session_dic, existing_sessions):

    res = []
    keys = ["name", "recurrenceRule", "startTime", "endTime"]
    for dic in existing_sessions:
        updated_dict = dict((k, dic[k]) for k in keys if k in dic)
        res.append(updated_dict)

    for s in res:
        start = datetime.datetime.strptime(
            s["startTime"], "%Y-%m-%dT%H:%M:%S.%fZ").time()
        s["startTime"] = str(start)
        end = datetime.datetime.strptime(
            s["endTime"], "%Y-%m-%dT%H:%M:%S.%fZ").time()
        s["endTime"] = str(end)

        end_date = s["recurrenceRule"]["endDate"]
        s["recurrenceRule"]["endDate"] = str(
            datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ").date())

    return(session_dic in res)


def change_day_name(day):
    day = str(day).strip()
    switcher = {
        "الأحد": "su",
        "الاحد": "su",
        "الاثنين": "mo",
        "الإثنين": "mo",
        "الثلاثاء": "tu",
        "الاربعاء": "we",
        "الأربعاء": "we",
        "الخميس": "th",
        "الجمعة": "fr",
        "السبت": "sa",
    }
    return(switcher.get(day, "Invalid day"))


def change_file(file):

    df = pd.read_csv(
        file, usecols=["COURSE_ID", "DAY_NAME", "START_TIME", "END_TIME"])
    df.dropna(subset=["DAY_NAME", "START_TIME", "END_TIME"], inplace=True)
    df.sort_values(by=['COURSE_ID'], inplace=True)
    df["DAY_NAME"] = df["DAY_NAME"].apply(lambda val: change_day_name(val))
    df = df.groupby(["COURSE_ID", "START_TIME", "END_TIME"]
                    ).agg(lambda x: x.tolist())
    df.to_csv('reading-file.csv')
    df.to_csv('updated-data.csv')


def sessions(course):
    new_data = []
    for key, value in course.items():
        session_name = key
        for key, value in value.items():
            start_time = datetime.datetime.strptime(
                key.split("-")[0], "%H:%M").time()
            start_time = subtract_3_hours((datetime.datetime.combine(
                date.today(), start_time)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

            end_time = datetime.datetime.strptime(
                key.split("-")[1], "%H:%M").time()
            end_time = subtract_3_hours((datetime.datetime.combine(
                date.today(), end_time)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
            days_of_week = value
            new_data.append({"course_id": session_name, "start_time": start_time,
                             "end_time": end_time, "days_of_week": days_of_week})
    return new_data


def drop_course(course_id):
    df = pd.read_csv("reading-file.csv")
    index_ = df[df['COURSE_ID'] == course_id].index
    df.drop(index_, inplace=True)
    df.to_csv("reading-file.csv", index=False)


def subtract_3_hours(date_time):

    time_str = date_time
    date_format_str = "%Y-%m-%dT%H:%M:%S.%fZ"
    given_time = datetime.datetime.strptime(time_str, date_format_str)
    final_time = given_time - timedelta(3)
    final_time_str = final_time.strftime(date_format_str)
    return(final_time_str)


def read_file(file):

    data = pd.read_csv(file)
    df = data.rename(columns={'COURSE_ID': 'course_id', "START_TIME": "start_time",
                              "END_TIME": "end_time", "DAY_NAME": "days_of_week"})
    df["days_of_week"] = df["days_of_week"].apply(eval)
    df_dict = df.to_dict(orient='records')
    return df_dict


def group_sessions(data):
    updated_data = {}
    for course in data:
        day = course["days_of_week"]
        key = f"{course['start_time']}-{course['end_time']}"
        course_id = course["course_id"]
        if course_id not in updated_data:
            updated_data[course_id] = {}
        if key not in updated_data[course_id]:
            updated_data[course_id][key] = []
        if day not in updated_data[course_id][key]:
            updated_data[course_id][key] = day
    return(updated_data)
