from flask import Flask, render_template, request, jsonify
from get_comport import get_comport
from robot import Robot
import threading

app = Flask(__name__)
robot = None


def initialize_robot():
    global robot
    if robot is None:
        port = get_comport('ATEN USB to Serial', 'USB-Serial Controller')
        robot = Robot(port, baudrate=38400)

    def run_robot():
        while True:
            robot.run()

    robot_thread = threading.Thread(target=run_robot, daemon=True)
    robot_thread.start()


initialize_robot()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/servo', methods=['POST'])
def servo():
    on = request.json['on']
    robot.servo(on)
    return jsonify({'status': 'success'})


@app.route('/api/alarm_reset', methods=['POST'])
def alarm_reset():
    robot.alarm_reset()
    return jsonify({'status': 'success'})


@app.route('/api/pause', methods=['POST'])
def pause():
    pause = request.json['pause']
    robot.pause(pause)
    return jsonify({'status': 'success'})


@app.route('/api/home', methods=['POST'])
def home():
    robot.home()
    return jsonify({'status': 'success'})


@app.route('/api/jog', methods=['POST'])
def jog():
    data = request.json
    slave = data['slave']
    positive_side = data['positive_side']
    move = data['move']
    robot.jog(slave, positive_side, move)
    return jsonify({'status': 'success'})


@app.route('/api/current_position', methods=['GET'])
def current_position():
    robot.current_position()
    return jsonify(robot.current_position_vel)


@app.route('/api/move_to', methods=['POST'])
def move_to():
    row = request.json['row']
    robot.move_to(row)
    return jsonify({'status': 'success'})


@app.route('/api/set_to', methods=['POST'])
def set_to():
    data = request.json
    robot.set_to(data['slave'], data['row'], data['position'], data['speed'], data['acc'], data['dec'])
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
