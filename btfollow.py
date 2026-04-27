'''
btfollow is a program that...

LAST: Dr. A (04.27.26) - Simplified Bluetooth
'''

# GOTO line 17 to change leader's MAC address

import os
import sys
import time
import bluetooth
import json
sys.path.append('/home/pi/sphero')

from sphero_sdk import SpheroRvrObserver
from sphero_sdk import RawMotorModesEnum

rvr = SpheroRvrObserver()

# Replace with Leader's MAC address
LEADER_MAC = "D8:3A:DD:67:DE:90"  # <-- PUT YOUR LEADER'S MAC HERE
LEADER_CHANNEL = 1  # Fixed channel


def connect_to_leader(leader_mac_address, channel):
    """Connect to leader via Bluetooth - SIMPLIFIED VERSION"""
    
    print(f"Connecting to Leader at {leader_mac_address} on channel {channel}...")
    
    # Create client socket and connect directly
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    
    try:
        sock.connect((leader_mac_address, channel))
        print("Connected to Leader!\n")
        return sock
    except Exception as e:
        print(f"Connection failed: {e}")
        return None


def main():
    sock = None
    
    try:
        print("=== FOLLOWER RVR ===")
        print("Initializing RVR...\n")
        
        rvr.wake()
        time.sleep(2)
        
        # Connect to leader
        sock = connect_to_leader(LEADER_MAC, LEADER_CHANNEL)
        
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
