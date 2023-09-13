## talk to the model 2 series scope

import sys,os
#import curses
#import serial
import numpy as np
import time
import os
import pyvisa

def open_scope(**kwargs):
    
    class defaults():
        com = 'USB0::1689::261::SGVJ0000517::0::INSTR'
        model = 'MSO24'
            
    inputs = defaults
 
    for k,v in kwargs.items():
        setattr(inputs,k.lower(),v)
               
    
    print('open scope',end='')
    rm = pyvisa.ResourceManager()
    tek = rm.open_resource(inputs.com)
    temp = tek.query('*IDN?')
    time.sleep(0.1)
    if temp.find(inputs.model) >= 0:
        print(u'\u2713')
    else:
        print('x')
        
    return tek

def waveform_init(com,**kwargs):
    '''
    kwargs available
    
    encdg = 'binary'
    source = 'ch1'
    start = 1
    stop = 10000
    byt_nr = 2
    header = 0
    numavg = 10
    '''
    
    #defaults
    class defaults():
        encdg = 'binary'
        source = 'ch1'
        start = 1
        stop = 10000
        byt_nr = 2
        header = 0
        numavg = 10
    
    class value_parents():
        encdg= ':wfmoutpre:'
        source = ':data:'
        start = ':data:'
        stop = ':data:'
        byt_nr = ':wfmoutpre:'
        header = ':'
        numavg = ':acquire:'
    
    inputs = defaults()
    parents = value_parents()
    
    for k,v in kwargs.items():
        setattr(inputs,k.lower(),v)
        
    for k in dir(defaults):
        if not k.startswith('__'):
            com.write(getattr(parents,k) + k + ' ' + str(getattr(inputs,k)))
            print(getattr(parents,k) + k + ' ' + str(getattr(inputs,k)))
            
    
    return inputs
    
def read_waveform(com,**kwargs):
    
    class defaults():
        source = 'ch1'
        start = 1
        stop = 10000
        
    class value_parents():
        source = ':data:'
        start = ':data:'
        stop = ':data:'
        
    class output():
        xzero = 0
    
    inputs = defaults
    data = output
    parents = value_parents()
    
    for k,v in kwargs.items():
        setattr(inputs,k.lower(),v)
     
    for k in dir(defaults):
        if not k.startswith('__'):
            com.write(getattr(parents,k) + k + ' ' + str(getattr(inputs,k)))
            #print(getattr(parents,k) + k + ' ' + str(getattr(inputs,k)))
        
    data.xzero = float(com.query(':wfmoutpre:xzero?'))
    data.xincr = float(com.query(':wfmoutpre:xincr?'))
    data.pt_off = float(com.query(':wfmoutpre:pt_off?'))
    data.ymult = float(com.query(':wfmoutpre:ymult?'))
    data.pos = float(com.query(':'+ inputs.source + ':pos?'))
     
    #read the waveform. With MSB byte order, the 'H' datatype return 0-65,535 for bottom
    #to top of the screen position.
    data.wave = com.query_binary_values(":curve?",datatype='H',is_big_endian=True)
    #data.wave = np.array(data.wave)/65535
    data.wave = np.array(data.wave)
    
    #this value is the voltage measured. The pos variable is weird. it seems to
    #be the location of the zero with -5 at the bottom of the screen and +5 at the top.
    data.volts = data.wave*data.ymult - (data.pos + 5)/10*65535*data.ymult
    
    return data
    
