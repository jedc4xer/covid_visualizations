import kivy
kivy.require('2.0.0')

from kivy.config import Config
Config.set('kivy', 'exit_on_escape', '0')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, WipeTransition
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.graphics import *
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.core.window import Window

from concurrent.futures import ThreadPoolExecutor as Executor
from PIL import Image
from matplotlib import dates as dt

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime as date

import threading
import time
import winsound

Builder.load_file("covidgui.kv")
print("*********************\n\n\nTHIS PROGRAM IS NOT FULLY COMPLETE AND CERTAIN PATHS WILL RUN TO COMPLETION WHILE OTHERS WILL FAIL\n\n*******")
# Initialize Environment Variables
class InitInfo():
    
    def __init__(self):
        try: 
            self.last = [x for x in pd.read_csv("Updated_Through.txt").columns]
            self.last[1], self.last[2] = f'{int(self.last[1]):,}',f'{int(self.last[2]):,}'
        except:
            self.last = ["Unknown"] * 3
        
        try:
            self.favorites = pd.read_csv("Favorites.txt").columns.values.tolist()
            self.fav_loaded = "True"
        except:
            self.favorites = "Unknown"
            self.fav_loaded = "False"
            
        try:
            self.load_times_main = pd.read_csv("load_times.csv")
            self.load_times = self.load_times_main.values.tolist()
            self.load_times_actual = self.load_times_main.loc[self.load_times_main['Method'] == 'Loading'].Time
            print(self.load_times_actual)
        except:
            self.load_times = []
            print("Error with Load_times file")
            
    def ret_last_updated(self):
        return(self.last)
        
    def ret_variables(self):
        return(self.last,self.favorites,self.fav_loaded)
    
    def ret_average_load_time(self):
        return round(self.load_times_actual.mean(),2) if len(self.load_times) > 2 else ""
    
    def ret_load_times(self):
        return self.load_times
Initialize = InitInfo()

class SaveAndClose:
    
    def __init__(self):
        self.load_times = LoadData().return_data().load_times
        
    def save_load_times(self):
        self.load_times = pd.DataFrame(self.load_times)
        self.load_times.to_csv("load_times.csv",index = False)
        
class LoadData():
    
    def __init__(self,which_data):
        self.which_data = which_data
        self.start = None
        self.data = None
        self.is_loaded = False
    
    def load_data(self):
        try:
            self.start = time.perf_counter()
            print(f'Timer Started: {self.start}')
            if self.which_data == 'Time Series State Level':
                self.which_data = 'Time Series SL Data'
            options = ['State Level Data','Time Series SL Data','Time Series US Data','US Cases','US Deaths']
            if self.which_data not in options:
                assert 1 == 0
            skip = 1 if self.which_data == 'State Level Data' else 0
            self.data = pd.read_csv(self.which_data + '.csv',skiprows = skip)
            self.is_loaded = True
            print("load passed")
        except:
            self.is_loaded = False
            print("load failed")
            
    def ret_state_of_data(self):
        return self.is_loaded
            
    def return_data(self,which_data):
        if 'Time Series' in which_data:
            sort_on = 'Date'
            ascend = True
        else:
            sort_on = "Cases_per_capita"
            ascend = False

        self.data_for_display = self.data #.sort_values(sort_on, ascending = ascend)#[['State',
                                                                                                       #   'Cases_per_capita',
                                                                                                        #  'Deaths_per_capita','Population',
                                                                                                         # 'Longitude', 'Latitude','Code']]
        print(f'Time Variable Check: {self.start}')
        load_time = time.perf_counter() - self.start
        #load_times = InitInfo.ret_load_times()
        Initialize.load_times.append(["Loading",load_time])
       # load_times = pd.DataFrame(load_times,columns = ["Method","Time"])
       # load_times.to_csv("load_times.csv", index = False)
        return(self.data_for_display)
    
    def data_return(self):
        pass

class UpdateData():
    
    def __init__(self):
        self.urls = ["https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv",
           "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"]
        pass
    
    def start_update(self):
        UpdateData.start_update.cases_deaths = [[],[]]
        with Executor() as executor: # Process pool for speeding up the data gathering.
            cases = executor.submit(UpdateData.get_updated_data, self.urls[0])
            deaths = executor.submit(UpdateData.get_updated_data, self.urls[1])
            UpdateData.start_update.cases_deaths[0],  UpdateData.start_update.cases_deaths[1] = cases.result(), deaths.result()
        return
    
    def get_updated_data(url): # Get data from source and transform it
        df = pd.read_csv(url)
        df = pd.DataFrame.transpose(df) # Compress this
        df.reset_index(inplace = True)
        return (df.values.tolist())
    
    def return_data(self):
        return(UpdateData.start_update.cases_deaths)
    
    def save_compiled_data_to_csv(self):
        tabs = ["US Cases","US Deaths","State Level Data","Time Series SL Data","Time Series US Data"]
        for i,each_list in enumerate(UpdateData.start_update.cases_deaths):
            print(f'Compiling {tabs[i]}')
            if i == 3:
                each_list = each_list[2:]
            if i == 4:
                each_list = each_list[1:]
            headers = [x for x in each_list[0]]
            if i in [3,4]:
                each_list = each_list[1:]
            each_list = pd.DataFrame(each_list,columns = [x for x in headers])
            if i == 4:
                last_data = [each_list[_].values.tolist()[-1] for _ in ['Date','Cases','Deaths']] # This variable collects the most recent information so that it can be displayed on program start
            each_list.to_csv(tabs[i] + '.csv', index = False)
        updated_date_file = open("Updated_Through.txt","w+")
        updated_date_file.write(",".join(str(x) for x in last_data))
        print("Finished with CSV Files...")
        
