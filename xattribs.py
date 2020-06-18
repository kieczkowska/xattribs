import xattr
import os
import datetime as dt
import time
from biplist import *
import sqlite3
import argparse


def hex_to_int(string):
    string = ''.join(reversed(string.split()))
    return int(string,16)

def list_airdropped_files(directory):
    airdropped_files = {}
    non_aidr = []
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
        except Exception as error:
            #continue;
            if "Attribute not found" in str(error):
                non_aidr.append(file)

            #print("ERROR: ", error)
            continue;
    print("Files / directories in the given directory which don't have the quarantine attribute: \n", non_aidr)
    return airdropped_files

# feel free to complete this with your values for faster usage
path = ""
path2db = ""
pretty_print = False

parser = argparse.ArgumentParser()
parser.add_argument('--dir', default=path,
                    help='path to directory to check')
parser.add_argument('--db', default=path2db,
                    help='path to db')
parser.add_argument('--pretty-print', action='store_true',
                    help='pretty print flag')
args = parser.parse_args()
path = args.dir
path2db = args.db
pretty_print = args.pretty_print

file_list = list_airdropped_files(path)
conn = sqlite3.connect(path2db)
conn.row_factory = sqlite3.Row
cursor = conn.execute("SELECT LSQuarantineEventIdentifier as EventID, datetime(LSQuarantineTimeStamp + strftime('%s','2001-01-01'), 'unixepoch') as TimestampUTC, LSQuarantineSenderName as SenderName FROM LSQuarantineEvent WHERE LSQuarantineAgentName LIKE 'sharingd';");

for row in cursor:
    try:
        if row[0] in file_list.keys():
            file_list[row[0]]["sender_name"] = row[2]

    except Exception as error:
        #continue;
        print("ERROR: ", error)

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
else:
    print(file_list)
