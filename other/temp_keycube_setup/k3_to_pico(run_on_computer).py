import serial

keycube_port = 'COM5' # Keycube device port, will change depending on computer
pico_port = 'COM4'    # Pico device port, will change depending on computer

baudrate = 115200

keycube_ser = serial.Serial(keycube_port, baudrate, timeout=1)
pico_ser = serial.Serial(pico_port, baudrate, timeout=1)


while True:
    line = keycube_ser.readline().decode('utf-8', errors='ignore').strip()
    if line:
        #print(line)
        pico_ser.write((line + "\r\n").encode("utf-8"))

#W = 45 , A = 43, S = 42, D = 41