class GetFunctions():
    
    def __init__(self):
        self.cases_deaths = UpdateData().return_data()
 
        self.state_info = {'Alabama': {'Latitude': 33.258881699999996, 'Longitude': -86.8295337, 'code': 'AL'}, 'Alaska': {'Latitude': 64.44596130000001, 'Longitude': -149.680909, 'code': 'AK'}, 
                      'Arizona': {'Latitude': 34.395342, 'Longitude': -111.763275, 'code': 'AZ'}, 'Arkansas': {'Latitude': 35.2048883, 'Longitude': -92.4479108, 'code': 'AR'}, 
                      'California': {'Latitude': 36.7014631, 'Longitude': -118.755997, 'code': 'CA'}, 'Colorado': {'Latitude': 38.7251776, 'Longitude': -105.607716, 'code': 'CO'}, 
                      'Connecticut': {'Latitude': 41.6500201, 'Longitude': -72.7342163, 'code': 'CT'}, 'Delaware': {'Latitude': 38.6920451, 'Longitude': -75.4013315, 'code': 'DE'}, 
                      'Florida': {'Latitude': 27.7567667, 'Longitude': -81.4639835, 'code': 'FL'}, 'Georgia': {'Latitude': 32.329380900000004, 'Longitude': -83.1137366, 'code': 'GA'}, 
                      'Guam': {'Latitude': 13.4501257, 'Longitude': 144.757551, 'code': 'GU'}, 'Hawaii': {'Latitude': 19.58726775, 'Longitude': -155.42688969999998, 'code': 'HI'}, 
                      'Idaho': {'Latitude': 43.644764200000004, 'Longitude': -114.01540700000001, 'code': 'ID'}, 'Illinois': {'Latitude': 40.079660600000004, 'Longitude': -89.4337288, 'code': 'IL'}, 
                      'Indiana': {'Latitude': 40.327012700000004, 'Longitude': -86.1746933, 'code': 'IN'}, 'Iowa': {'Latitude': 41.9216734, 'Longitude': -93.3122705, 'code': 'IA'}, 
                      'Kansas': {'Latitude': 38.27312, 'Longitude': -98.58218719999999, 'code': 'KS'}, 'Kentucky': {'Latitude': 37.5726028, 'Longitude': -85.1551411, 'code': 'KY'}, 
                      'Louisiana': {'Latitude': 30.8703881, 'Longitude': -92.007126, 'code': 'LA'}, 'Maine': {'Latitude': 45.709097, 'Longitude': -68.8590201, 'code': 'ME'}, 
                      'Maryland': {'Latitude': 39.5162234, 'Longitude': -76.9382069, 'code': 'MD'}, 'Massachusetts': {'Latitude': 42.3788774, 'Longitude': -72.03236600000001, 'code': 'MA'}, 
                      'Michigan': {'Latitude': 43.6211955, 'Longitude': -84.6824346, 'code': 'MI'}, 'Minnesota': {'Latitude': 45.98965870000001, 'Longitude': -94.6113288, 'code': 'MN'}, 
                      'Mississippi': {'Latitude': 32.9715645, 'Longitude': -89.7348497, 'code': 'MS'}, 'Missouri': {'Latitude': 38.7604815, 'Longitude': -92.5617875, 'code': 'MO'}, 
                      'Montana': {'Latitude': 47.3752671, 'Longitude': -109.63875700000001, 'code': 'MT'}, 'Nebraska': {'Latitude': 41.7370229, 'Longitude': -99.5873816, 'code': 'NE'}, 
                      'Nevada': {'Latitude': 39.515882500000004, 'Longitude': -116.85372269999999, 'code': 'NV'}, 'New Hampshire': {'Latitude': 43.484913299999995, 'Longitude': -71.6553992, 'code': 'NH'}, 
                      'New Jersey': {'Latitude': 40.0757384, 'Longitude': -74.4041622, 'code': 'NJ'}, 'New Mexico': {'Latitude': 34.5708167, 'Longitude': -105.993007, 'code': 'NM'}, 
                      'New York': {'Latitude': 40.7127281, 'Longitude': -74.0060152, 'code': 'NY'}, 'North Carolina': {'Latitude': 35.6729639, 'Longitude': -79.03929190000001, 'code': 'NC'}, 
                      'North Dakota': {'Latitude': 47.6201461, 'Longitude': -100.540737, 'code': 'ND'}, 'Northern Mariana Islands': {'Latitude': 14.149020499999999, 'Longitude': 145.2134525, 'code': 'MP'}, 
                      'Ohio': {'Latitude': 40.225356899999994, 'Longitude': -82.6881395, 'code': 'OH'}, 'Oklahoma': {'Latitude': 34.9550817, 'Longitude': -97.2684063, 'code': 'OK'}, 
                      'Oregon': {'Latitude': 43.9792797, 'Longitude': -120.737257, 'code': 'OR'}, 'Pennsylvania': {'Latitude': 40.9699889, 'Longitude': -77.72788309999999, 'code': 'PA'}, 
                      'Puerto Rico': {'Latitude': 18.2214149, 'Longitude': -66.4132818, 'code': 'PR'}, 'Rhode Island': {'Latitude': 41.7962409, 'Longitude': -71.59923719999999, 'code': 'RI'}, 
                      'South Carolina': {'Latitude': 33.687438799999995, 'Longitude': -80.4363743, 'code': 'SC'}, 'South Dakota': {'Latitude': 44.6471761, 'Longitude': -100.348761, 'code': 'SD'}, 
                      'Tennessee': {'Latitude': 35.7730076, 'Longitude': -86.28200809999998, 'code': 'TN'}, 'Texas': {'Latitude': 31.8160381, 'Longitude': -99.51209859999999, 'code': 'TX'}, 
                      'Virgin Islands': {'Latitude': 18.4024395, 'Longitude': -64.5661642, 'code': 'VI'}, 'Utah': {'Latitude': 39.4225192, 'Longitude': -111.714358, 'code': 'UT'}, 
                      'Vermont': {'Latitude': 44.5990718, 'Longitude': -72.5002608, 'code': 'VT'}, 'Virginia': {'Latitude': 37.1232245, 'Longitude': -78.4927721, 'code': 'VA'}, 
                      'Washington': {'Latitude': 47.7511, 'Longitude': -120.7401, 'code': 'WA'}, 'District of Columbia': {'Latitude': 38.89379365, 'Longitude': -76.98799757, 'code': 'DC'}, 
                      'West Virginia': {'Latitude': 38.475840600000005, 'Longitude': -80.84084150000001, 'code': 'WV'}, 'Wisconsin': {'Latitude': 44.4308975, 'Longitude': -89.6884637, 'code': 'WI'}, 
                      'Wyoming': {'Latitude': 43.1700264, 'Longitude': -107.56853400000001, 'code': 'WY'}}
  
    def get_state_level_data(self):
        
        #self.state_name_loc()
        cases_df, deaths_df, states_locs = self.cases_deaths[0], self.cases_deaths[1], self.state_info
        states = [x for x in states_locs]
        overall_list = []
        
        for state in states: # Iterate through each state in list to isolate information about that state in the data

            # Get Death Info
            length = len(deaths_df)
            impact_list = []
            overall = [0,0]
            overall_cases = 0
            for i in range(1,len(deaths_df[0])):
                loc = deaths_df[10][i]
                if state not in loc:
                    continue
                deaths = deaths_df[length - 1][i]
                pop = int(deaths_df[11][i])
                if pop == 0:
                    continue
                if deaths == 0:
                    continue
                overall[0] = overall[0] + deaths
                overall[1] = overall[1] + pop

            if overall[1] == 0:
                dpc = 0
            else:
                dpc = float((overall[0])/overall[1]) * 100000
                dpc = round(dpc,3)

            # Get cases info
            length = len(cases_df) # resetting this variable in case there is a mismatch
            impact_list = []
            for i in range(1,len(cases_df[0])):
                loc = cases_df[10][i]
                if state not in loc:
                    continue
                cases = cases_df[length-1][i]
                if cases == 0:
                    continue
                overall_cases = overall_cases + cases

            if overall[1] == 0:
                cpc = 0
            else:
                cpc = float((overall_cases)/overall[1])*100000
                cpc = round(cpc,3)
            lat,long,code = states_locs[state]['Latitude'],states_locs[state]['Longitude'],states_locs[state]['code']
            overall_list.append([state,overall_cases,overall[0],cpc,dpc,overall[1],lat,long,code])
        columns = ["State","Cases","Deaths","Cases_per_capita","Deaths_per_capita","Population","Latitude","Longitude","Code"]
        overall_list.insert(0,columns)
        self.cases_deaths.append(overall_list)
        return
        #return(overall_list)
    
    def get_time_series_state_level_data(self):
        e = enumerate # Assigned function for cleaner code
    
        cases_df, deaths_df, states = self.cases_deaths[0],self.cases_deaths[1],[x for x in self.state_info]

        time_series_list = []
        date_list = ["Population","Date","Date"]
        for x in range(12,len(deaths_df)):
            date_list.append(deaths_df[x][0])
        time_series_list.append(date_list)

        #function_list = [GetFunctions.build_overall_deaths,GetFunctions.build_overall_cpc,GetFunctions.build_overall_dpc]
        #variables_list = [deaths_df,cases_df,deaths_df]

        i1 = 0
        size = len(states)
        for state in states:
            overall_cases, pop = BuildFunctions.build_overall_cases(state,cases_df,deaths_df)
            overall_deaths = BuildFunctions.build_overall_deaths(state,pop,deaths_df)
            overall_cpc = BuildFunctions.build_overall_cpc(state,pop,cases_df)
            overall_dpc = BuildFunctions.build_overall_dpc(state,pop,deaths_df)

            time_series_list.append(overall_cases)
            time_series_list.append(overall_deaths)        
            time_series_list.append(overall_cpc)
            time_series_list.append(overall_dpc)        

            cpd = []
            for i,x in e(time_series_list[-4]):
                if i > 3:
                    cpd.append(x-y)
                elif i == 3:
                    cpd.append(x)
                y = x
            cpd.insert(0,pop)
            cpd.insert(1,state)
            cpd.insert(2,state + " Cases Per Day")
            time_series_list.append(cpd)

            dpd = []
            for i,x in e(time_series_list[-4]):
                if i > 3:
                    dpd.append(x-y)
                elif i == 3:
                    dpd.append(x)
                y = x
            dpd.insert(0,pop)
            dpd.insert(1,state)
            dpd.insert(2,state + " Deaths Per Day")
            time_series_list.append(dpd)

            ma7_c = []
            for i,x in e(cpd):
                if i >= 10:
                    last = cpd[i - 7:i]
                    ma = sum(last)/len(last)
                    ma7_c.append(ma)
                elif i < 3:
                    continue
                elif i < 10:
                    ma7_c.append(0)

                    #ma7_c.append(x)
            ma7_c.insert(0,pop)
            ma7_c.insert(1,state)
            ma7_c.insert(2,state + " New Cases 7 Day Moving Average")
            time_series_list.append(ma7_c)

            ma7_d = []
            for i,x in e(dpd):
                if i >= 10:
                    last = dpd[i - 7:i]
                    ma = sum(last)/len(last)
                    ma7_d.append(ma)
                elif i < 3:
                    continue
                elif i < 10:
                    ma7_d.append(0)

                    #ma7_d.append(x)
            ma7_d.insert(0,pop)
            ma7_d.insert(1,state)
            ma7_d.insert(2,state + " New Deaths 7 Day Moving Average")
            time_series_list.append(ma7_d)

            d2c_ratio = []
            for i,x in e(overall_deaths):
                if i < 3:
                    continue
                else:
                    if overall_cases[i] > 0:
                        calc = x/overall_cases[i]
                    else:
                        calc = 0
                d2c_ratio.append(calc)

            d2c_ratio.insert(0,pop)
            d2c_ratio.insert(1,state)
            d2c_ratio.insert(2,state + " Case Fatality Rate")
            time_series_list.append(d2c_ratio)
            i1 += 1

        new_df = pd.DataFrame(time_series_list)
        new_df = pd.DataFrame.transpose(new_df)
        new_df = new_df.values.tolist()
        self.cases_deaths.append(new_df)
        return
        #new_df.to_csv("Updated Covid Stats.csv",index = False)
        #return(new_df)
    
    def get_time_series_us_data(self):

        cases_df, deaths_df = self.cases_deaths[0],self.cases_deaths[1] 

        time_series_list = []
        date_list = ["Population","Date"]
        for x in range(12,len(deaths_df)):
            date_list.append(deaths_df[x][0])
        time_series_list.append(date_list)

        pop = 0 
        # get cases info
        overall_cases = []
        #time_series_list.append(state)
        for cnt in range(11,len(cases_df)):
            cases = 0         
            for i in range(1,len(cases_df[0])):
                if cnt < 12:
                    pop = pop + int(deaths_df[11][i])
                cases = cases + int(cases_df[cnt][i])
            overall_cases.append(cases)
        overall_cases.insert(0,pop)
        overall_cases.insert(1,"Cases")
        time_series_list.append(overall_cases)

        # get death info
        overall_deaths = []
        for cnt in range(12,len(deaths_df)):
            deaths = 0
            for i in range(1,len(deaths_df[0])):
                deaths = deaths + int(deaths_df[cnt][i])
            overall_deaths.append(deaths)
        overall_deaths.insert(0,pop)
        overall_deaths.insert(1,"Deaths")
        time_series_list.append(overall_deaths)

        i = 0
        cpd = []
        for x in time_series_list[1]:
            if i > 2:
                cpd.append(x-y)
            elif i>1:
                cpd.append(x)
            y = x
            i += 1
        cpd.insert(0,pop)
        cpd.insert(1,"Cases Per Day")
        time_series_list.append(cpd)

        i = 0
        dpd = []
        for x in time_series_list[2]:
            if i > 2:
                dpd.append(x-y)
            elif i>1:
                dpd.append(x)
            y = x
            i += 1
        dpd.insert(0,pop)
        dpd.insert(1,"Deaths Per Day")
        time_series_list.append(dpd)

        overall_cpc = []
        for cnt in range(11,len(cases_df)):
            cpc = 0         
            for i in range(1,len(cases_df[0])):
                cpc = cpc + int(cases_df[cnt][i])
            cpc = (cpc/pop) * 100000
            overall_cpc.append(cpc)
        overall_cpc.insert(0,pop)
        overall_cpc.insert(1,"Cases per 100,000")
        time_series_list.append(overall_cpc)

        # get death info
        overall_dpc = []
        #time_series_list.append(state)
        for cnt in range(12,len(deaths_df)):
            dpc = 0
            for i in range(1,len(deaths_df[0])):
                dpc = dpc + int(deaths_df[cnt][i])
            dpc = (dpc/pop)*100000
            overall_dpc.append(dpc)
        overall_dpc.insert(0,pop)
        overall_dpc.insert(1,"Deaths per 100,000")
        time_series_list.append(overall_dpc)       

        ma7_c = []
        for i,x in enumerate(cpd):
            if i >= 9:
                last = cpd[i - 7:i]
                ma = sum(last)/len(last)
                ma7_c.append(ma)
            elif i < 2:
                continue
            elif i < 9:
                ma7_c.append(0)

                #ma7_c.append(x)
        ma7_c.insert(0,pop)
        ma7_c.insert(1,"New Cases 7 Day Moving Average")
        time_series_list.append(ma7_c)

        ma7_d = []
        for i,x in enumerate(dpd):
            if i >= 9:
                last = dpd[i - 7:i]
                ma = sum(last)/len(last)
                ma7_d.append(ma)
            elif i < 2:
                continue
            elif i < 9:
                ma7_d.append(0)

                #ma7_d.append(x)
        ma7_d.insert(0,pop)
        ma7_d.insert(1,"New Deaths 7 Day Moving Average")
        time_series_list.append(ma7_d)

        d2c_ratio = []
        for i,x in enumerate(overall_deaths):
            if i < 2:
                continue
            else:
                if overall_cases[i] > 0:
                    calc = x/overall_cases[i]
                else:
                    calc = 0
            d2c_ratio.append(calc)

        d2c_ratio.insert(0,pop)
        d2c_ratio.insert(1,"Case Fatality Rate")
        time_series_list.append(d2c_ratio)


        new_df = pd.DataFrame(time_series_list)
        new_df = pd.DataFrame.transpose(new_df)
        new_df = new_df.values.tolist()
        self.cases_deaths.append(new_df)
        return
        #return(new_df)
    
