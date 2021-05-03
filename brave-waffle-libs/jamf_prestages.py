#!/usr/bin/env python

"""jamf_prestage.py
A tool to view the Jamf cloud console prestage information for computer and mobile
devices via API call.
"""

#
#   GitHub: @captam3rica
#

#######################################################################################
#
#   A tool to view the Jamf cloud console prestage information for computer and mobile
#   devices via API call.
#
#   usage: jamf_prestage.py [-h] --mdmurl MDMURL [--get-smartgroups] [--add-
#          smartgroup] --filepath FILEPATH [--version]
#
#######################################################################################


__version__ = "1.0.0"


import argparse
import base64
import csv
import json
import os
import sys

import getpass
import requests

# Script name
SCRIPT_NAME = sys.argv[0]


def argument_parser():
    """Build the arg parser"""
    parser = argparse.ArgumentParser(prog=f"{SCRIPT_NAME}", allow_abbrev=False)

    parser.version = __version__
    parser.add_argument(
        "--mdmurl",
        type=str,
        help="Jamf Pro tenant url (example.jamfcloud.com).",
        required=True,
    )

    parser.add_argument(
        "--computer-prestages",
        action="store_true",
        help="List the computer prestages in Jamf console.",
        required=False,
    )

    parser.add_argument(
        "--mobile-prestages",
        action="store_true",
        help="List the mobile device prestages in Jamf console.",
        required=False,
    )

    parser.add_argument(
        "--search-mobile-assignment",
        type=str,
        metavar="[prestage_id]",
        help="Search for devices in a device prestage. Pass the prestage id. Requires that a file be passed with the --file-input flag.",
        required=False,
    )

    parser.add_argument(
        "--input-file",
        type=str,
        metavar='"/path/to/file"',
        help="Enter path to the spreadsheet(csv file) or drag the file into this Terminal window.",
        required=False,
    )

    parser.add_argument("--version", action="version", help="Show this tools version.")

    arguments = parser.parse_args()

    return arguments


def get_username():
    """Return the username entered"""
    return input("Enter Jamf Pro username: ")


def get_password():
    """Return the user's password"""
    count = 1
    password = None

    while True and count <= 3:
        password = getpass.getpass(prompt="Enter password: ", stream=None)
        count += 1
        return password


def get_access_token(url, headers):
    """Return the Bearer token from Jamf"""
    endpoint = "/uapi/auth/tokens"
    access_token = None

    try:
        response = requests.post(url + endpoint, headers=headers, timeout=15)

        if response.status_code is requests.codes["ok"]:
            data = response.json()
            access_token = data["token"]

        response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"{error}")
        print("Failed to return token ...")
        # Let the user know that a 401 could mean that the creds are wrong
        if response.status_code == 401:
            print("Make sure that your credentials are entered correctly ...")
            sys.exit()

    return access_token


def build_api_headers(auth_token):
    """Return headers containing the bearer token as authorization"""
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    return headers


def invalidate_access_token(url, headers):
    """Return the Bearer token from Jamf"""
    endpoint = "/uapi/auth/invalidateToken"

    try:
        response = requests.post(url + endpoint, headers=headers, timeout=15)

        if response.status_code == 204:
            print("Access Token scrubbed ...")

        response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print("Failed to kill access token ...")
        sys.exit(f"Error: {error}")


def load_csv_file_contents(file):
    """Open the csv file and return the data"""
    csv_data = []
    with open(file, mode="r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for line in reader:
            csv_data.append(line)
    return csv_data


def jamf_computer_prestages(mdmurl, headers, page=0, page_size=100):
    """Return computer prestage profiles from Jamf console"""
    endpoint = (
        f"/uapi/v2/computer-prestages?page={page}&page-size={page_size}&sort=id%3Aasc"
    )

    try:
        response = requests.get(mdmurl + endpoint, headers=headers, timeout=30)

        if response.status_code is requests.codes["ok"]:
            data = response.json()
            results = data["results"]
            print("Prestage ID\tPrestage Name")
            print("----------------------------------------------")
            for prestage in results:
                print(f"{prestage['id']}\t\t{prestage['displayName']}")
            print("")

        response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"{error}")
        print("Failed to retrieve computer prestage profiles ...")
        # Let the user know that a 401 could mean that the creds are wrong
        if response.status_code == 401:
            print("Make sure that your credentials are entered correctly ...")
            sys.exit()


