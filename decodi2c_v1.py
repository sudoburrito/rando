#decode I2C
from numpy import nonzero, roll, diff, array, logical_not

#*********************************************************
def find_fall(data,**kwargs):
    
    class defaults():
        fall_sep = 100
        fall_steps = 10
        fall_level = (max(data)-min(data))/2
            
    inputs = defaults
 
    for k,v in kwargs.items():
        setattr(inputs,k.lower(),v)
        
        
    
    temp = nonzero((data - roll(data,inputs.fall_steps)) < -inputs.fall_level)
    
    fall = temp[0][nonzero(diff(temp)>inputs.fall_sep)[1]]
    
    return fall


#*********************************************************
def decode_logic(data,**kwargs):
    
    class defaults():
        invert = False
            
    inputs = defaults
 
    for k,v in kwargs.items():
        setattr(inputs,k.lower(),v)
    mid = (max(data)-min(data))/2
    
    logic = array(data > mid)
    
    if inputs.invert:
        logic = logical_not(logic)
        
    logic = logic.astype('int')
    
    return logic
    
    