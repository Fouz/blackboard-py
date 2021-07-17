import os.path
import sys
import json
import requests
import jwt
import time
import datetime
from datetime import timedelta
from requests.exceptions import HTTPError
from datetime import date
from func import check_session, drop_course, read_file, group_sessions, drop_course, sessions

# Tokens for Learn and Collab authentication, generated by the learn_auth() and collab_auth functions and stored as global variables.
learn_token = ""
collab_token = ""

# Learn variables, these will be populated from the configuration file
learn_url = ""
learn_key = ""
learn_secret = ""

# Collab variables, these will be populated from the configuration file
collab_url = ""
collab_key = ""
collab_secret = ""

# Helper methods
# Checks if file exists


def check_file(file_name):
    if os.path.isfile(f'./{file_name}'):
        print(
            f'***- {file_name} is required and present in the application folder.')
        return True
    else:
        print(f'***- {file_name} is required and can´t be found in the apllication folder. Please make sure the file is in place and try again.')
        return False
        sys.exit()

# Gets configuration variables from config file


def get_config():
    with open("./config.json") as conf:
        data = json.load(conf)
        global learn_url
        learn_url = data["learn_url"]
        global learn_key
        learn_key = data["learn_key"]
        global learn_secret
        learn_secret = data["learn_secret"]
        global collab_url
        collab_url = data["collab_url"]
        global collab_key
        collab_key = data["collab_key"]
        global collab_secret
        collab_secret = data["collab_secret"]
    print("***- Configuration has been set up")

# REST authentication for Learn


def learn_auth():
    global learn_token
    try:
        url_token = "/learn/api/public/v1/oauth2/token"  # POST
        params = {"grant_type": "client_credentials"}
        headers = {'Content-Type': "application/x-www-form-urlencoded"}
        r = requests.request("POST", learn_url+url_token, headers=headers,
                             params=params, auth=(learn_key, learn_secret))
        r.raise_for_status()
        # Response as Json
        data = json.loads(r.text)
        token = data["access_token"]
        print(f'***- Authentication successful! Welcome to {learn_url}.')
        return token
    except requests.exceptions.HTTPError as e:
        print("***-An error has ocurred: ")
        print(repr(e))
        sys.exit()

# REST authentication for Collaborate


