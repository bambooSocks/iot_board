#Task 4
import requests #access to HTTP 1.1
import sys
import time
import datetime #supplies modules for manipulating data and time
import temp_get #my function, gets requests from http

time_now = datetime.datetime.now #combination of date and time

def log_data(path):
    #any open files will be closed automatically after the session
    with open(path, "w") as f:
        try:
            while True:
                f.write("{} {}\n".format(time_now(),temp_get.main()))
                print("{} {} Celsius\n".format(time_now(),temp_get.main()))
                time.sleep(1)
                
        except KeyboardInterrupt:
            #when the user interrupts the program with ctrl c or somethin
            print("Interrupted, quitting the program...")
        
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Too few arguments. Please input python task4.py <path for the file>")
        exit()
    path = sys.argv[1]
        