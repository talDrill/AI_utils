import detectron2
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog
import cv2


def single_frame_pose_est_detectron2(frame_arr, cfg):
    predictor = DefaultPredictor(cfg)
    outputs = predictor(frame_arr)
    return outputs