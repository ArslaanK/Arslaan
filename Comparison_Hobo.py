#!/usr/bin/env python 3.5.2
# -*- coding: utf-8 -*-
"""
Description:
    
Input(s):
Output(s):
@author: slawler@dewberry.com
Created on Sun Oct 23 18:10:24 2016
"""

#------------Load Python Modules--------------------#
import matplotlib.pyplot as plt
from matplotlib import pylab
from matplotlib.dates import DayLocator, HourLocator, DateFormatter
import fileinput
import datetime
import pandas as pd
import os
import requests
from scipy.interpolate import interp1d
import csv

#------------------------------------User Inputs

root_dir = r'C:\Users\slawler\Desktop\Arslaan'

#---------------------defining all 3 files----------- using the string type and later in the end merging all dataframes in one---

adcirc_file1 = 'fortmf.61'
adcirc_file2 = 'fortff.61'
adcirc_file3 = 'fortfso.61'
adcirc_file4 = 'fortfsc.61'

with open('hoboS1ES.txt') as f:
    content = f.readlines()

lines = [line.rstrip('\n') for line in open('hoboS1ES.txt')]

start, freq = "09-2015-20 18:06","360s" #---Date Format: %m-%Y-%d %H:%M

#----------------------definitation of stations----
nodesx = {'1':{'8632200':[]}}
nodesy = {'27':{'8632200':[]}}
nodesz = {'1':{'8632200':[]}}
nodesa = {'1':{'8632200':[]}}

noaa_time_step = '6T'

#--NOAA API https://tidesandcurrents.noaa.gov/api/
datum     = "NAVD"   #"NAVD"                  #Datum
units     = "metric"                         #Units
time_zone = "gmt"                         #Time Zone
fmt       = "json"                            #Format
url       = 'http://tidesandcurrents.noaa.gov/api/datagetter'
product   = 'water_level'                     #Product


#------------------------------------Read file & Extract Time Series Data

#--------- multiple reading files in 3 nodes type (nodex,nodey,nodez)

f1 = os.path.join(root_dir,adcirc_file1)

stationsx = dict()
for n in nodesx:
    for key in nodesx[n]:
        stationsx[n]= key

for line in fileinput.input(f1):
    n = line.strip().split(' ')[0]
    if n in nodesx:
        data = line.strip().split()[1]
        nodesx[n][stationsx[n]].append(float(data))
        periodsx = len(nodesx[n][stationsx[n]])
        
f2 = os.path.join(root_dir,adcirc_file2)

stationsy = dict()
for n in nodesy:
    for key in nodesy[n]:
        stationsy[n]= key

for line in fileinput.input(f2):
    n = line.strip().split(' ')[0]
    if n in nodesy:
        data = line.strip().split()[1]
        nodesy[n][stationsy[n]].append(float(data))
        periodsy = len(nodesy[n][stationsy[n]])
        
f3 = os.path.join(root_dir,adcirc_file3)

stationsz = dict()
for n in nodesz:
    for key in nodesz[n]:
        stationsz[n]= key

for line in fileinput.input(f3):
    n = line.strip().split(' ')[0]
    if n in nodesz:
        data = line.strip().split()[1]
        nodesz[n][stationsz[n]].append(float(data))
        periodsz = len(nodesz[n][stationsz[n]])
                
f4 = os.path.join(root_dir,adcirc_file4)

stationsa = dict()
for n in nodesa:
    for key in nodesa[n]:
        stationsa[n]= key

for line in fileinput.input(f4):
    n = line.strip().split(' ')[0]
    if n in nodesa:
        data = line.strip().split()[1]
        nodesa[n][stationsa[n]].append(float(data))
        periodsa = len(nodesa[n][stationsa[n]])


for n in nodesx: #---This is sloppy, we can improve this: we just need the lenght of the array
    for key in nodesx[n]:
        period = len(nodesx[n][key])   
        
   
      
#---------------------Ping NOAA API for Validation Data,Create NOAA Dataframe

noaa = pd.DataFrame()
gages = dict()

first = datetime.datetime.strptime(start,"%m-%Y-%d %H:%M" )
last =  pd.date_range(first,periods = period, freq=freq)[-1]
 
for n in nodesx:
    for key in nodesx[n]:
        g = int(key)
       
    t0     = first.strftime('%Y%m%d %H:%M')
    t1     = last.strftime('%Y%m%d %H:%M')
    api_params = {'begin_date': t0, 'end_date': t1,
                'station': g,'product':product,'datum':datum,
                'units':units,'time_zone':time_zone,'format':fmt,
                'application':'web_services' }
        
    pred=[];obsv=[];t=[]

    try:
        r = requests.get(url, params = api_params)
        jdata =r.json()
    
        for j in jdata['data']:
            t.append(str(j['t']))
            obsv.append(str(j['v']))
            pred.append(str(j['s']))
        colname = str(g)    
        noaa[colname]= obsv
        noaa[colname] = noaa[colname].astype(float)
        gages[jdata['metadata']['id']]=jdata['metadata']['name']
    except:
        print(g,'No Data')      
     
