#!/usr/bin/python3
# -*- coding: utf-8 -*-


from influxdb import InfluxDBClient
from datetime import datetime,timedelta

import paho.mqtt.client as paho
broker="localhost"
port=1883
topic="hello/world"
def on_publish(client,userdata,result):             #create function for callback
    print("data published \n")
    pass
client1= paho.Client("control1")                           #create client object


yday = 1 			#used at timedeltas
debug = 0 			#Output debug info, er no

client = InfluxDBClient(host='localhost', port=8087)
client.switch_database('mqttwarn')

prix_HP = 0.1703 # € per kW
prix_HC = 0.1319 # € per kW
prix_tariff_blue = 12.61 # € per month
prix_alt = 0.1467  # € per kW
prix_alt_month = 130.32/12 # € per month

date_str_yday = datetime.strftime(datetime.now() - timedelta(yday), '%Y-%m-%d')
date_str_older = datetime.strftime(datetime.now() - timedelta(yday+1), '%Y-%m-%d')
date_str_early = "T22:00:00Z"	#This currently works in French summer time
date_str_late = "T21:59:59Z"

date_str_e = date_str_older + date_str_early
date_str_l = date_str_yday + date_str_late
if debug == 1:
	print("Early Date String " + date_str_e)
	print("Late Date String: " + date_str_l)

query_start = "select value FROM EnergyMon WHERE time >= '"
query_term_HP = "' and topic = 'Linky-020828327174-data_index_p' limit 1"
query_term_HC = "' and topic = 'Linky-020828327174-data_index_c' limit 1"

query_str_hp_e = query_start + date_str_e + query_term_HP
query_str_hp_l = query_start + date_str_l + query_term_HP
query_str_hc_e = query_start + date_str_e + query_term_HC                           
query_str_hc_l = query_start + date_str_l + query_term_HC

if debug == 1:
	print("The respective query strings are: \n" + query_str_hp_e + "\n" + query_str_hp_l + "\n" + query_str_hc_e + "\n" + query_str_hc_l + "\n")


# Query for HP lower val
q = client.query(query_str_hp_e)
points = q.get_points()
if len(q) == 0 :
	msg = "\nFontgrain Linky Data \n---No data found in the earlier query "
	client1.on_publish = on_publish                          #assign function to callback
	client1.connect(broker,port)                                 #establish connection
	ret= client1.publish(topic,msg,qos=0,retain=False)                   #publish



for item in points:
	HP_old = item['value']
	if debug == 1:
		print("The old value is " + repr(HP_old) + "\n")



r = client.query(query_str_hp_l)
points1 = r.get_points()
for item in points1:
        HP_new = item['value']
if debug == 1:
	print("The new value is " + repr(HP_new) + "\n")



# Calculate HP cost
HP_diff = HP_new - HP_old
HP_monetary = HP_diff * (prix_HP/1000)


q = client.query(query_str_hc_e)
points = q.get_points()
for item in points:
        HC_old = item['value']
if debug == 1:
	print("The old value is " + repr(HC_old) + "\n")


r = client.query(query_str_hc_l)
points1 = r.get_points()
for item in points1:
        HC_new = item['value']
if debug == 1:
	print("The new value is " + repr(HC_new) + "\n")


# Calculate HC cost
HC_diff = HC_new - HC_old
HC_monetary = HC_diff * (prix_HC/1000)

#Calculate the daily cost
day_cost_tb = HC_monetary + HP_monetary + (prix_tariff_blue/30)
day_cost_alt = (HC_diff + HP_diff) * (prix_alt/1000) + (prix_alt_month/30)

# Print out the outcome
msg = ""
print("Fontgrain Daily Power Consumption figures for " + date_str_yday + ":\nHP: " + repr(HP_diff/1000) + " kW -- " + repr(round(HP_monetary,2)) + " €")
msg += "Fontgrain Daily Power Consumption figures for " + date_str_yday + ":\nHP: " + repr(HP_diff/1000) + " kW -- " + repr(round(HP_monetary,2)) + " €"

print("HC: " + repr(HC_diff/1000) + " kW -- " + repr(round(HC_monetary,2)) + " €")
msg += "\nHC: " + repr(HC_diff/1000) + " kW -- " + repr(round(HC_monetary,2)) + " €"

print("---Options comparison :---\nCurrent (HP/HC) Day Cost: " + repr(round(day_cost_tb,2)) + " € (or " + repr(round(day_cost_tb*30,2)) + "€ per month)\nOR- Alternative Day Cost: " + repr(round(day_cost_alt,2)) + " € (or " + repr(round(day_cost_alt*30,2)) + "€ per month)\n") 
msg += "\n---Options comparison :---\nCurrent (HP/HC) Day Cost: " + repr(round(day_cost_tb,2)) + " € (or " + repr(round(day_cost_tb*30,2)) + "€ per month)\nOR- Alternative Day Cost: " + repr(round(day_cost_alt,2)) + " € (or " + repr(round(day_cost_alt*30,2)) + "€ per month)\n"

client1.on_publish = on_publish                          #assign function to callback
client1.connect(broker,port)                                 #establish connection
ret= client1.publish(topic,msg,qos=0,retain=False)                   #publish

