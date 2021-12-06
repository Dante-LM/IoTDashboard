import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output, State
import RPi.GPIO as GPIO
import board, adafruit_dht
import smtplib, ssl, email, imaplib
from time import sleep
import time, sys
import threading as thread
from paho.mqtt import client as mqtt_client
import mariadb

# external_stylesheets = ['']

# Info to connect to the MQTT Broker 
broker = 'localhost'
port = 1883
lightTopic = "SmartHome/Dashboard/lightValue"
rfidTopic = "SmartHome/Dashboard/rfid"
topics = [(lightTopic, 0), (rfidTopic, 0)]
client_id = '1'

# Setting the GPIO pin for the DHT11 temperature/humidity sensor
dhtDevice = adafruit_dht.DHT11(board.D21)

app = dash.Dash(__name__)

# Setting the GPIO board mode and turning off warnings
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Setting the GPIO pins for the motor
Motor1A = 17
Motor1B = 27
Motor1E = 22

# Setting the GPIO pins and variables for the different components
led = 13
buzzer = 5

autoLed = 26
lightLevel = 512
lightPercent = 40
lightThresh = 50
setLightThresh = False

tempThresh = 30
setTempThresh = False
fanIsOn = False

# Setting up the led GPIO pins to output
GPIO.setup(led, GPIO.OUT)
GPIO.setup(autoLed, GPIO.OUT)
GPIO.setup(buzzer, GPIO.OUT)

# Connects the dashboard to the MQTT broker
def connect_mqtt():
    # Verifies the MQTT is connected
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

# Fetches the info for the current liht level from the MQTT broker
def subscribe(client: mqtt_client):
    # Assigns the info to variables
    def on_message(client, userdata, msg):
        if(msg.topic == 'SmartHome/Dashboard/rfid'):
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            rfid = msg.payload.decode()
            checkUser(rfid)
            rfid = ""
        if(msg.topic == 'SmartHome/Dashboard/lightValue'):
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            global lightLevel, lightPercent
            lightLevel = int(msg.payload.decode())
            lightPercent = round((lightLevel / 1024) * 100)    
    client.subscribe(topics)
    client.on_message = on_message

# Creates a client, connects it to the broker, and subscribes to the topics
def run_mqtt():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()

# Receives info from the LED button on the dashboard to toggle the LED on or off
def ledToggle(value):
    
    GPIO.output(led, value)
    
    outputString = ""
    if(value == True):
        outputString = "LED is ON"
    elif(value == False):
        outputString = "LED is OFF"
    
    return outputString

# Receives the temperature and humidity from the DHT11.
# If the temperature exceeds the threshhold, an email will
# be sent to the email to turn on a fan or not
def getDHTinfo():
    currentTemp = dhtDevice.temperature
    currentHumidity = dhtDevice.humidity
    global setTempThresh
    if(currentTemp > tempThresh and setTempThresh and not fanIsOn): 
        sendEmail("Temperature exceeds threshhold, would you like to turn on fan?")
        noReply = True
        setTempThresh = False
        while(noReply):
            reply = receiveEmailChecker()
            if(reply != "Nothing"):
                noReply = False
                if(reply == "yes"):
                    turnOnFan()
                    
    info = [currentTemp, currentHumidity]
    return info

# Turns the motor on
def turnOnFan():
    global fanIsOn
    fanIsOn = True
    GPIO.setup(Motor1A,GPIO.OUT)
    GPIO.setup(Motor1B,GPIO.OUT)
    GPIO.setup(Motor1E,GPIO.OUT)
    pulse = GPIO.PWM(22,100)
    pulse.start(10)
    time.sleep(3)
    turnOffFan()

# Turns the motor off
def turnOffFan():
    global fanIsOn
    fanIsOn = False
    GPIO.setup(Motor1A,GPIO.OUT)
    GPIO.setup(Motor1B,GPIO.OUT)
    GPIO.setup(Motor1E,GPIO.OUT)
    GPIO.output(Motor1A, GPIO.LOW)

# Checks if the current light level is below the threshold. Turns on the lights if it is
def lightLevelCheck(currentPercent):
    global lightThresh
    if(currentPercent < lightThresh):
        GPIO.output(autoLed, 1)
#         sendEmail('The automatic lights have turned on.')
    else:
        GPIO.output(autoLed, 0)
#         sendEmail('The automatic lights have turned off.')
        

def checkUser(rfidValue):
    conn = mariadb.connect(
    user="root",
    password="",
    host="localhost",
    database="IoT")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE rfid =?", (rfidValue,))
    valid = cursor.fetchone()
    if(valid is not None):
        print("valid user")
        global name, temp, setTempThresh, setLightThresh, lightThresh, tempThresh
        name = valid[1]
        sendEmail('{} has entered the house.'.format(name))
        lightThresh = valid[2]
        tempThresh = valid[3]
        
        setTempThresh = True
        setLightThresh = False        
    else:
        ringBuzzer()

def ringBuzzer():
    GPIO.output(buzzer,GPIO.HIGH)
    time.sleep(1)
    GPIO.output(buzzer,GPIO.LOW)

