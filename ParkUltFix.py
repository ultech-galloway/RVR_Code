import os
import sys
import time
import RPi.GPIO as GPIO

sys.path.append('/home/pi/sphero')

import asyncio
from sphero_sdk import SpheroRvrAsync
from sphero_sdk import SerialAsyncDal
from sphero_sdk import RawMotorModesEnum

# ── GPIO / Ultrasonic config ──────────────────────────────────────────────────
TRIG = 18
ECHO = 24

# ── Tuning knobs ──────────────────────────────────────────────────────────────
WALL_DISTANCE_CM   = 100
GAP_THRESHOLD_CM   = 70
SCAN_SPEED         = 60
SCAN_INTERVAL      = 0.2
FORWARD_AFTER_GAP  = 1.4

# ── Sensor helpers ────────────────────────────────────────────────────────────
def setup_ultrasonic():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    print("Ultrasonic sensor initialising…")
    time.sleep(0.5)

def get_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    pulse_start = time.time()
    timeout_start = pulse_start
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start - timeout_start > 0.1:
            return -1

    pulse_end = time.time()
    timeout_end = pulse_end
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end - timeout_end > 0.1:
            return -1

    distance = round((pulse_end - pulse_start) * 17150, 2)
    return distance

# ── Async motor helpers ────────────────────────────────────────────────────────
async def stop(rvr):
    await rvr.raw_motors(
        left_mode=RawMotorModesEnum.off.value,  left_duty_cycle=0,
        right_mode=RawMotorModesEnum.off.value, right_duty_cycle=0,
    )

async def drive_forward(rvr, speed=SCAN_SPEED):
    await rvr.raw_motors(
        left_mode=RawMotorModesEnum.forward.value,  left_duty_cycle=speed,
        right_mode=RawMotorModesEnum.forward.value, right_duty_cycle=speed,
    )

async def drive_reverse(rvr, speed=SCAN_SPEED):
    await rvr.raw_motors(
        left_mode=RawMotorModesEnum.reverse.value,  left_duty_cycle=speed,
        right_mode=RawMotorModesEnum.reverse.value, right_duty_cycle=speed,
    )

# ── Parallel-park sequence ────────────────────────────────────────────────────
async def parallel_park(rvr):
    
    print("▶ Backing up straight to align with spot…")
    await drive_reverse(rvr, speed=80)
    await asyncio.sleep(1.0)
    await stop(rvr)
    await asyncio.sleep(0.5)

    print("▶ Turning in (backing right)…")
    await rvr.raw_motors(
        left_mode=RawMotorModesEnum.reverse.value,  left_duty_cycle=160,
        right_mode=RawMotorModesEnum.reverse.value, right_duty_cycle=35,
    )
    await asyncio.sleep(0.7)
    await stop(rvr)
    await asyncio.sleep(0.3)

    print("▶ Straightening out…")
    await rvr.raw_motors(
        left_mode=RawMotorModesEnum.reverse.value,  left_duty_cycle=80,
        right_mode=RawMotorModesEnum.reverse.value, right_duty_cycle=140,
    )
    await asyncio.sleep(0.8)

    print("▶ Parked – stopping.")
    await stop(rvr)

# ── Main ──────────────────────────────────────────────────────────────────────
async def main(rvr):

    try:
        print("Waking RVR…")
        await rvr.wake()
        await asyncio.sleep(2)
        await rvr.reset_yaw()

        print("\n=== Scanning for parking spot ===")
        print("Rover will creep forward until a gap is detected.\n")

        await drive_forward(rvr, SCAN_SPEED)
        
        gap_detected = False

        while not gap_detected:
            distance = get_distance()

            if distance < 0:
                print("Sensor error – skipping reading")
            else:
                print(f"Distance: {distance:.1f} cm", end="")
                if distance > GAP_THRESHOLD_CM:
                    print("  ← GAP FOUND!")
                    gap_detected = True
                    break
                else:
                    print(f"  (wall at {distance:.1f} cm)")

            await asyncio.sleep(SCAN_INTERVAL)

        await stop(rvr)
        await asyncio.sleep(0.3)

        print(f"\nMoving forward {FORWARD_AFTER_GAP}s to centre on spot…")
        await drive_forward(rvr, SCAN_SPEED)
        await asyncio.sleep(FORWARD_AFTER_GAP)
        await stop(rvr)
        await asyncio.sleep(0.5)

        print("\n=== Beginning parallel park ===")
        await parallel_park(rvr)

        print("\n✅ Parallel park complete!")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        await stop(rvr)

    finally:
        await rvr.close()
        print("RVR connection closed.")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    rvr = SpheroRvrAsync(dal=SerialAsyncDal(loop))
    setup_ultrasonic()
    
    try:
        loop.run_until_complete(main(rvr))
    except KeyboardInterrupt:
        print('\nProgram terminated with keyboard interrupt.')
    finally:
        GPIO.cleanup()
        if loop.is_running():
            loop.close()
        print("GPIO cleaned up.")
