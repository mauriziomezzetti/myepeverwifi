################################################################
#                                                              #
# thanks to https://github.com/10der/hass-epever-solar-client  #
#                                                              #
################################################################


'''

#python3
#paho-mqtt==1.6.1
#PyYAML==6.0.1
#requests==2.31.0
#pymodbus==3.6.8          !!!!!!!!!!!!!!!!!!!!!!!


connettersi a hotspot creato da epever wifi 2.4g rj45d
andare a 10.10.100.254
user admin
pass admin

work mode AP+STA

STA Setting : IP FISSO (192.168.2.99)

Other setting: 
     protocol   TCP server
     port ID    9999
     TCP time   0
     
  
       


'''
import sys
import datetime
import os
import json
import logging
import ctypes
import threading
import signal
import time
from datetime import timedelta
#### pymodbus == 3.6.8
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import ModbusRtuFramer as ModbusFramer
from pymodbus.mei_message import ReadDeviceInformationRequest
#### pymodbus == 3.6.8
from paho.mqtt import client as mqtt_client
import random

#################### change this
version="myepeverwifi v1.0"
broker = "192.168.2.11"
usethisname = "user"
usethispassword = "pass"
port = 1883
#myserv="192.168.2.99"
myport="9999"


if (len(sys.argv)>1):
   arg1= str(sys.argv[1])
   arg1=arg1.strip()
else:
   arg1=""

if (arg1 == ""):
   print(version)
   print("USE python3 myepeverwifi.py 192.168.2.99")
   print("if epever static IP is 192.168.2.99")
   print("exit")
   sys.exit(1)

myserv=arg1




esiste=os.system("ping -c 1 "+ myserv)

if esiste==0:
    print(myserv+" UP")
else:
   print(version)
   print("USE python3 myepeverwifi.py 192.168.2.99")
   print("if epever static IP is 192.168.2.99")
   print(" ")
   print("your choice "+myserv+" is invalid")
   print("exit")
   sys.exit(1)



serv_names=arg1.split(".")
topic="EP_{:03d}".format(int(str(serv_names[0])))
topic+="{:03d}".format(int(str(serv_names[1])))
topic+="{:03d}".format(int(str(serv_names[2])))
topic+="{:03d}".format(int(str(serv_names[3])))
topic+="/status"

print(topic)


#sleeptime serve per mqtt
sleeptime = 1
client_id = f'python-mqtt-{random.randint(0, 1000)}'
clientm = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, client_id)

#client.username_pw_set(username=usethisname, password=usethispassword)

