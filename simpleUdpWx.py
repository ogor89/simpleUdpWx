import machine
import network
import socket
import time
from bme280 import BME280


sta_if = network.WLAN(network.STA_IF)


class Config:

    wifi_ssid = 'WiFi_name'  # WiFi SSID.
    wifi_passwd = 'WiFi_password'  # WiFi password.
    wifi_timeout = 60

    txDelay = 5  # Delay between frames (in minutes).
    servers = ['euro.aprs2.net']  # List of APRS-IS servers. ( ['server1', 'server2'] )

    call = 'N0CALL-1'  # Call with or without suffix.
    passwd = '12345'  # APRS-IS password.
    symbol = '/_'  # Two symbol coded APRS icon.
    latitude = '5000.00N'
    longitude = '01900.00E'
    comment = 'simpleUDP WX station'  # Comment attached to WX data.
    status = ''  # Status sent as separate APRS frame. If None or '' additional frame will not be sent.


def wifi_connect():
    connected = False
    if not sta_if.isconnected():
        print('Connecting...')
        sta_if.active(True)
        sta_if.connect(Config.wifi_ssid, Config.wifi_passwd)

        for timestep in range(0, Config.wifi_timeout):
            print(timestep, end=' ')
            time.sleep(1)
            if sta_if.isconnected():
                connected = True
                print('Connected!')
                time.sleep(2)
                break
    else:
        connected = True

    return connected


def wifi_disconnect():
    print('disconnecting...')
    time.sleep(2)
    if sta_if.isconnected():
        sta_if.disconnect()
    sta_if.active(False)


def get_ip_from_addr(address, ip=8080):
    return socket.getaddrinfo(address, ip)[0][-1]


def read_sensor():
    i2c = machine.I2C(scl=machine.Pin(14), sda=machine.Pin(16))
    bme = BME280(i2c=i2c)
    bme.read_compensated_data()  # First read after reset is corrupted.
    return bme.read_compensated_data()


def aprsis_login_line():
    login = ''
    name_splitted = Config.call.split('-')
    if 1 == len(name_splitted):
        login = Config.call
    elif 2 == len(name_splitted):
        login = name_splitted[0]

    # 'user SQ8BRZ pass 19115 vers espudp 0.1\n'
    return 'user ' + login + ' pass ' + Config.passwd + ' vers simpleUDPwx 0.0\n'


def aprs_header():
    return Config.call + '>APRS,TCPIP*:'


def aprs_position():
    return Config.latitude + Config.symbol[0] + Config.longitude + Config.symbol[1]


def aprs_wx():
    # TODO: Add better calculations.
    # TODO: Add calibration.
    t, p, h = read_sensor()

    # Temperature conversion from ºC to ºF
    tf = ((t*9//5)+3200) // 100
    if tf < 100:
        if tf < 10:
            tf = '0' + str(tf)
        tf = '0' + str(tf)
    else:
        tf = str(tf)

    # Humidity formatting
    h //= 1024
    if 99 < h:
        h = '99'
    elif h < 10:
        h = '0' + str(h)
    else:
        h = str(h)

    # Pressure calculation
    p //= 2560
    if 9999 < p:
        p = str(p)[:5]
    else:
        p = '0' + str(p)

    return '000/000g...t' + tf + 'r...p...P...h' + h + 'b' + p


def aprs_wx_frame():
    return aprs_header() + '!' + aprs_position() + aprs_wx() + Config.comment


def aprs_status_frame():
    if isinstance(Config.status, str) and '' != Config.status.strip():
        return aprs_header() + '>' + Config.status
    return None


def udp_send(message, to_addr=None, port=None):
    if to_addr is None:
        return False
    if port is None:
        port = 8080

    message = message.encode('utf-8')
    sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sck.sendto(message, (to_addr, port))


def aprsis_send_frames():
    udp_send(aprsis_login_line() +
             aprs_wx_frame(),
             get_ip_from_addr(Config.servers[0])[0])
    if aprs_status_frame() is not None:
        udp_send(aprsis_login_line() +
                 aprs_status_frame(),
                 get_ip_from_addr(Config.servers[0])[0])


while True:
    if wifi_connect():
        print('Network config:', sta_if.ifconfig())
        aprsis_send_frames()
    wifi_disconnect()
    time.sleep(Config.txDelay * 60)
