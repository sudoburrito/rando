#/usr/bin/python
#
#telemetry locations


import numpy as np

frame_len = 1288;
header_len = 0;

sync_pattern = [0x1A,0xCF,0xFC] #not actually used anywhere
sync_bytes = [0x1A,0xCF,0xFC,0x1D,0x87]; #0x87 added just for TM packet
sync_bytes_hns = [0x1A,0xCF,0xFC,0x1D,0xa0];
sync_bytes_ack = [0x1A,0xCF,0xFC,0x1D,0x10];
sync_bytes_adc = [0x1A,0xCF,0xFC,0x1D,0xFF]

loc_header = 0

loc_coarse_time = 26-header_len
loc_fine_time = 30-header_len

loc_packet_id = 4-header_len
loc_target_id = 5-header_len
loc_frame_count = 6-header_len
loc_cmdvalid = 10-header_len
loc_cmdinvalid = 11-header_len
loc_cmdid = 12-header_len
loc_cmdcsum = 13-header_len
loc_cmd_crc = 14-header_len
loc_mode = 16-header_len
loc_presetnum = 17-header_len
loc_frames_to_transmit = 18-header_len
##20 is free
loc_reboots = 21-header_len
loc_pps = 23-header_len
loc_dice_valid = 24-header_len
loc_stack_count = 32-header_len
loc_loop_count = 34-header_len
loc_time = 38-header_len 
loc_mag_xyzt = 42-header_len
loc_mag_status = 50-header_len

loc_cmd_pointer = 51-header_len
loc_cmd_wait = 52-header_len
loc_buffer_cnt = 53-header_len
loc_pps_debug = 54-header_len
loc_cmd_packet_type = 56-header_len
loc_good_cmd = 57-header_len
loc_eeprombyte = 58-header_len
loc_adc128_0 = 59

loc_max_dac = 75
loc_curr_limit = 77
loc_curr_flag = 78
loc_sun_sensor = 79
loc_survey_settings = 91
loc_cmd_echo = 1160-header_len
loc_tcnt2_start = 27-header_len
loc_scan_index = 192-header_len
loc_dac = 1000-header_len


loc_adc_0 = 59-header_len
loc_adc_1 = 46-header_len
loc_adc_2 = 62-header_len


loc_hns_adc = 25

#stolen from here https://gist.github.com/claymcleod/b670285f334acd56ad1c


def get_sync(in_packet,sync_bytes,frame_size):
    """
    Find the sync word locations in a data package.
    
    Function preallocates ouptput array size based on nominal frame size. 
    
    inputs:
        in_packet: The data package to search
        sync_bytes: Array of sync bytes. e.g. [0xEB, 0x90,0x20]
        frame_size: size in bytes of a full frame
        
    output:
        sync_loc: np_array of byte location of sync word start in in_package

    """
    
    #intialise sync array with 10% size margin. This looks horrible
    sync_loc = np.zeros(np.ceil(len(in_packet)/frame_size*1.1).astype(int)).astype(int)
    
    n_guess = len(sync_loc)

    #initalize counters
    k = 0 #place in packet
    i = 0 #number of syncs found

    #loop over the data looking for the sync bytes.
    while k < len(in_packet):

        temp = in_packet.find(bytes(sync_bytes),k)

        if temp >= 0:
            
            if (i < n_guess): sync_loc[i] = temp
            else: sync_loc = np.append(sync_loc,temp)
            
            i += 1
            k = temp + 1
            
        else:
            break
        
    sync_loc = sync_loc[:i] #trim off unused array

    return sync_loc

def get_header(data,sync):
    
    ver_num = np.zeros(len(sync)).astype(int)
    source = np.zeros(len(sync)).astype(int)
    destination = np.zeros(len(sync)).astype(int)
    message_id = np.zeros(len(sync)).astype(int)
    
    k = 0
    for i in (sync-header_len):
        ver_num[k] = data[i]
        source[k] = (data[i+1]<<8) + data[i+2]
        destination[k] = (data[i+3]<<8) + data[i+4]
        message_id[k] = (data[i+5]<<8) + data[i+6]
        k+=1
        
    return ver_num, source, destination, message_id

