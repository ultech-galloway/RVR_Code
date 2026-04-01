import os
import sys
import time
sys.path.append('/home/pi/sphero')

from sphero_sdk import SpheroRvrObserver
from sphero_sdk import RawMotorModesEnum

rvr = SpheroRvrObserver()

# Track which sensor last detected IR
last_detected_location = None

def infrared_message_received_handler(infrared_message):
    """Handler called when IR message is received"""
    global last_detected_location
    
    print('IR Message Received:', infrared_message)
    
    # infrared_message format example: 
    # {'Robot': [0]} means front sensor (0) detected signal
    # Sensor IDs: 0=front, 1=back, 2=left, 3=right
    
    if 'Robot' in infrared_message and len(infrared_message['Robot']) > 0:
        # Get the first sensor that detected the signal
        last_detected_location = infrared_message['Robot'][0]
        
        if last_detected_location == 0:
            print("  → Front sensor - SIGNAL AHEAD!")
        elif last_detected_location == 1:
            print("  → Back sensor - SIGNAL BEHIND!")
        elif last_detected_location == 2:
            print("  → Left sensor - SIGNAL ON LEFT!")
        elif last_detected_location == 3:
            print("  → Right sensor - SIGNAL ON RIGHT!")
    else:
        last_detected_location = None
        print("  → No signal detected")

def main():
    global last_detected_location
    
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
        print("Will drive toward detected signals.\n")

        # Main control loop
        while True:
            if last_detected_location == 0:
                # Signal in front - drive straight
                print("Action: Driving forward")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.forward.value,
                    left_speed=100,
                    right_mode=RawMotorModesEnum.forward.value,
                    right_speed=100
                )
            
            elif last_detected_location == 2:
                # Signal on left - turn left
                print("Action: Turning left")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.forward.value,
                    left_speed=50,
                    right_mode=RawMotorModesEnum.forward.value,
                    right_speed=120
                )
            
            elif last_detected_location == 3:
                # Signal on right - turn right
                print("Action: Turning right")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.forward.value,
                    left_speed=120,
                    right_mode=RawMotorModesEnum.forward.value,
                    right_speed=50
                )
            
            elif last_detected_location == 1:
                # Signal behind - spin around
                print("Action: Spinning to face signal")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.forward.value,
                    left_speed=100,
                    right_mode=RawMotorModesEnum.reverse.value,
                    right_speed=100
                )
            
            else:
                # No signal - stop and wait
                print("Action: No signal - stopped")
                rvr.raw_motors(
                    left_mode=RawMotorModesEnum.off.value,
                    left_speed=0,
                    right_mode=RawMotorModesEnum.off.value,
                    right_speed=0
                )
            
            time.sleep(0.5)  # Update every 0.5 seconds

    except KeyboardInterrupt:
        print('\n\nStopping...')

    finally:
        # Stop motors
        rvr.raw_motors(
            left_mode=RawMotorModesEnum.off.value,
            left_speed=0,
            right_mode=RawMotorModesEnum.off.value,
            right_speed=0
        )
        time.sleep(0.5)
        rvr.close()
        print("Receiver closed.")

if __name__ == '__main__':
    main()
