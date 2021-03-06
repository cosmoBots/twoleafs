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

def get_server_leaf1_info():
    global leaf1_info, leaf1
    leaf1_info = leaf1.get_latest_battery_status()

def get_server_leaf2_info():
    global leaf2_info, leaf2
    leaf2_info = leaf2.get_latest_battery_status()

def wait_update_battery_status(leaf,key,wait_time=1,retries=3,wait_time_retries=1):
    status = leaf.get_status_from_update(key)
    # Currently the nissan servers eventually return status 200 from get_status_from_update(), previously
    # they did not, and it was necessary to check the date returned within get_latest_battery_status().
    if status is None:
        print("Retrying in {0} seconds".format(wait_time))
        time.sleep(wait_time)
        status = leaf.get_status_from_update(key)
        
    if status is None:
        r = retries - 1
    
    while (status is None) and (r > 0):
        print("Retrying in {0} seconds".format(wait_time_retries))
        time.sleep(wait_time_retries)
        status = leaf.get_status_from_update(key)
        r = r - 1
    return status


def print_info(info):
    print("  date %s" % info.answer["BatteryStatusRecords"]["OperationDateAndTime"])
    #print("  date %s" % info.answer["BatteryStatusRecords"]["NotificationDateAndTime"])
    #print("  battery_capacity2 %s" % info.answer["BatteryStatusRecords"]["BatteryStatus"]["BatteryCapacity"])
    print("  battery_capacity %s" % info.battery_capacity)
    print("  charging_status %s" % info.charging_status)
    #print("  battery_capacity %s" % info.battery_capacity)
    #print("  battery_remaining_amount %s" % info.battery_remaining_amount)
    #print("  charging_status %s" % info.charging_status)
    #print("  is_charging %s" % info.is_charging)
    #print("  is_quick_charging %s" % info.is_quick_charging)
    print("  plugin_state %s" % info.plugin_state)
    print("  is_connected %s" % info.is_connected)
    print("  is_connected_to_quick_charger %s" % info.is_connected_to_quick_charger)
    #print("  time_to_full_trickle %s" % info.time_to_full_trickle)
    print("  time_to_full_l2 %s" % info.time_to_full_l2)
    #print("  time_to_full_l2_6kw %s" % info.time_to_full_l2_6kw)
    print("  battery_percent %s" % info.battery_percent)
    #print("  state_of_charge %s" % info.state_of_charge)

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

import pycarwings2
import time
from configparser import ConfigParser
import logging
import sys
from tplink_smartplug import SmartPlug

