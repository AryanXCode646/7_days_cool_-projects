import os
import cv2
import numpy as np
import requests

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
PROTO_URL = 'https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/MobileNetSSD_deploy.prototxt'
MODEL_URL = 'https://github.com/chuanqi305/MobileNet-SSD/raw/master/MobileNetSSD_deploy.caffemodel'

CLASSES = [
    'background','aeroplane','bicycle','bird','boat',
    'bottle','bus','car','cat','chair','cow','diningtable',
    'dog','horse','motorbike','person','pottedplant','sheep',
    'sofa','train','tvmonitor'
]

class ObjectDetector:
    def __init__(self, conf_threshold=0.4):
        os.makedirs(MODEL_DIR, exist_ok=True)
        self.prototxt = os.path.join(MODEL_DIR, 'MobileNetSSD_deploy.prototxt')
        self.model = os.path.join(MODEL_DIR, 'MobileNetSSD_deploy.caffemodel')
        self.conf_threshold = conf_threshold

        self.enabled = True
        try:
            if not os.path.exists(self.prototxt) or not os.path.exists(self.model):
                self._download_models()

            # attempt to load the network
            self.net = cv2.dnn.readNetFromCaffe(self.prototxt, self.model)
        except Exception as e:
            print('ObjectDetector disabled (models unavailable):', e)
            self.enabled = False
            self.net = None

    def _download(self, url, path):
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)

    def _download_models(self):
        try:
            if not os.path.exists(self.prototxt):
                print('Downloading prototxt...')
                self._download(PROTO_URL, self.prototxt)
            if not os.path.exists(self.model):
                print('Downloading caffemodel (this may take a moment)...')
                self._download(MODEL_URL, self.model)
        except Exception as e:
            print('Model download failed:', e)
            # do not raise; caller will disable detector
            return

    def detect(self, frame):
        # returns list of (label, conf)
        if not self.enabled or self.net is None:
            return []
        try:
            h, w = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
            self.net.setInput(blob)
            detections = self.net.forward()
            results = []
            for i in range(detections.shape[2]):
                conf = float(detections[0, 0, i, 2])
                if conf > self.conf_threshold:
                    idx = int(detections[0, 0, i, 1])
                    label = CLASSES[idx] if idx < len(CLASSES) else str(idx)
                    results.append((label, conf))
            return results
        except Exception:
            return []