class BuildFunctions():
    
    def build_overall_cases(state,cases_df,deaths_df):
        pop, overall_cases = 0, []
        for _ in range(11,len(cases_df)):
            cases = 0         
            for i in range(0,len(cases_df[0])):
                if state in cases_df[10][i]:
                    if _ < 12:
                        pop = pop + int(deaths_df[11][i])
                    cases = cases + int(cases_df[_][i])
            overall_cases.append(cases)
        overall_cases.insert(0,pop)
        overall_cases.insert(1,state)
        overall_cases.insert(2,state + " Cases")
        return(overall_cases,pop)
    
    def build_overall_deaths(state,pop,deaths_df):
        overall_deaths = []
        for _ in range(12,len(deaths_df)):
            deaths = 0
            for i in range(0,len(deaths_df[0])):
                if state in deaths_df[10][i]:
                    deaths = deaths + int(deaths_df[_][i])
            overall_deaths.append(deaths)
        overall_deaths.insert(0,pop)
        overall_deaths.insert(1,state)
        overall_deaths.insert(2,state + " Deaths")
        return(overall_deaths)
    
    def build_overall_cpc(state,pop,cases_df):
        overall_cpc = []
        for _ in range(11,len(cases_df)):
            cpc = 0         
            for i in range(0,len(cases_df[0])):
                if state in cases_df[10][i]:
                    cpc = cpc + int(cases_df[_][i])
            cpc = (cpc/pop) * 100000
            overall_cpc.append(cpc)
        overall_cpc.insert(0,pop)
        overall_cpc.insert(1,state)
        overall_cpc.insert(2,state + " Cases per 100,000")
        return(overall_cpc)
    
    def build_overall_dpc(state,pop,deaths_df):
        overall_dpc = []
        for _ in range(12,len(deaths_df)):
            dpc = 0
            for i in range(0,len(deaths_df[0])):
                if state in deaths_df[10][i]:
                    dpc = dpc + int(deaths_df[_][i])
            dpc = (dpc/pop)*100000
            overall_dpc.append(dpc)
        overall_dpc.insert(0,pop)
        overall_dpc.insert(1,state)
        overall_dpc.insert(2,state + " Deaths per 100,000")
        return(overall_dpc)
    
