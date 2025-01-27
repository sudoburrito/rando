#routines to read data from picoammeter and sourcemeter for
#testing of the polaris ion source
#
#6/2/22 v1 par
#6.21.23 v3 par more stuff in the initialization routine

import serial
import time
import glob
import os
import binascii
import numpy as np
import matplotlib.pyplot as plt
#import serial.rs485
from importlib import reload

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

def sm_sweep(sm,**kwargs):
    
    class defaults():
        start = -10
        stop = 10
        ranging = 'auto'
        spacing = 'linear'
        points = 10
        direction = 'up'
        arm_count = 1
        source_delay = 1
        trigger_delay = 0
        nplc = 10
        compliance = .001
        sm_info = ''
        extra = 'jumbo1'
        experiment = 'DIADEM'
    
    val = defaults()
    
    for k,v in kwargs.items():
        setattr(val,k.lower(),v)
        
    #clear buffer
    if sm.inWaiting() > 0:
        junk = sm.read(sm.inWaiting())
        
    #get info
    kwrite(sm,'*IDN?')
    time.sleep(1)
    setattr(val,'sm_info',sm.read(sm.inWaiting()))
    
    kwrite(sm,':SYST:BEEP:IMM 500,.1')    
    kwrite(sm,'*RST')
    kwrite(sm,':syst:azer:stat off')
    kwrite(sm,':trace:tstamp:format abs')
    kwrite(sm,':form:elem time, volt, curr')
    kwrite(sm,':SOURce:VOLT:MODE SWEep')
    kwrite(sm,':source:volt:start ' + '{v:.2e}'.format(v = val.start))
    kwrite(sm,':source:volt:stop ' + '{v:.2e}'.format(v = val.stop))
    kwrite(sm,':source:sweep:ranging ' + val.ranging)
    kwrite(sm,':source:sweep:spacing ' + val.spacing)
    kwrite(sm,':source:sweep:points ' + '{v:.2e}'.format(v = val.points))
    kwrite(sm,':source:sweep:direction ' + val.direction)
    kwrite(sm,':trig:count ' + '{v:.2e}'.format(v = val.points))
    kwrite(sm,':arm:count ' + '{v:.2e}'.format(v = val.arm_count))
    kwrite(sm,':source:delay '+ '{v:.2e}'.format(v = val.source_delay))
    kwrite(sm,':trigger:delay '+ '{v:.2e}'.format(v = val.trigger_delay))
    kwrite(sm,':sense:curr:NPLC ' + '{v:.2e}'.format(v = val.nplc))
    kwrite(sm,':sens:curr:prot:lev ' + '{v:.2e}'.format(v = val.compliance))
    kwrite(sm,':output on')
    kwrite(sm,':READ?')
    kwrite(sm,':output off')
    
    out = bytes(0) #create variable for data
    print('waiting for data', end='')
    while sm.inWaiting() == 0:
        time.sleep(1)
        print('.', end='')
    print('\nreading sourcemeter output.')
    
    data = bytes(0)
    nbuffer = sm.inWaiting()
    k = 0
    while(k<10):
        
        data = data + sm.read(sm.inWaiting())
        
        time.sleep(val.source_delay*2 + 1)
        nbuffer = len(data)
        
        print('\r',end='')
        print('bytes read: ',end='')
        print(nbuffer,end='')

        if sm.inWaiting() == 0:
            k+=1
    
    print('\r',end='')
    print('bytes read: ',end='')
    print(nbuffer,end='')
    
    print('')
    print('done')
    
    #play_tune(sm)
    
    data = data.strip().decode().split(',')
    
    volts = data[0::3]
    amps = data[1::3]
    
    for i in range(len(volts)):
        volts[i] = float(volts[i])
        amps[i] = float(amps[i])
        
    save_sm_data([volts,amps],val,file_experiment = val.experiment, file_extra=val.extra)
    play_tune(sm)
    return volts, amps

