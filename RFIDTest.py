import mariadb

global name
global temp
global setTempThresh
global setLightThresh
global lightThresh
global tempthresh

conn = mariadb.connect(
    user="root",
    password="",
    host="localhost",
    database="IoT")
 
cursor = conn.cursor()
#cursor.execute("CREATE USER IF NOT EXISTS 'IoTUser'@'localhost' IDENTIFIED BY 'IoTUser'")
cursor.execute("SELECT * FROM users WHERE rfid =?", (9996217154,))
valid = cursor.fetchone()
if(valid is not None):
    global name
    global temp
    global setTempThresh
    global setLightThresh
    global lightThresh
    global tempthresh
    name = valid[1]
    lightThresh = valid[2]
    tempthresh = valid[3]
        
    setTempThresh = True
    setLightThresh = False
        
    print(lightThresh)
    print(tempthresh)
else:
    print("no data in the table")