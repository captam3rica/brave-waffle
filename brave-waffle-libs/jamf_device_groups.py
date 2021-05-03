#!/usr/bin/env python

"""manage_smartgroups.py
A tool to add categories in the Jamf cloud console via API call.
"""

#
#   GitHub: @captam3rica
#

###############################################################################
#
#   Leverages the Jamf Cloud API to automatically add a list of smartgroup
#   to Jamf Cloud.
#
#   usage: manage_smartgroups.py [-h] --mdmurl MDMURL [--get-smartgroups] [--add-
#          smartgroup] --filepath FILEPATH [--version]
#
#   optional arguments:
#       -h, --help           show this help message and exit
#       --mdmurl MDMURL      Jamf Pro tenant url (example.jamfcloud.com).
#       --get-smartgroups    See the current smartgroups in the Jamf console.
#       --add-smartgroup     Add a smartgroup to a Jamf console.
#       --filepath FILEPATH  Enter path to the spreadsheet(csv file) or drag the file
#                            into this Terminal window.
#       --version            Show this tools version.
#
###############################################################################


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
    """Build the argument parser"""
    parser = argparse.ArgumentParser(prog=f"{SCRIPT_NAME}", allow_abbrev=False)

    parser.version = __version__
    parser.add_argument(
        "--mdmurl",
        type=str,
        metavar="example.jamfcloud.com",
        help="Jamf Pro tenant url (example.jamfcloud.com).",
        required=True,
    )

    parser.add_argument(
        "--get-computer-groups",
        action="store_true",
        help="See the current computer groups in the Jamf console.",
        required=False,
    )

    parser.add_argument(
        "--get-computer-group",
        type=str,
        metavar='"group_name"',
        help="Search for a computer group by group name.",
        required=False,
    )

    parser.add_argument(
        "--update-computer-group",
        type=str,
        metavar='"group_name"',
        help="Update Jamf computer group. Must supply name with this command.",
        required=False,
    )

    parser.add_argument(
        "--add-computer-group",
        action="store_true",
        help="Add a computer group to a Jamf console.",
        required=False,
    )

    parser.add_argument(
        "--get-mobile-groups",
        action="store_true",
        help="See the current computer groups in the Jamf console.",
        required=False,
    )

    parser.add_argument(
        "--add-mobile-group",
        action="store_true",
        help="Add a mobile smartgroup to a Jamf console.",
        required=False,
    )

    parser.add_argument(
        "--get-mobile-group",
        type=str,
        help="Search for a mobile device group by group id.",
        required=False,
    )

    parser.add_argument(
        "--input-file",
        type=str,
        help="Enter path to the spreadsheet(csv file) or drag the file into this Terminal window.",
        required=False,
    )

    parser.add_argument("--version", action="version", help="Show this tools version.")

    return parser.parse_args()


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
        print(f"Failed to return token ...")
        # Let the user know that a 401 could mean that the creds are wrong
        if response.status_code == 401:
            print(f"Make sure that your credentials are entered correctly ...")
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
        print(f"Failed to kill access token ...")
        sys.exit(f"Error: {error}")


def load_csv_file_contents(file):
    """Open the csv file and return the data"""
    csv_data = []
    with open(file, mode="r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for line in reader:
            csv_data.append(line)
    return csv_data


def jamf_computer_groups(mdmurl, headers):
    """Return all Jamf computer groups
    Returns group id, group name, and whether the group is smart.
    """
    # API URI Endpint
    endpoint = "/JSSResource/computergroups"

    results = ""

    try:

        # Make the API GET request
        response = requests.get(mdmurl + endpoint, headers=headers, timeout=30)

        # Get the received API status code
        status_code = response.status_code

        if status_code is requests.codes["ok"]:
            # If we like what we see from the API call
            data = response.json()
            results = data["computer_groups"]

        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"Requests Exception: {error}")

        # Let the user know that a 401 could mean that the creds are wrong
        if status_code == 401:
            print(f"Make sure that your credentials are entered correctly ...")
            sys.exit()

    return results


