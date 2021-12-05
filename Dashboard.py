import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import RPi.GPIO as GPIO
import board, adafruit_dht
import smtplib, ssl, email, imaplib
from time import sleep
import time, sys
import threading as thread
from paho.mqtt import client as mqtt_client

#external_stylesheets = ['']

# Info to connect to the MQTT Broker 
broker = 'localhost'
port = 1883
topic = "SmartHome/Dashboard"
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
# buzzer = which gpio?

autoLed = 26
lightLevel = 512
lightThresh = 50
setLightThresh = False

tempThresh = 30
setTempThresh = False
fanIsOn = False

# Setting up the led GPIO pins to output
GPIO.setup(led, GPIO.OUT)
GPIO.setup(autoLed, GPIO.OUT)

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

# Fetches the info of the DHT11 and RFID reader from the MQTT broker
def subscribe(client: mqtt_client):
    # Assigns the info to variables
    def on_message(client, userdata, msg):
#         print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        global lightLevel
        lightLevel = int(msg.payload.decode())
        lightPercent = (lightLevel / 1024) * 100
        print(f"LightLevel: {lightLevel} LightPercent: {lightPercent}")
    
    client.subscribe(topic)
    client.on_message = on_message

# Creates a client and connects it to the broker
def run_mqtt():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()

# Receives info from the LED button on the dashboard to toggle the LED on or off
def ledToggle(n_clicks):
    
    output = n_clicks % 2
    GPIO.output(led, output)
    
    outputString = ""
    if(output == 1):
        outputString = "LED is ON"
    elif(output == 0):
        outputString = "LED is OFF"
    
    return outputString

# Receives the temperature and humidity from the DHT11
# If the temperature exceeds the threshhold, an email will be sent to the email to turn on a fan or not
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
    print(info)
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


# def checkUser(rfidValue):
#     conn = mariadb.connect(
#     user="root",
#     password="",
#     host="localhost",
#     database="IoT")
#  
#     cursor = mydb.cursor()
#     cursor.execute("SELECT * FROM users WHERE rfid =?", (rfidValue,))
#     valid = cursor.fetchone()
#     if(valid is not None):
#         global name
#         global temp
#         global setTempThresh
#         global setLightThresh
#         global lightThresh
#         global tempThresh
#         name = valid[1]
#         lightThresh = valid[2]
#         tempThresh = valid[3]
#         
#         setTempThresh = True
#         setLightThresh = False
#     else:
#         ringBuzzer()
# 
# def ringBuzzer():
#     GPIO.output(buzzer,GPIO.HIGH)
#     time.sleep(3)
#     GPIO.output(buzzer,GPIO.LOW)

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

# Creates the initial gauge figure for the temperature
tempGauge = go.Figure(go.Indicator(
    mode = "gauge+number+delta",
    value = info[0],
    domain = {'x': [0,1], 'y':[0,1]},
    title = {'text':'Temperature'},
    gauge = {
            'axis':{'range':[-40,50]},
            'steps':[
                {'range':[-40,-20], 'color': "#00008b"},
                {'range':[-20,0], 'color': "#0000ff"},
                {'range':[0,20], 'color': "#ffff00"},
                {'range':[20,40], 'color': "#ffa500"},
                {'range':[40,50], 'color': "#ff0000"}
                ],
            'threshold':{'line':{'color':"#000000", 'width':4}, 'thickness':0.75, 'value': info[0]}
        }

    ))

# Creates the inital gauge figure for the humidity
humGauge = go.Figure(go.Indicator(
    mode = "gauge+number+delta",
    value = info[1],
    domain = {'x': [0,1], 'y':[0,1]},
    title = {'text':'Humidity'},
    gauge = {
            'axis':{'range':[0,100]},
            'steps':[
                {'range':[0,100], 'color': "#ffffff"}
                ],
            'threshold':{'line':{'color':"#000000", 'width':4}, 'thickness':0.75, 'value': info[1]}
        }
    ))

# Creates the layout for the dashboard with HTML and dash components
app.layout = html.Div(children=[
    html.H1(children='IoT Dashboard'),
    html.H2(children='Turn On or Off the Light'),
    html.Button('Toggle Light', id='led_button', value='toggle_light', n_clicks=0),
    html.Div(id='led_output'),
    html.Br(),
    
    html.H2(children='Fan Control'),
    dcc.Input(id='fan_input', type='number', placeholder=tempThresh),
    html.Button('Confirm Threshold', id='fan_button', value='fan_control', n_clicks=0),
    html.Br(),
    
    html.H2(children='Automatic Light Control'),
    dcc.Input(id='light_input', type='number', placeholder='50'),
    html.Button('Confirm Threshold', id='light_threshold', value='light_control', n_clicks=0),
    html.Br(),
    
    dcc.Graph(id='tempGauge', figure=tempGauge),
    dcc.Graph(id='humGauge', figure=humGauge),
    dcc.Interval(id = 'intervalComponent', interval = 1 * 3000, n_intervals = 0),
    html.Div(id='hidden-div', style={'display':'none'})
])

# Calls the ledToggle function when the button on the dashboard is clicked
@app.callback(
    Output('led_output', 'children'),
    [Input('led_button', 'n_clicks')]
)
def update_led_output_div(n):
    return '{}'.format(str(ledToggle(n)))

# Updates the temperature threshold when the button on the dashboard is clicked
@app.callback(
    Output('hidden-div', 'children'),
    [Input('fan_button', 'n_clicks')],
    [State('fan_input','value')],
    )
def update_fan_threshhold(clicks, input_value):
    if clicks is not None:
        global tempThresh
        tempThresh = input_value
        global setTempThresh
        setTempThresh = True
    return input_value

# Updates the light threshold when the button on the dashboard is clicked
@app.callback(
    Output('hidden-div', 'children'),
    [Input('light_threshold', 'n_clicks')],
    [State('light_input','value')],
    )
def update_light_threshhold(clicks, input_value):
    if clicks is not None:
        global lightThresh
        lightThresh = input_value
        global setLightThresh
        setLightThresh = True
    return input_value

# Updates the temperature and humidity gauges with the DHT11 info every 3 seconds 
@app.callback([
    Output('tempGauge', 'figure'),
    Output('humGauge', 'figure')],
    [Input('intervalComponent', 'n_intervals')]
)
def update_gauges(n_intervals):
    info = getDHTinfo()
    tempGauge = go.Figure(go.Indicator(
    mode = "gauge+number+delta",
    value = info[0],
    domain = {'x': [0,1], 'y':[0,1]},
    title = {'text':'Temperature'},
    gauge = {
            'axis':{'range':[-40,50]},
            'steps':[
                {'range':[-40,-20], 'color': "#00008b"},
                {'range':[-20,0], 'color': "#0000ff"},
                {'range':[0,20], 'color': "#ffff00"},
                {'range':[20,40], 'color': "#ffa500"},
                {'range':[40,50], 'color': "#ff0000"}
                ],
            'threshold':{'line':{'color':"#000000", 'width':4}, 'thickness':0.75, 'value': info[0]}
        }

    ))
    humGauge = go.Figure(go.Indicator(
    mode = "gauge+number+delta",
    value = info[1],
    domain = {'x': [0,1], 'y':[0,1]},
    title = {'text':'Humidity'},
    gauge = {
            'axis':{'range':[0,100]},
            'steps':[
                {'range':[0,100], 'color': "#ffffff"}
                ],
            'threshold':{'line':{'color':"#000000", 'width':4}, 'thickness':0.75, 'value': info[1]}
        }
    ))
    return [tempGauge, humGauge]


if __name__ == '__main__':
    app.run_server()
    