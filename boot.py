# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
import uos, machine
# uos.dupterm(None, 1) # disable REPL on UART(0)
import network
import gc
# import webrepl
import time
# webrepl.start()
gc.collect()

boot_sta_if = network.WLAN(network.STA_IF)
if boot_sta_if.isconnected():
    boot_sta_if.disconnect()
boot_sta_if.active(False)

time.sleep(10)

import simpleUdpWx
