# -*- coding: utf-8 -*-
"""
Created on Sun Oct  8 13:10:04 2017

@author: jtc9242
"""
print("Importing modules")

import urllib.request
import urllib.error
import socket
import subprocess
import re
import blinkt
import time
import select

# Global variables
TIMEOUT = 10
WAIT = 10

RGB = {'nrm': [50,50,50], 'wrn': [255,128,0], 'err': [255,0,0], 'off':[0,0,0], 'blk':[0,0,255]}

# Check if HTTP connection to host on port is available
def http_online(host, port=80):
    url = "{}:{}".format(host, port)
    try:
        urllib.request.urlopen(url, timeout=TIMEOUT)
        return True
    except urllib.error.URLError as e:
        print("{} offline".format(url))
        print(e.reason)
        return False


# Check status of pihole
def pihole_status():
    status = {}
    
    o = subprocess.check_output('pihole status', shell=True).decode()
    o = o.splitlines()
    o = [re.sub('[: -]', '', s) for s in o]
    
    if 'DNSserviceisrunning' in o:
        status["service"] = True
    else:
        status["service"] = False
        print("DNS service offline")
    if 'PiholeblockingisEnabled' in o:
        status['blocking'] = True
    else:
        print("BLocking disabled")
        status['blocking'] = False
    
    return status


# Get all pihole stats
def get_all():
    status = {}
    
    pihole = pihole_status()

    status['onl'] = http_online("http://www.google.co.uk")
    status['dns'] = pihole['service']
    status['blk'] = pihole['blocking']
    
    return status


# Draw to blinkt
def setall(r, g, b, brightness=None):
    blinkt.set_all(r, g, b, brightness=brightness)
    blinkt.show()
    
def pulse(rgb_f, rgb_i, t):
    t0 = time.time() # Time started
    delta = 0. # Initial delta t
    
    diff = [rgb_f[i]-rgb_i[i] for i in range(3)] # Change in RGB over full pulse
    
    while delta < t:
        delta = delta/t # Normalise delta time
        
        curr = [rgb_i[i] + delta*diff[i] for i in range(3)] # Calculate current rgb
        setall(*curr)
        
        t1 = time.time() # Record new time
        delta = t1 -t0 # Calculate new delta from new time
        
    setall(*rgb_f)


# Main loop
    
if __name__ == "__main__":

    print("Loading PiHole log")
    lists = ['/etc/pihole/gravity.list']
    
    f = subprocess.Popen(['tail','-F','/var/log/pihole.log'],\
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    p = select.poll()
    p.register(f.stdout)

    print("Running system status checker")
    
    i = 0
    while True:
    
        # If one wait period has passed, update base color
        if i == 0:
            #print("Updating status")
            # Update status
            status = get_all()

            # Update base color:
            if not status['blk']:
                rgb = RGB['wrn']
            elif not status['dns']:
                rgb = RGB['wrn']
            elif not status['onl']:
                rgb = RGB['err']
            else:
                rgb = RGB['nrm']
                
            setall(*rgb)
        
        # Add to counter
        i+=1
        if i >= WAIT:
            i=0
        
        
        # Check if ads have been blocked from log
        if p.poll(1): # If new data in log
            line = f.stdout.readline().decode().rstrip() # Read new log data, decode, and strip of newlines
        
            for list in lists: # For all given ad lists
                if list in line: # If the list name appears in the log line
                    pulse(rgb, RGB['blk'], 1) # Pulse over 1 second
                    print("BLOCKED:")
                    print(line) # Ad has been blocked
        
        else:
            setall(*rgb)
            time.sleep(1)
    
    