import requests
import json
import datetime


filename = "log.csv"


# function to log the actual temperature data in the file
def log(timestamp, temp):
    with open(filename, "a") as f:
        f.write(str(timestamp) + ',' + str(temp) + '\n')     


def read_temp():
    # request from the sensor
    r = requests.get('http://192.168.4.1/sensor/temperature')
    # return it in a json format
    print("temperature is", json.loads(r.content)["data"], "deg. Celsius")
    eval_resp(r)


def read_button(b):
    if b == 'b1':
        r = requests.get('http://192.168.4.1/pin/Button1')
    if b == 'b2':
        r = requests.get('http://192.168.4.1/pin/Button2')
    print("The button is", "pressed" if json.loads(r.content)["data"] == 0 else "released", "\n")
    eval_resp(r)


# make a time stamp
def read_timestamp():
    time_now = datetime.datetime.now()
    return time_now.ctime()


def eval_resp (resp):
    if resp.status_code == 200:
        print("SUCCESS\n")
    else:
        print("ERROR\n")


def print_valid_commands():
    print('\033[32mValid commands:\033[0m\n'
          'r/g/y - for toggling led color\n'
          'r/g/y=<on/off> - for setting specific color to led\n'
          's=<on/off> - for setting common state of leds\n'
          'b1/b2 - for button\n'
          't - for temperature\n'
          'n=<number>,<red>,<green>,<blue> - for setting neopixel to specific color\n'
          'no=<number> - for turning off neopixel\n'
          'na=<red>,<green>,<blue> - for setting all neopixels to specific color')


if __name__=="__main__":
    # create new file
    file = open(filename, "w")
    file.close()
    try:
        # loop logging many temperatures over time while the program is running
        while True:
            command = input('\033[32mEnter a command\033[0m (? for help):')
            try:
                if command == '?':
                    print_valid_commands()
                elif command == 't':
                    read_temp()
                elif 'r=' in command or 'g=' in command or 'y=' in command:
                    color, state = command.split('=')
                    if color == 'r':
                        eval_resp(requests.get('http://192.168.4.1/led?color=red&state='+state))
                    elif color == 'g':
                        eval_resp(requests.get('http://192.168.4.1/led?color=green&state='+state))
                    elif color == 'y':
                        eval_resp(requests.get('http://192.168.4.1/led?color=yellow&state='+state))
                elif command == 'r':
                    eval_resp(requests.get('http://192.168.4.1/led?color=red'))
                elif command == 'g':
                    eval_resp(requests.get('http://192.168.4.1/led?color=green'))
                elif command == 'y':
                    eval_resp(requests.get('http://192.168.4.1/led?color=yellow'))
                elif 's=' in command:
                    state = command.split('=')[1]
                    eval_resp(requests.get('http://192.168.4.1/led?state=' + state))
                elif command == 'b1' or command == 'b2':
                    read_button(command)
                elif 'n=' in command:
                    n, r, g, b = command.split('=')[1].split(',')
                    eval_resp(requests.get('http://192.168.4.1/neo?number=' + n + '&rgb=' + r + '-' + g + '-' + b))
                elif 'na=' in command:
                    r, g, b = command.split('=')[1].split(',')
                    eval_resp(requests.get('http://192.168.4.1/neo?rgb=' + r + '-' + g + '-' + b))
                elif 'no=' in command:
                    n, = command.split('=')[1]
                    eval_resp(requests.get('http://192.168.4.1/neo?number=' + n))
                else:
                    print("wrong command")
            except Exception:
                print("wrong command")
    except KeyboardInterrupt:  # ctrl+c
        print("You have been terminated")

