#routines to read data from picoammeter and sourcemeter for
#testing of the polaris ion source
#
#6/2/22 v1 par
#6.21.23 v3 par more stuff in the initialization routine
#7.18.24 v4 par more sourcemeter stuff for DIADEM

import serial
import time
import glob
import os
import binascii
import numpy as np
import matplotlib.pyplot as plt
import serial.rs485

## find serial ports
## I copy-pastaed this from stackoverflow
def serial_ports():
    """ Lists serial port names
        """

    ports = glob.glob('/dev/tty*')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
                ##print 'OSError'
                pass
        except EOFError:
                print('woot')
                pass
                    
    return result

## select which com port to use
def select_com_port(value, baud):
        """ print out availabe com ports and allow user to select one.
                Returns the com port pointer thingy.
        """

        lports = serial_ports()

        if value > -1:
            var = value
        else:
            print('Select from available com ports')
            print(lports)
            var = input(["[0-n]>>"])
        
        thingy = serial.Serial(lports[int(var)], baud, timeout=1)
        ##ser = serial.Serial(lports[0], 9600, timeout=1)


        ## print the com port to the screen
        print("Using COM port: " + thingy.name)

        #### get device info. Make sure it's what you think it is
        thingy.write("*IDN?\r".encode('utf-8'))
        time.sleep(1)
        print(thingy.read(thingy.inWaiting()) )

        return thingy
    
##************************************************************
# write a record to file
def write_logfile(filename,pathname,out,usetime):
    """
    append unformatted data to a file
    
    filename = ASCII filename without a path
    pathname = Optional ASCII pathname, defaluts to cwd if zero length input used ('')
    out = data to be written to file. Can be in format, this script doesnt care
    usetime = if a 1 then add the computer time to the start of the data. Anything else skips this.
    
    """
    #set path location
    if (len(pathname)==0):
        pathname = os.getcwd();
        
    logid = open(pathname + '/' + filename,'a');

    if (usetime == 1):
        logid.write("{:.2f}".format(time.time()) + ', ');
        
    if (not(isinstance(out, str))):
        out = str(out);
    
    logid.write(out + '\n');
    logid.close();
    
## automatically connect to the sourcemeter and picoammeter
def connect_pico():
    
    #get the open com ports, check to see if it has 'USB' in the string
    #if it does, open it and see if it's one of the supplies.
    
    pa = -1 #picoammeter
    sm = -1 #sourcemeter
    ig = -1 #ion gauge
    ps = -1 #power supply
    
    ports = serial_ports()
    #ports = glob.glob('/dev/ttyUSB*')
    
    for port in ports:
        if port.find('USB') >= 0:
            
            #open the port
            thingy = serial.Serial(port, 57600, timeout=1)
            
            #### get device info. 
            thingy.write("*IDN?\r".encode('utf-8'))
            time.sleep(.1)
            idn = thingy.read(thingy.inWaiting()) 
            
    
            if idn.find(b'KEITHLEY INSTRUMENTS INC.,MODEL 2400') >= 0:
                sm = thingy
                sm.write(b":SYST:BEEP:STAT ON\r")
                print(idn)
                continue
            if idn.find(b'KEITHLEY INSTRUMENTS INC.,MODEL 6485') >= 0:
                pa = thingy
                pa.write(b"*RST\r")
                print(idn)
                continue
            else:
                thingy.close()
            
            #find the ion gauge
#             thingy = serial.Serial(port, 19200, timeout=1)
#             thingy.write("#01VER\r".encode('utf-8'))
#             time.sleep(.1)
#             idn = thingy.read(thingy.inWaiting()) 
#             
#             if idn.find(b'*01 3351-101\r') == 0:
#                 ig = thingy
#                 print(idn)
#                 continue
    
    return pa, sm


def init_pa(pa,**kwards):
    
    """ 
    'median' <b> Enable (ON) or disable (OFF) median filter.
        'rank' <n> Specify median filter rank: 1 to 5. Default to 5.
    'average' <b> Enable (ON) or disable (OFF) digital filter.
        'tcon' <name> Select filter control: MOVing or REPeat. Default REP
        'count' number to average. defualt is 10.  
    """
    
    if 'rate' in kwards:
        rate = 6/kwards.get("rate")
    else:
        rate = 0.1
        
    if 'median' in kwards:
        temp = kwards.get("median")
        pa.write(("MED " + temp.upper() + "\r").encode('utf-8'))    
        
        if 'rank' in kwards:
            temp = kwards.get("rank")
        else:
            temp = 5
            
        pa.write(("RANK " + temp.upper() + "\r").encode('utf-8')) 
        
        
    if 'average' in kwards:
        temp = kwards.get("average")
        pa.write(("AVER " + temp.upper() + "\r").encode('utf-8'))
        
        if 'tcon' in kwards:
            temp = kwards.get("tcon")
        else:
            temp = 'REP'
        pa.write(("AVER:TCON " + temp.upper() + "\r").encode('utf-8'))   
        
        if 'count' in kwards:
            temp = kwards.get("count")
        else:
            temp = 10
        pa.write(("AVER:COUN " + str(temp) + "\r").encode('utf-8'))
        
    
    #junk = pa.read(pa.inWaiting())
    pa.write(b"SYST:ZCH OFF\r") #turn off zero check
    time.sleep(0.1)
    pa.write(b"TRIG:DEL 0\r")
    time.sleep(0.1)
    pa.write(b"RANG:AUTO ON\r") #auto ranging
    time.sleep(0.1)
    pa.write(b"FORM:ELEM READ, TIME\r") #set data format
    time.sleep(0.01) 
    pa.write(("NPLC %1.2f" % (rate) + "\r").encode('utf-8')) #set data format
    
    