def on_connect(clientm, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker with result: {rc}")
        clientm.publish(topic, msg)
        print (topic)
        print (msg)
        clientm.disconnect()
        print()
        print("========================================")
        print(f"Gracefully disconnected from MQTT Broker")
        time.sleep(sleeptime)
    else:
        print("Failed to connect to Broker, return code = ", rc)


def on_disconnect(clientm, userdata, rc):
    if rc != 0:
        print("Unexpected MQTT Broker disconnection!")
        time.sleep(1)



def value32(low, high):
    """value32"""
    return ctypes.c_int(low + (high << 16)).value / 100


def value16(value):
    """value16"""
    return ctypes.c_short(value).value / 100


def value8(value):
    """value8"""
    return [value >> 8, value & 0xFF]


def to_bool(value):
    """to_bool"""
    values = {
        0: False,
        1: True
    }
    return values.get(value, None)


def days(value):
    """days"""
    return f"Days {value}"


def minutes(value):
    """minutes"""
    return f"Minutes {value}"


def seconds(value):
    """seconds"""
    return f"Seconds {value}"


def hour_minute(value):
    """hour_minute"""
    hm = value8(value)
    return f"{hm[0]} hours {hm[1]} minutes"
    
    

def get_time(second, minute, hour):
    """get_time"""
    return datetime.time(hour, minute, second)


def to_float(low, high=None):
    """to_float"""
    if high is None:
        return value16(low)
    else:
        return value32(low, high)


client = ModbusTcpClient(myserv, port=myport, framer=ModbusFramer, retries=5)
success = client.connect()
print("\nconnesso: "+str(success)+"\n")

#send wake up
print("\nsend wake up command\n")
client.send(bytes.fromhex("20020000"))


print("Updating Device RTC...")
result = client.read_holding_registers(0x9013, 3, slave=1)
if not result.isError():
 stamp= ("Date(%s, %s, %s, %s, %s, %s)",
       2000 + (result.registers[2] >> 8),
       result.registers[2] & 0xFF,
       result.registers[1] >> 8,
       result.registers[1] & 0xFF,
       result.registers[0] >> 8,
       result.registers[0] & 0xFF)
print ("\nvecchia data "+str(stamp)+"\n")
now = datetime.datetime.now()
new_data = [0, 0, 0]
new_data[2] = ((now.year - 2000) << 8) + now.month
new_data[1] = (now.day << 8) + now.hour
new_data[0] = (now.minute << 8) + now.second
stamp=("Date(%s, %s, %s, %s, %s, %s)",
      2000 + (new_data[2] >> 8),
      new_data[2] & 0xFF,
      new_data[1] >> 8,
      new_data[1] & 0xFF,
      new_data[0] >> 8,
      new_data[0] & 0xFF)
print ("\nnuova data "+str(stamp)+"\n")
result = client.write_registers(0x9013, new_data, slave=1)
if not result.isError():
   print("Err:", "Updating Device RTC")
else:
   print("Device RTC Updated.")


#dati mppt
request = ReadDeviceInformationRequest(slave=1)
response = client.execute(request)
if not response.isError():
   result = []
   for idx in response.information:
        result.append(response.information[idx].decode("ascii"))
   print("\n"+str(result)+"\n")
else:
  logger.error(response)
  print("\nerr get dati mppt\n")


timestamp=int(time.time())
s_1='": "'
s_2='", '
mystr='{"timestamp": "'+str(timestamp)+'", '

############################### get data
result = client.read_input_registers(0x3100, 19, slave=1)
#print (result)
if not result.isError():
 mystr=mystr+'"chargingInputVoltage'+s_1+str(to_float(result.registers[0]))+s_2
 mystr+mystr+'"chargingInputCurrent'+s_1+str(to_float(result.registers[1]))+s_2
 mystr=mystr+'"chargingInputPower'+s_1+str(to_float(result.registers[2], result.registers[3]))+s_2
 
 mystr=mystr+'"chargingOutputVoltage'+s_1+str(to_float(result.registers[4]))+s_2
 mystr=mystr+'"chargingOutputCurrent'+s_1+str(to_float(result.registers[5]))+s_2
 mystr=mystr+'"chargingOutputPower'+s_1+str(to_float(result.registers[6], result.registers[7]))+s_2
 
 mystr=mystr+'"dischargingOutputVoltage'+s_1+str(to_float(result.registers[12]))+s_2
 mystr=mystr+'"dischargingOutputCurrent'+s_1+str(to_float(result.registers[13]))+s_2
 mystr=mystr+'"dischargingOutputPower'+s_1+str(to_float( result.registers[14], result.registers[15]))+s_2

 mystr=mystr+'"batteryTemperature'+s_1+str(to_float(result.registers[16]))+s_2
 mystr=mystr+'"temperatureInside'+s_1+str(to_float(result.registers[17]))+s_2
 mystr=mystr+'"powerComponentsTemperature'+s_1+str(to_float(result.registers[18]))+s_2
 #print ("\n"+str(data)+"\n")
else:
 print("\nerr get data\n")

################################# get data2
result = client.read_input_registers(0x311A, 2, slave=1)
if not result.isError():
 mystr=mystr+'"batterySoC'+s_1+str(to_float(result.registers[0]) * 100)+s_2
 mystr=mystr+'"remoteBatteryTemperature'+s_1+str(to_float(result.registers[1]))+s_2
 #print ("\n"+str(data2)+"\n")
else:
 print("\nerr get data2\n")

################################# get data3
result = client.read_input_registers(0x311D, 1, slave=1)
if not result.isError():
 mystr=mystr+'"batteryRealRatedPower'+s_1+str(to_float(result.registers[0]))+s_2
 #print ("\n"+str(data3)+"\n")
else:
 print("\nerr get data3\n")

################# get_battery_load 
result = client.read_input_registers(0x310C, 4, slave=1)
if not result.isError():
 mystr=mystr+'"loadVoltage'+s_1+str(to_float(result.registers[0]))+s_2
 mystr=mystr+'"loadCurrent'+s_1+str(to_float(result.registers[1]))+s_2
 mystr=mystr+'"loadPower'+s_1+str(to_float(result.registers[2], result.registers[3]))+s_2
 #print("\n"+str(all_data)+"\n")
else:
 print("\nerr get battery load\n")


###################### get_battery_settings
result = client.read_holding_registers(0x9000, 15, slave=1)
if not result.isError():
   battery_type = {
                0: "User defined",
                1: "Sealed",
                2: "GEL",
                3: "Flooded"
                }
   mystr=mystr+'"batteryType'+s_1+str(battery_type.get(result.registers[0]))+s_2
   mystr=mystr+'"batteryCapacity'+s_1+str(result.registers[1])+s_2
   mystr=mystr+'"temperatureCompensationCoefficient'+s_1+str(to_float(result.registers[2]))+s_2
   mystr=mystr+'"highVoltDisconnect'+s_1+str(to_float(result.registers[3]))+s_2
   mystr=mystr+'"chargingLimitVoltage'+s_1+str(to_float(result.registers[4]))+s_2
   mystr=mystr+'"overVoltageReconnect'+s_1+str(to_float(result.registers[5]))+s_2
   mystr=mystr+'"equalizationVoltage'+s_1+str(to_float(result.registers[6]))+s_2
   mystr=mystr+'"boostVoltage'+s_1+str(to_float(result.registers[7]))+s_2
   mystr=mystr+'"floatVoltage'+s_1+str(to_float(result.registers[8]))+s_2
   mystr=mystr+'"boostReconnectVoltage'+s_1+str(to_float(result.registers[9]))+s_2
   mystr=mystr+'"lowVoltageReconnect'+s_1+str(to_float(result.registers[10]))+s_2
   mystr=mystr+'"underVoltageRecover'+s_1+str(to_float(result.registers[11]))+s_2
   mystr=mystr+'"underVoltageWarning'+s_1+str(to_float(result.registers[12]))+s_2
   mystr=mystr+'"lowVoltageDisconnect'+s_1+str(to_float(result.registers[13]))+s_2
   mystr=mystr+'"dischargingLimitVoltage'+s_1+str(to_float(result.registers[14]))+s_2
   #print ("\n"+str(settings)+"\n")
else:
   #logger.error(result)
   print ("\nerr get battery setting\n")

"""get_battery_stat"""
result = client.read_input_registers(0x3300, 31, slave=1)
if not result.isError():
   mystr=mystr+'"maxVoltToday'+s_1+str(to_float(result.registers[0]))+s_2
   mystr=mystr+'"minVoltToday'+s_1+str(to_float(result.registers[1]))+s_2
   mystr=mystr+'"maxBatteryVoltToday'+s_1+str(to_float(result.registers[2]))+s_2
   mystr=mystr+'"minBatteryVoltToday'+s_1+str(to_float(result.registers[3]))+s_2
   mystr=mystr+'"consumedEnergyToday'+s_1+str(to_float(result.registers[4], result.registers[5]))+s_2
   mystr=mystr+'"consumedEnergyMonth'+s_1+str(to_float(result.registers[6], result.registers[7]))+s_2
   mystr=mystr+'"consumedEnergyYear'+s_1+str(to_float(result.registers[8], result.registers[9]))+s_2
   mystr=mystr+'"totalConsumedEnergy'+s_1+str(to_float(result.registers[10], result.registers[11]))+s_2
   mystr=mystr+'"generatedEnergyToday'+s_1+str(to_float(result.registers[12], result.registers[13]))+s_2
   mystr=mystr+'"generatedEnergyMonth'+s_1+str(to_float(result.registers[14], result.registers[15]))+s_2
   mystr=mystr+'"generatedEnergyYear'+s_1+str(to_float(result.registers[16], result.registers[17]))+s_2
   mystr=mystr+'"totalGeneratedEnergy'+s_1+str(to_float(result.registers[18], result.registers[19]))+s_2
   mystr=mystr+'"carbonDioxideReduction'+s_1+str(to_float(result.registers[20], result.registers[21]))+s_2
   mystr=mystr+'"batteryVoltage'+s_1+str(to_float(result.registers[26]))+s_2
   mystr=mystr+'"batteryCurrent'+s_1+str(to_float(result.registers[27], result.registers[28]))+s_2
   mystr=mystr+'"batteryTemperature'+s_1+str(to_float(result.registers[29]))+s_2
   mystr=mystr+'"ambientTemperature'+s_1+str(to_float(result.registers[30]))+s_2
   #print("\n"+str(stat)+"\n")
else:
   #logger.error(result)
   print ("\nerr get battery stat\n")


###################### get_battery_status
result = client.read_input_registers(0x3200, 3, slave=1)
if not result.isError():
    value = result.registers[0]
    battery_status_voltage = {
                0: "Normal",
                1: "Overvolt",
                2: "Under volt",
                3: "Low Volt Disconnect",
                4: "Fault"
            }
    battery_status_temperature = {
                0: "Normal",
                1: "Over Temperature",
                2: "Low Temperature"
            }
    abnormal_status = {
                0: "Normal",
                1: "Abnormal"
            }
    wrong_status = {
                0: "Correct",
                1: "Wrong"
            }
    mystr=mystr+'"voltage'+s_1+str(battery_status_voltage.get(value & 0x0007, None))+s_2
    mystr=mystr+'"temperature'+s_1+str(battery_status_temperature.get((value >> 4) & 0x000f, None))+s_2
    mystr=mystr+'"internalResistance'+s_1+str(abnormal_status.get((value >> 8) & 0x0001, None))+s_2
    mystr=mystr+'"ratedVoltage'+s_1+str(wrong_status.get((value >> 15) & 0x0001, None))+s_2

    value = result.registers[1]
    charging_equipment_status_input_voltage = {
                0: "Normal",
                1: "No power connected",
                2: "Higher Volt Input",
                3: "Input Volt Error"
            }
    charging_equipment_status_battery = {
                0: "Not charging",
                1: "Float",
                2: "Boost",
                3: "Equalization"
            }
    fault_status = {
                0: "Normal",
                1: "Fault"
            }
    running_status = {
                0: "Standby",
                1: "Running"
            }
            
    mystr=mystr+'"inputVoltage'+s_1+str(charging_equipment_status_input_voltage.get((value >> 14) & 0x0003, None))+s_2
    mystr=mystr+'"mosfetShort'+s_1+str(to_bool((value >> 13) & 0x0001))+s_2
    mystr=mystr+'"chargingAntiReverseMosfetShort'+s_1+str(to_bool((value >> 12) & 0x0001))+s_2
    mystr=mystr+'"antiReverseMosfetShort'+s_1+str(to_bool((value >> 11) & 0x0001))+s_2
    mystr=mystr+'"inputOverCurrent'+s_1+str(to_bool((value >> 10) & 0x0001))+s_2
    mystr=mystr+'"loadOverCurrent'+s_1+str(to_bool((value >> 9) & 0x0001))+s_2
    mystr=mystr+'"loadShort'+s_1+str(to_bool((value >> 8) & 0x0001))+s_2
    mystr=mystr+'"loadMosfetShort'+s_1+str(to_bool((value >> 7) & 0x0001))+s_2
    mystr=mystr+'"pvInputShort'+s_1+str(to_bool((value >> 4) & 0x0001))+s_2
    mystr=mystr+'"battery'+s_1+str(charging_equipment_status_battery.get((value >> 2) & 0x0003, None))+s_2
    mystr=mystr+'"fault'+s_1+str(fault_status.get((value >> 1) & 0x0001, None))+s_2
    mystr=mystr+'"running'+s_1+str(running_status.get((value) & 0x0001, None))+s_2

    value = result.registers[2]
    discharging_equipment_status_voltage = {
                0: "Normal",
                1: "Low",
                2: "High",
                3: "No access input volt error"
            }
    discharging_equipment_status_output = {
                0: "Light Load",
                1: "Moderate",
                2: "Rated",
                3: "Overload"
            }
    discharging_equipment_status = {}

    mystr=mystr+'"inputVoltage'+s_1+str(discharging_equipment_status_voltage.get((value >> 14) & 0x0003, None))+s_2
    mystr=mystr+'"outputPower'+s_1+str(discharging_equipment_status_output.get((value >> 12) & 0x0003, None))+s_2
    mystr=mystr+'"shortCircuit'+s_1+str(to_bool((value >> 11) & 0x0001))+s_2
    mystr=mystr+'"unableDischarge'+s_1+str(to_bool((value >> 10) & 0x0001))+s_2
    mystr=mystr+'"unableStopDischarging'+s_1+str(to_bool((value >> 9) & 0x0001))+s_2
    mystr=mystr+'"outputVoltageAbnormal'+s_1+str(to_bool((value >> 8) & 0x0001))+s_2
    mystr=mystr+'"inputOverpressure'+s_1+str(to_bool((value >> 7) & 0x0001))+s_2
    mystr=mystr+'"highVoltageSideShortCircuit'+s_1+str(to_bool((value >> 6) & 0x0001))+s_2
    mystr=mystr+'"boostOverpressure'+s_1+str(to_bool((value >> 5) & 0x0001))+s_2
    mystr=mystr+'"outputOverpressure'+s_1+str(to_bool((value >> 4) & 0x0001))+s_2
    mystr=mystr+'"fault'+s_1+str(fault_status.get((value >> 1) & 0x0001, None))+s_2
    mystr=mystr+'"running'+s_1+str(running_status.get(value & 0x0001, None))+'"}'

    #print("\nbatteryStatus"+str(battery_status)+"\n")
    #print("\nequipmentStatus"+str(equipment_status)+"\n")
    #print("\ndischargingEquipmentStatus"+str(discharging_equipment_status)+"\n")
else:
    #logger.error(result)
    print("\n err get status\n")


print ("my str")
print(mystr)            

msg=mystr
clientm.on_connect = on_connect
clientm.on_disconnect = on_disconnect
clientm.connect(broker, port, 60)


if __name__ == "__main__":
    clientm.loop_forever()