def jamf_mobile_groups(mdmurl, headers):
    """Return all Jamf mobile groups
    Returns group id, group name, and whether the group is smart.
    """
    # API URI Endpint
    endpoint = "/JSSResource/mobiledevicegroups"

    results = ""

    try:

        # Make the API GET request
        response = requests.get(mdmurl + endpoint, headers=headers, timeout=30)

        # Get the received API status code
        status_code = response.status_code

        if status_code is requests.codes["ok"]:
            # If we like what we see from the API call
            data = response.json()
            results = data["mobile_device_groups"]

        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"Requests Exception: {error}")

        # Let the user know that a 401 could mean that the creds are wrong
        if status_code == 401:
            print(f"Make sure that your credentials are entered correctly ...")
            sys.exit()

    return results


def jamf_computer_group_id(data, name):
    """Return Jamf computer group id
    Args:
        data: All jamf computer group data
        name: Group name to search for
    """
    group_id = ""
    for group in data:
        if name in group["name"]:
            group_id = group["id"]
    return group_id


def get_jamf_computer_group(mdmurl, headers, name):
    """Search for a Jamf computer group by name
    If the group is found, returns a list of computers.
    """
    endpoint = f"/JSSResource/computergroups/name/{name}"
    computer_list = []
    try:

        # Make the API GET request
        response = requests.get(mdmurl + endpoint, headers=headers, timeout=30)

        # Get the received API status code
        status_code = response.status_code

        if status_code is requests.codes["ok"]:
            # If we like what we see from the API call
            data = response.json()
            computer_group = data["computer_group"]

            print("ID\tName\t\t\tSerial Number")
            print("----------------------------------------------------------")
            for computer in computer_group["computers"]:
                print(
                    f"{computer['id']}\t{computer['name']}\t\t{computer['serial_number']}"
                )
                computer_list.append(computer)

            duplicate_computer_entries = look_for_duplicates(
                jamf_computer_group_attribute(computer_list, "serial_number")
            )

            print("")
            print(f"Group: {computer_group['name']}")
            print(f"Total Computer Records: {len(computer_group['computers'])}")
            print(f"Duplicates Found: {len(duplicate_computer_entries)}")

            if len(duplicate_computer_entries) > 0:
                for entry in duplicate_computer_entries:
                    print(entry)

            print("")

        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"Requests Exception: {error}")

        # Let the user know that a 401 could mean that the creds are wrong
        if status_code == 401:
            print(f"Make sure that your credentials are entered correctly ...")
            sys.exit()


def jamf_mobile_group(mdmurl, headers, id):
    """Search for a Jamf computer group by id
    If the group is found, returns a list of mobile devices.
    """
    endpoint = f"/JSSResource/mobiledevicegroups/id/{id}"
    print(endpoint)
    mobile_device_list = []
    try:

        # Make the API GET request
        response = requests.get(mdmurl + endpoint, headers=headers, timeout=30)

        # Get the received API status code
        status_code = response.status_code

        if status_code is requests.codes["ok"]:
            # If we like what we see from the API call
            data = response.json()

            print(data)
            mobile_group = data["mobile_device_group"]

            print("ID\tName\t\t\tSerial Number")
            print("----------------------------------------------------------")
            print(f"Group: {mobile_group['name']}")
            print(f"Total Computer Records: {len(mobile_group['mobile_devices'])}")
            for mobile_device in mobile_group["mobile_devices"]:
                print(
                    f"{mobile_device['id']}\t{mobile_device['name']}\t\t{mobile_device['serial_number']}"
                )
                mobile_device_list.append(mobile_device)

        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"Requests Exception: {error}")

        # Let the user know that a 401 could mean that the creds are wrong
        if status_code == 401:
            print(f"Make sure that your credentials are entered correctly ...")
            sys.exit()

    print("")
    print(
        f"Duplicates Found: {len(look_for_duplicates(jamf_computer_group_attribute(mobile_device_list, 'serial_number')))}"
    )
    print("")


def jamf_computer_group_attribute(data, search_key):
    """Return a list of Jamf computer attributes from a computer group
    Possible attributes: id, serial_number,"""
    attribute_list = []
    computer_list = data
    for attribute in computer_list:
        attribute_list.append(attribute[search_key])
    return attribute_list


def look_for_duplicates(data):
    """Look for duplicate computer records in a computer group"""
    dup_list = []
    unique_list = []
    computers = data
    for computer in computers:
        if computer in unique_list:
            dup_list.append(computer)
        else:
            unique_list.append(computer)
    return dup_list


