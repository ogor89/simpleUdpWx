import machine
import network
import socket
import time
from bme280 import BME280
from config import Config as _Config


class Config(_Config):
    _version = '1.1.0'

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
                print('Sending:')
                print(message)
                sock.sendto(message, (to_addr, self.udp_default_port))


class AprsWx:
    """
    Holds creating of TNC-2 formatted messages for APRS network.
    Additionally it holds BME280 sensor.
    """

    # TODO: Add wake-up and sleep functionality for BME280.
    # TODO: Create separate class for sensor functionality.
    # TODO: Change methods to class variables (with getters only).

    @staticmethod
    def _read_sensor():
        # I2C SCL is on IO14, SDA on IO16
        i2c = machine.I2C(scl=machine.Pin(14), sda=machine.Pin(16))
        bme = BME280(i2c=i2c)
        bme.read_compensated_data()  # First read after reset is corrupted.
        return bme.read_compensated_data()

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

        # 'user SQ8BRZ pass 19115 vers espudp 0.1\n'
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
        # TODO: Add pressure normalisation.
        # TODO: test normalization.
        t, p, h = AprsWx._read_sensor()

        # Temperature conversion from ºC to ºF
        tf = ((AprsWx._normalize_temperature(t)*9//5)+3200) // 100
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
        p = AprsWx._normalize_pressure(p, t / 100)
        p //= 10
        if 9999 < p:
            p = str(p)[:5]
        else:
            p = '0' + str(p)[:4]

        # g, r, p and P parameters are not supported.
        return '000/000g...t' + tf + 'r...p...P...h' + h + 'b' + p

    @staticmethod
    def _wx_frame():
        """
        Returns complete TNC-2 formatted WX frame.
        '!' after header means station can't respond for messages (Tx only).
        :return: str
        """
        return AprsWx._header() + '!' + AprsWx._position() + AprsWx._calculate_wx() + Config.comment

    @staticmethod
    def _status_frame():
        """
        Returns complete TNC-2 formatted status frame.
        Can be used as additional comment.
        :return: str
        """
        if isinstance(Config.status, str) and '' != Config.status.strip():
            return AprsWx._header() + '>' + Config.status
        return None

    @staticmethod
    def generate_frames():
        """
        Returns list with TNC-2 formatted frames.
        :return: list of str
        """
        messages = [AprsWx._is_login_line() + AprsWx._wx_frame()]
        if AprsWx._status_frame() is not None:
            messages = messages + [AprsWx._is_login_line() + AprsWx._status_frame()]
        return messages