class DataVisualizations():
    
    def __init__(self, data):
        self.data = data
        self.last = Initialize.ret_last_updated()
        
    def visualize_geo(self):
        print("starting")
        df = self.data
        df['text'] = "Cases Per 100K<br>" + df['State']
        limits = [(0,len(df))]
        colors = ["royalblue"]
        scale = min([x for x in df['Cases_per_capita'] if x > 0])

        fig = go.Figure()

        for i in range(1):
            lim = limits[i]
            df_sub = df[lim[0]:lim[1]]
            fig.add_trace(go.Scattergeo(
                locationmode = 'USA-states',
                lon = df_sub['Longitude'],
                lat = df_sub['Latitude'],
                text = df_sub['text'],
                marker = dict(
                    size = (df_sub['Cases_per_capita']/scale) * 2,
                    color = colors[i],
                    line_color='rgb(40,40,40)',
                    line_width=0.5,
                    sizemode = 'area'
                ),
                name = '{0} - {1}'.format(lim[0],lim[1])))
       
        fig.update_layout(
                title_text = 'US COVID Cases',
                showlegend = False,
                geo = dict(
                    scope = 'usa',
                    landcolor = 'rgb(217, 217, 217)',
                )
            )
        #fig.show()
        print("Checkpoint C")
        fig.write_html(r"C:\Users\jedba\Desktop\Python\Jeds_Programs\COVID_Data\COVID_Case_Map.html")
        print("Map Written")
        
    def visualize_geo_choro(self):
        
        df = self.data
        df['text'] = df['State'] + "<br>Cases Per 100K<br>" + round(df['Cases_per_capita'],2).astype(str)
        #Try '{:,.2f}'
        
        fig = go.Figure(data = go.Choropleth(
            locations = df['Code'],
            z = df['Cases_per_capita'],
            locationmode = 'USA-states',
            colorscale = 'rdylgn_r', # _r is colorscale reversed
            colorbar_title = 'Cases Per 100K',
            hovertext = df['text']
        ))        
                  
        fig.update_layout(
                title_text = 'US COVID Cases<br>Data: ' + self.last[0] +'<br>Cases Per 100K',
                showlegend = False,
                geo = dict(
                    scope = 'usa',
                )
            )
        
        fig.write_html(r"C:\Users\jedba\Desktop\Python\Jeds_Programs\COVID_Data\COVID_Case_Map.html")
        print("Map Written")
        
    def plot_data(self,locale):
        data_cols = [x for x in self.data.columns if locale in x or x == 'Date']
        dataset = self.data[[x for x in data_cols]]
        
        try:
            dates = dataset.Date.values.tolist()
        except:   
            dataset.columns = [x for x in dataset.iloc[1].values]
            dataset = dataset.drop(0)
            dataset = dataset.drop(1)
            dates = dataset.Date.values.tolist()
        sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})

        df1 = dataset
        variables = [x for x in df1.columns[1:]]
        n=len(variables)
        fig,ax = plt.subplots(n,1, figsize=(20,n*5), sharex=True)
        for i in range(n):
            plt.sca(ax[i])
            col = variables[i]
            print(col)
            g = sns.barplot(x = dataset["Date"], y = dataset[col])
            g.xaxis.set_major_locator(ticker.MultipleLocator(12))
            g.xaxis.set_major_formatter(dt.DateFormatter("%d-%b"))
            g.xaxis.grid(True)
            if max(dataset[col]) < 1:
                g.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.0%}'))
            else:
                g.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
            g.set(ylabel = None)
            fig.autofmt_xdate()
            plt.title(col,{'fontsize': 18})
        name_specs = locale + " " + str(date.datetime.now()).split()[0]
        save_path = (r"Graphs/" + "Covid-Graph " + name_specs)
        plt.savefig(save_path)

        return(name_specs + '.png')
    
    def interactive_plot(self,data_choice):
        fig = px.bar(self.data, x='Date', y=data_choice,
        hover_data=['Date', 'Cases','Deaths'], color='New Cases 7 Day Moving Average',
        labels={'US COVID Data':'Data 1'}, height=400)
        fig.update_layout(title={
                                'text': f'{locale} - {data_choice}',
                                'y':0.9,
                                'x':0.5,
                                'xanchor': 'center',
                                'yanchor': 'top'})
        fig.write_html(r"C:\Users\jedba\Desktop\Python\Jeds_Programs\COVID_Data\COVID_US_Chart.html")
    
    def combine_graphs(self,sources):
        im_for_size = Image.open(r"Graphs/" + "Covid-Graph " + sources[0])
        combined = Image.new(im_for_size.mode,(im_for_size.width * len(sources),im_for_size.height))
        for i,x in enumerate(sources):
            save_path = (r"Graphs/" + "Covid-Graph " + x)
            img = Image.open(save_path)
            combined.paste(img,(i * img.width,0))
        return(combined)
    
    ############## GUI Python Control #####################
    #######################################################

