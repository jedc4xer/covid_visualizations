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

from concurrent.futures import ThreadPoolExecutor as Executor

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime as date

import threading
import time
import winsound

Builder.load_file("covidgui.kv")

# Map
# 1. Is there any data?
# 2. When was the data updated last?
# 3. Does the file need to be updated?
# 4. Have any favorites been saved? What are they?
# 5. Display Information

# Initialize Environment Variables
class InitInfo:
    
    def __init__(self):
        try: 
            self.last_date = pd.read_csv("Updated_Through.txt").columns[0]
        except:
            self.last_date = "Unknown"
        
        try:
            self.favorites = pd.read_csv("Favorites.txt").columns
            self.fav_loaded = "True"
        except:
            self.favorites = "Unknown"
            self.fav_loaded = "False"
            
        try:
            self.load_times_main = pd.read_csv("load_times.csv")
            self.load_times = self.load_times_main.values.tolist()
            self.load_times_actual = self.load_times_main.Time      
        except:
            self.load_times = []
            
    def ret_last_updated(self):
        return(self.last_date)
        
    def ret_variables(self):
        return(self.last_date,self.favorites,self.fav_loaded)
    
    def ret_average_load_time(self):
        print(self.load_times_actual)
        return round(self.load_times_actual.mean(),2) if len(self.load_times) > 2 else ""
    
    def ret_load_times(self):
        return self.load_times
    
class SaveAndClose:
    
    def __init__(self):
        self.load_times = LoadData().return_state_level().load_times
        
    def save_load_times(self):
        self.load_times = pd.DataFrame(self.load_times)
        self.load_times.to_csv("load_times.csv",index = False)
        
class LoadData():
    
    def __init__(self):
        self.start = True
        LoadData.load_data.is_loaded = False
        pass
    
    def load_data(self):
        LoadData.load_data.start = time.perf_counter()
        try:
            #LoadData.load_data.covid_data = pd.read_excel("US COVID Data.xlsx",sheet_name = ["State Level Data","Time Series SL Data",
                                                                                                   #"Time Series US Data"])
            LoadData.load_data.covid_data = pd.read_csv("StateLevelData.csv")
            LoadData.load_data.is_loaded = True
        except:
            LoadData.load_data.is_loaded = False
            
    def ret_state_of_data(self):
        return LoadData.load_data.is_loaded
            
    def return_state_level(self):
        #self.data_for_display = LoadData.load_data.state_level_data["State Level Data"].sort_values("Cases_per_capita", ascending = False)[['State',
                                                                                                          # 'Cases_per_capita',
                                                                                                          # 'Deaths_per_capita','Population',
                                                                                                         #  'Longitude', 'Latitude']]
        self.data_for_display = LoadData.load_data.covid_data.sort_values("Cases_per_capita", ascending = False)[['State',
                                                                                                          'Cases_per_capita',
                                                                                                          'Deaths_per_capita','Population',
                                                                                                          'Longitude', 'Latitude']]
        print(self.data_for_display)
        load_time = time.perf_counter() - LoadData.load_data.start
        load_times = InitInfo().ret_load_times()
        load_times.append(["Loading",load_time])
        print(load_times)
        load_times = pd.DataFrame(load_times,columns = ["Method","Time"])
        load_times.to_csv("load_times.csv", index = False)
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
            headers = [x for x in each_list[0]]
            each_list = pd.DataFrame(each_list,columns = [x for x in headers])
            if i == 0:
                last_date = each_list['UID'].values.tolist()[-1]
            each_list.to_csv(tabs[i] + '.csv', index = False)
        updated_date_file = open("Updated_Through.txt","w+")
        updated_date_file.write(last_date)
        print("Finished with CSV Files...")
        
