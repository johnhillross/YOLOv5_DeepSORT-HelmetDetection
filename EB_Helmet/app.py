from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import pymysql
import time

from camera import Camera

# init flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# init pymysql
conn = pymysql.connect(host='localhost', user='root', password='123456', database='eb_helmet')
cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)

# init source and format
savedir = 'D:/#Data/Detect/'
format = '.jpg'


def setup():
    global webcams
    webcams = {}

    cursor.execute("select * from webcam")
    conn.commit()
    rows = cursor.fetchall()

    for row in rows:
        device = row['device']
        source = row['source']
        camera = Camera(device, source, savedir, format, socketio)

        print('Set up webcam: %s' % device)

        webcams[device] = camera


@socketio.on('lonlat')
def lonlat_push(device):

    cursor.execute("select * from webcam where device = %s", (device))
    conn.commit()

    webcam = cursor.fetchone()
    longitude = webcam['longitude']
    latitude = webcam['latitude']

    socketio.emit('lonlat:' + device, {'longitude': longitude, 'latitude': latitude})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stream/<string:device>')
def stream(device):

    camera = webcams[device]

    def generate():
        while True:
            socketio.sleep(0)
            yield (b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + camera.frame() + b'\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


def count(device, date, hour):
    cursor.execute("select count(*) as num from eb_rider where device = %s and date(time) = %s and hour(time) = %s and lane = 0", (device, date, hour))
    conn.commit()
    Motor_Lane = cursor.fetchone()['num']

    cursor.execute("select count(*) as num from eb_rider where device = %s and date(time) = %s and hour(time) = %s  and lane = 1", (device, date, hour))
    conn.commit()
    Bicycle_Lane = cursor.fetchone()['num']

    cursor.execute("select count(*) as num from eb_rider where device = %s and date(time) = %s and hour(time) = %s  and direction = 0", (device, date, hour))
    conn.commit()
    Up = cursor.fetchone()['num']

    cursor.execute("select count(*) as num from eb_rider where device = %s and date(time) = %s and hour(time) = %s  and direction = 1", (device, date, hour))
    conn.commit()
    Down = cursor.fetchone()['num']

    cursor.execute("select count(*) as num from eb_rider where device = %s and date(time) = %s and hour(time) = %s  and helmet = 0", (device, date, hour))
    conn.commit()
    With_Helmet = cursor.fetchone()['num']

    cursor.execute("select count(*) as num from eb_rider where device = %s and date(time) = %s and hour(time) = %s  and helmet = 1", (device, date, hour))
    conn.commit()
    Without_Helmet = cursor.fetchone()['num']

    cursor.execute("select count(*) as num from eb_rider where device = %s and date(time) = %s and hour(time) = %s  and helmet = 2", (device, date, hour))
    conn.commit()
    Miss = cursor.fetchone()['num']

    result = {'Date': date, 'Hour': hour, 'Motor_Lane': Motor_Lane, 'Bicycle_Lane': Bicycle_Lane, 'Up': Up, 'Down': Down, 'With_Helmet': With_Helmet, 'Without_Helmet': Without_Helmet, 'Miss': Miss}
    return result


@socketio.on('count_past')
def count_past_push(device):

    past = {}

    curDate = time.strftime('%Y-%m-%d', time.localtime())
    curHour = time.strftime('%H', time.localtime())

    for hour in range(0, int(curHour)):
        past[hour] = count(device, curDate, hour)

    socketio.emit('past:' + device, past)


@socketio.on('count_current')
def count_current_push(device):

    current = {}

    curDate = time.strftime('%Y-%m-%d', time.localtime())
    curHour = time.strftime('%H', time.localtime())

    current =  count(device, curDate, curHour)

    socketio.emit('current:' + device, current)


if __name__ == '__main__':

    print('Set up all webcams')
    setup()

    print('Flask server run on 127.0.0.1:8000')
    socketio.run(app, host='127.0.0.1', port=8000, debug=False)

    cursor.close()
    conn.close()