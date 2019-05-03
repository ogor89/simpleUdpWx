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
