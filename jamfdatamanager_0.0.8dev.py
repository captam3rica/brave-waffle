#!/usr/bin/env python

"""jamfdatamanager.py
A script to update Jamf settings and device inventory in the Jamf console.
"""

#
# GitHub: @captam3rica
#


#######################################################################################
#
#   DESCRIPTION
#
#       This tool is designed to assist with updating Jamf device inventory information
#       and Jamf Settings in the Jamf Pro console. This tool takes a CSV spreadsheet as
#       input.
#
#   USAGE
#
#       usage: jamfdatamanager.py [-h] --url URL [--update-device-records] [--add-
#               buildings] [--add-departments] [--delete-departments]
#               --filepath FILEPATH [--version] [-v LEVEL]
#
#       optional arguments:
#         -h, --help            show this help message and exit
#         --url URL             Jamf Pro tenant url (example.jamfcloud.com).
#         --update-device-records
#                                Update a list of device records
#         --add-buildings       Add one or more buildings to Jamf Pro console.
#         --delete-departments  Remove one or more departments to Jamf Pro console.
#         --filepath FILEPATH   Enter path to the spreadsheet(csv file) or drag the
#                               file into this Terminal window.
#         --version             Show this tools version.
#         -v LEVEL, --verbose LEVEL
#
#   NOTES
#
#       - Department: national store number
#       - Building: Operations Mananger (person)
#
#   TODOs
#
#       - [done] - Add function to check token time to live and renew access token if
#                  needed.
#
########################################################################################

__version__ = "0.0.8dev"


import argparse
import base64
import csv
import decimal
import getpass
import os
import sys
import time

import requests

try:
    import pathlib
except ImportError as error:
    print(error)
    sys.exit(
        "Looks like you need to open a Terminal and run python3 -m pip install pathlib."
    )


HERE = pathlib.Path("__file__").parent
SCRIPT_NAME = sys.argv[0]


