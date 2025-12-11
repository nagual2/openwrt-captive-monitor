#!/usr/bin/env python3
"""Serial console tool for OpenWrt router management via COM port."""

import serial
import time
import sys

def send_command(ser, command, wait_time=2):
    """Send command to serial port and read response."""
    # Clear input buffer
    ser.reset_input_buffer()

    # Send command
    ser.write(f"{command}\n".encode())
    ser.flush()

    # Wait for response
    time.sleep(wait_time)

    # Read response
    response = b""
    while ser.in_waiting > 0:
        response += ser.read(ser.in_waiting)
        time.sleep(0.1)

    return response.decode('utf-8', errors='ignore')

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "COM1"
    baudrate = int(sys.argv[2]) if len(sys.argv) > 2 else 115200

    print(f"Connecting to {port} at {baudrate} baud...")

    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )

        print("Connected! Sending commands...")
        time.sleep(1)

        # Send newline to get prompt
        ser.write(b"\n")
        time.sleep(0.5)

        # Read commands from stdin or execute provided command
        if len(sys.argv) > 3:
            command = sys.argv[3]
            print(f"\n=== Executing: {command} ===")
            response = send_command(ser, command)
            print(response)
        else:
            # Interactive mode - read from stdin
            for line in sys.stdin:
                command = line.strip()
                if command:
                    print(f"\n=== Executing: {command} ===")
                    response = send_command(ser, command)
                    print(response)

        ser.close()
        print("\nConnection closed.")

    except serial.SerialException as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
