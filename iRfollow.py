"""
FOR RVR SWARM MVP

Follow RVR Code, Receiving
Spring 2026 Robotics, Galloway
Dr. A

LAST: 04.14.26
"""

import os
import sys
import time
sys.path.append('/home/pi/sphero')

from sphero_sdk import SpheroRvrObserver
from sphero_sdk import RawMotorModesEnum

rvr = SpheroRvrObserver()

# Global variables to track sensor readings
current_readings = {'front': 255, 'right': 255, 'back': 255, 'left': 255}

def parse_infrared_readings(sensor_data):
    """
    Parse the 32-bit sensor data into individual sensor readings
    Returns dict with 'front', 'back', 'left', 'right' keys
    """
    # Extract each byte from the 32-bit value
    front = sensor_data & 0xFF          # bits 0-7
    right = (sensor_data >> 8) & 0xFF   # bits 8-15
    back = (sensor_data >> 16) & 0xFF   # bits 16-23
    left = (sensor_data >> 24) & 0xFF   # bits 24-31
    
    return {
        'front': front,
        'right': right,
        'back': back,
        'left': left
    }

def infrared_readings_handler(infrared_data):
    """Handler for infrared sensor readings"""
    global current_readings
    
    if 'SensorData' in infrared_data:
        sensor_data = infrared_data['SensorData']
        current_readings = parse_infrared_readings(sensor_data)

def determine_direction(readings):
    """
    Determine which direction has the strongest signal
    Returns: 'front', 'back', 'left', 'right', or None
    """
    # Filter out 255 (empty) readings
    valid_readings = {k: v for k, v in readings.items() if v < 255}
    
    if not valid_readings:
        return None
    
    # Find direction with lowest value (strongest signal)
    # IR codes 0-15 mean signal detected, lower = stronger
    strongest_direction = min(valid_readings, key=valid_readings.get)
    
    return strongest_direction

def main():
    global current_readings
    
    try:
        print("=== IR RECEIVER RVR ===")
        print("Polling IR sensors for signals...\n")
        
        rvr.wake()
        time.sleep(2)

        print("Starting sensor polling...")
        print("Will turn toward detected signals.\n")

        # Main control loop - poll sensors continuously
        while True:
            # Request current IR sensor readings
            rvr.get_bot_to_bot_infrared_readings(handler=infrared_readings_handler)
            time.sleep(0.1)  # Give time for response
            
            readings = current_readings
            
            # Show readings
            print(f"Readings - Front:{readings['front']:3d} Right:{readings['right']:3d} " +
                  f"Back:{readings['back']:3d} Left:{readings['left']:3d}", end="")
            
            direction = determine_direction(readings)
            
            if direction == 'front':
                print(" → Signal AHEAD - stopped")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.off.value,
                    left_duty_cycle=0,
                    right_mode=RawMotorModesEnum.off.value,
                    right_duty_cycle=0
                )
            
            elif direction == 'left':
                print(" → Signal LEFT - turning left")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.reverse.value,
                    left_duty_cycle=80,
                    right_mode=RawMotorModesEnum.forward.value,
                    right_duty_cycle=80
                )
            
            elif direction == 'right':
                print(" → Signal RIGHT - turning right")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.forward.value,
                    left_duty_cycle=80,
                    right_mode=RawMotorModesEnum.reverse.value,
                    right_duty_cycle=80
                )
            
            elif direction == 'back':
                print(" → Signal BEHIND - turning around")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.reverse.value,
                    left_duty_cycle=80,
                    right_mode=RawMotorModesEnum.forward.value,
                    right_duty_cycle=80
                )
            
            else:
                print(" → No signal - stopped")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.off.value,
                    left_duty_cycle=0,
                    right_mode=RawMotorModesEnum.off.value,
                    right_duty_cycle=0
                )
            
            time.sleep(0.2)

    except KeyboardInterrupt:
        print('\n\nStopping...')

    finally:
        # Stop motors
        rvr.raw_motors(
            left_mode=RawMotorModesEnum.off.value,
            left_duty_cycle=0,
            right_mode=RawMotorModesEnum.off.value,
            right_duty_cycle=0
        )
        time.sleep(0.5)
        rvr.close()
        print("Receiver closed.")

if __name__ == '__main__':
    main()
