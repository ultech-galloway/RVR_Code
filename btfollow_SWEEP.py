'''
btfollow_SWEEP.py - Connect to leader RVR and follow commands.
Scales speed during sweep maneuvers based on follower position.

Each follower independently resets yaw to 0 based on its actual 
position in the real world, not relative to the lead RVR.

Change FOLLOWER_POSITION on Line 32 for each RVR:
  Position 1 = 25% speed during sweeps (innermost)
  Position 2 = 50% speed during sweeps
  Position 3 = 75% speed during sweeps
  Position 4 = 100% speed during sweeps (outermost)

LAST: Dr. A (05.07.26) - Added sweep scaling
'''

import os
import sys
import time
import bluetooth
import json
sys.path.append('/home/pi/sphero')

from sphero_sdk import SpheroRvrObserver
from sphero_sdk import RawMotorModesEnum

rvr = SpheroRvrObserver()

# CONFIGURATION - Change these for each follower RVR
LEADER_MAC = "D8:3A:DD:67:DF:F8"  # Leader's MAC address
LEADER_CHANNEL = 1  # Fixed channel
FOLLOWER_POSITION = 1  # Change to 1, 2, 3, or 4 for each follower


def connect_to_leader(leader_mac_address, channel):
    """Connect to leader via Bluetooth"""
    
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
        print(f"=== FOLLOWER RVR (Position {FOLLOWER_POSITION}) ===")
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
                        
                        if command["action"] == "reset_yaw":
                            print(f"  → Resetting yaw to 0")
                            rvr.reset_yaw()
                        
                        elif command["action"] == "drive":
                            speed = command["speed"]
                            heading = command["heading"]
                            flags = command["flags"]
                            is_sweeping = command.get("sweeping", False)
                            
                            # Only scale speed during sweeps for formation
                            if is_sweeping:
                                speed_multiplier = FOLLOWER_POSITION * 0.25
                                adjusted_speed = int(speed * speed_multiplier)
                                print(f"  → SWEEP MODE: speed={adjusted_speed} (original={speed}, pos={FOLLOWER_POSITION}), heading={heading}")
                            else:
                                adjusted_speed = speed
                                print(f"  → Driving: speed={adjusted_speed}, heading={heading}")
                            
                            rvr.drive_with_heading(
                                speed=adjusted_speed,
                                heading=heading,
                                flags=flags
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
