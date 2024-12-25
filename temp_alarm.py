import os
import glob
import time
import smtplib
from email.message import EmailMessage

# === 1) SETUP FOR TEMPERATURE SENSOR ===

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def read_temp_raw():
    """Read raw lines directly from the sensor file."""
    with open(device_file, 'r') as f:
        lines = f.readlines()
    return lines

def read_temp():
    """
    Parse the raw temperature data and return the temperature in Celsius.
    Returns None if there's a read error.
    """
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()

    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c
    return None

# === 2) SETUP FOR SENDING EMAIL ===

# Replace with your real credentials
from_email_addr = "REPLACE_WITH_SENDER_EMAIL_ADDRESS"
from_email_password = "REPLACE_WITH_SENDER_APP_PASSWORD"
to_email_addr = "REPLACE_WITH_RECIPIENT_EMAIL_ADDRESS"

# Alert for very low temperature
ALERT_SUBJECT = "[ALARM] Temperature Below -12°C!"
ALERT_BODY = """\
Warning! The sensor has measured a temperature below -12°C.
Immediate action may be required.
"""

# Twice-daily status email
STATUS_SUBJECT = "[INFO] Twice-Daily Status Update"
STATUS_BODY = """\
Hello!

This is your twice-daily status update:
- The system is still running.
- The current temperature is {temp_c:.2f}°C.

Regards,
Your Raspberry Pi
"""

def send_email(subject, body):
    """Generic email-sending function."""
    msg = EmailMessage()
    msg.set_content(body)
    msg['From'] = from_email_addr
    msg['To'] = to_email_addr
    msg['Subject'] = subject

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email_addr, from_email_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f"Error sending email: {e}")

def send_temperature_alarm(temp_c):
    """Send an email alert about low temperature (in Celsius)."""
    body = f"{ALERT_BODY}\nCurrent Temperature: {temp_c:.2f}°C"
    send_email(ALERT_SUBJECT, body)

def send_status_email(temp_c):
    """Send a twice-daily status email with the current temperature."""
    body = STATUS_BODY.format(temp_c=temp_c)
    send_email(STATUS_SUBJECT, body)

# === 3) MAIN LOOP ===

def main():
    TEMPERATURE_THRESHOLD = -12.0  # Celsius threshold
    CHECK_INTERVAL = 5            # seconds between temperature checks
    STATUS_EMAIL_INTERVAL = 43200  # 12 hours in seconds

    # Flags and timers to prevent spamming
    alarm_email_sent = False

    # Initialize last_status_email_time so that it triggers an immediate status email.
    # This way, you'll get a status email right after the script starts reading the sensor.
    last_status_email_time = time.time() - STATUS_EMAIL_INTERVAL

    while True:
        temp_c = read_temp()
        if temp_c is not None:
            print(f"Current temperature: {temp_c:.2f}°C")

            # 1) Check for low-temp alarm
            if temp_c < TEMPERATURE_THRESHOLD and not alarm_email_sent:
                send_temperature_alarm(temp_c)
                alarm_email_sent = True
            elif temp_c >= TEMPERATURE_THRESHOLD and alarm_email_sent:
                alarm_email_sent = False

            # 2) Send a status email twice a day
            current_time = time.time()
            if (current_time - last_status_email_time) >= STATUS_EMAIL_INTERVAL:
                send_status_email(temp_c)
                last_status_email_time = current_time

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