class HomeScreen(Screen):
    
    def on_enter(self):
        self.pbar.pos_hint = {'x':.25, 'top': -10}
        threading.Thread(target = self.get_initial).start()
   
    def reload_screen(self):
        threading.Thread(target = self.get_initial).start()
     
    def update_thread(self):
        threading.Thread(target = self.update_data).start()
        
    def update_labels(self,string1,progress):
        self.pbar.value = progress
        if string1 != None:
            self.statuslabel2.text = string1
        return

    def get_initial(self):
        self.last = Initialize.ret_last_updated()
        self.statuslabel1.text = f"\n Data Through: {self.last[0]}\n US Cases: {self.last[1]}\n US Deaths: {self.last[2]}"
   
    def update_data(self): 
        
        start = time.perf_counter()
        label_list = ['Downloading Data...','DONE\n','Consolidating State Level Data...','DONE\n','Consolidating Time Series State Level Data...','DONE\n',
                      'Consolidating Time Series US Data...','DONE\n','Saving Data...','DONE\n','Performance Recording...','DONE\nUpdate Completed']
        self.pbar.pos_hint = {'x':.25, 'top': 1.08}

        self.update_labels(label_list[0],14.3)
        UpdateData().start_update()
        self.update_labels("".join(x for x in label_list[:1]),28.59)

        GetFunctions().get_state_level_data()
        self.update_labels("".join(x for x in label_list[:3]),42.8)

        GetFunctions().get_time_series_state_level_data()
        self.update_labels("".join(x for x in label_list[:5]),57.1)

        GetFunctions().get_time_series_us_data()
        self.update_labels("".join(x for x in label_list[:7]),71.4)

        UpdateData().save_compiled_data_to_csv()
        self.update_labels("".join(x for x in label_list[:9]),85.7)
        
        load_time = time.perf_counter() - start
        Initialize.load_times.append(["Updating",load_time])
        if load_time > 60:
            load_time = str(round(load_time/60,2)) + " minutes"
        else:
            load_time = str(round(load_time,2)) + " seconds"
        self.update_labels("".join(x for x in label_list) + "\nTime Elapsed: " + load_time,100)
        self.statuslabel1.text = f"\n Data Through: {self.last[0]}\n US Cases: {self.last[1]}\n US Deaths: {self.last[2]}\n - Data Loaded -"

