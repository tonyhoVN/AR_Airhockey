import serial
import time 

port = 'COM11'
bluetooth = serial.Serial(port, 9600) #Start communications with the bluetooth unit
print("Connected")
# bluetooth.flushInput() #This gives the bluetooth a little kick

while True:
    a = str(input("Digital: "))
    bluetooth.write(str.encode(str(a)))
    time.sleep(100)