def main():
    "Run the main logic"

    parser = argparse.ArgumentParser(
        prog="jamfdatamanager.py",
        description="A tool to update device inventory records and other information in Jamf Pro.",
        allow_abbrev=False,
    )

    parser.version = __version__
    parser.add_argument(
        "--url",
        type=str,
        help="Jamf Pro tenant url (example.jamfcloud.com).",
        required=True,
    )

    # NEW THING
    parser.add_argument(
        "--update-device-records",
        action="store_true",
        help="Update a list of device records",
    )

    # NEW THING
    parser.add_argument(
        "--add-buildings",
        action="store_true",
        help="Add one or more buildings to Jamf Pro console.",
    )

    # NEW THING
    # parser.add_argument(
    #     "--update-buildings",
    #     action="store_true",
    #     help="Update one or more building names in Jamf Pro",
    # )

    # NEW THING
    parser.add_argument(
        "--add-departments",
        action="store_true",
        help="Add one or more departments to Jamf Pro console.",
    )

    # NEW THING
    # parser.add_argument(
    #     "--update-departments",
    #     action="store_true",
    #     help="Update one or more department names in Jamf Pro.",
    # )

    # NEW THING
    parser.add_argument(
        "--delete-departments",
        action="store_true",
        help="Remove one or more departments to Jamf Pro console.",
    )

    parser.add_argument(
        "--filepath",
        type=str,
        help="Enter path to the spreadsheet(csv file) or drag the file into this Terminal window.",
        required=True,
    )
    parser.add_argument("--version", action="version", help="Show this tools version.")
    parser.add_argument("-v", "--verbose", action="store", metavar="LEVEL")

    arguments = parser.parse_args()

    if arguments.url:
        print(f"Your Jamf Cloud URL is: https://{arguments.url}")
        url = "https://%s" % arguments.url

    INPUT_FILE = arguments.filepath

    if not os.path.exists(INPUT_FILE):
        print(f"The file {os.path.basename(INPUT_FILE)} does not exist ...")
        sys.exit()

    if arguments.verbose:
        print("Verbose output is turned on.")

    ####################################################################################

    convert_pass = base64.b64encode(
        f"{get_username()}:{get_password()}".encode("utf-8")
    )

    # Header information
    basic_headers = {
        "Authorization": "Basic %s" % convert_pass.decode("utf-8"),
        "Accept": "application/json",
    }

    print(f"Running {SCRIPT_NAME} ... ")

    start_time = time.perf_counter()

    access_token = get_access_token(url=url, headers=basic_headers)
    access_headers = build_api_headers(auth_token=access_token)

    csv_data = load_csv_file_contents(file=INPUT_FILE)

    print(csv_data)

    sys.exit()

    # Return current buildings in Jamf conosole.
    # Buildings = Managers
    # jamf_building_data = return_jamf_building(url, access_headers, page_size=5000)
    jamf_building_data = classic_return_jamf_building(url, basic_headers)
    jamf_building_names = get_jamf_building_attribute(jamf_building_data, "name")

    # Return current departments in Jamf conosole.
    # Buildings = Managers
    jamf_departments = return_jamf_departments(url, access_headers)
    jamf_department_names = get_jamf_deptmartment_attribute(jamf_departments, "name")

    if arguments.update_device_records:
        # List of manager entries that need to be updated in Jamf.
        updated_building_records = remove_duplicates(
            data=csv_data, search_key="Update Device Record (Y/N)"
        )

        new_buildings = check_for_new_record(
            current_building_list=jamf_building_names,
            updated_building_list=updated_building_records,
        )

        if new_buildings != []:
            # If the new manager list is populated create the new managers in Jamf.
            jamf_add_building(url, access_headers, new_buildings)

        device_building_assignment_updates = return_devices_with_manager_updates(
            spreadsheet=csv_data
        )

        all_mobile_devices = all_mobile_devices_in_jamf(access_headers)

        completed_device_records = []
        incomplete_device_records = []

        for serial_number, building in device_building_assignment_updates.items():
            jamf_device_id = get_mobile_device_jamf_id(
                jamf_object_data=all_mobile_devices, serial_number=serial_number
            )
            jamf_building_id = get_jamf_building_attribute(
                data=jamf_building_data, search_key="id",
            )

            if jamf_device_id:
                print(f"Found {serial_number} with ID: {jamf_device_id}")

                update_device_building_assignment(
                    headers=access_headers,
                    device_id=jamf_device_id,
                    building=building,
                    building_id=jamf_building_id,
                    serial_number=serial_number,
                )

                completed_device_records.append(serial_number)

            else:
                incomplete_device_records.append(serial_number)

        print("")
        print(f"Total device records: {len(device_building_assignment_updates)}")
        print(f"Number completed: {len(completed_device_records)}")
        print()
        if len(incomplete_device_records) > 0:
            print(f"Number incomplete: {len(incomplete_device_records)}")
            for serial_number in incomplete_device_records:
                print(f"{serial_number}")

    if arguments.add_buildings:
        # Added builds to jamf in this block of code.
        # Compare buildings in Jamf to buildings in spreadsheet to see if there are
        # buildings that arlready exist in jamf and if so skip those.
        print("You have set the --add-buildings option ...")

        # list of unique building names from input file.
        buildings = remove_duplicates(csv_data, "Building")

        # List of unique buildings that do not exist in Jamf
        new_buildings = check_for_new_record(
            current_list=jamf_building_names, new_list=buildings, thing="buildings"
        )

        check = 0

        if new_buildings != []:
            # If there are new buildings that need to be added that do not already
            # exists in jamf.

            for name in new_buildings:

                # Get a new access token if elapsed time is more than 1200 sec (20
                # minutes)
                if check_run_time(start_time) == 1200 and check < 1:
                    access_headers = build_api_headers(
                        auth_token_keep_alive(url, access_headers)
                    )
                    check += 1

                # Get a new access token if elapsed time is more than 2400 sec (40
                # minutes)
                if check_run_time(start_time) == 2400 and check < 2:
                    access_headers = build_api_headers(
                        auth_token_keep_alive(url, access_headers)
                    )
                    check += 1

                # Get a new access token if elapsed time is more than 3600 sec (60
                # minutes)
                if check_run_time(start_time) == 3600 and check < 3:
                    access_headers = build_api_headers(
                        auth_token_keep_alive(url, access_headers)
                    )
                    check += 1

                jamf_add_building(url, access_headers, name)

        else:
            print("No new buildings to add ...")

        print("Total new buildings added to Jamf: %s" % len(new_buildings))

    if arguments.add_departments:
        # Added departments to jamf in this block of code.
        # Compare departments in Jamf to departments in spreadsheet to see if there are
        # departments that arlready exist in jamf and if so skip those.
        print("You have set the --add-departments option ...")

        # list of unique department names from input file.
        departments = remove_duplicates(csv_data, "Department")

        # List of unique departments that do not exist in Jamf
        new_departments = check_for_new_record(
            current_list=jamf_department_names,
            new_list=departments,
            thing="departments",
        )

        check = 0

        if new_departments != []:
            # If there are new departments that need to be added that do not already
            # exists in jamf.
            for name in new_departments:
                # Loop through the list of new managers and add them to the Jamf
                # Console.

                # Get a new access token if elapsed time is more than 1200 sec (20
                # minutes)
                if check_run_time(start_time) == 1200 and check < 1:
                    access_headers = build_api_headers(
                        auth_token_keep_alive(url, access_headers)
                    )
                    check += 1

                # Get a new access token if elapsed time is more than 2400 sec (40
                # minutes)
                if check_run_time(start_time) == 2400 and check < 2:
                    access_headers = build_api_headers(
                        auth_token_keep_alive(url, access_headers)
                    )
                    check += 1

                # Get a new access token if elapsed time is more than 3600 sec (60
                # minutes)
                if check_run_time(start_time) == 3600 and check < 3:
                    access_headers = build_api_headers(
                        auth_token_keep_alive(url, access_headers)
                    )
                    check += 1

                jamf_add_department(url, access_headers, name)
        else:
            print(f"No new departments to add ...")

        print(f"Total new departments added to Jamf: {len(new_departments)}")

    if arguments.delete_departments:
        # Remove departments in jamf in this block of code.
        print(f"You have set the --delete-departments option ...")

        # List of departments that need to be removed.
        departments = remove_duplicates(csv_data, "Department")

        # Each time a department is removed add it to this list.
        total_removed = []

        check = 0

        for name in departments:

            # Get a new access token if elapsed time is more than 1200 sec (20 minutes)
            if check_run_time(start_time) == 1200 and check < 1:
                access_headers = build_api_headers(
                    auth_token_keep_alive(url, access_headers)
                )
                check += 1

            # Get a new access token if elapsed time is more than 2400 sec (40 minutes)
            if check_run_time(start_time) == 2400 and check < 2:
                access_headers = build_api_headers(
                    auth_token_keep_alive(url, access_headers)
                )
                check += 1

            # Get a new access token if elapsed time is more than 3600 sec (60 minutes)
            if check_run_time(start_time) == 3600 and check < 3:
                access_headers = build_api_headers(
                    auth_token_keep_alive(url, access_headers)
                )
                check += 1

            dept_id = return_jamf_department_id(url, access_headers, name=name)

            if dept_id is not None:
                # If there are departments that need to be removed
                print(f"Removing {name} ...")
                removal_status = jamf_delete_department(url, access_headers, dept_id)

                # Only append to total_removed if the status code is successful.
                if removal_status == 204:
                    total_removed.append(name)

            else:
                print(f"Department not in Jamf: {name}")

        print(f"Total departments removed from Jamf: {len(total_removed)}")

    # Get the time after script completes
    end_time = time.perf_counter()

    print(f"Process Report:")
    print(f"Total time (sec): {end_time - start_time:0.4f}")

    invalidate_access_token(url=url, headers=access_headers)


