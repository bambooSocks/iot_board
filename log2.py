import requests
import json
import datetime
import time


filename="log.csv"   #we make a csv file bc it's more suitable for data of this format

f = open(filename, "w")
f.close()


def log(timestamp, temp): #function to log the actual temperature data in the file
    with open(filename, "a") as f:
        f.write(str(timestamp) + ',' + str(temp) + '\n')     
     
def read_temp():
    r = requests.get('http://192.168.4.1/sensor/temperature') #request from the sensor
    return json.loads(r.content)["data"] #retur it in a json format
        
def read_timestamp(): #make a time stamp
    time_now = datetime.datetime.now()
    return time_now.ctime()
    

    
    
if __name__=="__main__":
    try:
        while True:  #loop logging many temperatures over time while the program is running
            #to stop the program press ctrl+c
            log(read_timestamp(), read_temp())
            time.sleep(1) #delay for a second (plus delay time that takes to compute stuff)
    except KeyboardInterrupt: #ctrl+c
        print("You have been terminated")
    
    