def jamf_mobile_device_prestages(mdmurl, headers, page=0, page_size=100):
    """Return mobile device prestage profiles from Jamf console"""
    endpoint = f"/uapi/v2/mobile-device-prestages?page={page}&page-size={page_size}&sort=id%3Aasc"

    try:
        response = requests.get(mdmurl + endpoint, headers=headers, timeout=30)

        if response.status_code is requests.codes["ok"]:
            data = response.json()
            results = data["results"]
            print("Prestage ID\tPrestage Name")
            print("----------------------------------------------")
            for prestage in results:
                print(f"{prestage['id']}\t\t{prestage['displayName']}")
            print("")

        response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"{error}")
        print("Failed to retrieve mobile device prestage profiles ...")
        # Let the user know that a 401 could mean that the creds are wrong
        if response.status_code == 401:
            print("Make sure that your credentials are entered correctly ...")
            sys.exit()


def device_prestage_scope(mdmurl, headers, device_id):
    """Return device scope for a specific mobile device prestage"""
    endpoint = f"/uapi/v1/mobile-device-prestages/{device_id}/scope"
    device_list = []
    try:
        response = requests.get(mdmurl + endpoint, headers=headers, timeout=30)
        if response.status_code is requests.codes["ok"]:
            data = response.json()
            assignments = data["assignments"]
            for device in assignments:
                device_list.append(device["serialNumber"])

        response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"{error}")
        print("Failed to retrieve mobile device prestage profiles ...")
        # Let the user know that a 401 could mean that the creds are wrong
        if response.status_code == 401:
            print("Make sure that your credentials are entered correctly ...")
            sys.exit()

    return device_list


def main():
    """The magic happens here"""

    # Store the arguments passed to the parser
    arguments = argument_parser()

    if arguments.mdmurl:
        print(f"Your Jamf Cloud URL is: https://{arguments.mdmurl}")
        mdmurl = f"https://{arguments.mdmurl}"

    # Build the basic headers by asking the user for their username and password
    basic_headers = {
        "Authorization": "Basic %s"
        % base64.b64encode(f"{get_username()}:{get_password()}".encode("utf-8")).decode(
            "utf-8"
        ),
        "Accept": "application/json",
        "Content-Type": "text/plain",
        "Cache-Control": "no-cache",
    }

    # Get access token and create headers.
    access_token = get_access_token(url=mdmurl, headers=basic_headers)
    access_headers = build_api_headers(auth_token=access_token)

    if arguments.input_file:
        file = arguments.input_file
        # Make sure the input file exists at the specified path.
        if not os.path.exists(file):
            print(f"The file {os.path.basename(file)} does not exist ...")
            sys.exit()
        # Load input file Contents
        input_file_data = load_csv_file_contents(file)

    if arguments.computer_prestages:
        jamf_computer_prestages(mdmurl, access_headers)

    if arguments.mobile_prestages:
        jamf_mobile_device_prestages(mdmurl, access_headers)

    if arguments.search_mobile_assignment:
        scoped_devices_list = device_prestage_scope(
            mdmurl, access_headers, device_id=arguments.search_mobile_assignment
        )

        for record in input_file_data:
            record_serial_number = record["serial_number"].lstrip("S")
            if record_serial_number in scoped_devices_list:
                print(f"{record_serial_number}: {CHECKMARK}")
            else:
                print(f"{record_serial_number}: {XMARK}")

    # Cleanup the bearer token
    invalidate_access_token(mdmurl, access_headers)


if __name__ == "__main__":
    main()
