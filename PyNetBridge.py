# // Author & Copyrighted by:  Quincy Rodge A. Macalalag
# // Date: Upda to date 2024
# // FIlename: PyBridge.py
# // Copyright © 2024 Quincy Rodge A. Macalalag
# // All rights reserved. This code and its accompanying documentation are protected by copyright law and international treaties. Unauthorized reproduction or distribution of this code, or any portion of it, may result in severe civil and criminal penalties, and will be prosecuted to the maximum extent possible under the law.
# // For licensing inquiries or to obtain permission for usage, please contact qrodgemacalalag@gmail.com.


import time
import subprocess


def remove_wifi_credentials(interface, interface_path):
    try:
        # Read the contents of the interface configuration file
        with open(interface_path, "r") as f:
            lines = f.readlines()

        # Filter out the lines related to the specified interface
        new_lines = [
            line
            for line in lines
            if not (
                line.strip().startswith(f"wpa-ssid {interface}")
                or line.strip().startswith("wpa-psk")
            )
        ]

        # Write the modified configuration back to the file
        with open(interface_path, "w") as f:
            f.writelines(new_lines)

        # Restart networking services
        subprocess.run(["systemctl", "restart", "networking"])

        print(f"Removed Wi-Fi credentials for interface {interface}.")
    except Exception as e:
        print(f"Error: {e}")


def configure_wifi(new_ssid, interface, interface_path, networks, change_ssid=False):

    if change_ssid:
        if new_ssid not in networks:
            return "Invalid Network. Re run the program and enter valid network name"
        else:
            passphrase_for_new_ssid = get_str(f"Enter password for [{new_ssid}]: ")
            try:
                with open(interface_path, "w") as f:
                    f.write("source /etc/network/interfaces.d/*\n")
                    f.write("auto lo\n")
                    f.write("iface lo inet loopback\n\n")
                    f.write(f"allow-hotplug {interface}\n")
                    f.write(f"iface {interface} inet dhcp\n")
                    f.write(f"\twpa-ssid {new_ssid}\n")
                    f.write(f"\twpa-psk {passphrase_for_new_ssid}\n")

                subprocess.run(["sudo", "systemctl", "restart", "networking"])

                time.sleep(2)

                iwconfig_output = subprocess.check_output(
                    ["iwconfig", interface], text=True
                )

                if "Access Point: Not-Associated" in iwconfig_output:
                    print(
                        "Error: Network configuration was not updated. Incorrect password?"
                    )
                    return

                subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"])

                print("Interface configuration updated successfully.")
            except Exception as e:
                print(f"Error what: {e}")
            finally:
                print("Done Configuring interfaces")
                exit(0)

    ssid = get_str("Enter ssid: ")
    passphrase = get_str(f"Enter password for [{ssid}]: ")

    with open(interface_path, "w") as f:
        f.write("source /etc/network/interfaces.d/*\n")
        f.write("auto lo\n")
        f.write("iface lo inet loopback\n\n")
        f.write(f"allow-hotplug {interface}\n")
        f.write(f"iface {interface} inet dhcp\n")
        f.write(f"\twpa-ssid {ssid}\n")
        f.write(f"\twpa-psk {passphrase}\n")

    subprocess.run(["sudo", "systemctl", "restart", "networking"])

    time.sleep(2)

    iwconfig_output = subprocess.check_output(["iwconfig", interface], text=True)

    if "Access Point: Not-Associated" in iwconfig_output:
        print("Error: Network configuration was not updated. Incorrect password?")
        return

    subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"])

    print("Interface configuration updated successfully.")


def get_available_networks():
    try:
        # Run iwlist command to list available networks and filter by ESSID
        iwlist_process = subprocess.Popen(
            ["iwlist", "wlan0", "scan"], stdout=subprocess.PIPE
        )
        grep_process = subprocess.Popen(
            ["grep", "ESSID"],
            stdin=iwlist_process.stdout,
            stdout=subprocess.PIPE,
            text=True,
        )
        iwlist_process.stdout.close()  # Close the stdout of the first process
        output = grep_process.communicate()[0]

        # Check if the command was successful
        if grep_process.returncode == 0:
            # Extract SSID from each line
            networks = [
                line.split(":")[1].strip().replace('"', "")
                for line in output.split("\n")
                if line.strip()  # Skip empty lines
            ]
            return networks
        else:
            print("Error: Failed to list available networks.")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def display_ifaces():
    try:
        # Run iwconfig to get the available interfaces
        iwconfig_process = subprocess.run(["iwconfig"], capture_output=True, text=True)
        if iwconfig_process.returncode == 0:
            interfaces = []
            # Split the output by newline and extract interface names
            for line in iwconfig_process.stdout.split("\n"):
                if line.strip() != "":
                    interface_name = line.split(" ")[0]
                    interfaces.append(interface_name)
            return interfaces
        else:
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def current_inet_status(interface):
    try:
        # Run iwconfig and grep commands together to extract ESSID
        result = subprocess.run(["iwconfig", interface], capture_output=True, text=True)
        essid = subprocess.run(
            [
                "grep",
                "-o",
                'ESSID:"[^"]*"',
            ],
            input=result.stdout,
            capture_output=True,
            text=True,
        )

        # Check if both commands were successful
        if result.returncode == 0 and essid.returncode == 0:
            output = essid.stdout.strip()
            if output.startswith('ESSID:"') and output.endswith('"'):
                return output[7:-1]  # Remove 'ESSID:"' prefix and '"' suffix
            else:
                return "SSID not found"
        else:
            return "Error: Couldn't retrieve ESSID"
    except Exception as e:
        return f"Error: {e}"


def get_str(message=" "):
    value = ""
    while value == "":
        value = input(message)
    return value


def get_yes_or_no(message):
    value = ""
    while value != "y" and value != "n":
        value = input(message).lower()
    return value == "y"


def valid_interface(interface, valid_interfaces):
    for iface in valid_interfaces:
        iface_char_len = len(iface)
        if interface[:iface_char_len] == iface:
            return True
        return False


def edit_interface_conf(
    interface_path="/etc/network/interfaces",
):
    try:

        """Modify the interface config"""
        interfaces = [inet for inet in display_ifaces() if inet != ""]

        print("Available interfaces: ", interfaces)
        interface = get_str("Enter interface: ")
        if interface not in interfaces:
            print("Invalid Interface. Re run the program.")
            return

        networks = get_available_networks()
        print(networks)
        current_inet = current_inet_status(interface)
        print("Curent inet: ", current_inet)
        if current_inet != "Error: Couldn't retrieve ESSID":
            change_inet = get_yes_or_no(
                "You are already connected to a network. Do you wish to change it? [y/n]: "
            )
            new_ssid = get_str("Enter new ssid: ")
            if new_ssid == current_inet:
                print("You are already connected to this network!")
                exit(0)

            if not change_inet:
                print("Keeping the network as it is.")
                exit(0)

            remove_wifi_credentials(interface, interface_path)

            configure_wifi(
                new_ssid, interface, interface_path, networks, change_ssid=True
            )
        configure_wifi("", interface, interface_path, networks, change_ssid=False)

        # Check if networking services were restarted successfully
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
        exit(0)
    except Exception as e:
        print(f"An error occured: {e}")
        exit(1)
    finally:
        print("Program finished.")
        exit(0)


if __name__ == "__main__":
    edit_interface_conf()
