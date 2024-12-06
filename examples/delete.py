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
conn = micropg.connect(host='127.0.0.1',
                    user='postgres',
                    password='123456',
                    database='postgres')
cur = conn.cursor()

cur.execute("DELETE FROM customers WHERE id=2;")
conn.commit()
conn.close()
