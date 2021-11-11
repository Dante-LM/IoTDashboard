import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import RPi.GPIO as GPIO
import board
import adafruit_dht

#external_stylesheets = ['']

global led
global tempGauge
global humGauge

dhtDevice = adafruit_dht.DHT11(board.D24)

app = dash.Dash(__name__)

led = 13

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
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
    info = [currentTemp, currentHumidity]
    return info

    
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
    html.Button('Toggle Light', id='led_button', value='toggle_light', n_clicks=0),
    html.Br(),
    html.Div(id='led_output'),
    dcc.Graph(id='tempGauge', figure=tempGauge),
    dcc.Graph(id='humGauge', figure=humGauge),
    dcc.Interval(id = 'intervalComponent', interval = 1 * 3000, n_intervals = 0)
])


@app.callback(
    Output('led_output', 'children'),
    [Input('led_button', 'n_clicks')]
)
def update_led_output_div(n):
    return '{}'.format(str(ledToggle(n)))


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
