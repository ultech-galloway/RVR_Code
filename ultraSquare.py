"""
Ultrasonic-Guided Square Drive for Sphero RVR
Robot drives forward until it detects an
obstacle within 30cm, then turns 90 degrees.
Repeats 4 times to create a square.

LAST: 04.01.2026
BY: Dr. A
"""

import os
import sys
import time
import RPi.GPIO as GPIO
sys.path.append('/home/pi/sphero')

import asyncio
from sphero_sdk import SpheroRvrAsync
from sphero_sdk import SerialAsyncDal
from sphero_sdk import DriveFlagsBitmask

loop = asyncio.get_event_loop()
rvr = SpheroRvrAsync(dal=SerialAsyncDal(loop))

# GPIO Pin Setup for Ultrasonic Sensor
TRIG = 18
ECHO = 24

def setup_ultrasonic():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    print("Ultrasonic sensor initializing...")
    time.sleep(0.5)

def get_distance():
    # Send 10us pulse to trigger
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    
    # Wait for echo to start
    pulse_start = time.time()
    timeout_start = pulse_start
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start - timeout_start > 0.1:
            return -1
    
    # Wait for echo to end
    pulse_end = time.time()
    timeout_end = pulse_end
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end - timeout_end > 0.1:
            return -1
    
    # Calculate distance
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    
    return distance

async def drive_until_obstacle(heading, obstacle_distance=30):
    print(f"Driving forward at heading {heading}° until obstacle detected...")
    
    # Keep driving until obstacle detected
    while True:
        distance = get_distance()
        
        if distance > 0:
            print(f"  Distance: {distance} cm", end='\r')
            
            if distance <= obstacle_distance:
                print(f"\n  Obstacle detected at {distance} cm! Stopping...")
                break
        else:
            print("  Sensor error - continuing...", end='\r')
        
        # Send drive command repeatedly to keep moving
        await rvr.drive_with_heading(speed=60, heading=heading, flags=DriveFlagsBitmask.none.value)
        await asyncio.sleep(0.1)
    
    # Stop the RVR
    await rvr.drive_with_heading(speed=0, heading=heading, flags=DriveFlagsBitmask.none.value)
    await asyncio.sleep(0.5)
    print("  Motors stopped.\n")

async def turn_90_degrees(current_heading):
    new_heading = (current_heading + 90) % 360
    print(f"Turning 90° clockwise (from {current_heading}° to {new_heading}°)...")
    
    await rvr.drive_with_heading(speed=0, heading=new_heading, flags=DriveFlagsBitmask.none.value)
    await asyncio.sleep(1)
    print("  Turn complete.\n")
    
    return new_heading

async def main():
    try:
        print("=== Ultrasonic-Guided Square Drive ===\n")
        
        print("Waking up RVR...")
        await rvr.wake()
        await asyncio.sleep(2)
        await rvr.reset_yaw()
        
        setup_ultrasonic()
        
        print("Ready! RVR will drive until obstacle is within 30cm, stop, then turn 90°.")
        print("Press Ctrl+C to stop\n")
        await asyncio.sleep(2)
        
        # Drive in a square (4 sides)
        heading = 0
        
        for side in range(4):
            print(f"--- Side {side + 1} of 4 ---")
            await drive_until_obstacle(heading, obstacle_distance=30)
            heading = await turn_90_degrees(heading)
            await asyncio.sleep(1)
        
        print("Square complete! All 4 sides driven.")
        
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user")
        
    finally:
        await rvr.drive_with_heading(speed=0, heading=0, flags=DriveFlagsBitmask.none.value)
        GPIO.cleanup()
        await rvr.close()
        print("RVR connection closed. GPIO cleaned up.")

if __name__ == '__main__':
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print('\nProgram terminated with keyboard interrupt.')
        loop.run_until_complete(rvr.close())
    finally:
        if loop.is_running():
            loop.close()
        GPIO.cleanup()
