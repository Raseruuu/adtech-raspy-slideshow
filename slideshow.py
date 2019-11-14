import tkinter as tk
import os, random, sys
from os import path
import os.path
from os.path import abspath, dirname
import shutil
import json, httplib2
import urllib.request
import datetime
from PIL import Image, ImageTk, ImageSequence
from decouple import config
import requests
import time
from datetime import datetime as dt

ADTECH_ENDPOINT = "http://54.255.190.93/api/v1"

class SlideShowApp(object):
    def __init__(self):
        self.tk = tk.Tk()
        self.tk.attributes('-fullscreen', True)
        self.frame = tk.Frame(self.tk)
        self.canvas = tk.Canvas(self.tk, width=self.tk.winfo_screenwidth(), height=self.tk.winfo_screenheight())
        self.canvas.pack()
        self.state = False
        self.tk.bind('<F11>', self.toggle_fullscreen)
        self.tk.bind('<Escape>', self.end_fullscreen)

        self.current_date = None
        self.base_dir = 'Images'        #Base directory for your images
        self.group_static = {
                            #  1: {
                            #      'category': 'daily_context', 'method': 'draw',
                            #      'slides': {
                            #                 1 : { 'name': 'TOD', 'path': 'TOD', 'callback': 'drawTOD'},
                            #                 2 : { 'name': 'Weather', 'path': 'Weather', 'callback': 'drawWeather'}
                            #                 }
                            #      },
                            #  2: {
                            #      'category': 'photo_context', 'method': 'image',
                            #      'slides': {
                            #                 1 : { 'name': 'Family', 'path': 'Family'}
                            #                 }
                            #      },
                            #  3: {
                            #      'category': 'reminders', 'method': 'image',
                            #      'slides': {
                            #                 1 : { 'name': 'Inspirational', 'path': 'Inspirational'},
                            #                 2 : { 'name': 'Health', 'path': 'Health'}
                            #                 }
                            #      },
                             2: {
                                 'category': 'advertisements', 'method': 'image',
                                 'slides': {
                                            1 : { 'name': 'cache', 'path': 'cache'}
                                            }
                                 }
                            }

        self.group_annual = {}      #placeholder for future slides
        self.group_scheduled = {}   #placeholder for futer slides

        # self.group_seasonal = {
                            #    1: {
                            #        'category': 'Holidays', 'method': 'image',
                            #        'slides': {
                            #                    1 : { 'name': 'Christmas', 'months': [12], 'path': 'Holidays/Christmas'},
                            #                    2 : { 'name': 'Easter', 'months': [4], 'path': 'Holidays/Easter'},
                            #                    3 : { 'name': 'Halloween', 'months': [10], 'path': 'Holidays/Halloween'},
                            #                    4 : { 'name': 'Independence', 'months': [7], 'path': 'Holidays/Independence'},
                            #                    5 : { 'name': 'Labor', 'months': [9], 'path': 'Holidays/Labor'},
                            #                    6 : { 'name': 'Memorial', 'months': [5], 'path': 'Holidays/Memorial'},
                            #                    8 : { 'name': 'Mothers', 'months': [5], 'path': 'Holidays/Mothers'},
                            #                    9 : { 'name': 'NewYear', 'months': [1], 'path': 'Holidays/NewYear'},
                            #                    10 : { 'name': 'Thanksgiving', 'months': [11], 'path': 'Holidays/Thanksgiving'},
                            #                    11 : { 'name': 'Valentines', 'months': [2], 'path': 'Holidays/Valentines'}
                            #                    }
                            #        },

                            #    2: {
                            #        'category': 'Seasons', 'method': 'image',
                            #        'slides': {
                            #                    1 : {'name': 'Fall', 'months': [9,10,11], 'path': 'Seasons/Fall'},
                            #                    2 : {'name': 'Winter', 'months': [12,1,2], 'path': 'Seasons/Winter'},
                            #                    3 : {'name': 'Spring', 'months': [3,4,5], 'path': 'Seasons/Spring'},
                            #                    4 : {'name': 'Summer', 'months': [6,7,8], 'path': 'Seasons/Summer'}
                            #                    }
                            #        }
                            #    }

        self.eligible_slides = self.group_static
        print("Group Static: ", self.group_static)
        self.black_path = os.path.join(self.base_dir, 'Static', 'black1280.png')

        #Weather API
        self.weather_last_update = None
        self.weather_update_frequency = datetime.timedelta(seconds=3600)
        self.weather_cache = None
        self.weather_api_path = 'http://api.openweathermap.org/data/2.5/weather?zip=77034,us&units=imperial&APPID=bf21b5e020e1fcdbe8' #replace 77034 with your zip code
        self.weather_types = ['Thunderstorm', 'Drizzle', 'Rain', 'Snow']
        self.weather_cloud_types = {
               800 : 'Clear',
               801 : 'LightClouds',
               802 : 'LightClouds',
               803 : 'LightClouds',
               804 : 'OverCast'
               }

        #Advertisement API
        self.advertisement_last_update = None
        self.advertisement_update_frequency = datetime.timedelta(seconds=3600)
        self.advertisement_cache = None
        self.access_token = None
        self.connected = False              # flag for internet connection
        self.pre_registered = False         # validation flag  if .env file already has deviceid and deviceName
        self.pre_login = False              # validation flag  if .env file already has email and password
        self.device_registered = False      # flag for registered status
        self.login_failed = False           # flag for online login status - bad data, user doesn't exist, or passed the wrong password
        self.playlist_associated = False    # Device has playlist associated with it
        self.playlist_empty = False         # Device has playlist associated with it, but it's empty. 
        self.connection_timeout = 0
        self.ad_index = 0
        self.ad_list = []                   # Ads to be shown by device
        self.ads_pool = []                  # All ads from all playlist in queue
        self.current_ad = None
        self.ad_timer_list = []
        self.ad_timer = 0
        self.play_random = False           # Randomize slides
        self.counter_timeout = 0           # Counter for initial wifi connect 
        self.login()
        # self.test_register()
        self.register_device()
        self.dir = os.path.dirname(os.path.abspath(__file__))
        self.cache_dir = self.dir + '/Images/cache/'
        
        
        
        ## Clear cache folder on startup
        if os.path.exists(self.cache_dir):
            for file in os.listdir(self.dir +'/Images/cache'):
                os.remove(self.cache_dir+file)
        else:
            os.makedirs(self.cache_dir)


    def toggle_fullscreen(self, event=None):
        self.state = not self.state
        self.tk.attributes('-fullscreen', self.state)


    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes('-fullscreen', False)
        return 'break'


    def callback(self):
        get_image()


    def login(self):
        if config('email', default=None) and config('password', default=None):   # Check if .env file has deviceId and deviceName
            self.pre_login = True 
        else:
            if os.path.exists('.env'):
                os.remove('.env')
                print('.env file deleted')

            self.pre_login = False

        try:
            response = requests.post(
                ADTECH_ENDPOINT + '/auth/login', 
                data={'email': config('email', cast=str), 'password': config('password', cast=str)}
            )
            print("Login response: ", response.text)
            if response.status_code == 200:     # Success
                self.access_token = response.json().get('token')
                self.login_failed = False

            elif response.status_code == 404:   # User not found
                print(response.text)
                if os.path.exists('.env'):
                    os.remove('.env')
                    print('.env file deleted')
                print("Login error - User not found")
                self.login_failed = True

            elif response.status_code == 422:   # Invalid password
                print(response.text)
                if os.path.exists('.env'):
                    os.remove('.env')
                    print('.env file deleted')
                print("Login error - Invalid password")
                self.login_failed = True

            elif response.status_code == 400:   # Bad Data
                print(response.text)
                print("Login error - Bad data") 
                if os.path.exists('.env'):
                    os.remove('.env')
                    print('.env file deleted')
                self.login_failed = True

            self.connected = True 

        except Exception as e:
            print(e)
            print("Login failed. check Internet?")
            self.login_failed = True
            self.connected = False


    def register_device(self):
        if config('deviceUid', default=None) and config('deviceName', default=None):   # Check if .env file has deviceId and deviceName
            self.pre_registered = True 
            print("Pre-registered!")
        else:
            if os.path.exists('.env'):
                os.remove('.env')
                print('.env file deleted')
            self.pre_registered = False

        try:
            response = requests.post(
                ADTECH_ENDPOINT + '/devices', 
                data={'deviceUid': config('deviceUid', cast=str), 
                    'deviceName': config('deviceName', cast=str)
                }, 
                headers = {'Authorization':self.access_token}
            )
            print("Register response: ", response.status_code, response.text)

            if response.status_code == 201:     # Register successful!
                print("Registered Successfully!")
                self.device_registered = True

            elif response.status_code == 302:   # Device already exists
                print("Device already registered!")
                self.device_registered = True

                #TODO: Check if device belongs to the user. Add invalid user validation
            elif response.status_code == 422:   # Bad Data
                print("Register - Bad data")
                if os.path.exists('.env'):
                    os.remove('.env')
                    print('.env file deleted')
                self.device_registered = False

            self.connected = True
        
        except Exception as e:
            print(e)
            print("Register Device Error: Register failed. Check Env file and Internet?")
            self.device_registered = False
            self.connected = False

    def check_device_status(self):
        print("******************************************************************************************")
        # Continuously check if device is still registered 
        # (just in case it was removed in the webdashboard)
        # If the device is removed, the device must clear .env file
        try:
            print("Checking Device Register Status")
            response = requests.get(
                ADTECH_ENDPOINT + "/devices",
                headers = {'Authorization': self.access_token}
            )
            # print(response.status_code)
            # print(response.text)
            all_devices = response.json().get("devices")
            # print(all_devices)

            check_device_name = None
            for device in all_devices:
                # print(device.items())
                for k, v in device.items():
                    # if (k == "deviceUid" and v == config('deviceUid') ):
                    #     # print("Device Unique ID:", k, v)
                    if (k == "deviceName" and v == config('deviceName')):
                        check_device_name = v      
                        # print("Device Name:", k, v)          

            # device_name_check = response.json().get("devices")[0].get("deviceName")
            print("Device Name Retrieved:", check_device_name)
            
            if check_device_name == None:
                if os.path.exists(self.dir + '/.env'):
                    os.remove(self.dir + '/.env')
                    print('.env file deleted')
                self.device_registered = False
                self.pre_registered = False

        except Exception as e:
            # print(e)
            print("Check Device Status Error: No Env file or Internet?")
            self.connected = False

        print("******************************************************************************************")

    def json_request(self, method='GET', path=None, body=None):
        connection = httplib2.Http()
        response, content = connection.request(
                                               uri = path,
                                               method = method,
                                               headers = {'Content-Type': 'application/json; charset=UTF-8'},
                                               body = body,
                                               )
        return json.loads(content.decode())


    def fetch_weather(self):    # Unused
        result = self.json_request(path=self.weather_api_path)

        #get temperature from "main" set
        if 'main' in result:
            temperature = int(result['main']['temp'])

        #parse weather conditions
        weather_conditions = []
        weather_context = None
        weather_context_images = []

        if 'weather' in result:
            weather_list = result['weather']
            for condition in weather_list:
                weather_conditions.append(condition['description'].title())
                if condition['main'] in self.weather_types:
                    weather_context_images.append(condition['main'])
                elif condition['id'] in self.weather_cloud_types:
                    weather_context_images.append(self.weather_cloud_types.get(condition['id'], None))

            weather_context = ', '.join(weather_conditions)

            self.weather_last_update = datetime.datetime.now()
            self.weather_cache = {
                                  'temperature': temperature,
                                  'description': weather_context,
                                  'background': weather_context_images[0]
                                  }
            print('updating weather cache at', self.weather_last_update)
            print(self.weather_cache)


    def fetch_advertisement(self):  # From test_data.json
        print("******************************************************************************************")
        print("Fetching Ads")

        try:
            result = requests.get(
                ADTECH_ENDPOINT + "/devices/" + config('deviceUid', default=None, cast=str) + "/carousel", 
                headers = {'Authorization':self.access_token}
            )
            print("Fetch Ads Response: ", result.status_code, result.json())

            if result.status_code == 200:
                data = result.json()
                print("A playlist is associated with this device.")
                print("Downloading playlist..")
                try:
                    self.ads_pool = []           # All the ads from all playlist in queue
                    queue_name = data ["queueName"]
                    time_start = data["timeStart"]
                    time_end = data["timeEnd"]
                    carousel_data = data["playlists"]                    
                    print("Queue Name:", queue_name)

                    for playlist in carousel_data:
                        print(carousel_data.index(playlist)+1, end = '. ')
                        print(playlist["playlistName"], end = ' - ')
                        print("Random" if playlist["playRandom"] else "Sequential")
                        
                        cache_files = os.listdir(self.cache_dir)
                        # print("Cache Files: ", cache_files)
                        ad_urls = playlist["advertisements"]["advertUrls"]
                        ad_names = playlist["advertisements"]["advertNames"]
                        # print(ad_urls)

                        # Completely adds all ads from all playlist on queue to a global list of ads
                        for playlist in carousel_data:             
                            for ad in playlist["advertisements"]["advertNames"]:
                                if ad not in self.ads_pool:
                                    self.ads_pool.append(ad)

                        # Download image links if its not in the cache folder already
                        for ad in range(len(ad_urls)):             
                            url = ad_urls[ad]
                            title = ad_names[ad]
                            # print(" ", url, title)
                            if title not in cache_files:
                                print("Downloading", title)
                                urllib.request.urlretrieve(url, self.cache_dir + title)