def get_username():
    """Return the username entered"""
    return input("Enter Jamf Pro username: ")


def get_password():
    """Return the user's password"""
    count = 1
    password = None

    while True and count <= 3:
        password = getpass.getpass(prompt="Enter password: ", stream=None)
        password_verify = getpass.getpass(prompt="Verify password: ", stream=None)
        if count < 3:
            if password == password_verify and password != "" and password_verify != "":
                break
            print("Passwords not the same. Please enter password again.")
            count += 1
        else:
            sys.exit()

    return password


def get_access_token(url, headers):
    """Return the Bearer token from Jamf"""
    endpoint = "/uapi/auth/tokens"
    access_token = None

    try:
        response = requests.post(url + endpoint, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            access_token = data["token"]

        response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"Failed to return token ...")
        sys.exit(f"Error: {error}")

    return access_token


def auth_token_keep_alive(url, headers):
    """Invalidate existing token and generate new token with extended expiration based
    on existing token credentials

    args:
        url: Jamf console url
        headers: Current access token headers.
    """
    endpoint = "/uapi/auth/keepAlive"
    access_token = None

    try:
        response = requests.post(url + endpoint, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            access_token = data["token"]

        response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"Failed to return token ...")
        sys.exit(f"Error: {error}")

    return access_token


def check_access_token_age(check_num, run_time):
    """Check to see if a new access token should be generated

    This function checks the age of the current bearer token to see if a new one needs
    to be generated. If a new token needs to be generated a new set of bearer token
    headers will be generated contianing the new bearer token. If a new bearer token
    does not need to be created the current headers will be returned.

    args:
        url: Jamf console url
        headers: Current access token headers.
        check_num: Number of times a new bearer token has been generated
        run_time: The amount of time passed since starting the script.
    """

    # Set access headers equal to the current headers
    result = check_num

    print(run_time)

    # Get a new access token if elapsed time is more than 1200 sec (20 minutes)
    if run_time == 30 and check_num < 1:
        result += 1

    # Get a new access token if elapsed time is more than 2400 sec (40 minutes)
    if run_time == 2400 and check_num < 2:
        result += 1

    # Get a new access token if elapsed time is more than 3600 sec (60 minutes)
    if run_time == 3600 and check_num < 3:
        result += 1

    return result