def get_valid_invalid(data,sync):
    
    
    num_valid = np.zeros(len(sync)).astype(int)
    num_invalid = np.zeros(len(sync)).astype(int)
    k = 0
    
    for i in sync:
        num_valid[k] = (data[i+loc_cmdvalid] & 0xFF) 
        num_invalid[k] = (data[i+loc_cmdvalid+1] & 0xFF)
        k+=1
        
    return num_valid, num_invalid
    
def get_dice_valid_invalid(data,sync):
    
    
    num_valid = np.zeros(len(sync)).astype(int)
    num_invalid = np.zeros(len(sync)).astype(int)
    k = 0
    
    for i in sync:
        num_valid[k] = (data[i+loc_dice_valid] & 0xFF) 
        num_invalid[k] = (data[i+loc_dice_valid+1] & 0xFF)
        k+=1
        
    return num_valid, num_invalid   
    
def get_cmd_crc(data,sync):
    
    thingy = np.zeros(len(sync)).astype(int)
    k = 0
    
    for i in sync+loc_cmd_crc:
        thingy[k] = (data[i]<<8) + data[i+1]
        k+=1
        
    return thingy


def get_frame_count(in_packet,sync):
    
    t32 = np.zeros(len(sync)).astype(int)
    
    k = 0;
    for i in sync+loc_frame_count:
        t32[k] = ((in_packet[i]<<24) + (in_packet[i+1]<<16) + (in_packet[i+2]<<8) + (in_packet[i+3]))
        k += 1
    
    return t32
    
def get_elapsed_time(in_packet,sync):
    
    t32 = np.zeros(len(sync)).astype(int)
    
    k = 0;
    for i in sync+loc_time:
        t32[k] = ((in_packet[i]<<24) + (in_packet[i+1]<<16) + (in_packet[i+2]<<8) + (in_packet[i+3]))
        k += 1
    
    return t32   
    
def get_loop_count(in_packet,sync):
    
    t32 = np.zeros(len(sync)).astype(int)
    
    k = 0;
    for i in sync+loc_loop_count:
        t32[k] = ((in_packet[i]<<24) + (in_packet[i+1]<<16) + (in_packet[i+2]<<8) + (in_packet[i+3]))
        k += 1
    
    return t32    
    
def get_coarse_time(in_packet,sync):
    
    t32 = np.zeros(len(sync)).astype(int)
    
    k = 0;
    for i in sync+loc_coarse_time:
        t32[k] = ((in_packet[i]<<24) + (in_packet[i+1]<<16) + (in_packet[i+2]<<8) + (in_packet[i+3]))
        k += 1
    
    return t32
 
      
def get_fine_time(data,sync):
    
    thingy = np.zeros(len(sync)).astype(int)
    k = 0
    
    for i in sync+loc_fine_time:
        thingy[k] = (data[i]<<8) + data[i+1]
        k+=1
        
    return thingy
    
def get_packet_id(data,sync):
    
    thingy = np.zeros(len(sync)).astype(int)
    k = 0
    for i in sync+loc_packet_id:
        thingy[k] = data[i]
        k+=1
        
    return thingy
    
def get_target_id(data,sync):
    
    thingy = np.zeros(len(sync)).astype(int)
    k = 0
    for i in sync+loc_target_id:
        thingy[k] = data[i]
        k+=1
        
    return thingy   
     
def get_cmdid(data,sync):
    
    cmdid = np.zeros(len(sync)).astype(int)
    k = 0
    for i in sync+loc_cmdid:
        cmdid[k] = data[i]
        k+=1
        
    return cmdid