def working_session():
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
        username = parser.get('get-leaf-info', 'username')
        password = parser.get('get-leaf-info', 'password')
        username2 = parser.get('get-leaf-info', 'username2')
        password2 = parser.get('get-leaf-info', 'password2')
        region = parser.get('get-leaf-info', 'region')
        plug1address = parser.get('get-leaf-info', 'plug1address')
        plug2address = parser.get('get-leaf-info', 'plug2address')
        plug3address = parser.get('get-leaf-info', 'plug3address')
        useweekday = ("True" == parser.get('get-leaf-info', 'cfg_use_weekday'))
        start_minimum_price = int(parser.get('get-leaf-info', 'start_minimum_price'))
        end_minimum_price = int(parser.get('get-leaf-info', 'end_minimum_price'))
        start_maximum_price = int(parser.get('get-leaf-info', 'start_maximum_price'))
        end_maximum_price = int(parser.get('get-leaf-info', 'end_maximum_price'))

        current_date_and_time = datetime.datetime.now()
        current_hour = current_date_and_time.hour

        if (current_hour >= start_minimum_price) and (current_hour < end_minimum_price):
            print("Time slot: Minimum price")
            charge_min = True
            charge_tgt = True
            charge_max = True
            charge_min_prio = True
            charge_tgt_prio = True
            charge_max_prio = True
        else:
            if (current_hour >= start_maximum_price) and (current_hour < end_maximum_price):
                print("Time slot: Maximum price")
                charge_min = False
                charge_tgt = False
                charge_max = False
                charge_min_prio = False
                charge_tgt_prio = False
                charge_max_prio = False
            else:
                print("Time slot: Normal price")
                charge_min = True
                charge_tgt = False
                charge_max = False
                charge_min_prio = True
                charge_tgt_prio = True
                charge_max_prio = False

        print("Using weekday?",useweekday)
        if not(useweekday):
            todaypriority = int(parser.get('Normal', 'todaypriority'))
            leaf1min = int(parser.get('Normal', 'leaf1min'))
            leaf2min = int(parser.get('Normal', 'leaf2min'))
            leaf1tgt = int(parser.get('Normal', 'leaf1tgt'))
            leaf2tgt = int(parser.get('Normal', 'leaf2tgt'))
            leaf1max = int(parser.get('Normal', 'leaf1max'))
            leaf2max = int(parser.get('Normal', 'leaf2max'))
        else:
            advancehours = int(parser.get('get-leaf-info', 'advancehours'))
            hours_added = datetime.timedelta(hours = advancehours)
            future_date_and_time = current_date_and_time + hours_added
            weekday=calendar.day_name[future_date_and_time.weekday()]
            print("Weekday:",weekday)
            todaypriority = int(parser.get(weekday, 'todaypriority'))
            leaf1min = int(parser.get(weekday, 'leaf1min'))
            leaf2min = int(parser.get(weekday, 'leaf2min'))
            leaf1tgt = int(parser.get(weekday, 'leaf1tgt'))
            leaf2tgt = int(parser.get(weekday, 'leaf2tgt'))
            leaf1max = int(parser.get(weekday, 'leaf1max'))
            leaf2max = int(parser.get(weekday, 'leaf2max'))

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


        sleepsecs = 10     # Time to wait before polling Nissan servers for update
        sleepsecs2 = 10     # Time to wait before polling Nissan servers for update
        
        # Main program

        #logging.debug("login = %s, password = %s, region = %s" % (username, password, region))
        #logging.debug("login2 = %s, password2 = %s, region = %s" % (username2, password2, region))

        print("Prepare Session 1")
        s = pycarwings2.Session(username, password, region)
        print("Login...1")
        leaf1 = s.get_leaf()

        print("Prepare Session 2")
        s2 = pycarwings2.Session(username2, password2, region)
        print("Login...2")
        leaf2 = s2.get_leaf()

        # Give the nissan servers a bit of a delay so that we don't get stale data'
        time.sleep(1)

        print("********** First Car Last Status ************")
        print("get_latest_battery_status from servers")  
        try:
            leaf1_info = leaf1.get_latest_battery_status()
            #start_date = leaf1_info.answer["BatteryStatusRecords"]["OperationDateAndTime"]
            #print("start_date=", start_date)
            print_info(leaf1_info)
            bat1 = leaf1_info.battery_percent
            
        except:
            print("No hubo suerte con el leaf1")
            bat1 = 0

        print("request an update from the car itself")
        key = leaf1.request_update()

        print("********** Second Car Last Status ************")
        print("get_latest_battery_status from servers")
        try:
            leaf2_info = leaf2.get_latest_battery_status()
            #start_date = leaf2_info.answer["BatteryStatusRecords"]["OperationDateAndTime"]
            #print("start_date=", start_date)
            print_info(leaf2_info)
            bat2 = leaf2_info.battery_percent        
        except:
            print("No hubo suerte con el leaf2")
            bat2 = 0
            
        print("request an update from the car itself")
        key2 = leaf2.request_update()

        # Give the nissan servers a bit of a delay so that we don't get stale data
        time.sleep(1)
        print("***** Waiting for status update *****")
        print("... First car")
        update_status = wait_update_battery_status(leaf1,key,sleepsecs,5,5)
        print("... Second car")
        update_status2 = wait_update_battery_status(leaf2,key2,sleepsecs2,5,5)

        print("********** First Car Current Status************")
        if (update_status is not None):
            print("OK: >>>>",update_status.answer['status'])
            try:
                latest_leaf_info = leaf1.get_latest_battery_status()
                #latest_date = latest_leaf_info.answer["BatteryStatusRecords"]["OperationDateAndTime"]
                #print("latest_date=", latest_date)
                print_info(latest_leaf_info)
                print("llegue aqui!")
                bat1 = latest_leaf_info.battery_percent
                conn1 = latest_leaf_info.is_connected    
                print("llegue aqui B!")
                print(latest_leaf_info.answer["BatteryStatusRecords"]["OperationDateAndTime"])
                print("llegue aqui B2!")
                locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
                print(latest_leaf_info.answer["BatteryStatusRecords"]["OperationDateAndTime"])
                date_time_obj = datetime.datetime.strptime(latest_leaf_info.answer["BatteryStatusRecords"]["OperationDateAndTime"], '%d-%b-%Y %H:%M')
                print("llegue aqui C!")
                unixtime = int((time.mktime(date_time_obj.timetuple())-3600)*1000)
                print("llegue aqui D!")
                remainingtime = latest_leaf_info.time_to_full_l2.total_seconds()
                print("pero si fue bien!")

            except:
                print("No hay informacion actualizada para leaf1")
                conn1 = True
                
            try:
                print("Vamos con la subida de datos")
                category = "car1"
                pload = {'ts':unixtime, "values":{         
                    category+'_bat':bat1,
                    category+'_conn':conn1,
                    category+'_time2full':remainingtime
                    }}
                print(pload)
                print("========")
                r = requests.post(config_tb.telemetry_address,json = pload)
                print(r.status_code)
            
            except:
                print("No se pudo subir la información de leaf1 al panel")

                
        else:
            print("ERROR: >>>> status could not be retrieved")
            conn1 = True

        print("********** Second Car Current Status************")
        if (update_status2 is not None):
            print("OK: >>>>",update_status2.answer['status'])
            try:
                latest_leaf_info2 = leaf2.get_latest_battery_status()
                #latest_date2 = latest_leaf_info2.answer["BatteryStatusRecords"]["OperationDateAndTime"]
                #print("latest_date2=", latest_date2)
                print_info(latest_leaf_info2)
                print("llegue aqui 2")
                bat2 = latest_leaf_info2.battery_percent
                conn2 = latest_leaf_info2.is_connected
                date_time_obj = datetime.datetime.strptime(latest_leaf_info2.answer["BatteryStatusRecords"]["OperationDateAndTime"], '%d-%b-%Y %H:%M')
                unixtime = int((time.mktime(date_time_obj.timetuple())-3600)*1000)
                remainingtime = latest_leaf_info2.time_to_full_l2.total_seconds()
                print("incluso acabe")
       
            except:
                print("No hay informacion actualizada para leaf2")
                conn2 = True
                
            try:
                print("intentamos subir al panel del coche 2")
                category = "car2"
                pload = {'ts':unixtime, "values":{         
                    category+'_bat':bat2,
                    category+'_conn':conn2,
                    category+'_time2full':remainingtime
                    }}
                print(pload)
                print("========")
                r = requests.post(config_tb.telemetry_address2,json = pload)
                print(r.status_code)
                print("acabe con el panel2")

            except:
                print("No se pudo subir la información de leaf2 al panel")
                
        else:
            print("ERROR: >>>> status could not be retrieved")
            conn2 = True
        
        
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        if (todaypriority == 1):
            charge_leaf1_min = charge_min_prio
            charge_leaf2_min = charge_min
            charge_leaf1_tgt = charge_tgt_prio
            charge_leaf2_tgt = charge_tgt
            charge_leaf1_max = charge_max_prio
            charge_leaf2_max = charge_max
        else:
            charge_leaf2_min = charge_min_prio
            charge_leaf1_min = charge_min
            charge_leaf2_tgt = charge_tgt_prio
            charge_leaf1_tgt = charge_tgt
            charge_leaf2_max = charge_max_prio
            charge_leaf1_max = charge_max 

        charge_leaf1 = 0
        charge_leaf2 = 0

        print("charge_leaf1_min",charge_leaf1_min)
        print("charge_leaf2_min",charge_leaf2_min)
        
        if (bat1 < leaf1min):
            print("leaf1 < min")
            if charge_leaf1_min:
                charge_leaf1 = 10
        else:
            if (bat1 < leaf1tgt):
                print("leaf1 < tgt")
                if charge_leaf1_tgt:
                    charge_leaf1 = 5
            else:
                if (bat1 < leaf1max):
                    print("leaf1 < max")
                    if charge_leaf1_max:
                        charge_leaf1 = 1
                else:
                    print("leaf1 >= max")                   

        if (bat2 < leaf2min):
            print("leaf2 < min")
            if charge_leaf2_min:
                charge_leaf2 = 10
        else:
            if (bat2 < leaf2tgt):
                print("leaf2 < tgt")
                if charge_leaf2_tgt:
                    charge_leaf2 = 5
            else:
                if (bat2 < leaf2max):
                    print("leaf2 < max")
                    if charge_leaf2_max:
                        charge_leaf2 = 1
                else:
                    print("leaf2 >= max")

        if todaypriority == 1:
            if (charge_leaf1 > 0):
                charge_leaf1 += 1

        else:
            if (charge_leaf2 > 0):
                charge_leaf2 += 1
            
        print("charge points 1",charge_leaf1)
        print("charge points 2",charge_leaf2)
        
        if not(conn1):
            charge_leaf1 = 0
        
        print("charge points 1",charge_leaf1)
        print("charge points 2",charge_leaf2)
        
        if charge_leaf1 > charge_leaf2:
            turn_1_on()
        else:
            if charge_leaf1 < charge_leaf2:
                car2present = turn_2_on()
                if not car2present:
                    print ("Let's proceed to the next in the queue")
                    if (charge_leaf1 > 0):
                        turn_1_on()
                        
                    else:
                        turn_off()
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
        print('Sleeping for 5 minutes')
        time.sleep(300)




workingSessionThread = threading.Thread(target=working_session, name="leafsSession")
print("*** Lanzo leafsSession")
workingSessionThread.start()
veces = 1
while(1):
    time.sleep(10)
    threadvivo = workingSessionThread.is_alive()
    if not threadvivo:
        workingSessionThread = threading.Thread(target=working_session, name="leafsSession")
        print("*** Relanzo leafsSession",veces)
        workingSessionThread.start()


    
            