# Sends an email with the given text
def sendEmail(text):
    sender ="dantelomonaco.iot@gmail.com"
    password = "vanieriotemail321"
    receiver = "dantelomonaco.iot2@gmail.com"
    port = 465
    subject = "From Dante's RPI"
    message = 'Subject: {}\n\n{}'.format(subject, text)
    context = ssl.create_default_context()
    print("sending")
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, message)
        print("sent email!")

# Checks the inbox for any new emails and checks if the fan should be turned on or off
def receiveEmailChecker() :
    while True:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login('dantelomonaco.iot@gmail.com', 'vanieriotemail321')
        mail.list()
        mail.select("inbox") # connect to inbox.
        result, data = mail.search(None, "(UNSEEN)")

        ids = data[0]
        id_list = ids.split() 
        if(len(id_list)) > 0:
            latest_email_id = id_list[-1] 
        else:
            return "Nothing"
        result, data = mail.fetch(latest_email_id, "(RFC822)")
        raw_email = data[0][1] 
        decoded_data = email.message_from_string(raw_email.decode("utf-8"))
        if type(decoded_data.get_payload()[0]) is str:
            break
        else:
            text = decoded_data.get_payload()[0].get_payload();
            answer1 = text[0:3].lower()
            answer2 = text[0:2].lower()
            if(str(answer1) == "yes" or str(answer2) == "yes"):
                return "yes"
            elif(str(answer1) == "no" or str(answer2) == "no"):
                return "no"
            else:
                return "Invalid"

# Gets the initial info from the DHT11
info = getDHTinfo()

# Creates a new thread to run the MQTT subsribing method
try:
    thread.Thread(target=run_mqtt, args=(), name='MQTT-Thread', daemon=True).start()
except:
    print ("Error: unable to start thread")

# Creates the layout for the dashboard with HTML and dash components
app.layout = html.Div(
# style={'backgroundColor':'black',
#        'color':'#3479f3'},
children=[
    html.H1(children='IoT Dashboard'),
    html.H2(children='Turn On or Off the Light'),
    daq.ToggleSwitch(
        id='led_button',
        value=False,
        color='#3479f3',
        label='Light Toggle',
        labelPosition='bottom'
    ),
    html.Div(id='led_output'),
    html.Br(),
    
    html.H2(children='Fan Control'),
    daq.Slider(
        id='fan_input',
        color='#3479f3',
        min=-40,
        max=50,
        value=tempThresh,
        step=1,
    ),
    html.Div(id='fan_input_value'),
    
    html.Br(),
    
    html.H2(children='Automatic Light Control'),
    daq.Slider(
        id='light_input',
        color='#3479f3',
        min=0,
        max=100,
        value=lightThresh,
        step=1,
    ),
    html.Div(id='light_input_value'),

    html.Br(),

    daq.Gauge(id='tempGauge',
              label='Temperature',
              color={'gradient':True,
                     'ranges':{
                         '#00008b':[-40,-20],
                         '#0000ff':[-20,0],
                         '#ffff00':[0,20],
                         '#ffa500':[20,40],
                         '#ff0000':[40,50]}},
              scale={'start':-40,
                     'interval':5,
                     'labelInterval':2},
              showCurrentValue=True,
              units='\xb0 C', value=info[0],
              max=50,
              min=-40),
    daq.Gauge(id='humGauge',
              label='Humidity',
              color='#3479f3',
              showCurrentValue=True,
              units='%',
              value=info[1],
              max=100,
              min=0),
    daq.Gauge(id='lightGauge',
              label='Light Level',
              color='#3479f3',
              showCurrentValue=True,
              units='%',
              value=lightPercent,
              max=100,
              min=0),
    
    dcc.Interval(id = 'intervalComponent', interval = 1 * 3000, n_intervals = 0),
    html.Div(id='hidden-div', style={'display':'none'}),
    html.Div(id='hidden-div2', style={'display':'none'})
])

# Calls the ledToggle function when the button on the dashboard is clicked
@app.callback(
    Output('led_output', 'children'),
    [Input('led_button', 'value')]
)
def update_led_output_div(value):
    return '{}'.format(ledToggle(value))

# Updates the fan threshold when the value of the slider is changed
@app.callback(
    dash.dependencies.Output('fan_input_value', 'children'),
    [dash.dependencies.Input('fan_input', 'value')])
def update_output(value):
    return 'You have selected "{}"'.format(value)

# Updates the light threshold when the value of the slider is changed
@app.callback(
    dash.dependencies.Output('light_input_value', 'children'),
    [dash.dependencies.Input('light_input', 'value')])
def update_output(value):
    global lightThresh, lightPercent
    lightThresh = value
    lightLevelCheck(lightPercent)
    return 'You have selected "{}"'.format(value)

# Update the temperature and humidity gauges every 3 seconds
@app.callback([
    Output('tempGauge', 'value'),
    Output('humGauge', 'value')],
    [Input('intervalComponent', 'n_intervals')]
)
def update_dht_gauges(n_intervals):
    info = getDHTinfo()
    return [info[0], info[1]]

# Updates the light level gauge with the MQTT broker info every 3 seconds 
@app.callback([
    Output('lightGauge', 'value')],
    [Input('intervalComponent', 'n_intervals')]
)
def update_light_gauge(n_intervals):
    lightLevelCheck(lightPercent)
    return [lightPercent]
    
if __name__ == '__main__':
    app.run_server()
    