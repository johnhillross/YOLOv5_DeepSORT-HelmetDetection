import os
import cv2
import math
from collections import deque
import time
import pymysql
import base64

from tracker import Tracker
from detector import Detector


class Camera(object):


    def __init__(self, device, source, savedir, format, socketio):

        # init yolov5 and deepsort
        self.EB_detector = Detector('EB')
        self.Helmet_detector = Detector('Helmet')
        self.tracker = Tracker()

        # initialization parameter
        self.device = device
        self.format = format
        self.socketio = socketio

        # Set Dataloader
        self.dataset = cv2.VideoCapture(source)

        # Set save directory
        self.savedir = savedir + str(self.device) + '/' + time.strftime('%Y-%m-%d', time.localtime()) + '/'

        if not os.path.exists(self.savedir):
            os.makedirs(self.savedir)

        # midpoint paths
        self.paths = {}

        # connect to database
        self.conn = pymysql.connect(host="localhost", user="root", password="123456", database="eb_helmet")
        self.cursor = self.conn.cursor()

        # save fps
        self.fps_file = open('result/fps/fps.txt','w')


    def __del__(self):
        self.dataset.release()
        self.conn.close()
        self.fps_file.close()


    def compute_color_for_labels(label):
        """ Simple function that adds fixed color depending on the class """
        color = [int((p * (label ** 2 - label + 1)) % 255) for p in (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)]
        return tuple(color)


    def draw_bbox_trace(img, box, className, trace, identitie, offset=(0, 0)):
        x1, y1, x2, y2 = [int(i) for i in box]
        x1 += offset[0]
        x2 += offset[0]
        y1 += offset[1]
        y2 += offset[1]
        # box text and bar
        color = Camera.compute_color_for_labels(identitie)
        label = '{}{:d}'.format(className, identitie)
        t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 2, 2)[0]
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        cv2.rectangle(img, (x1, y1), (x1 + t_size[0] + 3, y1 + t_size[1] + 4), color, -1)
        cv2.putText(img, label, (x1, y1 + t_size[1] + 4), cv2.FONT_HERSHEY_PLAIN, 2, [255, 255, 255], 2)

        # draw trace
        if len(trace) > 1:
            for i in range(len(trace) - 1):
                cv2.line(img, tuple(trace[i]), tuple(trace[i+1]), color, 5)

        return img


    def get_midpoint(bbox):
        x1, y1, x2, y2 = bbox
        midpoint = (int((x1 + x2) / 2), int((y1 + y2) / 2))  # minus y coordinates to get proper xy format
        return midpoint


    def intersect(A, B, C, D):
        return Camera.ccw(A, C, D) != Camera.ccw(B, C, D) and Camera.ccw(A, B, C) != Camera.ccw(A, B, D)


    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


    def vector_angle(midpoint, previous_midpoint):
        x = midpoint[0] - previous_midpoint[0]
        y = midpoint[1] - previous_midpoint[1]
        return math.degrees(math.atan2(y, x))


    def frame(self):

        # calculate fps
        start_time = time.time()

        ret, origin_img = self.dataset.read()
        draw_img = origin_img.copy()

        if origin_img is None:
            return
        
        # set lines
        Motor_Lane = [(0, int(0.4 * origin_img.shape[0])), (int(0.4 * origin_img.shape[1]), int(0.5 * origin_img.shape[0]))]
        Bicycle_Lane = [(int(0.4 * origin_img.shape[1]), int(0.5 * origin_img.shape[0])), (origin_img.shape[1], int(0.5 * origin_img.shape[0]))]

        # draw yellow lines
        cv2.line(draw_img, Motor_Lane[0], Motor_Lane[1], (0, 255, 255), 10)
        cv2.line(draw_img, Bicycle_Lane[0], Bicycle_Lane[1], (0, 255, 255), 10)

        # detect, classes[0]: With Helmet; classes[1]: Without Helmet; classes[2]: EB Rider
        bboxes = self.EB_detector.detect(origin_img, classes=[2])

        if len(bboxes) > 0:

            # track
            outputs = self.tracker.track(bboxes, origin_img)
        
            for track in outputs:

                bbox_xyxy = track[:4]
                className = track[4]
                identitie = track[5]
                trace = track[-1]

                # draw box for visualization
                Camera.draw_bbox_trace(draw_img, bbox_xyxy, className, trace, identitie)

                # count for cross line objects
                midpoint = Camera.get_midpoint(bbox_xyxy)

                # save previous_midpoint
                if identitie not in self.paths:
                    self.paths[identitie] = deque(maxlen=2)
                self.paths[identitie].append(midpoint)
                previous_midpoint = self.paths[identitie][0]
                
                if Camera.intersect(midpoint, previous_midpoint, Motor_Lane[0], Motor_Lane[1]) or Camera.intersect(midpoint, previous_midpoint, Bicycle_Lane[0], Bicycle_Lane[1]):

                    # init information
                    lane = 0
                    direction = 0
                    helmet = 0

                    # Motor Lane or Bicycle Lane
                    if Camera.intersect(midpoint, previous_midpoint, Motor_Lane[0], Motor_Lane[1]):

                        # draw red lines
                        cv2.line(draw_img, Motor_Lane[0], Motor_Lane[1], (0, 0, 255), 15)
                        
                        # 0 stand for Motor Lane
                        lane = 0

                    elif Camera.intersect(midpoint, previous_midpoint, Bicycle_Lane[0], Bicycle_Lane[1]):

                        # draw red lines
                        cv2.line(draw_img, Bicycle_Lane[0], Bicycle_Lane[1], (0, 0, 255), 15)

                        # 1 stand for Bicycle Lane
                        lane = 1

                    # Up or Down
                    angle = Camera.vector_angle(midpoint, previous_midpoint)

                    if angle < 0:

                        # 0 stand for Up
                        direction = 0
                    
                    elif angle > 0:

                        # 1 stand for Down
                        direction = 1

                    # detect, classes[0]: With Helmet; classes[1]: Without Helmet
                    bboxes = self.Helmet_detector.detect(origin_img[bbox_xyxy[1]:bbox_xyxy[3], bbox_xyxy[0]:bbox_xyxy[2]], classes=[0, 1])

                    # With Helmet or Without Helmet or Miss
                    if len(bboxes) > 0:
                        
                        max_conf = 0
                        max_conf_className = ''

                        for *xyxy, conf, className in bboxes:

                            if conf > max_conf:
                                max_conf = conf
                                max_conf_className = className
                        
                        if max_conf_className == 'With Helmet':

                            # 0 stand for with helmet
                            helmet = 0

                        elif max_conf_className == 'Without Helmet':

                            # 1 stand for without helmet
                            helmet = 1
                    
                    else:

                        # 2 stand for miss
                        helmet = 2
                    
                    # save image
                    path = self.savedir + str(identitie) + self.format
                    cv2.imwrite(path, origin_img[bbox_xyxy[1]:bbox_xyxy[3], bbox_xyxy[0]:bbox_xyxy[2]])

                    # set message
                    message = {'device': self.device, 'identitie': identitie, 'lane': lane, 'direction': direction, 'helmet': helmet, 'image': 'data:image/jpeg;base64,' + base64.b64encode(cv2.imencode('.jpg', origin_img[bbox_xyxy[1]:bbox_xyxy[3], bbox_xyxy[0]:bbox_xyxy[2]])[1]).decode('utf-8'), 'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}
                    self.socketio.emit('catch:'+self.device, message)

                    # write mysql
                    # 这样参数化的方式，让 mysql 通过预处理的方式避免了 sql 注入的存在。
                    # 需要注意的是，不要因为参数是其他类型而换掉 %s，pymysql 的占位符并不是 python 的通用占位符。
                    # 同时，也不要因为参数是 string 就在 %s 两边加引号，mysql 会自动去处理。
                    sql = "insert into eb_rider(device, identitie, lane, direction, helmet, path, time) values (%s, %s, %s, %s, %s, %s, NOW())"
                    params = [self.device, identitie, lane, direction, helmet, path]
                    try:
                        self.cursor.execute(sql, params)
                        self.conn.commit()
                    except:
                        self.conn.rollback()

                if len(self.paths) > 50:
                    del self.paths[list(self.paths)[0]]
        

        # show fps
        label = 'FPS: {:.2f}'.format(1.0 / (time.time() - start_time))
        cv2.putText(draw_img, label, (50,100), cv2.FONT_HERSHEY_DUPLEX, 3.0, (0, 0, 255), 10)

        # save fps
        self.fps_file.write('%.2f\n' % (1.0 / (time.time() - start_time)))

        # resize img, encode faster
        frame = cv2.resize(draw_img, (960, 540))
        frame = cv2.imencode('.jpg', frame)[1].tobytes()

        # return stream
        return frame

