"""
FOR RVR SWARM MVP

Lead RVR Code, Transmitting
Spring 2026 Robotics, Galloway
Dr. A

LAST: 04.09.26
"""

import os
import sys
import time
sys.path.append('/home/pi/sphero')

from sphero_sdk import SpheroRvrObserver
from sphero_sdk import InfraredCodes

rvr = SpheroRvrObserver()

def main():
    try:
        print("=== IR SENDER RVR ===")
        print("Broadcasting IR signals...\n")
        
        rvr.wake()
        time.sleep(2)

        # Start broadcasting
        rvr.start_robot_to_robot_infrared_broadcasting(
            far_code=InfraredCodes.one.value,
            near_code=InfraredCodes.zero.value
        )
        
        print("Broadcasting on far_code=1, near_code=0")
        print("Press Ctrl+C to stop\n")

        # Keep broadcasting
        while True:
            print("Broadcasting...")
            time.sleep(2)

    except KeyboardInterrupt:
        print('\n\nStopping...')

    finally:
        rvr.stop_robot_to_robot_infrared_broadcasting()
        time.sleep(0.5)
        rvr.close()
        print("Sender closed.")

if __name__ == '__main__':
    main()