class GetFunctions():
    
    def __init__(self):
        self.cases_deaths = UpdateData().return_data()
        #self.state_info = None
    
   # def state_name_loc(self): # hardcoded dictionary built from geopy.geocoders
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
        #return
    
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
            cpd.insert(2,"Cases Per Day")
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
            dpd.insert(2,"Deaths Per Day")
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
            ma7_c.insert(2,"New Cases 7 Day Moving Average")
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
            ma7_d.insert(2,"New Deaths 7 Day Moving Average")
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
            d2c_ratio.insert(2,"Case Fatality Rate")
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
        overall_cases.insert(2,"Cases")
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
        overall_deaths.insert(2,"Deaths")
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
        overall_cpc.insert(2,"Cases per 100,000")
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
        overall_dpc.insert(2,"Deaths per 100,000")
        return(overall_dpc)
   
    
        
        
    # Save Compiled Data to Excel File
    def save_compiled_data(cases_deaths):
        writer = pd.ExcelWriter(program_path + "US COVID Data.xlsx", engine='xlsxwriter')
        tabs = ["US Cases","US Deaths","State Level Data","Time Series SL Data","Time Series US Data"]
        compiled_dict_for_quick_load = {}
        for i,each_list in enumerate(cases_deaths):
            print("Compiling",tabs[i])
            headers = [x for x in each_list[0]]
            each_list = pd.DataFrame(each_list,columns = [x for x in headers])
            if i < 2:
                each_list.to_excel(writer, sheet_name = tabs[i],index = False)#,header = None)
                compiled_dict_for_quick_load[tabs[i]] = each_list
            elif i == 2:
                each_list.to_excel(writer, sheet_name = tabs[i],index = False)
                compiled_dict_for_quick_load[tabs[i]] = each_list
            else:
                each_list.to_excel(writer, sheet_name = tabs[i],index = False)#,header = None)
                compiled_dict_for_quick_load[tabs[i]] = each_list

        writer.save()
        
        UpdateData.save_compiled_data.compiled_dict_for_quick_load = compiled_dict_for_quick_load
        UpdateData.save_compiled_data.sheets = [x for x in compiled_dict_for_quick_load.keys()]
        last_date = compiled_dict_for_quick_load[sheets[0]]["UID"].values.tolist()[-1]
        updated_date_file = open(program_path + "Updated_Through.txt","w+")
        updated_date_file.write(last_date)
        print("Finished with Excel File...")
        return(last_date)

############END UPDATE BLOCK#####################
#################################################
#################################################

    
class DataVisualizations():
    
    def __init__(self, data):
        self.data = data
        self.last_date = InitInfo().ret_last_updated()
    
    def visualize_geo(self):
        print("starting")
        df = self.data
        df['text'] = df['State'] + "<br>Cases Per Capita<br>" + (round(df['Cases_per_capita'],2).astype(str))
        limits = [(0,len(df))]
        print(limits)
        colors = ["royalblue"]
        scale = min([x for x in df['Cases_per_capita'] if x > 0])

        fig = go.Figure()

        for i in range(1):
            lim = limits[i]
            df_sub = df[lim[0]:lim[1]]
            print(df_sub)
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
        print("starting")
        df = self.data
        df['text'] = df['State'] + "<br>Cases Per Capita<br>" + (round(df['Cases_per_capita'],2).astype(str))
        
        fig = go.Figure(data = go.Choropleth(
            locations = df['code'],
            z = df['Cases_per_capita'],
            locationmode = 'USA-states',
            colorscale = 'rdylgn_r',
            colorbar_title = 'Cases Per Capita',
            hovertext = df['text']
        ))        
                  
        fig.update_layout(
                title_text = 'US COVID Cases<br>Data: ' + self.last_date +'<br>Cases Per Capita',
                showlegend = False,
                geo = dict(
                    scope = 'usa',
                )
            )
        
        print("Checkpoint C")
        fig.write_html(r"C:\Users\jedba\Desktop\Python\Jeds_Programs\COVID_Data\COVID_Case_Map.html")
        print("Map Written")
# GUI Scripting ------------
# --------------------------
        