def check_run_time(start_time):
    """Return the ammount of elapsed time in seconds since starting

    https://realpython.com/python-rounding/

    Args:
        time: time at start of program
    """
    return decimal.Decimal(time.perf_counter() - start_time).quantize(
        decimal.Decimal("1")
    )


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
    with open(file, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)
        for line in reader:
            csv_data.append(line)
    return csv_data


def remove_duplicates(data, search_key):
    """Parse the input file received and only return unique entries back as a list

    Args:
        data: JSON data returned from input file.
        search_key: Key that we wanted to search for in the data.
    Return: list of unique values
    """
    unique_values = []
    for line in data:
        if search_key in line.keys() and line[search_key] != "":
            value = line[search_key].strip()

        if value not in unique_values:
            unique_values.append(value)

    unique_values.sort()

    return unique_values


def classic_return_jamf_building(url, headers):
    """Return building information from Jamf console using the Classic API

    uri: /JSSResource/buildings

    Args:
        url: MDM url
        headers: bearer token headers
    """

    endpoint = f"/JSSResource/buildings"
    buildings = None
    try:
        response = requests.get(url + endpoint, headers=headers, timeout=30)
        status_code = response.status_code
        if status_code is requests.codes["ok"]:
            # Response code 200
            data = response.json()
            buildings = data["buildings"]
        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"Failed to return buildings ...")
        print(f"This could be due to insufficient permissions for the API user.")
        sys.exit(f"Error: {error}")

    return buildings


