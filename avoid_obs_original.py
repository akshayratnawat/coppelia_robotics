"""Basic obstacle avoidance with Braitenberg algorithm

"""
import sys
import time  # used to keep track of time
import numpy as np  # array library

import sim
from sensors.odometery import Odometer
from sensors.position import RobotGPS
import matplotlib.pyplot as plt  # used for image plotting

# Pre-Allocation
saving = False
PI = np.pi  # constant

sim.simxFinish(-1)  # just in case, close all opened connections

clientID = sim.simxStart('127.0.0.1', 19999, True, True, 5000, 5)

if clientID != -1:  # check if client connection successful
    print('Connected to remote API server')

else:
    print('Connection not successful')
    sys.exit('Could not connect')

# retrieve motor  handles
_, left_motor_handle = sim.simxGetObjectHandle(clientID, 'Pioneer_p3dx_leftMotor', sim.simx_opmode_oneshot_wait)
_, right_motor_handle = sim.simxGetObjectHandle(clientID, 'Pioneer_p3dx_rightMotor', sim.simx_opmode_oneshot_wait)

gps = RobotGPS(clientID)
gps_start = gps.get_position(actual=True)
print(gps.get_orientation())
odometer = Odometer(clientID, 0.098, pose=[gps_start[0], gps_start[1], gps.get_orientation()[2]])

sensor_handles = []  # empty list for handles
sensor_val = np.array([])  # empty array for sensor measurements
random_positions = []
accurate_positions = []
odometer_positions = []

# orientation of all the sensors:
sensor_loc = np.array([
    -PI / 2, -50 / 180.0 * PI, -30 / 180.0 * PI,
    -10 / 180.0 * PI, 10 / 180.0 * PI, 30 / 180.0 * PI,
    50 / 180.0 * PI, PI / 2, PI / 2,
    130 / 180.0 * PI, 150 / 180.0 * PI, 170 / 180.0 * PI,
    -170 / 180.0 * PI, -150 / 180.0 * PI, -130 / 180.0 * PI,
    -PI / 2
])

# for loop to retrieve sensor arrays and initiate sensors
for x in range(1, 16 + 1):
    # build list of handles
    resCode, sensor_handle = sim.simxGetObjectHandle(clientID, 'Pioneer_p3dx_ultrasonicSensor' + str(x),
                                               sim.simx_opmode_oneshot_wait)
    # print(f"{x}, {'Pioneer_p3dx_ultrasonicSensor' + str(x)} - Code: {resCode}")
    sensor_handles.append(sensor_handle)

    # get list of values
    # _, detectionState, detectedPoint, detectedObjectHandle, detectedSurfaceNormalVector = sim.simxReadProximitySensor(
    #     clientID, sensor_handle, sim.simx_opmode_streaming)
    # sensor_val = np.append(sensor_val, np.linalg.norm(detectedPoint))

# start time
t = time.time()

while (time.time() - t) < 15:
    odometer.update_motors()
    gps.update_position()

    random_positions.append(gps.get_position())
    accurate_positions.append(gps.get_position(actual=True))
    odometer_positions.append(odometer.get_position())
    print(f"{odometer} {gps}")

    # Loop Execution
    sensor_val = np.array([])
    for x in range(1, 16 + 1):
        resCode, detectionState, detectedPoint, detectedObjectHandle, detectedSurfaceNormalVector \
            = sim.simxReadProximitySensor(
                  clientID, sensor_handles[x - 1], sim.simx_opmode_oneshot_wait
              )
        # print(
        #     f"Result Code: {resCode}\n"
        #     f"Detection State {detectionState}\n"
        #     f"Detected Point {detectedPoint}\n"
        #     f"Detected Object Handle {detectedObjectHandle}"
        # )
        # get list of values
        sensor_val = np.append(sensor_val, np.linalg.norm(detectedPoint))
        # if x == 4:
        #     print(f"{resCode} - {detectedPoint} - {np.linalg.norm(detectedPoint)}")

        # if np.linalg.norm(detectedPoint) != 0:
        #     print(f"Non-Zero Reading {x}")

    # controller specific
    sensor_sq = sensor_val[0:8] * sensor_val[0:8]  # square the values of front-facing sensors 1-8

    if time.time() - t:

        min_ind = np.where(sensor_sq == np.min(sensor_sq))
        min_ind = min_ind[0][0]

        if sensor_sq[min_ind] < 0.2:
            steer = -1 / sensor_loc[min_ind]
        else:
            steer = 0

        # gain_map = {
        #     0: .25,
        #     1: .50,
        #     2: .75
        # }
        #
        # kp = gain_map.get(int(time.time() - t) // 60)

        v = 1  # forward velocity
        kp = 0.6  # steering gain
        vl = v + kp * steer
        vr = v - kp * steer
        # print("V_l =", vl)
        # print("V_r =", vr)

        if sensor_sq[min_ind] < 0.05:
            steer = -1 / sensor_loc[min_ind]
        else:
            steer = 0

    _ = sim.simxSetJointTargetVelocity(clientID, left_motor_handle, vl, sim.simx_opmode_streaming)
    _ = sim.simxSetJointTargetVelocity(clientID, right_motor_handle, vr, sim.simx_opmode_streaming)

    time.sleep(0.2)  # loop executes once every 0.2 seconds (= 5 Hz)

# Post Allocation
_ = sim.simxSetJointTargetVelocity(clientID, left_motor_handle, 0, sim.simx_opmode_streaming)
_ = sim.simxSetJointTargetVelocity(clientID, right_motor_handle, 0, sim.simx_opmode_streaming)

rxs = list(map(lambda x: x[0], random_positions))
rys = list(map(lambda x: x[1], random_positions))
xs = list(map(lambda x: x[0], accurate_positions))
ys = list(map(lambda x: x[1], accurate_positions))
oxs = list(map(lambda x: x[0], odometer_positions))
oys = list(map(lambda x: x[1], odometer_positions))

print(oxs, oys)

# plt.plot(rxs, rys, color='r')
plt.plot(xs, ys, color='b')
plt.plot(oxs, oys, color='g')
plt.show()
