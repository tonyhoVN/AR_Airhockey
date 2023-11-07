import serial
import time 

## Setup Connection
port = 'COM11' # Change COM to Bluetooth or Serial
bluetooth = serial.Serial(port, 9600) #Start communications with the bluetooth unit
print("Connected")
bluetooth.flushInput() #This gives the bluetooth a little kick

## Main loop
while True:
    a = str(input("Signal: ")) # Input signal: 1-LED ON , 0-LED OFF
    bluetooth.write(str.encode(str(a)))
    time.sleep(100)


