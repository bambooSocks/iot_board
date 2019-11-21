from machine import Pin
from machine import I2C
import network
import socket


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


class IotServer:
    def __init__(self):
        self._html = ''
        self._isRunning = False

        self._pin_names = ["Button1", "Button2"]
        self._pin_nums = [Pin(i, Pin.IN) for i in [33, 14]]
        self._pins = dict(zip(self._pin_names, self._pin_nums))

        self._temp_sensor = MCP9808(scl=Pin(22), sda=Pin(23))
        self._temp_sensor.set_resolution_level(MCP9808.RES_LEVEL2)

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
                for line in f:
                    self._html += line
        return self._html

    def generate_html(self):
        site = self.load_html()
        rows = ['<tr><td>{}</td><td bgcolor="{}">{}</td></tr>'
                    .format(k, "green" if v.value() else "red", v.value()) for k, v in self._pins.items()]
        rows.append('<tr><td>temp</td><td bgcolor="yellow">{}</td></tr>'.format(self._temp_sensor.read_temperature()))
        return site % '\n'.join(rows)

    def run(self):
        self._isRunning = True
        while self._isRunning:
            cl, addr = self._s.accept()
            print('Client connected from', addr)
            cl_file = cl.makefile('rwb', 0)
            request = bytes()
            while True:
                line = cl_file.readline()
                request += line
                print(line)
                if not line or line == b'\r\n':
                    break
            print("REQUEST:")
            print(request)
            response = self.generate_html()
            print("RESPONSE:")
            print(response)
            cl.send(response.encode())
            cl.close()

    def stop(self):
        self._isRunning = False


if __name__ == '__main__':
    s = IotServer()
    try:
        s.run()
    except KeyboardInterrupt:
        s.stop()
