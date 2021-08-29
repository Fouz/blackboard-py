import os
import subprocess
import pandas as pd
from func import change_file, split_file
from datetime import datetime
import time
import concurrent.futures


file_name = "data.csv"
change_file(file_name)
split_file('normalized-data.csv')

def excute_session(file):

    while True:
        df = pd.read_csv(file)
        if len(df.index) == 0:
            os.remove(file)
            break
        subprocess.call(
            ["python", "sessions.py", end_date, file])

if __name__ == "__main__":
    #  get end date
    while True:
        end_date = input("Please enter a date in this format Y-m-d: ")
        end_date1 = datetime.strptime(end_date, ("%Y-%m-%d"))
        end_date = end_date1.strftime(("%Y-%m-%dT%H:%M:%S.%fZ"))
        check_date = input(f"is {end_date1.date()} valid? (yes/no): ")
        if check_date == "yes" or check_date == "y":
            break
    print("\n")
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f1 = executor.submit(excute_session, "data1.csv")
        f1 = executor.submit(excute_session, "data2.csv")
        
    seconds = time.time() - start_time

    if os.path.isfile('data1.csv') == True:
        os.remove("data1.csv")
    if os.path.isfile('data2.csv') == True:
            os.remove("data2.csv")
    if os.path.isfile('normalized-data.csv') == True:
            os.remove("normalized-data.csv")

    print('\nTime Taken:', time.strftime("%H:%M:%S", time.gmtime(seconds)))
