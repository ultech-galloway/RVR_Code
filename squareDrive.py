"""
A short driving program for the Sphero RVR. Robot will drive
in square pattern using drive_with_heading' command.

Uses varible called 'heading' to create 4 sides of square.

LAST: 03/09/26
BY: Dr. A
"""

import os
import sys
sys.path.append('/home/pi/sphero')

import asyncio
from sphero_sdk import SpheroRvrAsync
from sphero_sdk import SerialAsyncDal
from sphero_sdk import DriveFlagsBitmask

# Initiate RVR
loop = asyncio.get_event_loop()

rvr = SpheroRvrAsync(
    dal=SerialAsyncDal(loop)
)


# Main function loop
async def main():
    """ Drive RVR in a square pattern """

    await rvr.wake()
    await asyncio.sleep(2)
    await rvr.reset_yaw()

    # Drive in a square (4 sides, variable called 'heading')
    for i in range(4):          # What is this line doing?
        heading = i * 90        # 0, 90, 180, 270 degrees
        
        print(f"Driving forward at heading {heading}...")
        await rvr.drive_with_heading(
            speed=86,
            heading=heading,
            flags=DriveFlagsBitmask.none.value
        )
        
        await asyncio.sleep(2)  # Drive forward for 2 seconds
        
        # Stop before turning
        await rvr.drive_with_heading(
            speed=0,
            heading=heading,
            flags=DriveFlagsBitmask.none.value
        )
        
        await asyncio.sleep(1)  # Wait 1 second before turning

    '''
    Can you think of another way I could have instructed it
    to drive in 4 lengths? It would use separate commands...
    '''


    print("Square complete! Stopping...")
    await rvr.drive_with_heading(
        speed=0,
        heading=0,
        flags=DriveFlagsBitmask.none.value
    )

    await rvr.close()


if __name__ == '__main__':
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print('\nProgram terminated with keyboard interrupt.')
        loop.run_until_complete(rvr.close())
    finally:
        if loop.is_running():
            loop.close()