def save_sm_data(data,settings,**kwargs):
    
    class defaults():
        file_path = '/home/pi/Documents/diadem/save_files/'
        file_time = time.strftime('%Y%m%d_%H%M%S')
        file_experiment = 'diadem'
        file_extra = ''
    
    val = defaults()
    
    for k,v in kwargs.items():
        setattr(val,k.lower(),v)
        
    full_name = val.file_experiment + '_' + val.file_time + '_'  + val.file_extra
    
    
    #file header
    logid = open(val.file_path + full_name + '.txt','w');
    
    
    logid.write('experiment: {}\r'.format(val.file_experiment))
    logid.write('file_created: {}\r'.format(val.file_time))
    logid.write('extra:  {}\r'.format(val.file_extra))
    logid.write('Sourcemeter: {}\r'.format(settings.sm_info))
    logid.write('start: {}\r'.format(settings.start))
    logid.write('stop: {}\r'.format(settings.stop))
    logid.write('source_delay: {}\r'.format(settings.source_delay))
    logid.write('trigger_delay: {}\r'.format(settings.trigger_delay))
    logid.write('pionts: {}\r'.format(settings.points))
    logid.write('direction: {}\r'.format(settings.direction))
    logid.write('NPLC: {}\r'.format(settings.nplc))
    logid.write('compliance: {}\r'.format(settings.compliance))
    logid.write('ranging: {}\r'.format(settings.ranging))
    logid.write('\n')
    logid.write('volts, amps')
    for i in range(len(data[0])):
        logid.write('\n')
        logid.write('{:.3e}'.format(data[0][i]) + ', ' '{:.3e}'.format(data[1][i]) )
        
    logid.close()
    
    print('file saved: ')
    print(val.file_path)
    print(full_name)
    
#     logid.write('Scan_i = {}\r'.format(scan_i))
#     logid.write('{}\r'.format(range_i))
#     logid.write('Scan_j = {}\r'.format(scan_j))
#     logid.write('{}\r'.format(range_j))
# 
#     logid.write('fixed OG = {}\r'.format(outer_grid_fixed))
#     logid.write('fixed IG = {}\r'.format(inner_grid_fixed))
#     logid.write('fixed RG = {}\r'.format(rpa_fixed))
#     logid.write('fixed RB = {}\r'.format(repeller_fixed))
#     logid.write('fixed L1 = {}\r'.format(L1_fixed))
#     logid.write('fixed L2 = {}\r'.format(L2_fixed))
#     logid.write('fixed L3 = {}\r'.format(L3_fixed))
#     logid.write('fixed FB = {}\r'.format(fil_bias_fixed))
#     logid.write('fixed EC = {}\r'.format(ec_fixed))
#     logid.write('filament num = {}\r'.format(fil_number))

def init_sm(sm,**kwargs):
    
    class defaults():
        term = 'rear'
        poin = 100
        cont = 'NEXT'
        sour = 'IMM'
        tcoun = poin
        acoun = 1
        sour_func = 'VOLT'
        sens_func = 'CURR'
        nplc = 10
        stat = 'OFF'
        comp = 1e-2
        sour_range = 200
        sens_range = 1e-2
        dire = 'UP'
        spac = 'LINEAR'
        sour_start = -10
        sour_stop = 10
        sour_step = (sour_stop-sour_start)/poin
        t_delay = 0
        s_delay = 1
        auto = 'ON'
        
    val = defaults()
    
    for k,v in kwargs.items():
        setattr(val,k.lower(),v)
        
    kwrite(sm,':rout:term ' + val.term)
    kwrite(sm,':trac:poin ' + '{var:.2e}'.format(var = val.poin))
    kwrite(sm,':trac:feed:cont ' + val.cont)
    kwrite(sm,':trig:sour IMM')
#     kwrite(sm,':trig:coun ' + '{var:.2e}'.format(var = val.tcoun))
#     kwrite(sm,':arm:coun ' + '{var:.2e}'.format(var = val.acoun))
#     kwrite(sm,':sour:func VOLT')
#     kwrite(sm,':sour:volt:mode swe')
#     kwrite(sm,':sense:func CURR')
#     kwrite(sm,':sense:curr:NPLC ' + '{var:.2e}'.format(var = val.nplc))
#     kwrite(sm,':syst:azer:stat off')
#     kwrite(sm,':sens:curr:prot:lev ' + '{var:.2e}'.format(var = val.comp))
    


