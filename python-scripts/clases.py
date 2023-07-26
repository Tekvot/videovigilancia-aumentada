import cv2
import copy
import numpy as np
import torch
import mediapipe as mp
import os
import requests
from src import model
from src import util
from src.body import Body
import base64
import face_recognition
import imutils
from imutils.video import VideoStream
from threading import Thread,Timer

class ImageUtils:
    mp_face_detection = mp.solutions.face_detection
    face_detection=mp_face_detection.FaceDetection(min_detection_confidence=0.5)
    rtsp_url = "rtsp://prel1992:Fores753***@192.168.100.213:554/stream1"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thickness = 1
    body_estimation = Body('model/body_pose_model.pth')
    face_encodings = []
    face_names = []
    faces_locations=[]
    video_stream = VideoStream(src=0).start()
    frame = None
    names=[]
    candidate = None
    subset    = None
    canvas    = None
    permiso=True
    draw_pose_permission=False
    draw_face_permission=False
    hilos=[]
    def __init__(self):
        self.load_faces('rostros')
        self.hilos.append(Thread(target=self.loop))
        self.hilos.append(Timer(0.5,self.pose_estimation_logic))
        self.hilos.append(Timer(1,self.face_identification))
        self.hilos.append(Timer(0.2,self.estimation_pose))
        for hilo in self.hilos:
            hilo.start()

    def image_to_base64(self,image):
        _, buffer = cv2.imencode('.jpg', image)
        encoded_image = base64.b64encode(buffer)
        return encoded_image.decode('utf-8')
    
    def load_faces(self,folder):
        for filename in os.listdir(folder):
            if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".JPG") or filename.endswith(".jpeg"):
                    #img = cv2.imread(os.path.join(folder+"/"+d, filename))
                    #image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    #results = face_detection.process(image_rgb)
                face_image = face_recognition.load_image_file(os.path.join(folder, filename))
                face_locations = face_recognition.face_locations(face_image)
                    #bbox=results.detections[0].location_data.relative_bounding_box
                    #print(bbox)
                    #print(face_locations)
                    #image_height, image_width, _ = img.shape
                    #bbox_start_point = [int(bbox.xmin * image_width), int(bbox.ymin * image_height), int((bbox.xmin + bbox.width) * image_width), int((bbox.ymin + bbox.height) * image_height)]
                if len(face_locations) != 0:
                    aux = face_recognition.face_encodings(face_image, face_locations,model="cnn")[0]
                    self.face_encodings.append(aux)
                self.face_names.append(filename.split('.')[0])

    def calculate_angle(self, p1, p2, p3):
        v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
        dot_product = np.dot(v1, v2)
        norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        cosine_angle = dot_product / norm_product
        angle = np.arccos(cosine_angle) * 180 / np.pi
        cv2.putText(self.frame, f"Right Angle: {angle:.2f}", (10, 20), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
        return angle
    
    def pose_estimation_logic(self):
        if self.candidate !=None and self.subset != None:
            neck_idx = np.where(self.subset[:, 0] != 1)[0]
            if len(neck_idx) > 0:
                neck_idx = neck_idx[0]
                right_shoulder_idx = self.subset[neck_idx][2]
                left_shoulder_idx = self.subset[neck_idx][5]
                if right_shoulder_idx != -1 and left_shoulder_idx != -1:
                    right_shoulder = self.candidate[int(right_shoulder_idx)]
                    left_shoulder = self.candidate[int(left_shoulder_idx)]
                    shoulder_angle = self.calculate_angle(self.frame, right_shoulder, left_shoulder, (self.frame.shape[1] // 2, self.frame.shape[0]))
                    print(shoulder_angle)
                    if shoulder_angle > 90 and self.permiso:
                        data = {
                            'name': 'bryan',
                            'dni': 70886887,
                            'image64': self.image_to_base64(cv2.resize(self.frame,(0,0),fx=0.5,fy=0.5)),
                            'alert':1
                        }
                        print('envio')
                        response = requests.post('http://localhost:4000', json=data)
                        self.permiso=False
    def estimation_pose(self):
        if self.frame is not None:
            self.candidate, self.subset = self.body_estimation(self.frame)
            #self.canvas = copy.deepcopy(self.frame)
            self.frame = util.draw_bodypose(self.frame, self.candidate, self.subset)
        h=Timer(0.35,self.estimation_pose)
        h.start()
            
    def face_identification(self):
        if self.frame is not None:
            self.names=[]
            face_locations = face_recognition.face_locations(self.frame)
            face_encodings = face_recognition.face_encodings(self.frame, face_locations,model="cnn")
            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(self.face_encodings, face_encoding)
                if any(matches):
                    first_match_index = np.argmax(True)
                    if self.face_names != None:
                        if len(face_encoding)!=0 and len(face_encoding)>first_match_index:
                            self.names.append(self.face_names[first_match_index])
                        else:
                            self.names.append("Desconocido")
            h=Timer(0.35,self.face_identification)
            h.start()
    def loop(self):
        while True:
            self.frame = self.video_stream.read()
            self.frame = cv2.resize(self.frame,(0,0),fx=0.4,fy=0.4)
            if self.candidate is not None and len(self.candidate) > 0 and self.subset is not None and len(self.subset) > 0:
                print("pose")
                self.candidate=None
                self.subset=None
            if len(self.faces_locations) > 0:
                for name,face_location in zip(self.names,self.faces_locations):
                    y1, x2, y2, x1 = face_location
                    cv2.rectangle(self.canvas, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(self.canvas,name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                self.names=[]
                self.faces_locations=[]
            cv2.imshow('demo', self.frame)
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()


utils=ImageUtils()