idx = pd.date_range(first,periods = len(noaa.index), freq=noaa_time_step)   
noaa = noaa.set_index(idx)   
    
##################################--MAKE CHANGES HERE--######################   #, 'oooo':3
#---Instructions:

#-For each station, enter the datum shift value
datum_dict = {'8632200':0}

adcircx = pd.DataFrame()

df = noaa.merge(adcircx, how='outer', left_index=True, right_index=True)

for key in datum_dict: 
    if key in noaa:
        df[key] = df[key]-datum_dict[key]
    else:
        print('Key not found: ',key)

#--------------------------Create ADCIRC DataFrame

#----------------------------------ADCIRC file A-----------------
adcircx = pd.DataFrame()

for key in nodesx:
    adcircx[key]=nodesx[key][stationsx[key]] 

adcircx.replace(to_replace=-99999.000000,value=0,inplace=True)
adc_idx = pd.date_range(first,periods = period, freq=freq)

adcircx = adcircx.set_index(adc_idx)
adcircx = adcircx.rename(columns={'1':'ModFemaFull'})

#----------------------------------ADCIRC file B-----------------
adcircy = pd.DataFrame()

for key in nodesy:
    adcircy[key]=nodesy[key][stationsy[key]] 

adcircy.replace(to_replace=-99999.000000,value=0,inplace=True)
adc_idx = pd.date_range(first,periods = period, freq=freq)

adcircy = adcircy.set_index(adc_idx)
adcircy = adcircy.rename(columns={'27':'FemaFull'})

#----------------------------------ADCIRC file C-----------------

adcircz = pd.DataFrame()

for key in nodesz:
    adcircz[key]=nodesz[key][stationsz[key]] 

adcircz.replace(to_replace=-99999.000000,value=0,inplace=True)
adc_idx = pd.date_range(first,periods = period, freq=freq)

adcircz = adcircz.set_index(adc_idx)
adcircz = adcircz.rename(columns={'1':'FemaSubOrg'})
#----------------------------------ADCIRC file D-----------------

adcirca = pd.DataFrame()

for key in nodesa:
    adcirca[key]=nodesa[key][stationsa[key]] 

adcirca.replace(to_replace=-99999.000000,value=0,inplace=True)
adc_idx = pd.date_range(first,periods = period, freq=freq)

adcirca = adcirca.set_index(adc_idx)
adcirca = adcirca.rename(columns={'1':'FemaSubChang'})
#------------------------------------Reading Hobo Data---------------------

linesh = pd.DataFrame(lines, dtype = 'float')

#==CHECK THIS OFFSET FOR UTC TIME CORRECTION...I guessed
utc_date_start = first + datetime.timedelta(hours=4)
adc_idx = pd.date_range(utc_date_start ,periods = period, freq=freq)

linesh = linesh.set_index(adc_idx)
linesh = linesh.rename(columns={0:'HOBOS1Es'})


#-------------------------Join ADCIRC & NOAA Dataframes, Resample ADCIRC values

df_adcirc = adcircx.merge(adcircy,left_index=True, right_index=True).merge(adcircz,left_index=True, right_index=True).merge(adcirca,left_index=True, right_index=True).merge(linesh,left_index=True, right_index=True)


 #--(Trying to merge all 3 data frames for 3 adcirc files)--------------------------
 


df = df.merge(df_adcirc, how='outer', left_index=True, right_index=True)

    
#----------------Different Approach to Plot Results        

#--Initialize Plot
fig, ax = plt.subplots(figsize=(12,6))
plt.grid(True)

#--Plot Observed Data
x = df.index 
y0 = df['8632200']
ax.plot(x ,y0, color = 'b', linewidth = 2, label = y0.name)   

#--Timeseries 1
y1 = df['HOBOS1Es']
ax.plot(x ,y1, color = 'r', label = y1.name)  

#--Timeseries  2
y2 = df['FemaFull']
ax.plot(x ,y2, color = 'black', label = y2.name)  


#--Add as many additional time series to the plot as you like....
#--Timeseries 3
#--Timeseries 4



#--Add Plot Formatting
plt.title('Validation Plot')
plt.xlabel('')
plt.ylabel('Stage (ft)', fontweight='bold')
plt.legend(loc="upper right")



'''
# Example of how to format date axis
plt.gca().xaxis.set_major_formatter(DateFormatter('%I%p\n%a\n%b%d'))
plt.gca().xaxis.set_major_locator(HourLocator(byhour=range(24), interval=12))


#--Set Axis Limits
plot_start = '2015-09-20 18:06:00'
plot_stop =  '2015-09-22 18:06:00'
ax.set_xlim(plot_start, plot_stop)    
#title = 'Validation_Example_w_axis_limits'
#plt.savefig('{}.png'.format(title), dpi = 600)

'''


#---Save Figure
#title = 'Validation_Example'
#plt.savefig('{}.png'.format(title), dpi = 600)
#plt.close()
