# def return_jamf_building(url, headers, page_size):
#     """Return building information from Jamf console
#
#     uri: /uapi/v1/buildings?page=0&page-size=100&sort=id
#
#     Args:
#         url: MDM url
#         headers: bearer token headers
#         page_size: number of results to return
#     """
#
#     endpoint = f"/uapi/v1/buildings?page-size={page_size}&sort=id"
#     results = None
#     try:
#         response = requests.get(url + endpoint, headers=headers, timeout=30)
#         status_code = response.status_code
#         if status_code is requests.codes["ok"]:
#             # Response code 200
#             data = response.json()
#             results = data["results"]
#         else:
#             response.raise_for_status()
#
#     except requests.exceptions.RequestException as error:
#         print(f"Failed to return buildings ...")
#         print(f"This could be due to insufficient permissions for the API user.")
#         sys.exit(f"Error: {error}")
#
#     return results


def get_jamf_building_attribute(data, search_key):
    """Parse input data returned from and return buildings defined in Jamf"""
    list = []

    for item in data:
        value = item[search_key]
        list.append(value)

    return list


def jamf_add_building(url, headers, name):
    """Add building(s) to Jamf Pro console

    uri: /uapi/v1/buildings
    `payload`: '{"name": "building_name"}'
    """
    # JSON payload
    payload = '{"name": "%s"}' % name

    attempt = 0
    status_code = None

    while status_code is not requests.codes["created"] and attempt < 6:

        try:
            response = requests.post(
                url + f"/uapi/v1/buildings",
                headers=headers,
                data=payload.encode("utf-8"),
                timeout=30,
            )

            status_code = response.status_code

            if status_code is requests.codes["created"]:
                print(f"New Building Added: {name}")
                break

            error_data = response.json()
            response.raise_for_status()

        except requests.exceptions.RequestException as error:
            print(f"Building not added ...")
            print(f"HTTP Error Code: {error}")
            if error_data:
                print(f"Jamf Error: {error_data}")
            attempt += 1
            if attempt == 5:
                print(f"Exiting ...")


def return_jamf_departments(url, headers):
    """Return all departments in the Jamf console.

    uri: /uapi/v1/departments
    """
    endpoint = "/uapi/v1/departments"
    results = ""
    try:
        response = requests.get(url + endpoint, headers=headers, timeout=30)
        status_code = response.status_code
        if status_code is requests.codes["ok"]:
            # Response code 200
            data = response.json()
            results = data["results"]
        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"Failed to return buildings ...")
        print(f"This could be due to insufficient permissions for the API user.")
        sys.exit(f"Error: {error}")

    return results


def return_jamf_department_id(url, headers, name):
    """Return specified department in the Jamf console.

    This function looks up a department based on specified name and returns the
    department id.

    uri: /uapi/v1/departments?search=name=="Department Name"

    args:
        url: Jamf console URL
        headers: Jamf access token headers
        name: Depmartment name
    """
    endpoint = f"/uapi/v1/departments?search=name=={name}"
    id = None
    try:
        response = requests.get(url + endpoint, headers=headers, timeout=30)
        status_code = response.status_code
        if status_code is requests.codes["ok"]:
            # Response code 200
            data = response.json()
            results = data["results"]

            for dept in results:

                # Find the exact name to make sure we get an exact match.
                if dept["name"] == name:
                    id = dept["id"]
        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"Failed to return department ...")
        print(f"This could be due to insufficient permissions for the API user.")
        sys.exit(f"Error: {error}")

    return id


def get_jamf_deptmartment_attribute(data, search_key):
    """Parse input data returned from Jamf"""
    list = []

    for item in data:
        value = item[search_key]
        list.append(value)

    return list


def jamf_add_department(url, headers, name):
    """Add department to Jamf Pro console

    uri: /uapi/v1/departments
    payload: '{"name": "department_name"}'
    """
    # JSON payload
    payload = '{"name": "%s"}' % name

    attempt = 0
    status_code = None

    while status_code is not requests.codes["created"] and attempt < 6:

        try:
            response = requests.post(
                url + f"/uapi/v1/departments",
                headers=headers,
                data=payload.encode("utf-8"),
                timeout=30,
            )

            status_code = response.status_code

            if status_code is requests.codes["created"]:
                print(f"New Department Added: {name}")
                break
            error_data = response.json()
            response.raise_for_status()

        except requests.exceptions.RequestException as error:
            print(f"Department not added ...")
            print(f"HTTP Error Code: {error}")
            if error_data:
                print(f"Jamf Error: {error_data}")
            attempt += 1
            if attempt == 5:
                print(f"Exiting ...")


