from machine import Pin, I2C
import network
import socket
import json


class MCP9808:
    # resolution levels
    RES_LEVEL1 = b'\x00' # +0.5C
    RES_LEVEL2 = b'\x01' # +0.25C
    RES_LEVEL3 = b'\x10' # +0.125C
    RES_LEVEL4 = b'\x11' # +0.0625C

    def __init__(self, scl, sda):
        self._i2c = I2C(scl=scl, sda=sda)
        self._addr = 0x18
        self._temp_reg = 0x05
        self._res_reg = 0x08

    # function to convert the raw temperature data to Celsius scale
    def _temp_to_c(self, raw_data):
        val = raw_data[0] << 8 | raw_data[1]
        temp = (val & 0xFFF) / 16
        if val & 0x1000:
            temp -= 256
        return temp

    def read_temperature(self):
        data = self._i2c.readfrom_mem(self._addr, self._temp_reg, 2)
        return self._temp_to_c(data)

    def set_resolution_level(self, level):
        self._i2c.writeto_mem(self._addr, self._res_reg, level)

    # function to make sensor reading consistent
    def read(self):
        return self.read_temperature()


class IotServer:
    def __init__(self):
        self._html = ''
        self._isRunning = False

        # setup all used input pins
        self._supported_pins = [33, 14]
        self._pin_names = ["Button1", "Button2"]
        self._pin_objs = [Pin(i, Pin.IN) for i in self._supported_pins]
        self._pins = dict(zip(self._pin_names, self._pin_objs))

        # setup all used sensors
        self._sensor_names = ["temperature"]
        self._sensor_objs = [MCP9808(scl=Pin(22), sda=Pin(23))]
        self._sensors = dict(zip(self._sensor_names, self._sensor_objs))

        #setup all used pins
        self._supported_leds = [15, 32, 13]
        self._leds_color = ["green", "yellow", "red"]
        self._led_objs = [Pin(i, Pin.OUT) for i in self._supported_leds]
        self._leds = dict(zip(self._leds_color, self._led_objs))


        # start access point
        self._ap = network.WLAN(network.AP_IF)
        self.start_ap("group12", "qqwweerrttyy")

        # start socket
        self._addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        self._s = socket.socket()
        self._s.bind(self._addr)
        self._s.listen(1)
        print('Listening on address:', self._addr)

    def start_ap(self, name, pswd):
        self._ap.active(True)
        self._ap.config(essid=name)
        self._ap.config(authmode=3, password=pswd)

    def load_html(self):
        # if empty read, otherwise return read data
        if self._html == '':
            with open("index.html", "r") as f:
                self._html = f.read()
        return self._html

    def generate_html(self):
        site = self.load_html()
        rows1 = ['<tr><td>{}</td><td bgcolor="{}">{}</td></tr>'
                     .format(k, "green" if v.value() else "red", v.value()) for k, v in self._pins.items()]
        rows2 = ['<tr><td>{}</td><td bgcolor="yellow">{}</td></tr>'
                     .format(k, v.read())for k, v in self._sensors.items()]
        return "HTTP/1.1 200 OK\nContent-type: text/html\n\n" + site % '\n'.join(rows1 + rows2) + "\r\n"

    def generate_json(self, dict_):
        return "HTTP/1.1 200 OK\nContent-type: application/json\n\n" + json.dumps(dict_) + "\r\n"

    def handle_request(self, request):
        # in case of no request return the website
        if request == b'':
            return self.generate_html()

        # parse the path and execute corresponding request
        path = request.decode().split(" ")[1]
        if path == '/':
            return self.generate_html()
        elif path == '/pins':
            d = {"pins": self._pin_names}
            return self.generate_json(d)
        elif path == '/sensors':
            d = {"sensors": self._sensor_names}
            return self.generate_json(d)
        elif "/sensor/" in path:
            sen = path.split("/")[-1]
            if sen in self._sensor_names:
                d = {"sensor": sen,
                     "data": self._sensors[sen].read()}
                return self.generate_json(d)
            else:
                return "HTTP/1.1 400 BAD REQUEST"
        elif "/pin/" in path:
            pin = path.split("/")[-1]
            if pin in self._pin_names:
                d = {"sensor": pin,
                     "data": self._pins[pin].value()}
                return self.generate_json(d)
            else:
                return "HTTP/1.1 400 BAD REQUEST"
        elif "/led" in path:
            query = path.split("?")[1:len(path)-1]
            state = ''
            color = ''
            for q in query:
                if 'state' in q:
                    s = q.split("=")[1]
                    if s == 'on' or s == 'off':
                        state = s
                        continue
                    else:
                        return "HTTP/1.1 400 BAD REQUEST"
                if 'color' in q:
                    c = q.split("=")[1]
                    if c in self._leds_color:
                        color = c
                    else:
                        return "HTTP/1.1 400 BAD REQUEST"
            if state == '' and color == '':
                return "HTTP/1.1 400 BAD REQUEST"
            elif state == '':
                current = self._leds[color].value()
                print("Current pin value is", current)
                self._leds[color].value(0 if current == 1 else 1)
                print("new pin value is", self._leds[color].value())
                return "HTTP/1.1 200 OK\n\nOK\r\n"
            elif color == '':
                for c in self._leds_color:
                    self._leds[c].value(1 if state == 'on' else 0)
                return "HTTP/1.1 200 OK\n\nOK\r\n"
            else:
                self._leds[color].value(1 if state == 'on' else 0)
                return "HTTP/1.1 200 OK\n\nOK\r\n"

        else:
            return "HTTP/1.1 404 NOT FOUND"

    def run(self):
        self._isRunning = True
        while self._isRunning:
            try:
                # wait for connection
                cl, addr = self._s.accept()
                print('Client connected from', addr)
                cl_file = cl.makefile('rwb', 0)
                # read request
                request = bytes()
                while True:
                    line = cl_file.readline()
                    request += line
                    print(line)
                    if not line or line == b'\r\n':
                        break
                print("REQUEST:")
                print(request)

                # handle request and return response
                response = self.handle_request(request)

                print("RESPONSE:")
                print(response)

                cl.send(response.encode())
                cl.close()
            except KeyboardInterrupt:
                self._isRunning = False

    def stop(self):
        self._isRunning = False


if __name__ == '__main__':
    s = IotServer()
    s.run()

