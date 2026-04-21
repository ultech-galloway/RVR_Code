'''
btlead is a program that...

LAST: Dr. A (04.21.26)
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
    """Start Bluetooth server in separate thread"""
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(5)
    
    port = server_sock.getsockname()[1]
    
    # Create service UUID
    uuid = "00001101-0000-1000-8000-00805F9B34FB"
    
    bluetooth.advertise_service(
        server_sock,
        "RVR_Leader",
        service_id=uuid,
        service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
        profiles=[bluetooth.SERIAL_PORT_PROFILE]
    )
    
    print(f"=== LEADER RVR - Bluetooth Server ===")
    print(f"Waiting for followers on RFCOMM channel {port}")
    print(f"Service UUID: {uuid}\n")

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


def main():
    try:
        print("=== LEADER RVR ===")
        print("Initializing RVR...\n")
        
        rvr.wake()
        time.sleep(2)
        
        # Start Bluetooth server in background thread
        bt_thread = threading.Thread(target=start_bluetooth_server)
        bt_thread.daemon = True
        bt_thread.start()
        
        print("Waiting for followers to connect...")
        print("(Give followers 10 seconds to connect)\n")
        time.sleep(10)
        
        print(f"Connected followers: {len(follower_clients)}")
        print("\nStarting movement sequence...\n")
        
        # Movement sequence
        print("PHASE 1: Moving forward for 5 seconds")
        command = {"action": "drive", "speed": 128, "heading": 0}
        broadcast_command(command)
        
        rvr.drive_with_heading(
            speed=128,
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
        command = {"action": "drive", "speed": 128, "heading": 90}
        broadcast_command(command)
        
        rvr.drive_with_heading(
            speed=128,
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
