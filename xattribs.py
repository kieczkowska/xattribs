import xattr
import os
import datetime as dt
import sqlite3
import argparse
import sys
import json


def hex_to_int(string):
    string = ''.join(reversed(string.split()))
    return int(string,16)

def list_airdropped_files(directory):

        airdropped_files = {}
        noq_files = []
        for file in os.listdir(directory):
            try:
                quarantine = xattr.getxattr("{}/{}".format(directory, file), "com.apple.quarantine")
                quarantine = quarantine.decode("utf-8")
                if "sharingd" in quarantine:
                    temp = {}
                    time = quarantine.split(";")[1]
                    unixTS = 978307200
                    date = dt.datetime.fromtimestamp(hex_to_int(time))
                    date = str(date)

                    temp["file_name"] = file
                    temp["file_path"] = "{}{}".format(directory, file)
                    temp["download_time"] = date

                    airdropped_files[quarantine.split(";")[-1]] = temp


            except FileNotFoundError:
                print("#### ERROR ####\nOops. Are you sure the given directory exists?")
                sys.exit(1)
            except OSError as error:
                noq_files.append(file)
        print("Files in {} without the com.apple.quarantine attribute: {}\n".format(directory, noq_files))
        return airdropped_files

stream = os.popen('id -un')
username = stream.read().strip()
# feel free to complete this with your values for faster usage
path = ""
path2db = "/Users/{}/Library/Preferences/com.apple.LaunchServices.QuarantineEventsV2".format(username)
pretty_print = False

parser = argparse.ArgumentParser(description="xattribs - a tool to view metadata of AirDropped files in a given directory.")
parser.add_argument('dir', default=path,
                    help='path to directory containing files of interest')
parser.add_argument('--db', default=path2db,
                    help='''path to the QuarantineEvents database; by default {}'''.format(path2db))
parser.add_argument('--pretty-print', action='store_true',
                    help='human-readable output')
parser.add_argument('--json', action='store_true',
                    help='JSON output')
args = parser.parse_args()
path = args.dir
path2db = args.db
pretty_print = args.pretty_print
json_print = args.json

file_list = list_airdropped_files(path)
try:
    conn = sqlite3.connect(path2db)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT LSQuarantineEventIdentifier as EventID, datetime(LSQuarantineTimeStamp + strftime('%s','2001-01-01'), 'unixepoch') as TimestampUTC, LSQuarantineSenderName as SenderName FROM LSQuarantineEvent WHERE LSQuarantineAgentName LIKE 'sharingd';");

    for row in cursor:
        if row[0] in file_list.keys():
            file_list[row[0]]["sender_name"] = row[2]

    if pretty_print == True:
        for file in file_list:
            uid = file
            print('''\nFile {}
            Path: {}
            Download time: {}
            Sender name: {}'''.format(file_list[uid]["file_name"],
                                      file_list[uid]["file_path"],
                                      file_list[uid]["download_time"],
                                      file_list[uid]["sender_name"]))
    elif json_print == True:
        print(json.dumps(file_list))

except sqlite3.OperationalError:
    print("#### ERROR ####\nOops. You're right you gave the right path to db?")
except FileNotFoundError:
    print("#### ERROR ####\nOops. Are you sure the given directory exists?")
