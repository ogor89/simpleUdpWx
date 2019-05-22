import time
import machine
import network
from classes import Config, Connection, Aprs, AprsWx, AprsTelemetry

# TODO: Add sleep based on RTC.

rtc = machine.RTC()
connection = Connection()
telemetry = AprsTelemetry()


def calculate_raport_no(rtc_datetime):
    rtc_datetime = (rtc_datetime[4] * 60 + rtc_datetime[5]) // Config.txDelay
    print("Telemetry frame:  ", rtc_datetime)
    if rtc_datetime > 999:
        rtc_reset()
        rtc_datetime = 0
    rtc_datetime = str(rtc_datetime)
    zero_no = 3 - len(rtc_datetime)
    return '0' * zero_no + rtc_datetime


def rtc_reset():
    rtc.datetime((2000, 1, 1, 5, 0, 0, 0, 0))


def main_routine(sleep_time):
    # Configure RTC.ALARM0 to be able to wake the device.
    # rtc = machine.RTC()
    rtc_datetime = rtc.datetime()
    print('\n\nRTC: ', rtc_datetime)
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)

    while True:
        # TODO: Unneeded loop because of deepsleep.
        # Set RTC.ALARM0 to fire after sleep_time minutes (waking the device).
        rtc.alarm(rtc.ALARM0, sleep_time * 60000)

        frames = Aprs.generate_main_frames() + \
            AprsWx.generate_wx_frames() + \
            telemetry.generate_telemetry_frames(calculate_raport_no(rtc_datetime))
        if connection.connect():
            print('Network config:', connection.ifconfig())
            connection.udp_send_messages(frames, connection.get_ip_from_config())
            connection.disconnect()

        print("Go to sleep...")
        machine.deepsleep()
        # time.sleep(sleep_time * 60)


if machine.reset_cause() != machine.DEEPSLEEP_RESET:
    print('\nDeactivating WLAN...')
    boot_sta_if = network.WLAN(network.STA_IF)
    boot_sta_if.active(False)
    time.sleep(10)

main_routine(Config.txDelay)
