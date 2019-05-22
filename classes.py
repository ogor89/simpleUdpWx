import machine
import network
import socket
import time
from bme280 import BME280
from config import Config as _Config


class Config(_Config):
    _version = '1.2.0-alpha.1'

    @staticmethod
    @property
    def version():
        return Config._version

    def __init__(self):
        pass


class Connection:
    """
    Class holds WiFi connection and sends TNC-2 formatted data to APTS-IS network.
    """
    # TODO: Add variable to hold time spent on connecting.

    _udp_default_port = 8080
    # TODO: Getter & setter for sta_if?
    sta_if = None

    @property
    def udp_default_port(self):
        """
        Returns default UDP port for APRS-IS connection.
        There is no setter.
        :return: int
        """
        return self._udp_default_port

    def __init__(self):
        self.sta_if = network.WLAN(network.STA_IF)

    def connect(self):
        """
        Activates WiFi interface nad connects to WiFi AP.
        When connects returns True, if interface is not connected after timeout time returns False.
        :return: bool
        """
        # TODO: Test with no delay time after connection.
        connected = False
        if not self.sta_if.isconnected():
            print('Connecting...')
            self.sta_if.active(True)
            self.sta_if.connect(Config.wifi_ssid, Config.wifi_passwd)

            for timestep in range(0, Config.wifi_timeout):
                print(timestep + 1, end=' ')
                time.sleep(1)
                if self.sta_if.isconnected():
                    connected = True
                    print('Connected!')
                    # Delay time
                    time.sleep(2)
                    break
        else:
            connected = True

        return connected

    def disconnect(self):
        """
        Deactivates WiFi interface. Disconnecting from AP is not needed.
        :return: None
        """
        # TODO: Test with no delay time before disconnecting.
        # TODO: Add bool return.
        print('disconnecting...')
        # Delay time
        time.sleep(2)
        self.sta_if.active(False)

    def ifconfig(self):
        """
        Returns current network configuration:
        (ip, subnet, gateway, dns)
        :return: tuple
        """
        return self.sta_if.ifconfig()

    def get_ip_from_config(self):
        """
        Gets IP of first active server from configuration.
        :return: str
        """
        ip = None
        for server in Config.servers:
            try:
                ip = socket.getaddrinfo(server, self.udp_default_port)[0][-1][0]
            except Exception:
                # TODO: Change to correct exception.
                continue
            break
        return ip

    def udp_send_messages(self, messages, to_addr):
        """
        Sends messages from given list to given IP address.
        Each message will be sent separately.
        :param messages: list of str
        :param to_addr: str
        :return: None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if isinstance(messages, list):
            for message in messages:
                message = message.encode('utf-8')
                # print('Sending:')
                # print(message)
                sock.sendto(message, (to_addr, self.udp_default_port))


class Aprs:
    """
    Holds creating of TNC-2 formatted messages for APRS network.
    """

    # TODO: Add wake-up and sleep functionality for BME280.
    # TODO: Create separate class for sensor functionality.
    # TODO: Change methods to class variables (with getters only). Think about that.

    @staticmethod
    def _is_login_line():
        """
        Generates APRS-IS login frame.
        :return: str
        """
        login = ''
        name_splitted = Config.call.split('-')
        if 1 == len(name_splitted):
            login = Config.call
        elif 2 == len(name_splitted):
            login = name_splitted[0]

        return 'user ' + login + ' pass ' + Config.passwd + ' vers simpleUDPwx 0.0\n'

    @staticmethod
    def _header():
        """
        APRS header. Call and destination.
        :return: str
        """
        return Config.call + '>APRS,TCPIP*:'

    @staticmethod
    def _position():
        """
        Position with combined symbol.
        :return: str
        """
        return Config.latitude + Config.symbol[0] + Config.longitude + Config.symbol[1]

    @staticmethod
    def _status_frame():
        """
        Returns complete TNC-2 formatted status frame.
        Can be used as additional comment.
        :return: str
        """
        if isinstance(Config.status, str) and '' != Config.status.strip():
            return Aprs._header() + '>' + Config.status
        return None

    @staticmethod
    def generate_main_frames():
        """
        Returns list with TNC-2 formatted status frame if status is configured. If not - returns empty list.
        :return: list of str
        """
        messages = []
        if Aprs._status_frame() is not None:
            messages = messages + [Aprs._is_login_line() + Aprs._status_frame()]
        return messages


class AprsWx(Aprs):
    """
    Holds creating of TNC-2 formatted weather messages for APRS network.
    Additionally it holds BME280 sensor.
    """
    @staticmethod
    def _read_sensor():
        # I2C SCL is on IO12, SDA on IO14
        i2c = machine.I2C(scl=machine.Pin(12), sda=machine.Pin(14))
        bme = BME280(i2c=i2c)
        bme.read_compensated_data()  # First read after reset is corrupted.
        return bme.read_compensated_data()

    @staticmethod
    def _normalize_temperature(absolute_temperature):
        """
        Returns temperature normalized to sea level from measured temperature and altitude from configuration.
        :param absolute_temperature: float
        :return: float
        """
        return absolute_temperature + (0.6 * Config.altitude) / 100

    @staticmethod
    def _normalize_pressure(absolute_pressure, absolute_temperature):
        """
        Returns pressure normalized to sea level from given parameters and altitude from configuration.
        :param absolute_pressure: float
        :param absolute_temperature: float
        :return: float
        """
        # TODO: Rename variables to english.
        tsr = (absolute_temperature + AprsWx._normalize_temperature(absolute_temperature)) / 2
        sb = 8000 * ((1 + 0.004 * tsr) / absolute_pressure)
        p = absolute_pressure + (Config.altitude / sb)
        p_sr = (absolute_pressure + p) / 2
        sb = 8000 * ((1 + 0.004 * tsr) / p_sr)
        return absolute_pressure + (Config.altitude / sb)

    @staticmethod
    def _calculate_wx():
        # TODO: Rename to _wx.
        """
        Returns WX part of APRS WX frame with position.
        :return: str
        """
        # TODO: Improve calculations (rounding).
        t, p, h = AprsWx._read_sensor()

        # Temperature conversion from ºC to ºF
        if Config.normalize_temperature:
            tf = AprsWx._normalize_temperature(t)
        else:
            tf = t
        tf = ((tf*9//5)+3200) // 100
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
        p //= 256
        if Config.normalize_pressure:
            p = AprsWx._normalize_pressure(p, t / 100)
        p //= 10
        if 9999 < p:
            p = str(p)[:5]
        else:
            p = '0' + str(p)[:4]

        # g, r, p and P parameters are not supported.
        return '000/000g...t' + tf + 'r...p...P...h' + h + 'b' + p

    @staticmethod
    def wx_frame():
        """
        Returns complete TNC-2 formatted WX frame.
        '!' after header means station can't respond for messages (Tx only).
        :return: str
        """
        return AprsWx._header() + '!' + AprsWx._position() + AprsWx._calculate_wx() + Config.comment

    @staticmethod
    def generate_wx_frames():
        """
        Returns list with TNC-2 formatted frame.
        :return: list of str
        """
        return [Aprs._is_login_line() + AprsWx.wx_frame()]


class AprsTelemetry(Aprs):
    """
    Holds creating of TNC-2 formatted telemetry messages for APRS network.
    Additionally it holds ADC.
    """
    # TODO: Calculate _telemetry_no from RTC and Config.txDelay.
    # TODO: Prepare all methods for all telemetry frames (T PARM UNIT EQNS (maybe BITS)).
    # TODO: Docstrings in class.

    _telemetry_no = None

    @property
    def telemetry_no(self):
        if 999 < self._telemetry_no:
            self._telemetry_no = 0
        telemetry_no = str(self._telemetry_no)
        self._telemetry_no += 1
        zero_no = 3 - len(telemetry_no)
        return '0' * zero_no + telemetry_no

    def __init__(self):
        self._telemetry_no = 0

    @staticmethod
    def _calculate_voltage(adc=0):
        """
        Calculates voltage for telemetry values frame.
        "adc" parameter is 0 to 1024 voltage measured by "machine.ADC(0).read()".
        Returns 3 digit string, human readable - dividing by 10 gives voltage in V.
        :param adc: int
        :return: str
        """
        # 0 -> 0.0V; 1024 -> 1.0V
        voltage = round((Config.adc_r / Config.adc_r_total) * adc)
        if voltage > 255:
            voltage = 255

        voltage = str(voltage)
        zero_no = 3 - len(voltage)
        return '0' * zero_no + voltage

    @staticmethod
    def _calculate_hires_voltage(adc=0):
        """
        Calculates voltage for telemetry values frame.
        "adc" parameter is 0 to 1024 voltage measured by "machine.ADC(0).read()".
        Returns 3 digit string with better resolution than _calculate_voltage(), but less human readable.
        :param adc: int
        :return: str
        """
        voltage = round((Config.adc_r / Config.adc_r_total * 10 / 2) * adc)
        if voltage > 255:
            voltage = 255

        voltage = str(voltage)
        zero_no = 3 - len(voltage)
        return '0' * zero_no + voltage

    def _calculate_telemetry_no(self, rtc_datetime):
        rtc_datetime = (rtc_datetime[4] * 60 + rtc_datetime[5]) // Config.txDelay
        # TODO: Remove print.
        # print("Telemetry frame:  ", rtc_datetime)
        rtc_datetime = str(rtc_datetime)
        zero_no = 3 - len(rtc_datetime)
        return '0' * zero_no + rtc_datetime

    def _telemetry_values_frame(self, raport_no):
        """
        Creates telemetry values frame.
        Not used parameters are 0 because of problems with some interpreters like aprs.fi.
        :return: str
        """
        # TODO: Report issue on GitHub for aprs.fi.
        adc = machine.ADC(0).read()
        # return Aprs._header() + 'T#' + self._calculate_telemetry_no(raport_no) + ',' + \
        return Aprs._header() + 'T#' + raport_no + ',' + \
            AprsTelemetry._calculate_voltage(adc) + ',' + \
            AprsTelemetry._calculate_hires_voltage(adc) + ',000,000,000,00000000'

    def _telemetry_parameters_frame(self):
        """
        Creates telemetry parameters name frame.
        Not used parameters are named because of problems with some interpreters like aprs.fi.
        :return: str
        """
        return Aprs._header() + ':' + Config.call + ' :PARM.Vbat10,Vbat5,val3,val4,val5'

    def _telemetry_units_frame(self):
        """
        Creates telemetry units frame.
        Not used parameters are named because of problems with some interpreters like aprs.fi.
        :return: str
        """
        return Aprs._header() + ':' + Config.call + ' :UNIT.V,V,u3,u4,u5'

    def _telemetry_equasions_frame(self):
        """
        Creates telemetry equations frame.
        Not used parameters are 0 because of problems with some interpreters like aprs.fi.
        :return: str
        """
        return Aprs._header() + ':' + Config.call + ' :EQNS.0,0.1,0, 0,0.02,0,0,0,0,0,0,0,0,0,0'

    def generate_telemetry_frames(self, raport_no):
        """
        Returns list with TNC-2 formatted frames for telemetry reporting.
        :return: list of str
        """
        return [Aprs._is_login_line() + self._telemetry_values_frame(raport_no),
                Aprs._is_login_line() + self._telemetry_parameters_frame(),
                Aprs._is_login_line() + self._telemetry_units_frame(),
                Aprs._is_login_line() + self._telemetry_equasions_frame()]
