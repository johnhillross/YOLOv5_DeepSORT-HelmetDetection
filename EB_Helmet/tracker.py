import torch

from deep_sort.utils.parser import get_config
from deep_sort.deep_sort import DeepSort

class Tracker:
    def __init__(self):

        #Init DeepSORT
        deepsort_cfg = get_config()
        deepsort_cfg.merge_from_file('deep_sort/configs/deep_sort.yaml')
        self.deepsort = DeepSort(deepsort_cfg.DEEPSORT.REID_CKPT,
                            max_dist=deepsort_cfg.DEEPSORT.MAX_DIST, min_confidence=deepsort_cfg.DEEPSORT.MIN_CONFIDENCE,
                            nms_max_overlap=deepsort_cfg.DEEPSORT.NMS_MAX_OVERLAP, max_iou_distance=deepsort_cfg.DEEPSORT.MAX_IOU_DISTANCE,
                            max_age=deepsort_cfg.DEEPSORT.MAX_AGE, n_init=deepsort_cfg.DEEPSORT.N_INIT, nn_budget=deepsort_cfg.DEEPSORT.NN_BUDGET,
                            use_cuda=True)
    
    def bbox_rel(self, xyxy):
        """" Calculates the relative bounding box from absolute pixel values. """
        bbox_left = min([xyxy[0], xyxy[2]])
        bbox_top = min([xyxy[1], xyxy[3]])
        bbox_w = abs(xyxy[0] - xyxy[2])
        bbox_h = abs(xyxy[1] - xyxy[3])
        x_c = (bbox_left + bbox_w / 2)
        y_c = (bbox_top + bbox_h / 2)
        w = bbox_w
        h = bbox_h

        return x_c, y_c, w, h
    
    def track(self, bboxes, img):

        # Adapt detections to deep sort input format
        bbox_xywh = []
        confs = []
        classNames = []

        for *xyxy, conf, className in bboxes:

            x_c, y_c, bbox_w, bbox_h = self.bbox_rel(xyxy)
            obj = [x_c, y_c, bbox_w, bbox_h]

            bbox_xywh.append(obj)
            confs.append(conf)
            classNames.append(className)
        
        xywhs = torch.Tensor(bbox_xywh)
        confss = torch.Tensor(confs)

        # Pass detections to deepsort
        outputs = self.deepsort.update(xywhs, confss, classNames, img)

        return outputs