def jamf_delete_department(url, headers, id):
    """Delete specified department from the Jamf console

    uri: /uapi/v1/departments/{id}
    payload: '{"name": "department_name"}'

    args:
        url: Jamf console url
        headers: Access token headers
        id: Jamf department ID
    """

    status_code = None

    try:
        response = requests.delete(
            url + f"/uapi/v1/departments/{id}", headers=headers, timeout=30,
        )

        status_code = response.status_code

        if status_code == 204:
            print(f"Department deleted ...")
        else:
            error_data = response.json()
            response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"Department not added ...")
        print(f"HTTP Error Code: {error}")
        print(f"Jamf Error: {error_data}")
        status_code = error_data["httpStatus"]

    return status_code


def check_for_new_record(current_list, new_list, thing):
    """Compare two lists and determine if there are new entries

    This function compares the current list in the Jamf console to a list
    of new buildling records to see if there are any netnew records that need to be
    added to the Jamf console.

    Args:
        current_list: Current list of items in Jamf
        new_list: New list of items to add
        thing: The item type that is being added. (Example: building, department, etc)
    """
    updated_list = []

    print(f"Looking to see if there are new {thing} to add ...")

    for thing in new_list:

        if thing not in current_list:
            updated_list.append(thing)

    if updated_list == []:
        print(f"No new {thing} names were found ...")

    return updated_list


def return_devices_with_manager_updates(spreadsheet):
    """Return device records that need to be updated

    Parses a csv file and looks for device records that need to be updated with new
    information. This is the update building info column.

    Serial number and Manager(building)
    """
    device_records_to_update = {}
    for row in spreadsheet:
        if "update" in row["Update Yes or no?"]:
            # Look at the "Update Yes or no?" column and pull serial numbers and
            # updated manager information.
            serial_number = row["Serial Number"]
            manager = row["Updated Building information"]
            device_records_to_update.update({serial_number: manager})

    return device_records_to_update


def all_mobile_devices_in_jamf(headers):
    """Returns all mobile device objects in the Jamf console

    /uapi/v1/mobile-devices
    """
    endpoint = "/uapi/v1/mobile-devices"

    try:
        response = requests.get(url + endpoint, headers=headers, timeout=30)

        if response.status_code == 200:
            return response.json()

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"Error: {error}")
        sys.exit()


def get_mobile_device_jamf_id(jamf_object_data, serial_number):
    """Return Jamf device ID for device matching a given serial number"""

    for device in jamf_object_data:
        if serial_number in device["serialNumber"]:
            device_id = device["id"]
            return device_id


# noqa: C0330
def update_device_building_assignment(
    url, headers, device_id, building, building_id, serial_number
):
    """Update the device inventory record with updated manager(building) information

    /uapi/v1/mobile-devices/{id}
    """
    print(f"Updating {serial_number} manager to {building}")

    # noqa: C0330
    payload = '{"location": {"building": {"name": %s, "id": %s}}}' % (
        building,
        building_id,
    )

    attempt = 0
    status_code = None

    while status_code is not requests.codes["ok"] and attempt < 6:

        try:
            response = requests.patch(
                url + f"/uapi/v1/mobile-devices/{device_id}",
                headers=headers,
                data=payload.encode("utf-8"),
                timeout=30,
            )
            status_code = response.status_code
            if status_code is requests.codes["ok"]:
                print("Manager updated ...")
            response.raise_for_status()

        except requests.exceptions.RequestException as error:
            print(f"Error: {error}")
            attempt += 1
            if attempt == 5:
                print(f"Exiting ...")


if __name__ == "__main__":
    main()
