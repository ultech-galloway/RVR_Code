'''
btlead is a program that...

LAST: Dr. A (04.27.26) - Added yaw reset
'''

import os
import sys
import time
import bluetooth
import json
import threading
sys.path.append('/home/pi/sphero')

from sphero_sdk import SpheroRvrObserver
from sphero_sdk import RawMotorModesEnum

rvr = SpheroRvrObserver()

# List of connected followers
follower_clients = []
clients_lock = threading.Lock()


def handle_follower_client(client_sock, client_info):
    """Communication with single follower"""
    print(f"Follower connected: {client_info}")
    
    with clients_lock:
        follower_clients.append(client_sock)
    
    try:
        while True:
            time.sleep(0.1)  # Keep connection alive
    except Exception as e:
        print(f"Follower {client_info} disconnected: {e}")
    finally:
        with clients_lock:
            if client_sock in follower_clients:
                follower_clients.remove(client_sock)
        client_sock.close()


def broadcast_command(command_data):
    """Send command to all connected followers"""
    message = json.dumps(command_data) + "\n"
    
    with clients_lock:
        for client_sock in follower_clients[:]:
            try:
                client_sock.send(message.encode('utf-8'))
                print(f"Sent to follower: {command_data}")
            except Exception as e:
                print(f"Error sending to follower: {e}")
                follower_clients.remove(client_sock)


def start_bluetooth_server():
    """Start Bluetooth server - SIMPLIFIED VERSION"""
    try:
        server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        
        # Bind to channel 1 (fixed channel, no service discovery needed)
        server_sock.bind(("", 1))
        server_sock.listen(5)
        
        print(f"=== LEADER RVR - Bluetooth Server ===")
        print(f"Listening on RFCOMM channel 1")
        print(f"Leader MAC: {bluetooth.read_local_bdaddr()[0]}")
        print(f"Followers should connect to this MAC on channel 1\n")
        
        while True:
            try:
                client_sock, client_info = server_sock.accept()
                print(f"Accepted connection from {client_info}")
                
                # Handle each client in a separate thread
                client_thread = threading.Thread(
                    target=handle_follower_client,
                    args=(client_sock, client_info)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                print(f"Error accepting connection: {e}")
                
    except Exception as e:
        print(f"Error starting Bluetooth server: {e}")


def main():
    try:
        print("=== LEADER RVR ===")
        print("Initializing RVR...\n")
        
        rvr.wake()
        time.sleep(2)
        
        # RESET YAW - Set current direction as "0 degrees"
        print("Resetting yaw to 0...")
        rvr.reset_yaw()
        time.sleep(1)
        print("Yaw reset complete!\n")
        
        # Start Bluetooth server in background thread
        bt_thread = threading.Thread(target=start_bluetooth_server)
        bt_thread.daemon = True
        bt_thread.start()
        
        print("Waiting for followers to connect...")
        print("(Give followers 15 seconds to connect)\n")
        time.sleep(15)
        
        print(f"Connected followers: {len(follower_clients)}")
        
        # Tell all followers to reset yaw
        print("\nTelling followers to reset yaw...")
        command = {"action": "reset_yaw"}
        broadcast_command(command)
        time.sleep(2)
        
        print("\nStarting movement sequence...\n")
        
        # Movement sequence
        print("PHASE 1: Moving forward for 5 seconds")
        command = {"action": "drive", "speed": 64, "heading": 0}
        broadcast_command(command)
        
        rvr.drive_with_heading(
            speed=64,
            heading=0,
            flags=0
        )
        time.sleep(5)
        
        print("PHASE 2: Stopping")
        command = {"action": "stop"}
        broadcast_command(command)
        
        rvr.drive_with_heading(
            speed=0,
            heading=0,
            flags=0
        )
        time.sleep(2)
        
        print("PHASE 3: Turning right (heading 90)")
        command = {"action": "drive", "speed": 64, "heading": 90}
        broadcast_command(command)
        
        rvr.drive_with_heading(
            speed=64,
            heading=90,
            flags=0
        )
        time.sleep(2)
        
        print("PHASE 4: Stopping and waiting for followers to catch up")
        command = {"action": "stop"}
        broadcast_command(command)
        
        rvr.drive_with_heading(
            speed=0,
            heading=0,
            flags=0
        )
        
        print("\nSequence complete. Waiting...")
        time.sleep(30)

    except KeyboardInterrupt:
        print('\n\nStopping...')

    finally:
        # Stop RVR
        rvr.drive_with_heading(speed=0, heading=0, flags=0)
        time.sleep(0.5)
        rvr.close()
        print("Leader closed.")


if __name__ == '__main__':
    main()
