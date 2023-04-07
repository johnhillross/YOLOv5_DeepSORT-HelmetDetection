import numpy as np
import torch
import torch.backends.cudnn as cudnn

from utils.parser import get_config
from utils.torch_utils import select_device
from models.experimental import attempt_load
from utils.datasets import letterbox
from utils.general import check_img_size, non_max_suppression, scale_coords

class Detector:

    def __init__(self, target):

        # Init YOLOv5
        yolov5_cfg = get_config()

        # select weights
        if target == 'EB':
            yolov5_cfg.merge_from_file('configs/eb.yaml')
            self.weights, self.imgsz, self.conf_thres, self.iou_thres, self.device, self.agnostic_nms, self.augment= yolov5_cfg.YOLOV5.WEIGHTS, yolov5_cfg.YOLOV5.IMG_SIZE, yolov5_cfg.YOLOV5.CONF_THRES, yolov5_cfg.YOLOV5.IOU_THRES, yolov5_cfg.YOLOV5.DEVICE, yolov5_cfg.YOLOV5.AGNOSTIC_NMS, yolov5_cfg.YOLOV5.AUGMENT
        elif target == 'Helmet':
            yolov5_cfg.merge_from_file('configs/helmet.yaml')
            self.weights, self.imgsz, self.conf_thres, self.iou_thres, self.device, self.agnostic_nms, self.augment= yolov5_cfg.YOLOV5.WEIGHTS, yolov5_cfg.YOLOV5.IMG_SIZE, yolov5_cfg.YOLOV5.CONF_THRES, yolov5_cfg.YOLOV5.IOU_THRES, yolov5_cfg.YOLOV5.DEVICE, yolov5_cfg.YOLOV5.AGNOSTIC_NMS, yolov5_cfg.YOLOV5.AUGMENT

        # Initialize
        self.device = select_device(self.device)
        self.half = self.device.type != 'cpu'  # half precision only supported on CUDA

        # Load model
        self.model = attempt_load(self.weights, map_location=self.device)  # load FP32 model
        self.imgsz = check_img_size(self.imgsz, s=self.model.stride.max())  # check img_size
        if self.half:
            self.model.half()  # to FP16

        cudnn.benchmark = True  # set True to speed up constant image size inference

        # Get names
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
    
    def detect(self, img, classes):

        im0 = img.copy()
        img = letterbox(img, new_shape=self.imgsz)[0]
        img = img[:, :, ::-1].transpose(2, 0, 1)
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).to(self.device)
        img = img.half() if self.half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Inference
        pred = self.model(img, augment=self.augment)[0]

        # Apply NMS
        pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, classes=classes, agnostic=self.agnostic_nms)

        bboxes = []

        # Process detections
        for det in pred:  # detections per image
            if det is not None and len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                for *xyxy, conf, cls in reversed(det):
                    
                    className = self.names[int(cls)]

                    bboxes.append((*xyxy, conf, className))
        
        return bboxes