def get_cmd_echo(data,sync):
    cmd_echo = np.zeros([len(sync),120]).astype(int)
    k = 0
    for i in sync+loc_cmd_echo:
        for j in range(120):
            cmd_echo[k,j] = data[(i+j)]
        k+=1
        
    return cmd_echo

    
def get_mag_status(data,sync):
    
    thingy = np.zeros(len(sync)).astype(int)
    
    k = 0
    
    for i in sync:
        thingy[k] = data[i+loc_mag_status]
        k+=1
        
    return thingy
    
def get_survey_settings(data,sync):
    
    loc_val = loc_survey_settings
    
    a1 = np.zeros(len(sync)).astype(int)
    a2 = np.zeros(len(sync)).astype(int)
    a3 = np.zeros(len(sync)).astype(int)
    a4 = np.zeros(len(sync)).astype(int)
    
    k = 0
    
    for i in sync:
        
        a1[k] = (data[i+loc_val+0]<<8) + data[i+loc_val+1]
        a2[k] = (data[i+loc_val+2]<<8) + data[i+loc_val+3]
        a3[k] = (data[i+loc_val+4]<<8) + data[i+loc_val+5]
        a4[k] = (data[i+loc_val+6]<<8) + data[i+loc_val+7]
        
        k+=1
        
    return a1,a2,a3,a4  
    
def get_mag_xyzt(data,sync):
    
    mag_x = np.zeros(len(sync)).astype(int)
    mag_y = np.zeros(len(sync)).astype(int)
    mag_z = np.zeros(len(sync)).astype(int)
    mag_t = np.zeros(len(sync)).astype(int)
    
    k=0
    
    for i in sync:
        mag_x[k] = (data[i+loc_mag_xyzt+0]<<8) + data[i+loc_mag_xyzt+1]
        mag_y[k] = (data[i+loc_mag_xyzt+2]<<8) + data[i+loc_mag_xyzt+3]
        mag_z[k] = (data[i+loc_mag_xyzt+4]<<8) + data[i+loc_mag_xyzt+5]
        mag_t[k] = (data[i+loc_mag_xyzt+6]<<8) + data[i+loc_mag_xyzt+7]
        k+=1
        
    return mag_x, mag_y, mag_z, mag_t

def get_sun_sensor(data,sync):
    
    loc_x = loc_sun_sensor
    
    a0 = np.zeros(len(sync)).astype(int)
    a1 = np.zeros(len(sync)).astype(int)
    a2 = np.zeros(len(sync)).astype(int)
    a3 = np.zeros(len(sync)).astype(int)
    a4 = np.zeros(len(sync)).astype(int)
    a5 = np.zeros(len(sync)).astype(int)
    
    k=0
    
    for i in sync:
        a0[k] = (data[i+loc_x+0]) + (data[i+loc_x+1]<<8)
        a1[k] = (data[i+loc_x+2]) + (data[i+loc_x+3]<<8)
        a2[k] = (data[i+loc_x+4]) + (data[i+loc_x+5]<<8)
        a3[k] = (data[i+loc_x+6]) + (data[i+loc_x+7]<<8)
        a4[k] = (data[i+loc_x+8]) + (data[i+loc_x+9]<<8)
        a5[k] = (data[i+loc_x+10]) + (data[i+loc_x+11]<<8)
        
        k+=1
        
    return a0,a1,a2,a3,a4,a5


def get_pps_debug(data,sync):
    
    thingy = np.zeros(len(sync)).astype(int)
    k = 0
    
    for i in sync+loc_pps_debug:
        thingy[k] = (data[i]<<8) + data[i+1]
        k+=1
        
    return thingy
    
def get_buffer_cnt(data,sync):
    
    thingy = np.zeros(len(sync)).astype(int)
    k = 0
    
    for i in sync+loc_buffer_cnt:
        thingy[k] = data[i]
        k+=1
        
    return thingy
 


