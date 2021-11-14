import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import RPi.GPIO as GPIO
import board, adafruit_dht
import smtplib, ssl, email, imaplib
from time import sleep
import time

#external_stylesheets = ['']

global currentTemp
global currentHumidity
global led
global tempThresh
global lightThresh
global setTempThresh

dhtDevice = adafruit_dht.DHT11(board.D26)

app = dash.Dash(__name__)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

Motor1A = 17
Motor1B = 27
Motor1E = 22

led = 13

setTempThresh = False
 
GPIO.setup(led, GPIO.OUT)

def ledToggle(n_clicks):
    
    output = n_clicks % 2
    GPIO.output(led, output)
    
    outputString = ""
    if(output == 1):
        outputString = "LED is ON"
    elif(output == 0):
        outputString = "LED is OFF"
    
    return outputString

def getDHTinfo():
    currentTemp = dhtDevice.temperature
    currentHumidity = dhtDevice.humidity
    if(currentTemp >= tempThresh && setTempthresh):
        sendEmail("Temperature exceeds threshhold, would you like to turn on fan?")
        noReply = True
        while(noReply):
            reply = receiveEmailChecker()
            if(reply != "Nothing"):
                noReply = False
                
        if(reply == "yes"):
            turnOnFan()
            
    info = [currentTemp, currentHumidity]
    return info

def turnOnFan():
    GPIO.setup(Motor1A,GPIO.OUT)
    GPIO.setup(Motor1B,GPIO.OUT)
    GPIO.setup(Motor1E,GPIO.OUT)
    GPIO.output(Motor1A, GPIO.HIGH)

def turnOffFan():
    GPIO.setup(Motor1A,GPIO.OUT)
    GPIO.setup(Motor1B,GPIO.OUT)
    GPIO.setup(Motor1E,GPIO.OUT)
    GPIO.output(Motor1A, GPIO.LOW)
    
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

app.layout = html.Div(children=[
    html.H1(children='IoT Dashboard'),
    html.H2(children='Turn On or Off the Light'),
    html.Button('Toggle Light', id='led_button', value='toggle_light', n_clicks=0),
    html.Div(id='led_output'),
    html.Br(),
    
    html.H2(children='Fan Control'),
    dcc.Input(id='fan_input', type='number'),
    html.Button('Confirm Threshold', id='fan_button', value='fan_control', n_clicks=0),
    html.Br(),
    
    html.H2(children='Automatic Light Control'),
    dcc.Input(type='number'),
    html.Button('Confirm Threshold', id='light_threshold', value='light_control', n_clicks=0),
    html.Br(),
    
    dcc.Graph(id='tempGauge', figure=tempGauge),
    dcc.Graph(id='humGauge', figure=humGauge),
    dcc.Interval(id = 'intervalComponent', interval = 1 * 3000, n_intervals = 0),
    html.Div(id='hidden-div', style={'display':'none'})
])


@app.callback(
    Output('led_output', 'children'),
    [Input('led_button', 'n_clicks')]
)
def update_led_output_div(n):
    return '{}'.format(str(ledToggle(n)))

@app.callback(
    Output('hidden-div', 'children'),
    [Input('fan_button', 'n_clicks')],
    [State('fan_input','value')],
    )
def update_threshhold_output_div(clicks, input_value):
    if clicks is not None:
        global tempThresh
        tempThresh = input_value
        setTempThresh = True
    return input_value

@app.callback([
    Output('tempGauge', 'figure'),
    Output('humGauge', 'figure')],
    [Input('intervalComponent', 'n_intervals')]
   
)
def update_temp_gauge(n_intervals):
    info = getDHTinfo()
    print(info)
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