def collab_auth():
    oauth_url = collab_url+"/token"
    exp = int(round(time.time() * 1000)) + 270000
    claims = {"iss": collab_key, "sub": collab_key, "exp": exp}
    # Encode the JWT assertion with the jWT module, that includes claims and the secret.
    assertion = jwt.encode(claims, collab_secret)
    credentials = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
    headers = {  # Content type is sent as a header
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    params = {  # grant credentials and assertion are sent as parameters
        'grant_type': credentials,
        'assertion': assertion
    }
    try:
        session = requests.session()
        r = session.post(oauth_url, params=params,
                         headers=headers, auth=(collab_key, collab_secret))
        r.raise_for_status()
        data = json.loads(r.text)
        print(f'***- Authentication successful! Welcome to {collab_url}.')
        collab_token = data['access_token']
        return collab_token
    except requests.exceptions.HTTPError as e:
        print("***-An error has ocurred: ")
        print(repr(e))


# Returns UUID for a Learn course, the course UUID is the external Id for the Course collaborate session context, and will be used to associate sessions to the course context.
def get_course_uuid(course_id):
    try:
        url_courses = "/learn/api/public/v2/courses/courseId:"  # GET
        auth_string = "Bearer "+learn_token
        session = requests.session()
        r = session.get(learn_url+url_courses+f"{course_id}", headers={
                        'Authorization': auth_string}, params={}, verify=True)
        r.raise_for_status()
        data = json.loads(r.text)
        print(f'***-uuid for {course_id} is {data["uuid"]}')
        return data

    except requests.exceptions.HTTPError as e:
        print("***-An error has ocurred: ")
        print(repr(e))
        sys.exit()

# In order to associate a session to a course context, we need to retrieve the context ID, in order to do so, we will leverage the external ID, as we know it is the course UUID


def get_collab_context_id(learn_course_uuid):
    authStr = "Bearer "+collab_token
    url_ctx = collab_url+"/contexts"
    params = {
        'extId': learn_course_uuid,
        'fields': 'results.id'
    }
    headers = {
        'Authorization': authStr,
        'Content-Type': 'application/json'
    }
    try:
        r = requests.get(url_ctx, params=params, headers=headers)
        r.raise_for_status
        data = json.loads(r.text)
        # print(f'***- Collaborate context id for external context id/course UUID is {data["results"][0]["id"]}.' )
        return data["results"][0]["id"]
    except requests.exceptions.HTTPError as e:
        print("***-  WOOOOPS, an error has ocurred: ")
        print(repr(e))

# Checks if there are existing sessions in a course context, and returns the session data to check settings


def check_existing_sessions(context_id):
    authStr = "Bearer "+collab_token
    url_sessions = collab_url+"/sessions"
    params = {
        "contextId": context_id
    }
    headers = {
        'Authorization': authStr,
        'Content-Type': 'application/json'
    }
    try:
        r = requests.get(url_sessions, params=params, headers=headers)
        r.raise_for_status()
        data = json.loads(r.text)
        if (data["results"]):
            # print("***- The following sessions are found in the course:")
            # print(json.dumps(data, indent=4, sort_keys=True))
            print("\n")
            return data
        else:
            print("***- No sessions found for this course")
    except requests.exceptions.HTTPError as e:
        print("***-  WOOOOPS, an error has ocurred: ")
        print(repr(e))

# Creates a Collaborate session


def create_collab_session(session_name, end_date, start_time, end_time, session_days_of_week):
    endTime = datetime.datetime.utcnow()+timedelta(days=1)
    payload = {
        "startTime": start_time,
        "endTime": end_time,
        "name": session_name,
        # new defs
        "occurrenceType": "P",
        "participantCanUseTools": "true",
        "persistentPinsEnabled": "true",
        "privateChatRestricted": "true",
        "profanityFilterEnabled": "true",
        "messagingStreamEnabled": "false",
        "raiseHandOnEnter": "false",
        "recurrenceRule": {
            "daysOfTheWeek": session_days_of_week,
            "endDate": end_date,
            "interval": 1,
            "recurrenceEndType": "on_date",
            "recurrenceType": "weekly"
        },
        "createdTimezone": "Asia/Riyadh",
        # the default settings
        "canDownloadRecording": "true",
        "showProfile": "false",
        "telephonyEnabled": "false",
        "openChair": "false",
        "mustBeSupervised": "true",
        "turnGlobalAccelerator": "false",
        "allowGuest": "false",
        "allowInSessionInvitees": "true",
        "anonymizeRecordings": "false",
        "boundaryTime": 15,
        "canAnnotateWhiteboard": "false",
        "canDownloadRecording": "true",
        "canEnableLargeSession": "true",
        "canPostMessage": "true",
        "canShareAudio": "true",
        "canShareVideo": "false",
        "editingPermission": "reader",
        "guestRole": "participant",
        "largeSessionEnable": "false",
        "integrationAttendance": {
            "enabled": "false",
        },
        "integrationAttendance": {
            "absenceThreshold": 3000,
            "enabled": "true",
            "lateThreshold": 1200,
            "presenceDurationThreshold": 250
        },
    }
    authStr = "Bearer "+collab_token
    url_sessions = collab_url+"/sessions"
    headers = {
        'Authorization': authStr,
        'Content-Type': 'application/json'
    }
    try:
        r = requests.post(url_sessions, headers=headers, json=payload)
        r.raise_for_status
        data = json.loads(r.text)
        print(f"\n{session_name} session created successfuly !!!")
        return data
    except requests.exceptions.HTTPError as e:
        print("***- WOOOOPS, an error has ocurred: ")
        print(repr(e))

# bind with id not session name


def get_collab_session_id(session_id):
    authStr = "Bearer "+collab_token
    url_sessions = collab_url+"/sessions"
    params = {
        'id': session_id,
        'fields': 'results.id'
    }
    headers = {
        'Authorization': authStr,
        'Content-Type': 'application/json'
    }
    try:
        r = requests.get(url_sessions, params=params, headers=headers)
        r.raise_for_status
        data = json.loads(r.text)
        print(
            f'***- Id for Collaborate session named {session_id} is {data["results"][0]["id"]}.')
        return data["results"][0]["id"]
    except requests.exceptions.HTTPError as e:
        print("***-  WOOOOPS, an error has ocurred: ")
        print(repr(e))

# Ties a Collaborate session to a course using Learn UUID as External context in Collaborate


def add_session_course(course_context_id, session_id):
    authStr = "Bearer "+collab_token
    payload = {
        "id": session_id
    }
    url_context = collab_url+f'/contexts/{course_context_id}/sessions'
    headers = {
        'Authorization': authStr,
        'Content-Type': 'application/json'
    }
    try:
        r = requests.post(url_context, headers=headers, json=payload)
        r.raise_for_status()
        print(
            f'Session with id {session_id} has been associated to course context {course_context_id}\n')
    except requests.exceptions.HTTPError as e:
        print("***- WOOOOPS, an error has ocurred: ")
        print(repr(e))

#  delete session by sessionId


def delete_session(session_id):

    authStr = "Bearer "+collab_token
    url_sessions = f"{collab_url}/sessions/{session_id}"
    headers = {
        'Authorization': authStr,
        'Content-Type': 'application/json'
    }
    try:
        r = requests.delete(url_sessions, headers=headers, verify=False)
        r.raise_for_status()
        print(f'Session with id {session_id} successfully deleted!')
    except requests.exceptions.HTTPError as e:
        print("***- WOOOOPS, an error has ocurred: ")
        print(repr(e))

# update session


def update_session(session_id, session_name, end_time, end_date, start_time, session_days_of_week):
    authStr = "Bearer "+collab_token
    url_sessions = f"{collab_url}/sessions/{session_id}"
    headers = {
        'Authorization': authStr,
        'Content-Type': 'application/json'
    }
    payload = {
        "startTime": start_time,
        "endTime": end_time,
        "name": session_name,
        # new defs
        "occurrenceType": "P",
        "participantCanUseTools": "true",
        "persistentPinsEnabled": "true",
        "privateChatRestricted": "true",
        "profanityFilterEnabled": "true",
        "messagingStreamEnabled": "false",
        "raiseHandOnEnter": "false",
        "recurrenceRule": {
            "daysOfTheWeek": session_days_of_week,
            "endDate": end_date,
            "interval": 1,
            "recurrenceEndType": "on_date",
            "recurrenceType": "weekly"
        },
        "createdTimezone": "Asia/Riyadh",
        # the default settings
        "canDownloadRecording": "true",
        "showProfile": "false",
        "telephonyEnabled": "false",
        "openChair": "false",
        "mustBeSupervised": "true",
        "turnGlobalAccelerator": "false",
        "allowGuest": "false",
        "allowInSessionInvitees": "true",
        "anonymizeRecordings": "false",
        "boundaryTime": 15,
        "canAnnotateWhiteboard": "false",
        "canDownloadRecording": "true",
        "canEnableLargeSession": "true",
        "canPostMessage": "true",
        "canShareAudio": "true",
        "canShareVideo": "false",
        "editingPermission": "reader",
        "guestRole": "participant",
        "largeSessionEnable": "false",
        "integrationAttendance": {
            "enabled": "false",
        },
        "integrationAttendance": {
            "absenceThreshold": 3000,
            "enabled": "true",
            "lateThreshold": 1200,
            "presenceDurationThreshold": 250
        },
    }
    try:
        r = requests.patch(url_sessions, headers=headers, json=payload)
        r.raise_for_status()
        print(f'Session with id {session_id} successfully updated!')
    except requests.exceptions.HTTPError as e:
        print("***- WOOOOPS, an error has ocurred: ")
        print(repr(e))


def compare_sessions(bb_sessions, excel_sessions, course, course_sessions, session_def):
    if bb_sessions == excel_sessions:
        asession = sessions({course: session_def[course]})
        for session in asession:
            session_object = {
                "name": session["course_id"],
                "recurrenceRule": {
                    "recurrenceType": "weekly",
                    "interval": 1,
                    "daysOfTheWeek": session["days_of_week"],
                    "recurrenceEndType": "on_date",
                    "endDate": str(datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ").date())
                },
                "startTime":  str(datetime.datetime.strptime(session["start_time"], "%Y-%m-%dT%H:%M:%S.%fZ").time()),
                "endTime": str(datetime.datetime.strptime(session["end_time"], "%Y-%m-%dT%H:%M:%S.%fZ").time())
            }
        if check_session(session_object, course_sessions["results"]):
            print("session already exist!")
        else:
            for i in range(bb_sessions):
                asession = sessions({course: session_def[course]})
                sess_id = course_sessions["results"][i]["id"]
                sess_name = asession[i]["course_id"]
                sess_end_time = asession[i]["end_time"]
                sess_start_time = asession[i]["start_time"]
                sess_days_of_week = asession[i]["days_of_week"]

                update_session(sess_id, sess_name, sess_end_time,
                               end_date, sess_start_time, sess_days_of_week)
        drop_course(asession[0]["course_id"])

    elif excel_sessions > bb_sessions:
        asession = sessions({course: session_def[course]})
        for i in range(bb_sessions):
            session_object = {
                "name": asession[i]["course_id"],
                "recurrenceRule": {
                    "recurrenceType": "weekly",
                    "interval": 1,
                    "daysOfTheWeek": asession[i]["days_of_week"],
                    "recurrenceEndType": "on_date",
                    "endDate": str(datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ").date())
                },
                "startTime":  str(datetime.datetime.strptime(asession[i]["start_time"], "%Y-%m-%dT%H:%M:%S.%fZ").time()),
                "endTime": str(datetime.datetime.strptime(asession[i]["end_time"], "%Y-%m-%dT%H:%M:%S.%fZ").time())
            }
            if check_session(session_object, course_sessions["results"]):
                print("session already exist!")
            else:
                asession = sessions({course: session_def[course]})
                sess_id = course_sessions["results"][i]["id"]
                sess_name = asession[i]["course_id"]
                sess_end_time = asession[i]["end_time"]
                sess_start_time = asession[i]["start_time"]
                sess_days_of_week = asession[i]["days_of_week"]

                update_session(sess_id, sess_name, sess_end_time,
                               end_date, sess_start_time, sess_days_of_week)
        for session in asession[bb_sessions:]:
            session_name = session['course_id']
            session_days_of_week = session["days_of_week"]
            start_time = session["start_time"]
            end_time = session["end_time"]
            session_id = create_collab_session(
                session_name, end_date, start_time, end_time, session_days_of_week)
            add_session_course(context, session_id["id"])

        drop_course(asession[0]["course_id"])

        # case 3
    else:
        asession = sessions({course: session_def[course]})
        for i in range(excel_sessions):
            session_object = {
                "name": asession[i]["course_id"],
                "recurrenceRule": {
                    "recurrenceType": "weekly",
                    "interval": 1,
                    "daysOfTheWeek": asession[i]["days_of_week"],
                    "recurrenceEndType": "on_date",
                    "endDate": str(datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ").date())
                },
                "startTime":  str(datetime.datetime.strptime(asession[i]["start_time"], "%Y-%m-%dT%H:%M:%S.%fZ").time()),
                "endTime": str(datetime.datetime.strptime(asession[i]["end_time"], "%Y-%m-%dT%H:%M:%S.%fZ").time())
            }
        if check_session(session_object, course_sessions["results"]):
            print("session already exist!")
        else:
            asession = sessions({course: session_def[course]})
            sess_id = course_sessions["results"][i]["id"]
            sess_name = asession[i]["course_id"]
            sess_end_time = asession[i]["end_time"]
            sess_start_time = asession[i]["start_time"]
            sess_days_of_week = asession[i]["days_of_week"]

            update_session(sess_id, sess_name, sess_end_time,
                           end_date, sess_start_time, sess_days_of_week)
        for session in course_sessions["results"][excel_sessions:]:
            delete_session(session["id"])
        drop_course(asession[0]["course_id"])


if __name__ == "__main__":

    check_file("config.json")
    reading_file = 'reading-file.csv'
    get_config()
    learn_token = learn_auth()
    collab_token = collab_auth()
    print("\n\n\n")
    end_date = datetime.datetime(2021, 7, 28).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    data1 = read_file(reading_file)
    session_def = group_sessions(data1)
    limit = 1
    for course in session_def:
        if limit == 2:
            break
        course_uuid = get_course_uuid(course)
        context = get_collab_context_id(course_uuid["uuid"])
        course_sessions = check_existing_sessions(context)

        if course_sessions is not None:
            bb_sessions = course_sessions["size"]
            excel_sessions = len(session_def[course].keys())
            compare_sessions(bb_sessions, excel_sessions,
                             course, course_sessions, session_def)
        if course_sessions is None:
            asession = sessions({course: session_def[course]})
            for session in asession:
                session_name = session['course_id']
                session_days_of_week = session["days_of_week"]
                start_time = session["start_time"]
                end_time = session["end_time"]
                session_id = create_collab_session(
                    session_name, end_date, start_time, end_time, session_days_of_week)
                add_session_course(context, session_id["id"])
            drop_course(asession[0]["course_id"])

        limit = limit + 1

    print('***- Exiting program')
    sys.exit()