def update_jamf_static_computer_group(
    mdmurl, headers, group_id, name, is_smart, serial_number
):
    """Get a list of categories defined in the Jamf Cloud console"""
    # API URI Endpint
    endpoint = f"/JSSResource/computergroups/id/{group_id}"

    payload = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <computer_group>
        <id>{group_id}</id>
        <name>{name}</name>
        <is_smart>{is_smart}</is_smart>
        <computer_additions>
            <computer>
                <serial_number>{serial_number}</serial_number>
            </computer>
        </computer_additions>
    </computer_group>"""

    try:

        # Make the API GET request
        response = requests.put(
            mdmurl + endpoint, headers=headers, data=payload, timeout=30
        )

        # Get the received API status code
        status_code = response.status_code

        if status_code == 201:
            print(f"{serial_number} added to {name} ...")
        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"Requests Exception: {error}")

        # Let the user know that a 401 could mean that the creds are wrong
        if status_code == 401:
            print(f"Make sure that your credentials are entered correctly ...")
            sys.exit()

        if status_code == 404:
            print(f"Unable to add {serial_number} to {name}")


def create_computer_group(mdmurl, headers, name):
    """Add one or more categories to the Jamf Console

    Args:
        mdmurl: The Jamf console URL
        headers: The bearer token api headers
        name: The name of the category to add to the Jamf console
    """
    # API URI Endpint
    endpoint = "/uapi/v1/categories"

    # API Payload
    payload = json.dumps({"name": "%s", "priority": 9}) % name

    status_code = ""
    count = 0

    # Loop until the http request is 201
    while status_code is not requests.codes["created"] or count == 4:

        try:
            # Make the API POST request
            response = requests.post(
                mdmurl + endpoint, headers=headers, data=payload, timeout=30
            )

            # Get the received API status code
            status_code = response.status_code

            if status_code is requests.codes["created"]:
                print(f"{name} added as a category!")
            else:
                response.raise_for_status()

        except requests.exceptions.RequestException as error:
            print(f"Requests Exception: {error}")
            count += 1

            # Let the user know that a 401 could mean that the creds are wrong
            if status_code == 401:
                print(f"Make sure that your credentials are entered correctly ...")
                sys.exit()

            if count == 3:
                print(f"Attempted to add {name} 3 times but failed ...")


def main():
    """The magic happens here"""

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
        input = arguments.input_file
        # Make sure the input file exists at the specified path.
        if not os.path.exists(input):
            print(f"The file {os.path.basename(input)} does not exist ...")
            sys.exit()
        # Load input file Contents
        input_file_data = load_csv_file_contents(input)

    # Get all computer and mobile groups
    all_jamf_computer_groups = jamf_computer_groups(mdmurl, basic_headers)
    all_jamf_mobile_groups = jamf_mobile_groups(mdmurl, basic_headers)

    if arguments.get_computer_groups:
        # Return the categories in Jamf Pro console
        print("ID\tName")
        print("-------------------------------------------------------------------")
        for group in all_jamf_computer_groups:
            print(f"{group['id']}\t{group['name']}(Smart: {group['is_smart']})")

    if arguments.get_computer_group:
        get_jamf_computer_group(
            mdmurl=mdmurl, headers=basic_headers, name=arguments.get_computer_group
        )

    if arguments.add_computer_group:
        # Do something
        pass

    if arguments.update_computer_group:
        # Update the give computer group
        group_name = arguments.update_computer_group
        group_id = jamf_computer_group_id(all_jamf_computer_groups, group_name)

        if group_id:
            print(f"Found id ({group_id}) for {group_name} ...")
            for record in input_file_data:
                update_jamf_static_computer_group(
                    mdmurl=mdmurl,
                    headers=basic_headers,
                    group_id=group_id,
                    name=group_name,
                    is_smart="false",
                    serial_number=record["serial_number"],
                )
        else:
            print(f"Unable to find id for {group_name}")

    if arguments.get_mobile_groups:
        # Return the categories in Jamf Pro console
        print("ID\tName")
        print("-------------------------------------------------------------------")
        for group in all_jamf_mobile_groups:
            print(f"{group['id']}\t{group['name']}(Smart: {group['is_smart']})")

    if arguments.get_mobile_group:
        jamf_mobile_group(
            mdmurl=mdmurl, headers=basic_headers, id=arguments.get_mobile_group
        )

    # Cleanup the bearer token
    invalidate_access_token(mdmurl, access_headers)


if __name__ == "__main__":
    main()
