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
