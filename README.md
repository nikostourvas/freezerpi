# ForGen Lab FreezerPi
This work is based on the awesome scripts provided by randomnerdtutorials.com

https://RandomNerdTutorials.com/raspberry-pi-motion-email-python/

https://RandomNerdTutorials.com/raspberry-pi-ds18b20-python/

https://github.com/adafruit/Adafruit_Learning_System_Guides/blob/main/Raspberry_Pi_DS18B20_Temperature_Sensing/code.py

## Hardware
- Raspberry Pi 4
- Ds18b20 temperature sensor

## Software

### How to connect your pi to eduroam
This assumes you already have access to your pi in headless mode.

Use the following where <connection_name> is just a name you give this connection (example: "SchoolWifi") and < ssid > is, you guessed it, the SSID (so "eduroam")
```
sudo nmcli connection add type wifi con-name "<connection_name>" ifname wlan0 ssid "<ssid>"
```

Here you set up authentication (put in your username and password). <connection_name> is the name you gave it earlier (in my example this would be "SchoolWifi"). <your_username> is the username you use to log into the eduroam network on your phone, for example. Usually it's the email given to you by the school (example: John123@University.com). <your_password> is the password you use, along with the username, when logging into the wifi (example: badpassword123)
```
sudo nmcli connection modify "<connection_name>" wifi-sec.key-mgmt wpa-eap 802-1x.eap peap 802-1x.phase2-auth mschapv2 802-1x.identity "<your_username>" 802-1x.password "<your_password>"
```

(Only if necessary) Add a CA certificate:
```
sudo nmcli connection modify "<connection_name>" 802-1x.ca-cert "/path/to/ca_cert.pem"
```
(optional) Adding priorities to the networks on your device. For me, after completing steps 1 and 2 I then had 2 networks saved; "eduroam" and "preconfigured"; if you don't have a keyboard and monitor for the raspberry pi and ssh is your only way of communicating with the device you should put a priority on the 2 networks so that if anything goes wrong it will connect to the original network on reboot. I say this because I was unable to ssh to my raspberry pi through the eduroam network. You add priorities with the following:

```
sudo nmcli connection modify "<connection_name>" connection.autoconnect-priority <number>
```
You can see the saved networks
```
nmcli connection show
```


### Temperature sensor
1) Place the temp_alarm.py script under the path `/home/pi/` (assumming your username is "pi")

2) Create a new file in /etc/systemd/system/. We will call it temp_alarm.service (see temp_alarm.service in the repo).

3) Enable and Start the Service

Reload systemd to read your new service file:
`sudo systemctl daemon-reload`

Enable the service at boot:
`sudo systemctl enable temp_alarm.service`

Start the service right now (for testing):
`sudo systemctl start temp_alarm.service`

Check the status to see if it’s running:
`systemctl status temp_alarm.service`

You should see output indicating the service is active (running), along with any logs printed by your Python script.


4) Verify at Reboot
Reboot your Pi:
`sudo reboot`

After the Pi boots:
`systemctl status temp_alarm.service`

If everything is correct, the service should show as active (running) and your script will autostart each time the Pi boots.