def kwrite(com,val):
    
    com.write((val + '\r').encode('utf-8'))

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
        
    if 'sour_arm' in kwards:
        temp = kwards.get("sour_arm")
        pa.write(("ARM:SOUR " + temp +"\r").encode('utf-8'))
    else:
        pa.write(b"ARM:SOUR IMM\r")
        time.sleep(0.1)
        
    if 'tlink_num' in kwards:
        temp = kwards.get("tlink_num")
        pa.write(("ARM:ILIN " + str(temp) + "\r").encode('utf-8'))
        time.sleep(0.1)
        
    if 'range' in kwards:
        temp = kwards.get("range")
        pa.write(b"CURR:RANG:AUTO OFF\r")
        time.sleep(0.01)
        pa.write(("CURR:RANG " + str(temp) +  "\r").encode('utf-8'))
        pa.write(b"CURR:RANG:AUTO OFF\r")
    else:
        pa.write(b"RANG:AUTO ON\r") #auto ranging
        time.sleep(0.1)
    
    #junk = pa.read(pa.inWaiting())
    pa.write(b"ARM:COUN 1\r")
    time.sleep(0.1)
    pa.write(b"SYST:ZCH OFF\r") #turn off zero check
    time.sleep(0.1)
    pa.write(b"TRIG:SOUR IMM\r")
    time.sleep(0.1)
    pa.write(b"TRIG:DEL 0\r")
    time.sleep(0.1)
    #pa.write(b"RANG:AUTO ON\r") #auto ranging
    #time.sleep(0.1)
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
    while ((len(out) < (28*nsamples)) & (k < 5000)):
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

def measure_current_tlink(pa,narms,nsamples):
    
    junk = pa.read(pa.inWaiting())
    pa.write(("ARM:COUN " + str(narms) + "\r").encode('utf-8'))
    time.sleep(0.01)
    pa.write(("TRIG:COUN " + str(nsamples) + "\r").encode('utf-8'))
    time.sleep(0.01)
    pa.write(("TRAC:POIN " +str(nsamples*narms) +"\r").encode('utf-8'))
    time.sleep(0.01)
    pa.write(b"TRAC:CLE\r")
    time.sleep(0.01)
    pa.write(b"TRAC:FEED:CONT NEXT\r")
    time.sleep(0.01)
    pa.write(b"STAT:MEAS:ENAB 512\r")
    time.sleep(0.01)
    pa.write(b"INIT\r")
    #time.sleep(0.05)
   
    
    time.sleep(narms + 1)
    
    pa.write(b"TRAC:DATA?\r")
    
    out = bytes(0) #create variable for data
    
    woot = time.time()
    k=0
    while ((len(out) < (28*nsamples*narms)) & (k < 500)):
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
    
    amps = np.zeros(nsamples*narms).astype('float')
    tsec = np.zeros(nsamples*narms).astype('float')
#     
    for i in range(nsamples*narms):
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


def play_tune(sm,**kwargs):
    
    class defaults():
        delay = 0.2
        
    
    val = defaults()
    
    for k,v in kwargs.items():
        setattr(val,k.lower(),v)
#     for i in range(200,100,-1):
#         sm.write((":SYST:BEEP:IMM "+ str(i*10)+ "," + str(.2) +",2\r").encode('utf-8'))
#     
    kwrite(sm,':SYST:BEEP:IMM 300,.1')
    time.sleep(val.delay)
    kwrite(sm,':SYST:BEEP:IMM 400,.1')
    time.sleep(val.delay)
    kwrite(sm,':SYST:BEEP:IMM 500,.1')
    time.sleep(val.delay)
    kwrite(sm,':SYST:BEEP:IMM 600,2')
    time.sleep(val.delay)
    kwrite(sm,':SYST:BEEP:IMM 500,.1')
    time.sleep(val.delay)
    kwrite(sm,':SYST:BEEP:IMM 400,.1')
    time.sleep(val.delay)
    kwrite(sm,':SYST:BEEP:IMM 300,.1')
    time.sleep(val.delay)
    kwrite(sm,':SYST:BEEP:IMM 200,2')
    time.sleep(val.delay)

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
            
