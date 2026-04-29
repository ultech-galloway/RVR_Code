'''
btlead_wasd.py - Drive leader with WASD keys via SSH/VNC.
Follower RVRs mirror leader's movements in real time.

Controls:
W - Forward
A - Turn Left  
S - Reverse
D - Turn Right
Spacebar - Stop
Q - Quit

LAST: Dr. A (04.29.26)
'''

import os
import sys
import time
import bluetooth
import json
import threading
sys.path.append('/home/pi/sphero')

from helper_keyboard_input import KeyboardHelper
from sphero_sdk import SpheroRvrObserver
from sphero_sdk import RawMotorModesEnum

rvr = SpheroRvrObserver()

# Keyboard helper
key_helper = KeyboardHelper()
current_key_code = -1

# List of connected followers
follower_clients = []
clients_lock = threading.Lock()

# Current driving state
speed = 0
heading = 0
flags = 0
running = True


def keycode_callback(keycode):
    global current_key_code
    current_key_code = keycode


def handle_follower_client(client_sock, client_info):
    """Communication with single follower"""
    print(f"Follower connected: {client_info}")
    
    with clients_lock:
        follower_clients.append(client_sock)
    
    try:
        while running:
            time.sleep(0.1)
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
            except Exception as e:
                print(f"Error sending to follower: {e}")
                follower_clients.remove(client_sock)


def start_bluetooth_server():
    """Start Bluetooth server"""
    try:
        server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        server_sock.bind(("", 1))
        server_sock.listen(5)
        
        print(f"=== LEADER RVR - Bluetooth Server ===")
        print(f"Listening on RFCOMM channel 1")
        print(f"Leader MAC: {bluetooth.read_local_bdaddr()[0]}")
        print(f"Followers should connect to this MAC on channel 1\n")
        
        while running:
            try:
                server_sock.settimeout(1.0)
                try:
                    client_sock, client_info = server_sock.accept()
                    print(f"Accepted connection from {client_info}")
                    
                    client_thread = threading.Thread(
                        target=handle_follower_client,
                        args=(client_sock, client_info)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except bluetooth.BluetoothError:
                    pass
                    
            except Exception as e:
                if running:
                    print(f"Error accepting connection: {e}")
                
    except Exception as e:
        print(f"Error starting Bluetooth server: {e}")


def main():
    global current_key_code
    global speed, heading, flags
    global running
    
    try:
        print("=== LEADER RVR - WASD CONTROL ===")
        print("Initializing RVR...\n")
        
        rvr.wake()
        time.sleep(2)
        
        print("Resetting yaw to 0...")
        rvr.reset_yaw()
        time.sleep(1)
        print("Yaw reset!\n")
        
        # Start Bluetooth server
        bt_thread = threading.Thread(target=start_bluetooth_server)
        bt_thread.daemon = True
        bt_thread.start()
        
        print("Waiting for followers to connect...")
        print("(Give followers 15 seconds to connect)\n")
        time.sleep(15)
        
        print(f"Connected followers: {len(follower_clients)}")
        
        # Tell followers to reset yaw
        print("\nTelling followers to reset yaw...")
        command = {"action": "reset_yaw"}
        broadcast_command(command)
        time.sleep(2)
        
        print("\n=== WASD CONTROL ACTIVE ===")
        print("W=Forward | A=Left | S=Reverse | D=Right | Space=Stop | Q=Quit\n")
        
        # Start keyboard input
        key_helper.set_callback(keycode_callback)
        key_thread = threading.Thread(target=key_helper.get_key_continuous)
        key_thread.daemon = True
        key_thread.start()
        
        # Main control loop
        while running:
            if current_key_code == 119:  # W - Forward
                if flags == 1:  # Was reversing
                    speed = 64
                else:
                    speed = min(speed + 64, 255)
                flags = 0
                print(f"Forward: speed={speed}")
                
            elif current_key_code == 97:  # A - Left
                heading = (heading - 10) % 360
                print(f"Turn Left: heading={heading}")
                
            elif current_key_code == 115:  # S - Reverse
                if flags == 0:  # Was going forward
                    speed = 64
                else:
                    speed = min(speed + 64, 255)
                flags = 1
                print(f"Reverse: speed={speed}")
                
            elif current_key_code == 100:  # D - Right
                heading = (heading + 10) % 360
                print(f"Turn Right: heading={heading}")
                
            elif current_key_code == 32:  # SPACE - Stop
                speed = 0
                flags = 0
                print("Stop")
                
            elif current_key_code == 113:  # Q - Quit
                print("Quitting...")
                running = False
                break
            
            # Reset key code
            current_key_code = -1
            
            # Send command to followers
            if speed > 0 or heading != 0:
                command = {"action": "drive", "speed": speed, "heading": heading, "flags": flags}
                broadcast_command(command)
            
            # Drive leader RVR
            rvr.drive_with_heading(speed, heading, flags)
            
            time.sleep(0.1)

    except KeyboardInterrupt:
        print('\n\nStopping...')
        running = False

    finally:
        # Stop everything
        command = {"action": "stop"}
        broadcast_command(command)
        
        rvr.drive_with_heading(speed=0, heading=0, flags=0)
        time.sleep(0.5)
        rvr.close()
        
        key_helper.end_get_key_continuous()
        print("Leader closed.")


if __name__ == '__main__':
    main()
