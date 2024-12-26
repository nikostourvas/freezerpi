import os
import glob
import time
import smtplib
from email.message import EmailMessage

# === 1) SETUP FOR TEMPERATURE SENSORS ===

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
# Find *all* DS18B20 sensor folders that start with '28'
device_folders = glob.glob(base_dir + '28*')

# Each sensor has a file called 'w1_slave' that holds temperature data
device_files = [f"{folder}/w1_slave" for folder in device_folders]

def read_temp_raw(device_file):
    """Read raw lines directly from one sensor's file."""
    with open(device_file, 'r') as f:
        lines = f.readlines()
    return lines

def read_temp(device_file):
    """
    Parse raw temperature data from a single sensor's file and return in °C.
    Returns None if there's a read error.
    """
    lines = read_temp_raw(device_file)
    # Wait until the first line ends with 'YES'
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(device_file)

    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c
    return None

# === 2) SETUP FOR SENDING EMAIL ===

# Replace with your credentials
from_email_addr = "REPLACE_WITH_SENDER_EMAIL_ADDRESS"
from_email_password = "REPLACE_WITH_SENDER_APP_PASSWORD"
to_email_addr = "REPLACE_WITH_RECIPIENT_EMAIL_ADDRESS"

ALERT_SUBJECT_TEMPLATE = "[ALARM] {sensor_name} Temperature Below -12°C!"
ALERT_BODY_TEMPLATE = """\
Warning! {sensor_name} has measured a temperature below -12°C.
Immediate action may be required.

Current Temperature: {temp_c:.2f}°C
"""

STATUS_SUBJECT = "[INFO] Twice-Daily Status Update"
STATUS_BODY_TEMPLATE = """\
Hello!

This is your twice-daily status update:
- The system is still running.
- Current temperatures for each sensor:
{sensor_readings}

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

def send_temperature_alarm(sensor_name, temp_c):
    """Send an email alert about low temperature (in Celsius) for a specific sensor."""
    subject = ALERT_SUBJECT_TEMPLATE.format(sensor_name=sensor_name)
    body = ALERT_BODY_TEMPLATE.format(sensor_name=sensor_name, temp_c=temp_c)
    send_email(subject, body)

def send_status_email(temps):
    """
    Send a twice-daily status email with all sensor readings.
    `temps` is a list of (sensor_name, temp_c).
    """
    # Build a readable string of sensor temperatures
    sensor_lines = []
    for sensor_name, temp_c in temps:
        sensor_lines.append(f"  - {sensor_name}: {temp_c:.2f}°C")
    sensor_readings_str = "\n".join(sensor_lines)

    body = STATUS_BODY_TEMPLATE.format(sensor_readings=sensor_readings_str)
    send_email(STATUS_SUBJECT, body)

# === 3) MAIN LOOP (MULTI-SENSOR LOGGING & ALARM) ===

def main():
    TEMPERATURE_THRESHOLD = -12.0  # Celsius threshold
    CHECK_INTERVAL = 5            # seconds between temperature checks
    STATUS_EMAIL_INTERVAL = 43200  # 12 hours in seconds

    # Track alarm states individually for each sensor
    # alarm_email_sent[i] = True if we have already sent an alarm for sensor i
    alarm_email_sent = [False] * len(device_files)

    # Initialize so we send a status email immediately on first loop
    last_status_email_time = time.time() - STATUS_EMAIL_INTERVAL

    # CSV log file path
    log_file_path = "/home/pi/temperature_log.csv"

    # Optionally: write a header row if file doesn't exist yet (simple check):
    # import os
    # if not os.path.isfile(log_file_path):
    #     with open(log_file_path, "w") as f:
    #         f.write("timestamp," + ",".join([f"sensor{i+1}" for i in range(len(device_files))]) + "\n")

    # For better labeling, create names for each sensor (optional).
    # For example, "Freezer A", "Freezer B", etc.
    # By default, we’ll just use sensor index or partial ID.
    sensor_names = []
    for i, folder in enumerate(device_folders):
        # or parse the folder name for ID: e.g. "28-abcdef123456"
        sensor_id = folder.split('/')[-1]  # e.g. "28-abcdef123456"
        # we can shorten or just keep the entire ID
        sensor_names.append(f"Sensor {i+1} ({sensor_id})")

    while True:
        # Read all sensor temperatures
        temps = []
        for dev_file, sensor_name in zip(device_files, sensor_names):
            temp_c = read_temp(dev_file)
            if temp_c is not None:
                temps.append((sensor_name, temp_c))
            else:
                # In case of read error, store None
                temps.append((sensor_name, None))

        # Log and handle alarms only if we have at least one valid reading
        if temps:
            # 1) Print to console & build data for logging
            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
            log_line_values = [timestamp_str]

            for i, (sensor_name, temp_c) in enumerate(temps):
                if temp_c is not None:
                    print(f"{sensor_name}: {temp_c:.2f}°C")
                    log_line_values.append(f"{temp_c:.2f}")

                    # Check alarm logic for this sensor
                    if temp_c < TEMPERATURE_THRESHOLD and not alarm_email_sent[i]:
                        send_temperature_alarm(sensor_name, temp_c)
                        alarm_email_sent[i] = True
                    elif temp_c >= TEMPERATURE_THRESHOLD and alarm_email_sent[i]:
                        alarm_email_sent[i] = False
                else:
                    print(f"{sensor_name}: ERROR reading temperature")
                    log_line_values.append("ERROR")

            # 2) Write to CSV log
            with open(log_file_path, "a") as logf:
                # e.g. "2024-12-25 12:00:00, -10.50, -8.25, 3.47, ..."
                logf.write(",".join(log_line_values) + "\n")

            # 3) Twice-daily status email
            current_time = time.time()
            if (current_time - last_status_email_time) >= STATUS_EMAIL_INTERVAL:
                # Send single email containing all sensor info
                send_status_email(temps)
                last_status_email_time = current_time

        # Wait until next interval
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
