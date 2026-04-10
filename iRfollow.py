"""
FOR RVR SWARM MVP

Follow RVR Code, Receiving
Spring 2026 Robotics, Galloway
Dr. A

LAST: 04.09.26
"""

import os
import sys
import time
sys.path.append('/home/pi/sphero')

from sphero_sdk import SpheroRvrObserver
from sphero_sdk import RawMotorModesEnum

rvr = SpheroRvrObserver()

# Track detected IR info
last_detected_location = None
last_detected_code = None

def infrared_message_received_handler(infrared_message):
    """Handler called when IR message is received"""
    global last_detected_location, last_detected_code
    
    print('IR Message Received:', infrared_message)
    
    # infrared_message format: {'Robot': [(sensor_id, code), ...]}
    # sensor_id: 0=front, 1=back, 2=left, 3=right
    # code: 1=far, 0=near (based on leader's broadcast settings)
    
    if 'Robot' in infrared_message and len(infrared_message['Robot']) > 0:
        # Get the first detection (sensor_id, code)
        detection = infrared_message['Robot'][0]
        
        if isinstance(detection, tuple) and len(detection) == 2:
            last_detected_location = detection[0]
            last_detected_code = detection[1]
        elif isinstance(detection, int):
            # Sometimes just the sensor ID is returned
            last_detected_location = detection
            last_detected_code = None
        
        sensor_names = {0: "Front", 1: "Back", 2: "Left", 3: "Right"}
        sensor_name = sensor_names.get(last_detected_location, "Unknown")
        
        signal_type = ""
        if last_detected_code == 1:
            signal_type = " (FAR signal)"
        elif last_detected_code == 0:
            signal_type = " (NEAR signal)"
        
        print(f"  → {sensor_name} sensor{signal_type}")
    else:
        last_detected_location = None
        last_detected_code = None
        print("  → No signal detected")

def main():
    global last_detected_location, last_detected_code
    
    try:
        print("=== IR RECEIVER RVR ===")
        print("Listening for IR signals...\n")
        
        rvr.wake()
        time.sleep(2)

        # Register the IR message handler
        rvr.on_robot_to_robot_infrared_message_received_notify(
            handler=infrared_message_received_handler
        )
        
        # Enable IR message notifications
        rvr.enable_robot_infrared_message_notify(is_enabled=True)
        
        print("IR listening enabled. Waiting for signals...")
        print("Will turn toward detected signals.\n")

        # Main control loop
        while True:
            if last_detected_location == 0:
                # Signal in front - stop (already facing it)
                print("Action: Signal ahead - stopped")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.off.value,
                    left_duty_cycle=0,
                    right_mode=RawMotorModesEnum.off.value,
                    right_duty_cycle=0
                )
            
            elif last_detected_location == 2:
                # Signal on left - turn left
                print("Action: Turning left toward signal")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.reverse.value,
                    left_duty_cycle=80,
                    right_mode=RawMotorModesEnum.forward.value,
                    right_duty_cycle=80
                )
            
            elif last_detected_location == 3:
                # Signal on right - turn right
                print("Action: Turning right toward signal")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.forward.value,
                    left_duty_cycle=80,
                    right_mode=RawMotorModesEnum.reverse.value,
                    right_duty_cycle=80
                )
            
            elif last_detected_location == 1:
                # Signal behind - turn around (spin left)
                print("Action: Signal behind - turning around")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.reverse.value,
                    left_duty_cycle=80,
                    right_mode=RawMotorModesEnum.forward.value,
                    right_duty_cycle=80
                )
            
            else:
                # No signal - stop and wait
                print("Action: No signal - stopped")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.off.value,
                    left_duty_cycle=0,
                    right_mode=RawMotorModesEnum.off.value,
                    right_duty_cycle=0
                )
            
            time.sleep(0.3)

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