def get_reboots(data,sync):
    
    thingy = np.zeros(len(sync)).astype(int)
    k = 0
    
    for i in sync+loc_reboots:
        thingy[k] = (data[i]<<8) + data[i+1]
        k+=1
        
    return thingy


def get_pps_status(data,sync):
    
    pps_status = np.zeros(len(sync)).astype(int)
    pps_use = np.zeros(len(sync)).astype(int)
    pps_present = np.zeros(len(sync)).astype(int)
    
    k = 0
    
    for i in sync+loc_pps:
        pps_status[k] = (data[i] & 0b10000000)>>7
        pps_use[k] = (data[i] & 0b01000000)>>6
        pps_present[k] = (data[i] & 0b00100000)>>5
        k +=1
        
    return pps_status, pps_use, pps_present


def get_adc(data,sync,adc_n):
    
    if adc_n == 0:
            ind = loc_adc_0
    elif adc_n == 1:
            ind = loc_adc_1
    elif adc_n == 2:
            ind = loc_adc_2
            
            
    
    adc_val = get_samples(data,sync,frame_len,ind,2,16,8,'l')
    
    return adc_val

# def get_rtc(data,sync):
#     
# #     year = np.zeros(len(sync)).astype(int)
# #     month = np.zeros(len(sync)).astype(int)
# #     day = np.zeros(len(sync)).astype(int)
# #     hour = np.zeros(len(sync)).astype(int)
# #     minute = np.zeros(len(sync)).astype(int)
# #     sec = np.zeros(len(sync)).astype(int)
#     rtc = np.zeros((len(sync),7)).astype(int)
#     
#     k=0
#     
#     for i in sync+loc_rtc:
#         
# #         year[k] = 10*((data[i+7]&0xF0)>>4) + (data[i+7]&0x0F) + 2000
# #         month[k] = 10*((data[i+6]&0x10)>>4) + (data[i+6]&0x0F)
# #         day[k] = 10*((data[i+5]&0xF0)>>4) + (data[i+5]&0x0F)
# #         hour[k] = 10*((data[i+3]&0x30)>>4) + (data[i+3]&0x0F)
# #         minute[k] = 10*((data[i+2]&0xF0)>>4) + (data[i+2]&0x0F)
# #         sec[k] = 10*((data[i+1]&0xF0)>>4) + (data[i+1]&0x0F) + \
# #                  ((data[i+0]&0xF0)>>4)/10 + (data[i+0]&0x0F)/100
#         rtc[k,0] = 10*((data[i+7]&0xF0)>>4) + (data[i+7]&0x0F) + 2000
#         rtc[k,1]= 10*((data[i+6]&0x10)>>4) + (data[i+6]&0x0F)
#         rtc[k,2]= 10*((data[i+5]&0xF0)>>4) + (data[i+5]&0x0F)
#         rtc[k,3]= 10*((data[i+3]&0x30)>>4) + (data[i+3]&0x0F)
#         rtc[k,4]= 10*((data[i+2]&0xF0)>>4) + (data[i+2]&0x0F)
#         rtc[k,5]= 10*((data[i+1]&0xF0)>>4) + (data[i+1]&0x0F)
#         rtc[k,6] = ((data[i+0]&0xF0)>>4)*10 + (data[i+0]&0x0F)
# 
# #         for j in range(8):
# #             rtc[k,j] = data[i+j]
#         
#         k+=1
#         
#     return rtc


##************************************************************
def get_adc128(data,sync):
    
    loc_x = loc_adc128_0
    
    a0 = np.zeros((len(sync),8)).astype(int)
    
    
    k=0
    
    for i in sync:
        for j in range(8):
            a0[k,j] = (data[i+loc_x+0+(j*2)]<<8) + (data[i+loc_x+1+(j*2)])
        k+=1
        
    return a0[:,0],a0[:,1],a0[:,2],a0[:,3],a0[:,4],a0[:,5],a0[:,6],a0[:,7]


