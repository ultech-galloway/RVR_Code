import os
import sys
import time
import RPi.GPIO as GPIO

# Add the SDK to the path
sys.path.append('/home/pi/sphero')

from sphero_sdk import SpheroRvrObserver

# Initialize RVR
rvr = SpheroRvrObserver()

# GPIO Pin Setup for Ultrasonic Sensor
TRIG = 18
ECHO = 24

def setup_ultrasonic():
    """Initialize the ultrasonic sensor GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    print("Ultrasonic sensor initializing...")
    time.sleep(0.5)

def get_distance():
    """Read distance from ultrasonic sensor in centimeters"""
    # Send 10us pulse to trigger
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    
    # Wait for echo to start
    pulse_start = time.time()
    timeout_start = pulse_start
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start - timeout_start > 0.1:  # 100ms timeout
            return -1  # Error value
    
    # Wait for echo to end
    pulse_end = time.time()
    timeout_end = pulse_end
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end - timeout_end > 0.1:  # 100ms timeout
            return -1  # Error value
    
    # Calculate distance
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # Speed of sound = 34300 cm/s, divide by 2
    distance = round(distance, 2)
    
    return distance

def main():
    """Main program to read and display ultrasonic sensor data"""
    try:
        # Wake up RVR
        print("Waking up RVR...")
        rvr.wake()
        time.sleep(2)
        
        # Setup ultrasonic sensor
        setup_ultrasonic()
        
        print("\n=== Ultrasonic Rangefinder Demo ===")
        print("Press Ctrl+C to exit\n")
        
        # Continuous reading loop
        while True:
            distance = get_distance()
            
            if distance > 0:
                print(f"Distance: {distance} cm ({distance / 2.54:.2f} inches)")
            else:
                print("Error reading sensor - out of range or timeout")
            
            time.sleep(0.5)  # Read every half second
            
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user")
        
    finally:
        # Clean up
        GPIO.cleanup()
        rvr.close()
        print("RVR connection closed. GPIO cleaned up.")

if __name__ == '__main__':
    main()
