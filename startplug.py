#!/usr/bin/env python
# coding: utf-8

import datetime
import calendar
import json
import threading
import config_tb
import requests

import locale

import requests

def telegram_bot_sendtext(bot_message,bot_token,bot_chatID):
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()
    

write_thingsboard = True
cte_charge_threshold = 300
last_plug1 = -1
last_plug2 = -1
last_plug3 = -1  


def turn_1_on():
    global plug1
    global plug2
    global plug3    
    plug3.turn_off()    
    plug2.turn_off()
    time.sleep(5)
    plug1.turn_on()
    print("Charging car 1")
    
def turn_off():
    global plug1
    global plug2
    global plug3  
    plug1.turn_off()
    plug2.turn_off()
    time.sleep(5)
    plug3.turn_on()  
    print("Charging no car")
    
def turn_2_on():
    global plug1
    global plug2
    global plug3  
    global leaf2
    plug3.turn_off()
    plug1.turn_off()
    time.sleep(5)
    plug2.turn_on()
    print("Trying to charge car 2")
    time.sleep(15)
    emeterinfo = infoEnchufe(plug2,"Checking Second car plug is charging?")
    print("emeter current ma",emeterinfo['current_ma'],cte_charge_threshold)
    if (emeterinfo['current_ma']< cte_charge_threshold):
        print("--------> Car 2 is not present <------- proceed to next car?")
        ret = False
        
    else:
        ret = True
        
    return ret    
    
    
    

def infoEnchufe(plx,name):
    print(name,":")
    print('Name:      %s' % plx.name)
    print('Model:     %s' % plx.model)
    print('Mac:       %s' % plx.mac)
    print('Time:      %s' % plx.time)

    print('Is on:     %s' % plx.is_on)
    print('Nightmode: %s' % (not plx.led))
    print('RSSI:      %s' % plx.rssi)
    emeterinfo = plx.command(('emeter', 'get_realtime'))
    print(emeterinfo)
    print('emeter ma',emeterinfo['current_ma'])
    print('emeter pw',emeterinfo['power_mw'])
    return emeterinfo
    
# In[ ]:

#!/usr/bin/env python

import time
from configparser import ConfigParser
import logging
import sys
from tplink_smartplug import SmartPlug

def startplug(plugnumber):
    global plug1
    global plug2
    global plug3
    global last_plug1
    global last_plug2
    global last_plug3    
    global leaf1
    global leaf2
    
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')     
    #help(SmartPlug)
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.getLogger("pycarwings2").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)

    parser = ConfigParser()
    candidates = ['config.ini', 'my_config.ini']
    found = parser.read(candidates)
      
    bot_token = parser.get('get-leaf-info', 'bot_token')
    print("bot_token",bot_token)
    bot_chatID = parser.get('get-leaf-info', 'bot_chatID')
    print("bot_chatID",bot_chatID)       
    test = telegram_bot_sendtext("Starting ....",bot_token,bot_chatID)   
  
    while(1):
        print("\n\n\n\n\n\nAnother loop\n\n\n\n")
        found = parser.read(candidates)     
        plug1address = parser.get('get-leaf-info', 'plug1address')
        plug2address = parser.get('get-leaf-info', 'plug2address')
        plug3address = parser.get('get-leaf-info', 'plug3address')

        current_date_and_time = datetime.datetime.now()
        current_hour = current_date_and_time.hour

        plug1 = SmartPlug(plug1address)
        emeterinfo1 = infoEnchufe(plug1,"First car plug")

        plug2 = SmartPlug(plug2address)
        emeterinfo2 = infoEnchufe(plug2,"Second car plug")

        plug3 = SmartPlug(plug3address)
        emeterinfo3 = infoEnchufe(plug3,"Water warmer plug")

        if (write_thingsboard):
            print(config_tb.telemetry_address)
            print(config_tb.telemetry_address2)
            unixtime = int(time.mktime(plug1.time.timetuple())*1000)
            unixtime2 = int(time.mktime(plug2.time.timetuple())*1000)   

            category = "plug1"
            
            pload = {'ts':unixtime, "values":{         
                category+'_is_on':plug1.is_on,
                category+'_rssi':plug1.rssi,
                category+'_current_ma':emeterinfo1['current_ma'],
                category+'_power_mw':emeterinfo1['power_mw'],
                }}
            print(pload)
            print("========")
            r = requests.post(config_tb.telemetry_address,json = pload)
            print(r.status_code)

            category = "plug2"
            pload = {'ts':unixtime, "values":{         
                category+'_is_on':plug2.is_on,
                category+'_rssi':plug2.rssi,
                category+'_current_ma':emeterinfo2['current_ma'],
                category+'_power_mw':emeterinfo2['power_mw'],
                }}
            print(pload)
            print("========")
            r = requests.post(config_tb.telemetry_address2,json = pload)
            print(r.status_code)

            category = "plug3"
            pload = {'ts':unixtime, "values":{         
                category+'_is_on':plug3.is_on,
                category+'_rssi':plug3.rssi,
                category+'_current_ma':emeterinfo3['current_ma'],
                category+'_power_mw':emeterinfo3['power_mw'],
                }}
            print(pload)
            print("========")
            r = requests.post(config_tb.telemetry_address3,json = pload)
            print(r.status_code)


        
        if plugnumber == 1:
            turn_1_on()
        else:
            if plugnumber == 2:
                car2present = turn_2_on()
            else:
                turn_off()        


        print('Plug 1 Is on:     %s' % plug1.is_on)
        print('Plug 2 Is on:     %s' % plug2.is_on)
        print('Plug 3 Is on:     %s' % plug3.is_on)

        if (last_plug1 != plug1.is_on):
            test = telegram_bot_sendtext('Leaf 1 %s' % plug1.is_on,bot_token,bot_chatID)
            
        if (last_plug2 != plug2.is_on):        
            test = telegram_bot_sendtext('Leaf 2 %s' % plug2.is_on,bot_token,bot_chatID)
            
        if (last_plug3 != plug3.is_on):        
            test = telegram_bot_sendtext('Other3 %s' % plug3.is_on,bot_token,bot_chatID)
        
        last_plug1 = plug1.is_on
        last_plug2 = plug2.is_on
        last_plug3 = plug3.is_on


startplug(1)
