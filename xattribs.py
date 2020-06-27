import xattr
import os
import datetime as dt
import sqlite3
import argparse
import sys
import json

def pretty_print(file_list, flag):
    if flag == "airdrop":
        for file in file_list:
            uid = file
            print('''\nFile {}
            Path: {}
            Time received: {}
            Sender name: {}'''.format(file_list[uid]["file_name"],
                                      file_list[uid]["file_path"],
                                      file_list[uid]["download_time"],
                                      file_list[uid]["sender_name"]))
    elif flag == "browser":
        for file in file_list:
            uid = file
            print('''\nFile {}
            Path: {}
            Browser name: {}
            Time downloaded: {}
            Origin URL: {}
            Data URL: {}'''.format(file_list[uid]["file_name"],
                                      file_list[uid]["file_path"],
                                      file_list[uid]["browser_name"],
                                      file_list[uid]["download_time"],
                                      file_list[uid]["origin_url"],
                                      file_list[uid]["data_url"]))
    return

# redo this to also do non-airdrop stuffs
def hex_to_int(string):
    string = ''.join(reversed(string.split()))
    return int(string,16)

def list_airdropped_files(directory):

        airdropped_files = {}
        downloaded_files = {}
        noq_files = []
        for file in os.listdir(directory):
            try:
                quarantine = xattr.getxattr("{}/{}".format(directory, file), "com.apple.quarantine")
                quarantine = quarantine.decode("utf-8")
                agent = quarantine.split(";")[2]

                temp = {}
                time = quarantine.split(";")[1]
                unixTS = 978307200
                date = dt.datetime.fromtimestamp(hex_to_int(time))
                date = str(date)

                temp["file_name"] = file
                temp["file_path"] = "{}/{}".format(directory, file)
                temp["download_time"] = date

                if agent == "sharingd":
                    airdropped_files[quarantine.split(";")[-1]] = temp
                elif agent in {"Chrome", "Brave", "Opera", "Firefox", "Google Chrome"}:
                    downloaded_files[quarantine.split(";")[-1]] = temp


            except FileNotFoundError:
                print("#### ERROR ####\nOops. Are you sure the given directory exists?")
                sys.exit(1)
            except OSError as error:
                noq_files.append(file)
        print("Files in {} without the com.apple.quarantine attribute: {}\n".format(directory, noq_files))
        return airdropped_files, downloaded_files

stream = os.popen('id -un')
username = stream.read().strip()
# feel free to complete this with your values for faster usage
path = ""
path2db = "/Users/{}/Library/Preferences/com.apple.LaunchServices.QuarantineEventsV2".format(username)

parser = argparse.ArgumentParser(description="xattribs - a tool to view metadata of AirDropped files in a given directory.")
parser.add_argument('dir', default=path,
                    help='path to directory containing files of interest')
parser.add_argument('--db', default=path2db,
                    help='''path to the QuarantineEvents database; by default {}'''.format(path2db))
parser.add_argument('--json', action='store_true',
                    help='JSON output')
args = parser.parse_args()
path = args.dir
path2db = args.db
json_print = args.json

airdropped_files, downloaded_files = list_airdropped_files(path)

try:
    conn = sqlite3.connect(path2db)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT LSQuarantineEventIdentifier as EventID, datetime(LSQuarantineTimeStamp + strftime('%s','2001-01-01'), 'unixepoch') as TimestampUTC, LSQuarantineSenderName as SenderName, LSQuarantineOriginURLString as OriginURL, LSQuarantineDataURLString as DataURL, LSQuarantineAgentName as Agent FROM LSQuarantineEvent WHERE LSQuarantineAgentName IN ('sharingd', 'Chrome', 'Safari', 'Opera', 'Brave', 'Firefox');")

    for row in cursor:
        if row[0] in airdropped_files.keys():
            airdropped_files[row[0]]["sender_name"] = row[2]
        elif row[0] in downloaded_files.keys():
            downloaded_files[row[0]]["origin_url"] = row[3]
            downloaded_files[row[0]]["data_url"] = row[4]
            downloaded_files[row[0]]["browser_name"] = row[5]

    if json_print == True:
        print("\n\n\n    💨💨💨 AirDropped files: \n", json.dumps(airdropped_files))
        print("\n\n\n    🔥🔥🔥 Downloaded files: \n", json.dumps(downloaded_files))
    else:
        print("\n\n\n    💨💨💨 AirDropped files: \n")
        pretty_print(airdropped_files, "airdrop")
        print("\n\n\n    🔥🔥🔥 Downloaded files: \n")
        pretty_print(downloaded_files, "browser")


except sqlite3.OperationalError as e:
    print("#### ERROR ####\nOops. You're right you gave the right path to db?")

except FileNotFoundError:
    print("#### ERROR ####\nOops. Are you sure the given directory exists?")
