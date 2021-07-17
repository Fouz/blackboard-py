import os
import subprocess
import time
import sys
import pandas as pd
from func import change_file

file_name = "data.csv"


if (os.path.isfile('updated-data.csv') and os.path.isfile('reading-file.csv')) == False:
    change_file(file_name)

while True:
    df = pd.read_csv("reading-file.csv")

    if len(df.index) == 0:
        break
    subprocess.call(["python", "sessions.py"])
    print("Restarting...\n")
    length = len(df.index)
    # time.sleep(0.2)

print("in order to start again please delete updated-data.csv and reading-file.csv ")
exit()
