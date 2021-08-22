import datetime
from datetime import timedelta
import pandas as pd
from datetime import date
import json


def check_session(session_dic, existing_sessions):
    # try:
    #     end_date = session_dic["recurrenceRule"]["endDate"]
    #     session_dic["recurrenceRule"]["endDate"] = str(datetime.datetime.strptime(
    #     end_date, "%Y-%m-%dT%H:%M:%S.%fZ").date())
    # except: pass
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
        try:
            end_date = s["recurrenceRule"]["endDate"]
            s["recurrenceRule"]["endDate"] = str(
                datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ").date())
        except:
            pass

    if session_dic in res:
        return True
    else:
        return False


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


def subtract_3_hours(val):
    dd = datetime.datetime.strptime(val, '%H:%M')
    final_time = ((dd - (timedelta(hours=3, minutes=0))).time()
                  ).strftime("%H:%M")
    return(final_time)


def change_file(file):
    df = pd.read_csv(
        file, usecols=["COURSE_ID", "DAY_NAME", "START_TIME", "END_TIME"])
    df.dropna(subset=["DAY_NAME", "START_TIME", "END_TIME"], inplace=True)
    df.sort_values(by=['COURSE_ID'], inplace=True)
    df["DAY_NAME"] = df["DAY_NAME"].apply(lambda val: change_day_name(val))
    df = df.groupby(["COURSE_ID", "START_TIME", "END_TIME"]
                    ).agg(lambda x: x.tolist())
    df.to_csv('normalized-data.csv')

    df2 = pd.read_csv("normalized-data.csv")
    df2["START_TIME"] = df2["START_TIME"].apply(
        lambda val: subtract_3_hours(val))
    df2["END_TIME"] = df2["END_TIME"].apply(
        lambda val: subtract_3_hours(val))
    df2.to_csv('normalized-data.csv')


def sessions(course):
    new_data = []
    for key, value in course.items():
        session_name = key
        for key, value in value.items():
            start_time = datetime.datetime.strptime(
                key.split("-")[0], "%H:%M").time()
            start_time = (datetime.datetime.combine(
                date.today(), start_time)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            end_time = datetime.datetime.strptime(
                key.split("-")[1], "%H:%M").time()
            end_time = (datetime.datetime.combine(
                date.today(), end_time)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            days_of_week = value
            new_data.append({"course_id": session_name, "start_time": start_time,
                             "end_time": end_time, "days_of_week": days_of_week})
    return new_data


def drop_course(course_id, reading_file):
    df = pd.read_csv(reading_file)
    index_ = df[df['COURSE_ID'] == course_id].index
    df.drop(index_, inplace=True)
    df.to_csv(reading_file, index=False)


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


def split_file(file):

    data = pd.read_csv(file)
    rowsize1 = len(data.index) // 2 + len(data.index) % 2

    df = data[:rowsize1]
    df2 = data[rowsize1:]

    df.to_csv(f'data1.csv', index=False)
    df2.to_csv(f'data2.csv', index=False)

    df = pd.read_csv("data1.csv")
    course_id = df.tail(1)['COURSE_ID'].values[0]
    # print(course_id)
    df = pd.read_csv("data1.csv")
    df = df.loc[df['COURSE_ID'] == course_id]

    df2 = pd.read_csv("data2.csv")
    df2 = df2.append(df)
    df2.to_csv("data2.csv", index=False)

    df = pd.read_csv("data1.csv")
    index_ = df[df['COURSE_ID'] == course_id].index
    df.drop(index_, inplace=True)
    df.to_csv("data1.csv", index=False)


# change_file("data.csv")
# reading_file = 'normalized-data.csv'
# data1 = read_file(reading_file)
# session_def = group_sessions(data1)
