import requests
import json

def main():
    r = requests.get('http://192.168.4.1/sensors')
    
    # what is this for??
    
    
    return r.json()