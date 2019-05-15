import time
from classes import Config, Connection, Aprs, AprsWx, AprsTelemetry

# TODO: Add sleep based on RTC.

connection = Connection()
telemetry = AprsTelemetry()


def main_routine(sleep_time):
    while True:
        frames = Aprs.generate_main_frames() + AprsWx.generate_wx_frames() + telemetry.generate_telemetry_frames()
        if connection.connect():
            print('Network config:', connection.ifconfig())
            connection.udp_send_messages(frames, connection.get_ip_from_config())
            connection.disconnect()

        time.sleep(sleep_time * 60)

main_routine(Config.txDelay)