##************************************************************
def get_dac(in_packet,sync):
    """
    Extract the 12bit dac values from TM frame
    
    in_packet: data package. May be multiple packets
    sync:  array of byte locations of frame starts
    
    """

    num_packets = len(sync)
    
    dac = np.zeros((num_packets,50)).astype('int')
    
    for j in range(num_packets):
        
        #isolate a single data frame from the packet
        frame = in_packet[(sync[j]):(sync[j]+1288)]
        
        for i in range(50):
            
            index = loc_dac + np.floor(i*1.5).astype('int')
            
            if (i%2):
                
                temp = ((frame[index] & 0x0F)<<8) + (frame[index+1])
            else:
                
                temp = (frame[index] << 4) + (frame[index+1] >> 4)
                
            dac[j][i] = temp
            
    return dac
                
##************************************************************
def get_hns_adc(in_packet,sync):
    """
    Extract the 12bit dac values from HNS frame
    
    in_packet: data package. May be multiple packets
    sync:  array of byte locations of frame starts
    
    """

    num_packets = len(sync)
    
    adc = np.zeros((num_packets,8)).astype('int')
    
    for j in range(num_packets):
        
        #isolate a single data frame from the packet
        frame = in_packet[(sync[j]):(sync[j]+56)]
        
        for i in range(8):
            
            index = loc_hns_adc + np.floor(i*1.5).astype('int')
            
            if (i%2):
                
                temp = ((frame[index] & 0x0F)<<8) + (frame[index+1])
            else:
                
                temp = (frame[index] << 4) + (frame[index+1] >> 4)
                
            adc[j][i] = temp
            
    return adc
    
##************************************************************
def get_samples(in_packet,sync_loc,pkt_len,samp_start,samp_bytes,samp_bits,nsamples,lr_adj):
    """
    Extract data from a data package
    
    in_packet: data package. May be multiple packets
    sync_loc:  array of byte locations of frame starts
    packet_len: length of a packet in bytes
    samp_start: byte location of start of dac data
    samp_bytes: number of bytes of each sample
    samp_bits: number of bits in each sample
    nsamples: number of samples in each frame
    lr_adj: 'L' or 'R', is data left or right adjusted in the bytes?
    
    """
    
    if (type(lr_adj) != 'str'):
        if(lr_adj == 0): lr_adj = 'r'
        elif(lr_adj == 1): lr_adj = 'l'
        

    num_packets = len(sync_loc)
    
    samp_data = np.zeros((num_packets,nsamples)).astype('int')
    
    for j in range(num_packets):
        
        #isolate a single data frame from the packet
        #going from sync to length of packet in case there is a header added
        frame = in_packet[(sync_loc[j]):(sync_loc[j]+pkt_len)]
        
        k = 0;
        for i in range(samp_start,samp_start+nsamples*samp_bytes,samp_bytes):
            
            for i2 in range(samp_bytes):
                
                if ((lr_adj.lower() == 'l')):
                    shiftval = 8 + (8*(samp_bytes-i2) - samp_bits);
                elif (lr_adj.lower() == 'r'):
                    shiftval = 8*(samp_bytes-i2) - 8
                    
                       
                if (shiftval > 0) & ((i+i2)<= len(frame)):
                    samp_data[j,k] = samp_data[j,k] + int((frame[i+i2])<<(shiftval));
                else:
                    samp_data[j,k] = samp_data[j,k] + int((frame[i+i2])>>abs(shiftval));
            
            k = k + 1;
            
                
    
    return samp_data

  

def check_frame_size(data,sync,frame_len,header_len):
    """
    Script to check the length of a frame
    """
    
    frame_check = np.zeros(len(sync)).astype(bool)
    
    k = 0
    for i in range(len(sync)):
        if (i < (len(sync)-1)):
            frame_check[i] = (sync[i+1]-sync[i]) >= frame_len
        else:
            frame_check[i] = (len(data) - sync[i] + header_len) >= frame_len
            
    return frame_check
    