def debug_measure_current(pa,nsamples):
    
    junk = pa.read(pa.inWaiting())
    
    pa.write(("TRIG:COUN " + str(nsamples) + "\r").encode('utf-8'))
    time.sleep(0.01)
    pa.write(("TRAC:POIN " +str(nsamples) +"\r").encode('utf-8'))
    time.sleep(0.01)
    pa.write(b"TRAC:CLE\r")
    time.sleep(0.01)
    pa.write(b"TRAC:FEED:CONT NEXT\r")
    time.sleep(0.01)
    pa.write(b"STAT:MEAS:ENAB 512\r")
    time.sleep(0.01)
    pa.write(b"INIT\r")
    time.sleep(0.05)
    pa.write(b"TRAC:DATA?\r")
    
def measure_current(pa,nsamples):
    
    junk = pa.read(pa.inWaiting())
    
    pa.write(("TRIG:COUN " + str(nsamples) + "\r").encode('utf-8'))
    time.sleep(0.01)
    pa.write(("TRAC:POIN " +str(nsamples) +"\r").encode('utf-8'))
    time.sleep(0.01)
    pa.write(b"TRAC:CLE\r")
    time.sleep(0.01)
    pa.write(b"TRAC:FEED:CONT NEXT\r")
    time.sleep(0.01)
    pa.write(b"STAT:MEAS:ENAB 512\r")
    time.sleep(0.01)
    pa.write(b"INIT\r")
    time.sleep(0.05)
    pa.write(b"TRAC:DATA?\r")
    
    out = bytes(0) #create variable for data
    
    woot = time.time()
    k=0
    while ((len(out) < (28*nsamples)) & (k < 1000)):
        out = out + pa.read(pa.inWaiting())
        time.sleep(0.02)
        k+=1
        #print('inwaiting = ' + str(pa.inWaiting()) + ', out = ' + str(len(out)) + ', k = ' + str(k))
        
    #print(time.time()-woot)
    #while pa.inWaiting()<(43*nsamples):
    #    time.sleep(0.01)
    #time.sleep(0.1)
    
    #out = pa.read(pa.inWaiting())
    
    out = out.strip().decode().replace('A','').split(',')
    
    amps = np.zeros(nsamples).astype('float')
    tsec = np.zeros(nsamples).astype('float')
#     
    for i in range(nsamples):
        amps[i] = float(out[i*2])
        tsec[i] = float(out[(i*2)+1])

    
    return amps, tsec

def measure_pressure(ig,nsamples):
    
    pressure = np.zeros(nsamples).astype('float')
    
    for i in range(nsamples):
        ig.write(b"#01RD\r")
        time.sleep(0.05)
        try:
            pressure[i] = float(ig.read(ig.inWaiting()).decode('utf-8')[3:])
        except:
            pressure[i] = float("NaN")
    
    return pressure


def play_tune(sm):
    
    for i in range(200,100,-1):
        sm.write((":SYST:BEEP:IMM "+ str(i*10)+ "," + str(.2) +",2\r").encode('utf-8'))
    
    

def log_pressure_emission(filename,nsamples,delay):
    
    pa, sm, ig = connect_meters();
    time.sleep(1)
    i = 0
    
    #volts = np.zeros(0)
    amps = np.zeros(0)
    pressure = np.zeros(0)

    init_pa(pa)

    print("starting data acquisition. will loop until CTL+C KeyboardInterrupt.")
    try:
        while 1:
            
            end = time.time()
            ain = measure_current(pa,nsamples)
            pin = measure_pressure(ig,nsamples)
            write_logfile(filename,'',str(np.mean(ain)) + ", " + str(np.mean(pin)),1)
            i+=1
            start = time.time()
            
            print(i,start-end, ain)
    except KeyboardInterrupt:
        print("ending data acquisition. thanks!!")
        pass
            
