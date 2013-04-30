#!/usr/bin/python
#
# Copyright (C) 2013
#
# Douglas Schilling Landgraf <dougsland@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details

import mechanize
import json
import sys
import getopt
import os.path
from urllib2 import HTTPError

VERSION = "1.0"
LIMIT_SEARCH = "20"
LOGIN_PAGE = "https://connect.garmin.com/signin"

ACTIVITIES_PAGE = "http://connect.garmin.com/proxy/activity-search-" \
        "service-1.2/json/activities?"

SHOW_ACTIVITIES_PER_PAGE = "http://connect.garmin.com/proxy/activity-search-" \
        "service-1.2/json/activities?&start=1&limit=" \
        + LIMIT_SEARCH + "&currentPage="

def usage():
    print "Usage: " +  sys.argv[0] + " [OPTIONS]"
    print "\t--user          \tGarmin connect username" 
    print "\t--password      \tGarmin connect password" 
    print "\t--totcx         \tExport garmin connect data to TCX" \
            " (Garmin XML format)" 
    print "\t--tokml         \tExport garmin connect data to KML" \
            " (Google Earth XML format)"
    print "\t--togpx         \tExport garmin connect data to GPX" \
            " (GPS Exchange Format)"
    print "\t--help          \tThis help menu\n"

    print "Example:"
    print "\t" + sys.argv[0] + " --user dougsland --password" \
            " SuperPassword --totcx"

def login(br_req, user, pwd):
    try:
        br_req.open(LOGIN_PAGE)
    except HTTPError, e:
        if e.code == 404:
            print "Cannot find URL %s" % LOGIN_PAGE
            sys.exit(1)

    print "Logging into garmin connect..."
    br_req.select_form('login')
    br_req['login:loginUsernameField'] = user
    br_req['login:password'] = pwd
    br_req.submit()

def export_data(br_req, type_export):
    try:
        output = br_req.open(ACTIVITIES_PAGE)
    except HTTPError, e:
        if e.code == 403:
            print "Looks like username/password aren't correct?"
            sys.exit(1)
        if e.code == 404:
            print "Cannot find URL %s" % ACTIVITIES_PAGE
            sys.exit(1)

    json_data = output.read()
    output.close()

    data = json.loads(json_data)
    total_activities = 0

    for page in range(1, data['results']['totalPages']+1):
        url = SHOW_ACTIVITIES_PER_PAGE + str(page)

        output = br_req.open(url)
        json_data = output.read()
        output.close()

        data = json.loads(json_data)

        for i in range(len(data['results']['activities'])):
            total_activities += 1

            name_activity = data['results']['activities'][i] \
                    ['activity']['activityName']

            id_activity = data['results']['activities'][i] \
                    ['activity']['activityId']

            export_file = str(id_activity) + "." + type_export

            if not os.path.exists(export_file):
                url_get = "http://connect.garmin.com/proxy/activity-" \
                    "service-1.2/" + str(type_export) + "/activity/" + \
                    str(id_activity) + "?full=true"

                try:
                    output = br_req.open(url_get)
                except HTTPError, e:
                    if e.code == 500:
                        print "Garmin connect is temporarily down" \
                                " for maintenance."
                        sys.exit(1)

                print "Downloading activity: %s file: %s.%s" % \
                        (name_activity, id_activity, type_export)

                with open(export_file, 'a') as act_file:
                    act_file.write(output.read())

                output.close()

    print "Number total activities: %s" % total_activities

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "u:p:tkghv", ["user=",
                "password=", "totcx", "tokml", "togpx", "help", "version"])
    except getopt.GetoptError, err:
        print(err)
        sys.exit(1)

    for o, a in opts:
        if o in ("-u", "--user"):
            user = a
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-p", "--password"):
            password = a
        elif o in ("-t", "--totcx"):
            type_export = "tcx"
        elif o in ("-f", "--tokml"):
            type_export = "kml"
        elif o in ("-f", "--togpx"):
            type_export = "gpx"
        elif o in ("-v", "--version"):
            print VERSION
            sys.exit(0)
        else:
            assert False, "unhandled option"
            sys.exit(1)

    argc = len(sys.argv)
    if argc != 6:
        usage()
        sys.exit(0)

    br_req = mechanize.Browser()
    login(br_req, user, password)
    export_data(br_req, type_export)
