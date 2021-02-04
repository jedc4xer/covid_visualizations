from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, WipeTransition
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.graphics import *
from matplotlib import dates as dt
from geopy.geocoders import Nominatim
from kivy.uix.progressbar import ProgressBar

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import seaborn as sns
import datetime as date
import requests
import time
import winsound
import threading

Builder.load_file('covidgui.kv')
            
last_date,load_time = False,False # notifies Kivy Class that data has not been loaded

# Load Existing Data from Excel File
def load_database():
    try:
        covid_data = pd.read_excel(r"C://Users/jedba/Desktop/Python/COVID Data/COVID Datasets/US COVID Data.xlsx",None)
        sheets = [x for x in covid_data.keys()]
        last_date = covid_data[sheets[0]]["UID"].values.tolist()[-1] # variable to print to screen label showing the last date for which data is available
    except:
        covid_data,sheets,last_date = False,False,"Failed"
        print("Load Failed")
    return(covid_data,sheets,last_date)

# update data MAIN FUNCTION
def get_updated_data():
    urls = ["https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv",
           "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"]
    tabs = ["US Cases","US Deaths"]
    cases_deaths = []
    for i,url in enumerate(urls):
        print("Updating",tabs[i],"...")
        df = pd.read_csv(url)
        df = pd.DataFrame.transpose(df)
        df.reset_index(inplace = True)
        cases_deaths.append(df.values.tolist())
    return(cases_deaths)
        
def save_compiled_data(cases_deaths):
    writer = pd.ExcelWriter(r"C://Users/jedba/Desktop/Python/COVID Data/COVID Datasets/US COVID Data.xlsx", engine='xlsxwriter')
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
    
    sheets = [x for x in compiled_dict_for_quick_load.keys()]
    last_date = compiled_dict_for_quick_load[sheets[0]]["UID"].values.tolist()[-1]
    updated_date_file = open(r"C://Users/jedba/Desktop/Python/COVID Data/COVID Datasets/Updated_Through.txt","w+")
    updated_date_file.write(last_date)
    print("Finished with Excel File...")
    return(compiled_dict_for_quick_load,sheets,last_date)

def get_geo_data(state):
    
    locator = Nominatim(user_agent='jdryer1@asu.edu')
    try:
        location = locator.geocode(state)
        lat = location.latitude
        long = location.longitude
    except:
        lat,long = "Error","Error"
    time.sleep(2)
    return(lat,long)  

def get_state_level_data(cases_deaths):
    
    cases_df, deaths_df,states = cases_deaths[0],cases_deaths[1],get_state_names()

    overall_list = []
    for state in states:
        # get death info
        length = len(deaths_df)
        impact_list = []
        overall = [0,0]
        overall_cases = 0
        for i in range(1,len(deaths_df[0])):
            loc = deaths_df[10][i]
            if state not in loc:
                continue
            deaths = deaths_df[length-1][i]
            pop = int(deaths_df[11][i])
            if pop == 0:
                continue
            if deaths == 0:
                continue
            overall[0] = overall[0]+deaths
            overall[1] = overall[1]+pop
        
        if overall[1] == 0:
            dpc = 0
        else:
            dpc = float((overall[0])/overall[1])*100000
            dpc = round(dpc,3)
        buffer = " "
        while len(buffer) + len(str(overall[0])) < len(state)+len("Deaths")-1:
            buffer = buffer + " "
            
        # get cases info
        length = len(cases_df)
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
        lat,long = get_geo_data(state)
        overall_list.append([state,overall_cases,overall[0],cpc,dpc,overall[1],lat,long])
    columns = ["State","Cases","Deaths","Cases_per_capita","Deaths_per_capita","Population","Latitude","Longitude"]
    overall_list.insert(0,columns)
    return(overall_list)

