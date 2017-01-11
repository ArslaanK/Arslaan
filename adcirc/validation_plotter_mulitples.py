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
import fileinput
import datetime
import pandas as pd
import os
import requests
from scipy.interpolate import interp1d

#------------------------------------User Inputs

root_dir = r'/Users/slawler/Desktop/Arslaan/adcirc'

#---------------------defining all 3 files----------- using the string type and later in the end merging all dataframes in one---

adcirc_file1 = 'fortx.61'
adcirc_file2 = 'forty.61'
adcirc_file3 = 'fortz.61'
start, freq = "09-2015-20 18:06","360s" #---Date Format: %m-%Y-%d %H:%M

#----------------------definitation of stations
nodesx = {'1':{'8632200':[]}}
nodesy = {'1':{'8632200':[]}}
nodesz = {'1':{'8632200':[]}}

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
        
f3 = os.path.join(root_dir,adcirc_file1)

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
adcircx = adcircx.rename(columns={'1':'x1'})

#----------------------------------ADCIRC file B-----------------
adcircy = pd.DataFrame()

for key in nodesy:
    adcircy[key]=nodesy[key][stationsy[key]] 

adcircy.replace(to_replace=-99999.000000,value=0,inplace=True)
adc_idx = pd.date_range(first,periods = period, freq=freq)

adcircy = adcircy.set_index(adc_idx)
adcircy = adcircy.rename(columns={'1':'y1'})

#----------------------------------ADCIRC file C-----------------

adcircz = pd.DataFrame()

for key in nodesz:
    adcircz[key]=nodesz[key][stationsz[key]] 

adcircz.replace(to_replace=-99999.000000,value=0,inplace=True)
adc_idx = pd.date_range(first,periods = period, freq=freq)

adcircz = adcircz.set_index(adc_idx)
adcircz = adcircz.rename(columns={'1':'z1'})


#-------------------------Join ADCIRC & NOAA Dataframes, Resample ADCIRC values

df_adcirc = adcircx.merge(adcircy,left_index=True, right_index=True).merge(adcircz,left_index=True, right_index=True)


 #--(Trying to merge all 3 data frames for 3 adcirc files)--------------------------
 

    
df = df.merge(df_adcirc, how='outer', left_index=True, right_index=True)

    
#--------------------------Plot Results for Each Station        
 

df.plot()