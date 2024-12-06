import network   # Handles the wifi connection
import micropg
import time

### To Do: Fill in your wifi connection data
ssid = 'WifiName'
password = 'Secret'

# Connect to network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    print("Wifi Status: ", wlan.status())
    time.sleep(1)

print("Wifi connected")

### To Do: Fill in your server connection data
db_host = '127.0.0.1'
db_user = 'postgres'
db_password = '123456'

# EXAMPLE: Create Database
micropg.create_database(
    host=db_host, user=db_user, password=db_password, database='testDatabase'
)

# EXAMPLE: Drop Database
micropg.drop_database(
    host=db_host, user=db_user, password=db_password, database='testDatabase'
)