def get_time_series_state_level_data(cases_deaths):
    
    cases_df, deaths_df,states = cases_deaths[0],cases_deaths[1],get_state_names()

    time_series_list = []
    date_list = ["Population","Date","Date"]
    for x in range(12,len(deaths_df)):
        date_list.append(deaths_df[x][0])
    time_series_list.append(date_list)
    
    i1 = 0
    size = len(states)
    for state in states:
        pop = 0 
        # get cases info
        overall_cases = []
        #time_series_list.append(state)
        for cnt in range(11,len(cases_df)):
            cases = 0         
            for i in range(0,len(cases_df[0])):
                if state in cases_df[10][i]:
                    if cnt < 12:
                        pop = pop + int(deaths_df[11][i])
                    cases = cases + int(cases_df[cnt][i])
            overall_cases.append(cases)
        overall_cases.insert(0,pop)
        overall_cases.insert(1,state)
        overall_cases.insert(2,"Cases")
        time_series_list.append(overall_cases)
        
        # get death info
        overall_deaths = []
        #time_series_list.append(state)
        for cnt in range(12,len(deaths_df)):
            deaths = 0
            for i in range(0,len(deaths_df[0])):
                if state in deaths_df[10][i]:
                    deaths = deaths + int(deaths_df[cnt][i])
            overall_deaths.append(deaths)
        overall_deaths.insert(0,pop)
        overall_deaths.insert(1,state)
        overall_deaths.insert(2,"Deaths")
        time_series_list.append(overall_deaths)
        
        overall_cpc = []
        #time_series_list.append(state)
        for cnt in range(11,len(cases_df)):
            cpc = 0         
            for i in range(0,len(cases_df[0])):
                if state in cases_df[10][i]:
                    cpc = cpc + int(cases_df[cnt][i])
            cpc = (cpc/pop)*100000
            overall_cpc.append(cpc)
        overall_cpc.insert(0,pop)
        overall_cpc.insert(1,state)
        overall_cpc.insert(2,"Cases per 100,000")
        time_series_list.append(overall_cpc)
        
        # get death info
        overall_dpc = []
        #time_series_list.append(state)
        for cnt in range(12,len(deaths_df)):
            dpc = 0
            for i in range(0,len(deaths_df[0])):
                if state in deaths_df[10][i]:
                    dpc = dpc + int(deaths_df[cnt][i])
            dpc = (dpc/pop)*100000
            overall_dpc.append(dpc)
        overall_dpc.insert(0,pop)
        overall_dpc.insert(1,state)
        overall_dpc.insert(2,"Deaths per 100,000")
        time_series_list.append(overall_dpc)        
        
        cpd = []
        for i,x in enumerate(time_series_list[-4]):
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
        for i,x in enumerate(time_series_list[-4]):
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
        for i,x in enumerate(cpd):
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
        for i,x in enumerate(dpd):
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
        for i,x in enumerate(overall_deaths):
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
    #new_df.to_csv("Updated Covid Stats.csv",index = False)
    return(new_df)

def get_time_series_us_data(cases_deaths):
    
    cases_df, deaths_df = cases_deaths[0],cases_deaths[1]
    
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
        cpc = (cpc/pop)*100000
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
    return(new_df)

def get_state_names():
    states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia',
              'Guam', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
              'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
              'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Northern Mariana Islands', 'Ohio', 'Oklahoma',
              'Oregon', 'Pennsylvania','Puerto Rico', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas',
              'Virgin Islands', 'Utah', 'Vermont', 'Virginia', 'Washington', 'District of Columbia', 'West Virginia', 'Wisconsin', 'Wyoming']
    return(states)

def plot_data(dataset,locale):
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
    fig,ax = plt.subplots(n,1, figsize=(20,n*5), sharex=False)
    for i in range(n):
        plt.sca(ax[i])
        col = variables[i]
        print(col)
        g = sns.barplot(x = dataset["Date"], y = dataset[col])
        g.xaxis.set_major_locator(ticker.MultipleLocator(12))
        g.xaxis.set_major_formatter(dt.DateFormatter("%d-%b"))
        if max(dataset[col]) < 1:
            g.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.0%}'))
        else:
            g.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        g.set(ylabel = None)
        g.set(xlabel = None)
        fig.autofmt_xdate()
        plt.title(locale + " " + col,{'fontsize': 18})
    file_name = (r"C://Users/jedba/Desktop/Python/COVID Data/US Visualizations/Covid-Graph " + locale + " " + str(date.datetime.now()).split()[0])
    plt.savefig(file_name)    
    return

def isolate_state_from_time_series(state):
    state_level_dataset = covid_data["Time Series SL Data"]
    state_level_dataset.reset_index(inplace = True)
    state_level_dataset.columns = [x for x in state_level_dataset.iloc[1].values]
    state_level_dataset = state_level_dataset.drop(0)
    state_level_dataset = state_level_dataset.drop(1)
    return(pd.concat([state_level_dataset["Date"],state_level_dataset[state]],axis = 1))

