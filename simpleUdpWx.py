import time
from classes import Config, Connection, AprsWx

connection = Connection()

while True:
    if connection.connect():
        print('Network config:', connection.ifconfig())
        connection.udp_send_messages(AprsWx.generate_frames(), connection.get_ip_from_config())
        connection.disconnect()

    time.sleep(Config.txDelay * 60)
