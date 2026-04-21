'''
btfollow is a program that...

LAST: Dr. A (04.21.26)
'''

# GOTO line 52 to change leader's MAC address

import os
import sys
import time
import bluetooth
import json
sys.path.append('/home/pi/sphero')

from sphero_sdk import SpheroRvrObserver
from sphero_sdk import RawMotorModesEnum

rvr = SpheroRvrObserver()


def connect_to_leader(leader_mac_address):
    """Connect to leader via Bluetooth"""
    uuid = "00001101-0000-1000-8000-00805F9B34FB"
    
    print(f"Searching for Leader at {leader_mac_address}...")
    
    # Find the service
    service_matches = bluetooth.find_service(uuid=uuid, address=leader_mac_address)
    
    if len(service_matches) == 0:
        print("Could not find the Leader RVR service")
        return None
    
    first_match = service_matches[0]
    port = first_match["port"]
    name = first_match["name"]
    host = first_match["host"]
    
    print(f"Connecting to '{name}' on {host}:{port}")
    
    # Create client socket
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((host, port))
    
    print("Connected to Leader!\n")
    return sock


def main():
    # Replace with Leader's MAC address
    LEADER_MAC = "XX:XX:XX:XX:XX:XX"
    
    sock = None
    
    try:
        print("=== FOLLOWER RVR ===")
        print("Initializing RVR...\n")
        
        rvr.wake()
        time.sleep(2)
        
        # Connect to leader
        sock = connect_to_leader(LEADER_MAC)
        
        if not sock:
            print("Failed to connect to Leader. Exiting.")
            return
        
        print("Waiting for commands from Leader...\n")
        
        # Receive and process commands
        buffer = ""
        while True:
            try:
                data = sock.recv(1024).decode('utf-8')
                if not data:
                    print("Leader disconnected")
                    break
                
                buffer += data
                
                # Process complete messages (which get newlines)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    
                    try:
                        command = json.loads(line)
                        print(f"Received command: {command}")
                        
                        if command["action"] == "drive":
                            speed = command["speed"]
                            heading = command["heading"]
                            print(f"  → Driving: speed={speed}, heading={heading}")
                            
                            rvr.drive_with_heading(
                                speed=speed,
                                heading=heading,
                                flags=0
                            )
                        
                        elif command["action"] == "stop":
                            print(f"  → Stopping")
                            rvr.drive_with_heading(
                                speed=0,
                                heading=0,
                                flags=0
                            )
                    
                    except json.JSONDecodeError as e:
                        print(f"Error parsing command: {e}")
                
            except Exception as e:
                print(f"Error receiving data: {e}")
                break

    except KeyboardInterrupt:
        print('\n\nStopping...')

    finally:
        # Stop RVR
        rvr.drive_with_heading(speed=0, heading=0, flags=0)
        time.sleep(0.5)
        rvr.close()
        
        if sock:
            sock.close()
        
        print("Follower closed.")


if __name__ == '__main__':
    main()
