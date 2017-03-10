#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: slawler@dewberry.com
Created on Mon Dec 19 16:14:23 2016
"""
#------------Load Python Modules--------------------#
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import pylab
from matplotlib.dates import DayLocator, HourLocator, DateFormatter
from matplotlib.font_manager import FontProperties
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta


#--User Input--##
fort22 = r'C:\Users\student.W7JF4Z7V1\Desktop\dfdf\fort.221'
plotdir = r'C:\Users\student.W7JF4Z7V1\Desktop\dfdf'
fort61 = r'C:\Users\student.W7JF4Z7V1\Desktop\dfdf\WLFort63.txt'
#defining path for Outputfile
f = r'C:\Users\student.W7JF4Z7V1\Desktop\dfdf\Output.txt'

frequency = '3600s'

#--Stations data
stations = [10, 15, 21, 23, 27, 36, 38]

station_dict = {10:'BISM2',  15:'BLTM2', 21:'APAM2', 23:'SLIM2', 
                27: 'KPTV2', 36:'SWPV2', 38:'CBBV2'}


station_datum_shift  = {10: 0.380, 15: 0.254, 21:0.235, 23: 0.259, 
                        27: 0.58, 36: 0.491, 38:0.35}               

station_names = {10:'Bishops Head, MD', 15: 'Baltimore, MD', 21: 'Annapolis, MD', 23:'Solomons Island, MD', 
                27:'Kiptopeke, VA', 36:'Sewells Point, VA', 38:'Chesapeake Bay Bridge Tunnel'}                
       
                
#---Get Start Date From fort.221
from datetime import datetime

with open(fort22,'r') as f:
    for i in range(0,1):
        line = f.readline().strip().split()
        timestamp = line[3]
        start_date = datetime.strptime(timestamp,'%Y%m%d%H')
        

#--Read in adcirc_data from Result(fort.*)
adcirc_data = pd.read_fwf(fort61, skiprows=3,widths = [15,18], 
                 names = ['station','value'])

adcirc_data['value'] = adcirc_data['value'].apply(pd.to_numeric, errors='coerce')
adcirc_data['station'] = adcirc_data['station'].astype(int)
adcirc_data   = adcirc_data.query('value >= -1000')


for s in stations:
      
    plt.interactive(False)  
    
    #--ADCIRC DATA Block   
    try:
        df = adcirc_data.query('station == {}'.format(s))  # Get Station adcirc_data
        records = len(df)
        idx = pd.date_range(start = start_date, periods = records, freq=frequency, tz='utc')
        df = df.set_index(idx)                              # Add datetime
        df['value'] = df['value'] + station_datum_shift[s]  # Datum Shift 
        name = station_names[s]
        gage = station_dict[s]
        #print(name)
   
    except:
        print("ADCIRC ERROR on station {}".format(name))
     
    #--AHPS DATA Block    
    try:
    
        #---Read HTML
        url = r'http://water.weather.gov/ahps2/hydrograph_to_xml.php?gage={}&output=tabular'.format(gage)
        r = requests.get(url)
        data = r.text
        soup = BeautifulSoup(data, "lxml")
        
        #---Data
        data = soup.find_all('table')[0] 
        data_rows = data.find_all('tr')[3:]
        
        #--Get the Current Year in UTC
        year = datetime.now(timezone.utc).strftime("%Y")
        
        
        #--Get the Current Year in UTC
        year = datetime.now(timezone.utc).strftime("%Y")
        
        #--Initialize Dictionaries
        obs_data =  {'Date(UTC)' : [],  'Stage' : []}
        forecast_data = {'Date(UTC)' : [],  'Stage' : []}
        value = 'Observed'              
        for row in data_rows:
            d = row.find_all('td')
            try:
                dtm   = d[0].get_text().split()[0] + '/' + str(year) +' '+ d[0].get_text().split()[1]
                stage = d[1].get_text()
        
                if value == 'Observed':
                    obs_data['Date(UTC)'].append(dtm) 
                    obs_data['Stage'].append(stage)
        
                elif value =='Forecast':
                    forecast_data['Date(UTC)'].append(dtm) 
                    forecast_data['Stage'].append(stage)
        
            except:
                check_value = str(d)
                if 'Forecast  Data ' in check_value:
                    value = 'Forecast'
                    
        #---Create & Format Dataframes
        df_obs = pd.DataFrame.from_dict(obs_data)
        df_obs['Date(UTC)'] = pd.to_datetime(df_obs['Date(UTC)'], format='%m/%d/%Y %H:%M')
        df_obs['Stage'] = df_obs['Stage'].astype(str).str[:-2].astype(np.float)
        df_obs = df_obs.set_index(df_obs['Date(UTC)'] )
        
        df_fcst = pd.DataFrame.from_dict(forecast_data)   
        df_fcst['Date(UTC)'] = pd.to_datetime(df_fcst['Date(UTC)'], format='%m/%d/%Y %H:%M')
        df_fcst['Stage'] = df_fcst['Stage'].astype(str).str[:-2].astype(np.float)
        df_fcst = df_fcst.set_index(df_fcst['Date(UTC)'] )
        
        # HERE IT GETS THE DATAFRAME READY FOR EACH STATION
        # I AM TRYING THIS, IT YIELDS AN OUTPUT FILE IN THE DIRECTORY 
        
        df_fcst.to_csv(f,sep='\t')

        #start, stop = df_obs.index[0], df_fcst.index[-1]
        
        
        #--Initialize Plots
        fig, ax = plt.subplots(figsize=(12,6))
        
        #--Plot AHPS Gage Observed
        x0 = df_obs['Date(UTC)']
        y0 = df_obs['Stage']
        ax.plot(x0 ,y0, color = 'b', linewidth = 2)       # Observed
        
        
        #--Plot AHPS Forecast
        x1 = df_fcst['Date(UTC)']
        y1 = df_fcst['Stage']
        ax.plot(x1 ,y1, color = 'r')         # Forecast
        #print(gage, len(df))   
        
        mpl.rcParams['timezone'] = 'US/Eastern'

        
    except:
        print("AHPS ERROR on station {}".format(name))
               

    try:
        x2 = df.index #+ timedelta(hours = 5)
        y2 = df['value'] * 3.28084
        ax.plot(x2 ,y2, color = 'black', linewidth = 5)       # Observed
        plot_start = df_obs['Date(UTC)'][-1]
        plot_stop = df.index[-1] +timedelta(hours = 24) 
        #--Set Axis Limits
        ax.set_xlim(plot_start, plot_stop)
        #ax.set_ylim(0, major)
        
        plt.title('{}, AHPS Gage: ({})'.format(name, gage))
        plt.xlabel('Eastern Time')
        plt.ylabel('Stage (ft)', fontweight='bold')
        
        #--Plot Formatting
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.2,
                         box.width, box.height * 0.8])
        
        fontP = FontProperties()
        fontP.set_size('small')
        
        plt.legend(['AHPS_Observed', 'AHPS_Forecast','ADCIRC'],
                  bbox_to_anchor=(0.75, -0.2),prop = fontP,
                  fancybox=False, shadow=False, ncol=3, scatterpoints = 0)
        

        ax.plot(x0 ,y0, color = 'b', marker = 'o')       # Add Points
        ax.plot(x1 ,y1, color = 'r', marker = 'o')       # Add Points
        plt.grid(True)
        plt.gca().xaxis.set_major_formatter(DateFormatter('%I%p\n%a\n%b%d'))
        plt.gca().xaxis.set_major_locator(HourLocator(byhour=range(24), interval=12))

        
        plt.savefig(r'{}/{}.png'.format(plotdir,  gage), dpi = 600)
        plt.close()
        
        
        

    except:
        print("Plotting ERROR on station {}".format(name))
