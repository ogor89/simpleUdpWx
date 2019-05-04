# simpleUDPwx
Simple, send-only, APRS-IS weather station based on ESP8266 and BME280 sensor.
*Simple* means simple to use, simple to understand and simple to learn on.
It is not recommended to use this software in battery powered projects because it is not using low-power mode of ESP8266.
This project is unstable and delivered "as is".

## Getting started

### Hardware requirements

### Installing

### Configuring
```
class Config:

    wifi_ssid = 'WiFi_name'  # WiFi SSID.
    wifi_passwd = 'WiFi_password'  # WiFi password.
    wifi_timeout = 60

    # List of APRS-IS servers. ( ['server1', 'server2'] )
    # Please make sure all of them supports UDP connection. You can use status.aprs2.net for that.
    servers = ['krakow.aprs2.net', 'euskadi.aprs2.net', 'romania.aprs2.net', 'belgium.aprs2.net']
    txDelay = 5  # Delay between frames (in minutes).

    call = 'N0CALL-1'  # Call with or without suffix.
    passwd = '12345'  # APRS-IS password.
    symbol = '/_'  # Two symbol coded APRS icon.
    latitude = '5000.00N'
    longitude = '01900.00E'
    comment = 'simpleUDP WX station'  # Comment attached to WX data.
    status = ''  # Status sent as separate APRS frame. If None or '' additional frame will not be sent.
```

Parameters needs to be changed:
* wifi_ssid
* wifi_passwd
* call
* passwd
* latitude
* longitude

## Versioning
We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/ogor89/simpleUdpWx/tags).

## Changelog
1.1.0-alpha

Fixes:
* Server IP getting loop now breaks on first active server.

Features:
* TODOs
* Docstrings
* Data normalisation.
* Separate file for classes and functions.
* More "object" approach.
* Version handling in software.

1.0.2

Fixes:
* Fixed wrong argument in UDP sending function call.

1.0.1

Fixes:
* Fixed problem with UDP sending.

Features:
* Multiple server address support.
* New UDP sending approach.
* Better server choosing from configuration.
* Configuration in separated file.

1.0.0

Features:
* BME280 sensor support.
* Calculating weather parameters (rounding down) without calibration.
* Sending APRS packages via UDP.
* Support for position and wx APRS parameters.
* Support for APRS comment frame.

## Known issues
* Can't work with no-DHCP network.

## Plans
1.2.0
* Power saving for ESP8266.
* Power saving for BME280.
* Transmit delay based on interrupt.
* Input voltage monitoring.
* *verbose* configuration parameter.
* DHCP support.
* Complete README.md file.

## Author
**Bartosz Ogrodnik** [ogor89](https://github.com/ogor89)
See also the list of [contributors](https://github.com/ogor89/simpleUdpWx/contributors) who participated in this project.

## License
[GNU GENERAL PUBLIC LICENSE](LICENSE)
Sensor driver:
[bme280](bme280.py) - [GitHub](https://github.com/catdog2/mpy_bme280_esp8266)