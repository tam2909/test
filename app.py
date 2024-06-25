from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO, emit
from datetime import datetime 
import pyodbc
import re

moi_time = [0, 0, 0, 0, 0]
moi_value = [0, 0, 0, 0, 0]
tem_time = [0, 0, 0, 0, 0]
tem_value = [0, 0, 0, 0, 0]
converted_moi_time = []
converted_tem_time = []

server = '34.45.228.139'  
database = 'test'   
username = 'sqlserver'         
password = 'sqlserver'  
connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
conn = pyodbc.connect(connection_string, timeout=10)
cursor = conn.cursor()


app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'mqtt.flespi.io'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = 'gtw4IvUv8okstsEiDrXmu8JHAliKEUEu1qpXKOUO5Q3eGvxDTd6AiNkNSLuGOcZ0'
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_REFRESH_TIME'] = 1.0 
mqtt = Mqtt(app)
socketio = SocketIO(app)



def fill(arr):
    while len(arr) < 5:
        arr = [0] + arr
    arr = arr[-5:]
    
def insert_temperature(time, temperature):
    cursor.execute('''
    INSERT INTO TEMPERATURE (recieve_time, Tem_value) VALUES (?, ?)
    ''', (time, temperature))
    conn.commit()

def insert_moisture(time, moisture):
    cursor.execute('''
    INSERT INTO MOISTURE (recieve_time, Moi_value) VALUES (?, ?)
    ''', (time, moisture))
    conn.commit()

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('test')
    
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global moi_time
    global moi_value
    global tem_time
    global tem_value
    global converted_moi_time
    global converted_tem_time
    
    time = datetime.now()
    converted_time = time.strftime('%Y-%m-%d %H:%M:%S')
    recieve_message = message.payload.decode()
    match = re.findall(r"[-+]?\d*\.\d+|\d+", recieve_message)
    print(match)
    if match:
        moisture = float(match[0])
        temperature = float(match[1])
    else:
        moisture = 0
        temperature = 0

    insert_moisture(converted_time, moisture)
    insert_temperature(converted_time, temperature)
    
    cursor.execute('''
    SELECT TOP 5 *
    FROM MOISTURE
    ORDER BY recieve_time DESC;
    ''') 
    rows = cursor.fetchall()
    print(rows)
    for row in reversed(rows): 
        moi_time.append(row[0])
        moi_value.append(row[1])
    
    cursor.execute('''
    SELECT TOP 5* 
    FROM TEMPERATURE
    ORDER BY recieve_time DESC
    ''') 
    
    rows = cursor.fetchall()
    print(rows)
    for row in reversed(rows): 
        print(row)
        tem_time.append(row[0])
        tem_value.append(row[1])
        
    
    moi_time = moi_time[-5:]
    moi_value = moi_value[-5:]
    tem_time = tem_time[-5:]
    tem_value = tem_value[-5:]
    
    fill(moi_time)
    fill(moi_value)
    fill(tem_time)
    fill(tem_value)
    
    print(moi_time)
    print(moi_value)
    print(tem_time)
    print(tem_value)
    converted_moi_time = []
    converted_tem_time = []
    
    for unit in moi_time:
        converted_moi_time.append(unit.strftime('%Y-%m-%d %H:%M:%S'))
    for unit in tem_time:
        converted_tem_time.append(unit.strftime('%Y-%m-%d %H:%M:%S'))
        


    socketio.emit('mqtt_message', {'tem_time': converted_tem_time, 'tem_value': tem_value, 'moi_time': converted_moi_time, 'moi_value': moi_value})

@app.route('/')
def index():
    return render_template('index.html', moi_time = converted_moi_time, moi_value = moi_value, tem_time = converted_tem_time, tem_value = tem_value)

@socketio.on('connect', namespace='/socket')
def test_connect():
    emit('mqtt_message', {'tem_time': converted_tem_time, 'tem_value': tem_value, 'moi_time': converted_moi_time, 'moi_value': moi_value})
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)
    #app.run(debug=True)
    
    