class VisualizationScreen(Screen):
    # This is the Python part of the Visualization Screen 
    # which holds all of the data visualization options
    # in one screen for simplicity.
    
    def on_enter(self):
        self.spinner_defaults = {'ls':'Load Data', 'vs': 'Visualize Data', 'vss': 'Graph Type',
                                 'dfs': 'Data Focus', 'lcs': 'Specify Locale'}
                              
        self.thread_manager(self.get_initial)
        self.data_is_loaded = False
        pass
    
    ############### Thread Manager ########################
    #######################################################
    
    def thread_manager(self,option):
        threading.Thread(target = option).start()
        
    ############### Base Functions ########################
    #######################################################
    
    def get_initial(self):
        self.last, self.favorites, self.fav_loaded = Initialize.ret_variables()
        self.average_load_time = Initialize.ret_average_load_time()
        try:
            self.is_data_loaded = self.Loader.ret_state_of_data()
            self.statuslabel1b.text = f"\n Data Through: {self.last[0]}\n - Data Loaded - \n Average Load Time: {self.average_load_time} seconds"
        except:
            self.statuslabel1b.text = f"\n Data Through: {self.last[0]}\n Please Load Data\n Average Load Time: {self.average_load_time} seconds"
            
    def return_data(self):
        self.statuslabel1b.text = f"\n Data Through: {self.last[0]}\n Loading Data...\n Average Load Time: {self.average_load_time} seconds"
            
        self.Loader.load_data()
        self.data = self.Loader.return_data(self.load_spinner.text)
        self.Visualizer = DataVisualizations(self.data) # Initialize Visualizations Class
        if self.load_spinner.text in ["Time Series SL Data","Time Series US Data"]:
            self.data_spinner_init()
        self.statuslabel1b.text = f"\n Data Through: {self.last[0]}\n - Data Loaded - \n Average Load Time: {self.average_load_time} seconds"        
        
    def update_labels(self,string1,progress):
        if progress == None:
            self.pbar2.value = 0
            self.pbar2.pos_hint = {'x':.25, 'top': -10}
        else:
            self.pbar2.value = progress
        if string1 != None:
            self.statuslabelviz.text = string1
        return
    
    ############### Callback Functions ####################
    #######################################################
    
    def load_spinner_callback(self):
        self.reset_spinner([self.viz_spinner,self.viz_style_spinner,self.data_focus_spinner,self.locale_spinner])
        try:
           # self.reset_spinner([self.viz_spinner,self.viz_style_spinner,self.data_focus_spinner,self.locale_spinner])
            self.Loader = LoadData(self.load_spinner.text) # Reinitialize the Loader Class when the data changes
            self.thread_manager(self.return_data)
            self.viz_spinner.pos_hint = {'x': .4, 'y': .68}
        except:
            self.error_handling(message = 'Error Loading Data')
        #dfso = [x for x in self.data.columns[1:]]
    
    def viz_spinner_callback(self):
        vtso = ['Static Graphs','Interactive Graphs','Intensity Map','Data Point Map','Tables'] # vtso = viz_type_spinner_options
        vs = self.viz_spinner.text
        if vs == vtso[2]:
            self.thread_manager(self.create_choropleth_map)
            self.reset_spinner([self.viz_style_spinner,self.data_focus_spinner])
        elif vs in vtso[0:2]:
            self.viz_style_spinner.pos_hint = {'x': .4, 'y': .61}  
        elif vs in vtso[-2:]:
            self.statuslabelviz.text = f'{vs} is not yet functional'
    
    def viz_style_spinner_callback(self):
        vsso = ['Column','Line','Scatterplot','Heatmap']  # vsso = viz_style_spinner_options
        vs = self.viz_spinner.text
        vss = self.viz_style_spinner.text
        ls = self.load_spinner.text
        if vss == vsso[0]:
            if vs == 'Static Graphs':
                self.thread_manager(self.graph_favorites)
            if vs == 'Interactive Graphs':
                self.data_focus_spinner.pos_hint = {'x': .4, 'y': .54}
                self.data_focus_spinner.values = [x for x in self.data.columns[1:]]
    
    def data_focus_spinner_callback(self):
        if self.load_spinner.text == 'Time Series State Level':
            self.locale_spinner.pos_hint = {'x': .4, 'y': .47}
            self.locale_spinner.values = [x for x in self.data.columns]
    
    def locale_choice_spinner_callback(self):
        self.thread_manager(self.create_interactive_plot,self.locale_spinner.text)
    
    def error_handling(self,message):
        self.statuslabelviz.text = message
        
    def reset_spinner(self,spinner_id):
        for id in spinner_id:
            print(str(id))
            id.pos_hint = {'x': .4, 'y': -10}   
            #id.text = self.spinner_defaults[str(id)]

    def data_spinner_init(self):
        self.data_focus_spinner.pos_hint = {'x': .4, 'y': .54}
        self.data_focus_spinner.values = [x for x in self.data.columns[1:]]
        
    def focus_data(self):
        print(self.data_focus_spinner.text)
        
    ############### Visualization Initiators ##############
    #######################################################
    
    def create_interactive_plot(self):
        self.statuslabel1b.text = f"\n Data Through: {self.last[0]}\n - Data Loaded - \n Average Load Time: {self.average_load_time} seconds\n * Creating Interactive Plot *"  
        self.Visualizer.interactive_plot(self.data_focus_spinner.text)
        self.statuslabel1b.text = f"\n Data Through: {self.last[0]}\n - Data Loaded - \n Average Load Time: {self.average_load_time} seconds\n * Interactive Plot Finished *"  
    
    def create_choropleth_map(self):
        self.statuslabel1b.text = f"\n Data Through: {self.last[0]}\n - Data Loaded - \n Average Load Time: {self.average_load_time} seconds\n * Map Loading... *"  
        self.Visualizer.visualize_geo_choro()
        self.statuslabel1b.text = f"\n Data Through: {self.last[0]}\n - Data Loaded - \n Average Load Time: {self.average_load_time} seconds\n * Map Succesfully Loaded *"   
    
    def graph_favorites(self):
        self.pbar2.pos_hint = {'x':.25, 'top': 1.08}
        self.statuslabel1b.text = f"\n Data Through: {self.last[0]}\n - Data Loaded - \n Average Load Time: {self.average_load_time} seconds\n * Graphing Favorited Locations *"  
        self.toptenlabel.text = '\nGraphing Favorites: \n' + "\n".join(x + " " for x in self.favorites)
        returned_graphs = []
        for i,state in enumerate(self.favorites):
            self.update_labels(f'Graphing {state}: {i+1} of {len(self.favorites)}',((i+1)/len(self.favorites))*100)
            returned_graphs.append(self.Visualizer.plot_data(state))
        self.update_labels(f'{len(self.favorites)} graphs have been built - now compiling',None)
        combined = self.Visualizer.combine_graphs(returned_graphs)    
        save_path = (r"Graphs/" + "Covid-Graph " + "Favorites" + " " + str(date.datetime.now()).split()[0] + ".png")
        combined.save(save_path)
        self.statuslabel1b.text = f"\n Data Through: {self.last[0]}\n - Data Loaded - \n Average Load Time: {self.average_load_time} seconds\n * Favorites Graph Completed *"  
 
sm = ScreenManager(transition=WipeTransition())
sm.add_widget(HomeScreen(name = 'homescreen'))  
sm.add_widget(VisualizationScreen(name = 'vizscreen'))  

class covidgui(App):
    
    def build(self):
        self.title = "COVID-19      Data Extraction & Visualization"
        Window.bind(on_request_close = self.on_request_close)
        return sm
    
    def on_request_close(self,instance):
        saving_load_times = pd.DataFrame(Initialize.load_times, columns = ["Method","Time"])
        saving_load_times.to_csv("load_times.csv", index = False)
        self.stop

try:
    if __name__=='__main__':
        covidgui().run()
except:
    print("This program has not been fully completed and tested. Certain paths, such as the one you just took, will result in failure.")
    self.stop