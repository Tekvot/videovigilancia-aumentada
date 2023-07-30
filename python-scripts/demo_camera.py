import cv2
import copy
import numpy as np
import torch
import mediapipe as mp
import os
#os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp'
import requests
from src import model
from src import util
from src.body import Body
import base64
import face_recognition
import imutils
from imutils.video import VideoStream
mp_face_detection = mp.solutions.face_detection
face_detection=mp_face_detection.FaceDetection(min_detection_confidence=0.5)
rtsp_url = "rtsp://admin:KCGZBB@192.168.100.224:554/"
def image_to_base64(image):
    # Codifica la imagen en formato base64
    _, buffer = cv2.imencode('.jpg', image)
    encoded_image = base64.b64encode(buffer)
    return encoded_image.decode('utf-8')
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.5
font_thickness = 1

body_estimation = Body('model/body_pose_model.pth')

def load_faces(folder):
    face_encodings = []
    face_names = []
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
                face_encodings.append(aux)
            face_names.append(filename.split('.')[0])
            
    return face_encodings, face_names

face_encodings, face_names = load_faces("rostros")

print(f"Torch device: {torch.cuda.get_device_name()}")

#cap = cv2.VideoCapture(0) #"rtsp://prel1992:Fores753***@192.168.100.103:554/stream1")
video_stream = VideoStream(rtsp_url).start()

def calculate_angle(frame, p1, p2, p3):
    # Calcula el ángulo entre tres puntos en el plano 2D
    v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
    v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])

    dot_product = np.dot(v1, v2)
    norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
    cosine_angle = dot_product / norm_product
    angle = np.arccos(cosine_angle) * 180 / np.pi
    cv2.putText(frame, f"Right Angle: {angle:.2f}", (10, 20), font, font_scale, (255, 255, 255), font_thickness)
    return angle

def pose_estimation_logic(frame, candidate, subset,permiso):
    neck_idx = np.where(subset[:, 0] != 1)[0]
    if len(neck_idx) > 0:
        neck_idx = neck_idx[0]
        right_shoulder_idx = subset[neck_idx][2]
        left_shoulder_idx = subset[neck_idx][5]
        cabeza = subset[neck_idx][0]
        brazo_izquierdo = subset[neck_idx][5],subset[neck_idx][6],subset[neck_idx][7]
        brazo_derecho = subset[neck_idx][2],subset[neck_idx][3],subset[neck_idx][4]
        if right_shoulder_idx != -1 and left_shoulder_idx != -1 and cabeza != -1 and brazo_izquierdo[1] != -1 and brazo_izquierdo[2] != -1 and brazo_derecho[1] != -1 and brazo_derecho[2] != -1:
            right_shoulder = candidate[int(right_shoulder_idx)]
            left_shoulder = candidate[int(left_shoulder_idx)]
            shoulder_angle = calculate_angle(frame, right_shoulder, left_shoulder, (frame.shape[1] // 2, frame.shape[0]))
            angulo_codo_cabeza = calculate_angle(frame,brazo_derecho[2],cabeza,(frame.shape[1] // 2, frame.shape[0]))
            print(angulo_codo_cabeza)
            if shoulder_angle > 180 and permiso:
                data = {
                    'name': 'bryan',
                    'dni': 178529634,
                    'image64': image_to_base64(cv2.resize(oriImg,(0,0),fx=0.5,fy=0.5)),
                    'alert':1
                }
                print('envio')
                response = requests.post('http://localhost:4000', json=data)
                permiso=False
    return False
permiso=True
while True:
    #ret, oriImg = cap.read()
    oriImg = video_stream.read()
    oriImg_=cv2.resize(oriImg,(0,0),fx=0.25,fy=0.25)
    candidate, subset = body_estimation(oriImg_)
    #canvas = copy.deepcopy(oriImg)
    #subset = (np.array(subset,dtype=np.uint32)*4).tolist()
    canvas = util.draw_bodypose(oriImg, candidate, subset,4)
    body_estimation.calculate_angle(candidate=candidate,subset=subset)
    #pose_estimation_logic(canvas,candidate, subset,permiso)
    if body_estimation.angle_degrees1 > 90 :
        data = {
                    'name': 'bryan',
                    'dni': 178529634,
                    'image64': image_to_base64(cv2.resize(oriImg,(0,0),fx=0.25,fy=0.25)),
                    'alert':1
                }
        print('envio')
        response = requests.post('http://localhost:4000', json=data)
        permiso=False

    face_locations = face_recognition.face_locations(oriImg)
    face_encodings_ = face_recognition.face_encodings(oriImg, face_locations,model="cnn")

    for face_encoding, face_location in zip(face_encodings_, face_locations):
        matches = face_recognition.compare_faces(face_encodings, face_encoding)
        name = "Unknown"
        if True in matches:
            first_match_index = np.argmax(True)
            if face_names != None:
                if len(face_encoding)!=0 and len(face_encoding)>first_match_index:
                    name = face_names[first_match_index]
        y1, x2, y2, x1 = face_location
        cv2.rectangle(canvas, (4*x1, 4*y1), (4*x2, 4*y2), (0, 0, 255), 3)
        cv2.putText(canvas, name, (4*x1, 4*y1 - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    #canvas=cv2.resize(canvas,(0,0),fx=1/0.4,fy=1/0.4)
    cv2.imshow('demo', canvas)
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break
#cap.release()
cv2.destroyAllWindows()