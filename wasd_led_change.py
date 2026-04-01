import os
import sys
import time
sys.path.append('/home/pi/sphero')

import asyncio

from helper_keyboard_input import KeyboardHelper
from sphero_sdk import SerialAsyncDal
from sphero_sdk import SpheroRvrAsync
from sphero_sdk import Colors

# initialize global variables
key_helper = KeyboardHelper()
current_key_code = -1
driving_keys = [119, 97, 115, 100, 32]  # W,A,S,D,SPACE
speed = 0
heading = 0
flags = 0

loop = asyncio.get_event_loop()
rvr = SpheroRvrAsync(
    dal=SerialAsyncDal(
        loop
    )
)

def keycode_callback(keycode):
    global current_key_code
    current_key_code = keycode
    print("Key code updated: ", str(current_key_code))

async def set_led_color(color):
    """Helper function to set LED color"""
    await rvr.led_control.set_all_leds_color(color=color)

async def main():
    """
    Controls:
    W - Forward (Green LEDs)
    A - Turn Left (Blue LEDs)
    S - Reverse (Red LEDs)
    D - Turn Right (Purple LEDs)
    Spacebar - Stop (White LEDs)
    """
    global current_key_code
    global speed
    global heading
    global flags

    await rvr.wake()
    await rvr.reset_yaw()
    
    # Start with white LEDs
    await set_led_color(Colors.white)

    while True:
        if current_key_code == 119:  # W
            # Forward
            if flags == 1:  # If was going reverse
                speed = 64
            else:
                speed += 64
            flags = 0
            await set_led_color(Colors.green)
            
        elif current_key_code == 97:  # A
            # Turn Left
            heading -= 10
            await set_led_color(Colors.blue)
            
        elif current_key_code == 115:  # S
            # Reverse
            if flags == 0:  # If was going forward
                speed = 64
            else:
                speed += 64
            flags = 1
            await set_led_color(Colors.red)
            
        elif current_key_code == 100:  # D
            # Turn Right
            heading += 10
            await set_led_color(Colors.purple)
            
        elif current_key_code == 32:  # SPACE
            # Stop
            speed = 0
            flags = 0
            await set_led_color(Colors.white)

        # Limit speed
        speed = min(max(speed, -255), 255)

        # Keep heading between 0 and 359
        heading = heading % 360

        # Reset key code
        current_key_code = -1

        # Drive command
        await rvr.drive_with_heading(speed, heading, flags)

        # Small delay to prevent flooding
        await asyncio.sleep(0.1)

def run_loop():
    global loop
    global key_helper
    key_helper.set_callback(keycode_callback)
    loop.run_until_complete(
        asyncio.gather(
            main()
        )
    )

if __name__ == "__main__":
    loop.run_in_executor(None, key_helper.get_key_continuous)
    try:
        run_loop()
    except KeyboardInterrupt:
        print("Keyboard Interrupt...")
        key_helper.end_get_key_continuous()
    finally:
        print("Press any key to exit.")
        exit(1)