#                                self.ad_list.append(title) #Added By Russel
                            # else:
                            #     print(title, "is already downloaded.")

                        # Delete ads in cache file if no longer in global list of ads
                        for file in cache_files:        
                            if file not in self.ads_pool:
                                print("Deleting:", file)
                                os.remove(self.cache_dir+file)

                    print("")
                    print("Cache Files: ", cache_files)
                    print("Ads pool contains:", self.ads_pool)
                    print("******************************************************************************************")
                    
                    # Choose which playlist should be displayed based on timestamps
                    current_time = int(time.time())
                    time_start = int(time_start/1000)
                    time_end = int(time_end/1000)
                    print("Current time:", dt.fromtimestamp(current_time))            

                    playlist_time_start = 0
                    playlist_time_end = 0

                    if current_time > time_start and current_time < time_end:
                        print("Queue currently selected:", queue_name)
                        for playlist in carousel_data:
                            # print(playlist, playlist.items())
                            for k, v in playlist.items():
                                # print(k, v)
                                if (k == "timeStartPlaylist"):
                                    playlist_time_start = int(v/1000)
                                if (k == "timeEndPlaylist"):
                                    playlist_time_end = int(v/1000)
                            print(current_time)
                            print(playlist_time_start)
                            print(playlist_time_end)
                            if current_time >= playlist_time_start or current_time < playlist_time_end:
                                print("Current Playlist:",playlist["playlistName"])
                                print("Timeframe:", dt.fromtimestamp(playlit_time_start), "until", dt.fromtimestamp(playlist_time_end))
                                self.ad_list = playlist["advertisements"]["advertNames"]
                                self.ad_timer_list = playlist["advertisements"]["advertTimers"]
                                self.play_random = playlist["playRandom"]

                            print(self.ad_list)
                        
                        self.playlist_associated = True

                    else:
                        self.playlist_associated = False

                except Exception as e:
                    print("Pass", e)
                    # print("Playlist did not change. Nothing to delete")

                if self.ad_list:
                    print("This playlist has", len(self.ad_list), "ads.")
                    self.playlist_empty = False
                else:
                    print("This playlist is empty.")
                    self.playlist_empty = True

            elif result.status_code == 404:
                print("No playlist associated with this device yet.")
                self.playlist_associated = False

            self.connected = True

        except Exception as e:
            print("Fetch Advertisement Error")
            print(e)
            self.connected = False

        # self.playlist_associated = False    # Remove this when testing for reals


    # def old_fetch_advertisement(self):
    #     print("Fetching Ads")
    #     try:
    #         cache_files = os.listdir(self.cache_dir)
    #         result = requests.get(
    #             ADTECH_ENDPOINT + "/devices/" + config('deviceUid', default=None, cast=str) + "/carousel", 
    #             headers = {'Authorization':self.access_token}
    #         )
    #         print("Fetch Ads Response: ", result.status_code, result.json())

    #         #TODO: Catch empty playlists and unassociated devices properly
    #         if result.status_code == 200:
    #             print("A playlist is associated with this device.")
    #             print("Downloading playlist..")
    #             try:
    #                 self.play_random = result.json().get("playRandom")
    #                 advertisements = result.json().get("advertisements")
    #                 ad_urls = advertisements.get("advertUrls")
    #                 self.ad_list = advertisements.get("advertNames")
    #                 self.ad_timer_list = advertisements.get("advertTimers")

    #                 for ad in range(len(self.ad_list)):
    #                     url = ad_urls[ad]
    #                     title = self.ad_list[ad]                          

    #                     if title not in cache_files:
    #                         print("Downloading", title)
    #                         urllib.request.urlretrieve(url, self.cache_dir + title)
                        
    #                 for file in cache_files:
    #                     if file not in self.ad_list:
    #                         print(file)
    #                         os.remove(self.cache_dir+file)

    #                 print("Ad list: ", self.ad_list)

    #             except Exception as e:
    #                 print("Pass", e)
    #                 # print("Playlist did not change. Nothing to delete")
  
    #             if self.ad_list:     # Check if ad_list is empty
    #                 print("Playlist has", len(self.ad_list), "ads.")
    #                 self.playlist_empty = False
    #             else:
    #                 print("Playlist is empty.")
    #                 self.playlist_empty = True

    #             self.playlist_associated = True

    #         elif result.status_code == 404:
    #             print("No playlist associated with this device yet.")
    #             self.playlist_associated = False

    #         self.connected = True
        
    #     except Exception as e:
    #         print("Fetch advertisement Error")
    #         print(e)
    #         self.connected = False


    def update_eligible_slides(self):
        #reset eligible to default
        self.eligible_slides = self.group_static
        #filter seasonal and daily slides
        # counter = 1
        # for k,v in self.group_seasonal.items():
        #     for x,y in v['slides'].items():
        #         if self.current_date.month in y['months']:
        #             self.eligible_slides[4]['slides'][counter] = y
        #             counter += 1


    def prepare_slide(self):
        #pick a group
        group = random.choice(list(self.eligible_slides))
        #TODO check for slide group method
        slide = random.choice(list(self.eligible_slides[group]['slides']))
        slide_full = self.eligible_slides[group]['slides'][slide]
        path = self.cache_dir

        if self.eligible_slides[group]['method'] == 'draw':
            callback = slide_full['callback']
            getattr(self, callback)()
        elif self.eligible_slides[group]['method'] == 'image':
            # Device has not logged in, has not registered and has no WiFi (First time - One time Setup (no .env file))
            if not self.connected and not self.access_token and not self.device_registered and not self.pre_registered:     
                path = self.dir + '/Images/Static/'
                full_path = os.path.join(path, 'setup_instructions.png')
                self.get_image(full_path)
                self.ad_timer = 1200000
            
            #TODO: Display Wifi network and status
            # Device is probably registered but there's no internet from the start. (2nd Time onwards)
            elif not self.connected and not self.access_token and not self.device_registered and self.pre_registered:       
                if self.connection_timeout < 10: # Initially wait..
                    self.connection_timeout += 1
                    path = self.dir + '/Images/Static/'
                    full_path = os.path.join(path, 'no_internet_from_start.png')       
                    self.get_image(full_path)
                    self.ad_timer = 20000
            
                else: # Timeout (Give up.. the wifi creds are probably wrong anyway.)
                    path = self.dir + '/Images/Static/'
                    full_path = os.path.join(path, 'no_internet.png')
                    self.get_image(full_path)
                    self.ad_timer = 10000 #0

            # Login failed but has internet (Wrong login credentials)
            elif self.connected and not self.pre_login and not self.access_token and self.login_failed:              
                path = self.dir + '/Images/Static/'
                full_path = os.path.join(path, 'resetup_login_failed.png')
                self.get_image(full_path)
                self.ad_timer = 1200000

            # Device is not registered but has internet (Login success, but failed to register)
            elif self.connected and self.access_token and not self.pre_registered and not self.device_registered:          
                path = self.dir + '/Images/Static/'
                full_path = os.path.join(path, 'resetup_register_failed.png')
                self.get_image(full_path)
                self.ad_timer = 1200000

            # No playlist associated with this device
            elif self.connected and not self.playlist_associated:      
                path = self.dir + '/Images/Static/'
                full_path = os.path.join(path, 'no_playlist.png')
                self.get_image(full_path)
                self.ad_timer = 10000   

            # Playlist is associated with the device but it's empty         
            elif self.playlist_associated and self.playlist_empty and self.connected:       
                path = self.dir + '/Images/Static/'
                full_path = os.path.join(path, 'empty_playlist.png')
                self.get_image(full_path)
                self.ad_timer = 10000

            # Device is registered but has no Internet (Functional but then suddenly disconnected)
            elif self.access_token and self.device_registered and not self.connected:          
                path = self.dir + '/Images/Static/'
                full_path = os.path.join(path, 'no_internet.png')
                # full_path = os.path.join(path, 'black1280.png')
                self.get_image(full_path)    
                self.ad_timer = 10000

            # Device is registered and has both wifi and associated playlist with ads (Normal operation)
            elif len(os.listdir(path)):     # Cache folder contains ads
                if self.play_random:        # Play images/ads at random
                    image = random.choice(self.ad_list)
                    print("Image :", image)
                    full_path = os.path.join(path, image)
                    self.get_image(full_path)
                    self.current_ad = image
                    self.ad_timer = self.ad_timer_list[ self.ad_list.index(str(self.current_ad)) ]
                    print("Randomized slides")

                else:                      # (Iterate) Selecting over adlist sequentially
                    # self.ad_list = os.listdir(path)
                    # print("Directory files list: ", self.ad_list)

                    image = self.ad_list[self.ad_index]
                    full_path = os.path.join(path, image)
                    self.get_image(full_path)
                    self.current_ad = image
                    
                    self.ad_timer = self.ad_timer_list[ self.ad_list.index(str(self.current_ad))]

                    print("Index : ", self.ad_index, "Image :", image, "Interval :", self.ad_timer)
                    print("Sequential slides")

                    if self.ad_index < len(self.ad_list)-1:
                        self.ad_index += 1
                    else:
                        self.ad_index = 0

            else:   # All else
                path = self.dir + '/Images/Static/'
                full_path = os.path.join(path, 'black1280.png')
                self.get_image(full_path)
                self.ad_timer = 30000


    def draw_rectangle(self):
        pass


    def slideshow(self):
        now = datetime.date.today()
        #now = datetime.date(2015, 7, 11)        #use for testing different date ranges
        if not self.current_date or now != self.current_date:
            self.current_date = now
            self.update_eligible_slides()

        if not self.weather_last_update or (datetime.datetime.now() - self.weather_last_update > self.weather_update_frequency):
            print("Registered: ", self.device_registered, ", Connected: ", self.connected)
            if not self.access_token:   # Self-restoring/reconnecting, in case of disconnection
                self.login()
                self.register_device()

            self.fetch_advertisement()
            self.check_device_status()

        self.prepare_slide()
        print("Ad TIMER:", self.ad_timer/1000, "seconds")
        self.tk.after(self.ad_timer, self.slideshow)    # Set ad_interval


    def get_image(self, path):
        #global tkpi
        image = Image.open(path)
        