# ******************* GUI CONTROL *********************************
# *****************************************************************
class MainScreen1(Screen):
    label1 = ObjectProperty(None)
    label2 = ObjectProperty(None)
    button1 = ObjectProperty(None)
    button3 = ObjectProperty(None)
    
    def on_enter(self):
        global covid_data,sheets,last_date,load_time
        
        if load_time:
            if last_date == "Failed":
                self.button1.text = "Unavailable"
                self.label1.text = "Loading Failed"
                self.label2.text = "Check the source file"
            else:
                self.button1.text = "Reload Data"
                self.label1.text = "Updated thru " + str(last_date)
                self.label2.text = str(load_time) + " to load data"
        else:
            try:
                last_date = pd.read_csv(r"C://Users/jedba/Desktop/Python/COVID Data/COVID Datasets/Updated_Through.txt")
                last_date = last_date.columns[0]
            except:
                last_date = "Unknown"
            self.button1.text = "Load Data"
            self.label1.text = "No Data Loaded...Data has been updated through " + str(last_date)
            self.label2.text = "Please Load or Update the Data"
               
    def btn1_call(instance):
        global covid_data,sheets,last_date,load_time
        start = time.perf_counter()
        covid_data,sheets,last_date = load_database()
        duration = 1000  # milliseconds
        freq = 185 # Hz
        winsound.Beep(freq, duration)
        load_time = time.perf_counter() - start
        if load_time > 60:
            load_time = str(round(load_time/60,2)) + " minutes"
        else:
            load_time = str(round(load_time,2)) + " seconds"
            
    def update_button1(self):
        threading.Thread(target=self.update_data).start()
            
    def update_labels(self,string1,string2,progress):
        self.pbar.value = progress
        if string1 != None:
            self.label1.text = string1
        if string2 != None:
            self.label2.text = string2
        return
        
    def update_data(self): 
        global covid_data,sheets,last_date,load_time
        
        start = time.perf_counter()
        #test_function()
        MainScreen1.update_labels(self,"Gathering and Calculating Data","Getting Updated Data from Database",10)
        cases_deaths = get_updated_data()
        MainScreen1.update_labels(self,None,"Calculating State Level Data",20)
        state_level_data = get_state_level_data(cases_deaths)
        MainScreen1.update_labels(self,None,"Calculating Time Series State Level Data",30)
        time_series_state_level_data = get_time_series_state_level_data(cases_deaths)
        MainScreen1.update_labels(self,None,"Calculating Time Series US Data",40)
        time_series_us_data = get_time_series_us_data(cases_deaths)
        
        MainScreen1.update_labels(self,"Compiling Data","Adding State Level Data",50)
        cases_deaths.append(state_level_data)
        MainScreen1.update_labels(self,None,"Adding Time Series State Level Data",63)
        cases_deaths.append(time_series_state_level_data)
        MainScreen1.update_labels(self,None,"Adding Time Series US Data",75)
        cases_deaths.append(time_series_us_data)
        MainScreen1.update_labels(self,None,"Saving Compiled Data ...",90)
        compiled_dict_for_quick_load,sheets,last_date = save_compiled_data(cases_deaths)
        MainScreen1.update_labels(self,"Update Completed",None,100)
        
        load_time = time.perf_counter() - start
        if load_time > 60:
            load_time = str(round(load_time/60,2)) + " minutes"
        else:
            load_time = str(round(load_time,2)) + " seconds"
        self.label2.text = "Excel File has been updated in " + load_time
        
        
        duration = 1000  # milliseconds
        freq = 185 # Hz
        winsound.Beep(freq, duration)
        
    def btn3_call(instance):
        global covid_data
        dataset = covid_data["Time Series US Data"]
        plot_data(dataset,"United States")
        print("Finished")
    pass

class MoreOptionsScreen(Screen):
    loc_labels = ObjectProperty(None)
    pickbtn = ObjectProperty(None)
    
    def on_enter(self):
        available_state_names = [x for x in get_state_names()]
        state_names = " | ".join(x for x in available_state_names)
        self.pickbtn.text = "Choose Below"
        self.loc_labels.text = "\n\n\n\n\n\n" + state_names
        
    def process(self):
        global picked_state
        state_names = get_state_names()
        text = self.loc_input.text 
        available_state_names = [x for x in get_state_names() if text.lower() in x.lower()]
        state_names = " | ".join(x for x in available_state_names)
        self.loc_labels.text = "\n\n\n\n\n\n" + state_names
        self.pickbtn.text = str(available_state_names[0]) if len(available_state_names) == 1 else "Reduce to 1 Location"
        if len(available_state_names) == 1:
            picked_state = available_state_names[0]
            
    def build_favorites_list(self):
        state_names = get_state_names()
        text = self.loc_input.text
        text = text.replace(", ",",")
        split_text = text.split(",")
        
        available_state_names = [x for x in state_names if x not in split_text]
        state_names1 = " | ".join(x for x in available_state_names)
        already_picked = [x for x in split_text if x in state_names]
        picked_states = "\n".join(x for x in already_picked)
        self.loc_labels.text = "\n\n\n\n\n\n" + state_names1
        self.favorites.text = "\n\n\n\n\n\n" + picked_states
    pass
         
class FocusedScreen(Screen):
    foc_det_lab = ObjectProperty(None)
    
    def on_enter(self):
        global covid_data, picked_state
        
        isolated_state = isolate_state_from_time_series(picked_state)
        isolated_state.columns = [x for x in isolated_state.iloc[0].values]
        isolated_state = isolated_state.drop(2)
        plot_data(isolated_state, picked_state)
        #print(isolated_state.columns)
        self.foc_det_lab.text = "Data Printed"
        #print(dataset.head())
        #self.foc_det_lab.text = str(" | ".join(x for x in dataset.columns[0:-2]))
    pass
    
sm = ScreenManager(transition=WipeTransition())
sm.add_widget(MainScreen1(name = 'mainscreen1'))  
sm.add_widget(MoreOptionsScreen(name = 'morescreen'))  
sm.add_widget(FocusedScreen(name = 'focusedscreen'))

class covidgui(App):
    
    def build(self):
        self.title = "COVID - 19      Data Extraction & Visualization"
        return sm
    
if __name__=='__main__':
    covidgui().run()