class HomeScreen(Screen):
    
    def on_enter(self):
        threading.Thread(target = self.get_initial).start()
        
    def load_thread(self):
        threading.Thread(target = self.return_state_level).start()
        
    def reload_screen(self):
        threading.Thread(target = self.get_initial).start()
        
    def geo_viz_thread(self):
        threading.Thread(target = self.geo_viz).start()
        
    def update_thread(self):
        threading.Thread(target = self.update_data).start()

    def get_initial(self):
        print("\n\nHere again...\n\n")
        self.last_date, self.favorites, self.fav_loaded = InitInfo().ret_variables()
        self.average_load_time = InitInfo().ret_average_load_time()
        self.is_data_loaded = LoadData().ret_state_of_data()
        if not self.is_data_loaded:
            print("Checkpoint A")
            self.statuslabel1.text = f"\n\n\n Data Through: {self.last_date}\n Please Load Data\n Average Load Time: {self.average_load_time} seconds"
            self.loadbutton.x_pos = {'x': .4, 'y': .82}
            self.updatebutton.x_pos = {'x': .4, 'y': .75}
            self.graphbutton.pos_hint = {'x': -10, 'y': .68} 
        else:
            print("Checkpoint B")
            self.statuslabel1.text = f"\n\n\n Data Through: {self.last_date}\n - Data Loaded - \n Average Load Time: {self.average_load_time} seconds"
            self.loadbutton.x_pos = {'x': .4, 'y': .82}
            self.updatebutton.x_pos = {'x': .4, 'y': .75}
            self.graphbutton.pos_hint = {'x': -10, 'y': .68}
            
    def return_state_level(self):
        self.statuslabel1.text = f"\n\n\n Data Through: {self.last_date}\n Loading Data...\n Average Load Time: {self.average_load_time} seconds"
        self.loadbutton.x_pos = {'x': -10, 'y': .82}
        self.updatebutton.x_pos = {'x': -10, 'y': .75}
        self.graphbutton.pos_hint = {'x': -10, 'y': .68}
            
        LoadData().load_data()
        self.sl_data = LoadData().return_state_level()
        self.statuslabel1.text = f"\n\n\n Data Through: {self.last_date}\n - Data Loaded - \n Average Load Time: {self.average_load_time} seconds"
        self.toptenlabel.text = "\n\n\nCases Per Capita Top 10  \n" + "\n".join(x + " " for x in self.sl_data["State"].head(10))
        self.loadbutton.x_pos = {'x': -10, 'y': .82}
        self.updatebutton.x_pos = {'x': .4, 'y': .75}
        self.graphbutton.pos_hint = {'x': .4, 'y': .68}        
        
    def geo_viz(self):
        DataVisualizations(LoadData.load_data.covid_data).visualize_geo_choro()
   
    def update_data(self): 
        
        start = time.perf_counter()
        #test_function()
        #MainScreen1.update_labels(self,"Gathering and Calculating Data","Getting Updated Data from Database",10)
        UpdateData().start_update()
        print('Passed 1')
        #MainScreen1.update_labels(self,None,"Calculating State Level Data",20)
        GetFunctions().get_state_level_data()
        print('Passed 2')
        #MainScreen1.update_labels(self,None,"Calculating Time Series State Level Data",30)
        GetFunctions().get_time_series_state_level_data()
        print('Passed 3')
        #MainScreen1.update_labels(self,None,"Calculating Time Series US Data",40)
        GetFunctions().get_time_series_us_data()
        print('Passed 4')
        
        UpdateData().save_compiled_data_to_csv()
        print('Passed 5')
        #MainScreen1.update_labels(self,"Update Completed",None,93)
        
        load_time = time.perf_counter() - start
        if load_time > 60:
            load_time = str(round(load_time/60,2)) + " minutes"
        else:
            load_time = str(round(load_time,2)) + " seconds"
            
        self.last_update.text = "\n Last Updated: " + str(last_date)
        self.label2.text = "Excel File has been updated in " + load_time
        
        #self.load_method()
        duration = 1000  # milliseconds
        freq = 185 # Hz
        winsound.Beep(freq, duration)
        
sm = ScreenManager(transition=WipeTransition())
sm.add_widget(HomeScreen(name = 'homescreen'))  
    
class covidgui(App):
    
    def build(self):
        self.title = "COVID-19      Data Extraction & Visualization"
        return sm
    
if __name__=='__main__':
    covidgui().run()
    
    
    
    
# Helpful printout buffer
#buffer = " "
#while len(buffer) + len(str(overall[0])) < len(state) + len("Deaths") - 1:
#buffer = buffer + " "