#        self.image = image.resize((self.tk.winfo_screenwidth(), self.tk.winfo_screenheight()))
#        self.tk.geometry('%dx%d' % (image.size[0], image.size[1]))        print("Image Type: "+str(path))
#        self.tkpi = ImageTk.PhotoImage(image)
#
#        label = tk.Label(self.tk, image=self.tkpi)
#        label.place(x=0,y=0,width=image.size[0], height=image.size[1])
         
        self.imagesequence = ImageSequence.Iterator(Image.open(path))
        
        self.imagesequence = [ImageTk.PhotoImage(image.resize((self.tk.winfo_screenwidth(), self.tk.winfo_screenheight()))) for image in self.imagesequence]
        # self.imagesequence = [ImageTk.PhotoImage(image) for image in self.imagesequence]

        self.image = self.canvas.create_image(self.tk.winfo_screenwidth()/2,self.tk.winfo_screenheight()/2, image=self.imagesequence[0])
        
        self.animate(0)
    def animate(self,counter):
        self.canvas.itemconfig(self.image, image = self.imagesequence[counter])
#        print(self.imagesequence[0])
        self.tk.after(50,lambda:self.animate((counter+1)%len(self.imagesequence)))


    def drawTOD(self):
        #set bg image to black static
        self.get_image(self.black_path)

        #contextual date / time
        now = datetime.datetime.now()
        hour_check = int(now.strftime('%H'))
        if hour_check > 4 and hour_check < 11:
            context_time = 'Morning'
        elif hour_check >= 11 and hour_check < 14:
            context_time = 'Mid Day'
        elif hour_check >= 14 and hour_check < 17:
            context_time = 'Afternoon'
        elif hour_check >= 17 and hour_check < 19:
            context_time = 'Evening'
        else:
            context_time = 'Night'

        context_tod = '{} {}'.format(now.strftime('%A'), context_time)
        full_tod = '{}\n{}'.format(now.strftime('%I:%M %p'), now.strftime('%B %d, %Y'))

        label = tk.Label(self.tk, text=context_tod, width=0, height=0, fg="#ffffff", bg="#000000", font=("Rouge", 95))
        label.place(relx=0.5, rely=0.3, anchor="center")
        label = tk.Label(self.tk, text=full_tod, width=0, height=0, fg="#ffffff", bg="#000000", font=("Rouge", 78))
        label.place(relx=0.5, rely=0.7, anchor="center")


    def drawWeather(self):  # Unused
        if self.weather_cache:
            #Set background image if available
            if 'background' in self.weather_cache:
                image_dir = os.path.join(self.base_dir, 'Weather', self.weather_cache['background'])
                image = random.choice(os.listdir(image_dir))
                full_path = os.path.join(image_dir, image)
                self.get_image(full_path)
            #else use black bg
            else:
                self.get_image(self.black_path)

            #draw the temp and weather description
            temperature = '{}{}'.format(self.weather_cache['temperature'], u'\N{DEGREE SIGN}')
            description = self.weather_cache['description']
            if temperature and description:
                label = tk.Label(self.tk, text=description, width=0, height=0, fg="#000", bg="#e6e6e6", font=("Rouge", 55))
                label.place(relx=0.5, rely=0.4, anchor="center")
                label = tk.Label(self.tk, text=temperature, width=0, height=0, fg="#000", bg="#e6e6e6", font=("Rouge", 45))
                label.place(relx=0.5, rely=0.6, anchor="center")
        else:
            pass

if __name__ == '__main__':
    w = SlideShowApp()
    w.slideshow()
    w.tk.mainloop()
