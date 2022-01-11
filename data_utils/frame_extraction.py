import cv2
import os
import logging
import argparse
import pandas as pd
import json
import numpy as np
import re


CLASS_MAP = {'pu': 1, 'pb': 2, 'sc': 3, 'hp': 4, 'ts': 5}
WIDTH = 3840
HEIGHT = 2160
START_LINE = "original_vido_id video_id frame_id path labels"

class DrillAnnotation:

    def __init__(self, path=None, my_file=None):
        if path:
            with open(path, 'r') as f:
                my_file = json.load(f)
        self.annotation = [x for x in my_file['annotations'] if x['attributes'] is not None]
        for annot in self.annotation:
            if 'bbox' in annot:
                annot['bbox'] = [int(x) for x in annot['bbox']]
        self.image = my_file['images']
        self.hand_touch = [x for x in self.annotation if x['attributes'].get('hand', '') == 'ts']
        self.actions = []

    def get_image(self, image_id):
        images = [x for x in self.image if x['id'] == image_id]
        return images[0] if len(images) == 1 else None

    def get_annot_on_image(self, image_id, excluded=[]):
        annotations = [x for x in self.annotation if x['image_id'] == image_id and x['id'] not in excluded]
        return annotations

    def parse_actions(self):
        actions = [x for x in self.annotation if 'action' in x['attributes']]
        for action in actions:
            classified = False
            for sequence in self.actions:
                if is_same_action(action, sequence[-1]):
                    sequence.append(action)
                    classified = True
                    break
            if not classified:
                self.actions.append([action])

    def format_row(self, annot):
        image = self.get_image(annot['image_id'])
        video = image['video'].split('.mp4')[0]
        start = DrillAnnotation.frame_to_float(image['file_name']) / 20
        x1 = round(annot['bbox'][0] / WIDTH, 3)
        y1 = round(annot['bbox'][1] / HEIGHT, 3)
        x2 = round((annot['bbox'][0] + annot['bbox'][2]) / WIDTH, 3)
        y2 = round((annot['bbox'][1] + annot['bbox'][3])/ HEIGHT, 3)
        confidence = 1
        return video, start, x1, y1, x2, y2, confidence

    def find_hand_owner(self, hand_annotation):
        potential_owners = self.get_annot_on_image(hand_annotation['image_id'], [hand_annotation['id']])
        hand_bbox = DrillAnnotation.get_bbox_from_tag(hand_annotation)
        scores = [DrillAnnotation.intersection_over_union(hand_bbox, self.get_bbox_from_tag(candidate)) for candidate in
                  potential_owners]
        winner = potential_owners[np.argmax(scores)] if len(scores) > 0 else None
        return winner

    @staticmethod
    def frame_to_float(name):
        """frame name in the form frame_xxxxx.jpg/png/...
        extract xxxx with x in [0-9]"""
        matches = re.findall('[0-9]+', name)
        assert len(matches) == 1
        return float(matches[0])

    @staticmethod
    def intersection_over_union(bbox1, bbox2):
        """each bbox much be of shape (x_left, y_up, width, height)"""
        assert bbox1[2] * bbox1[3] * bbox2[2] * bbox2[3] > 0
        x_left, x_right = max(bbox1[0], bbox2[0]), min(bbox1[0] + bbox1[2], bbox2[0] + bbox2[2])
        y_top, y_bottom = max(bbox1[1], bbox2[1]), min(bbox1[1] + bbox1[3], bbox2[1] + bbox2[3])

        intersection = max((x_right - x_left), 0) * max((y_bottom - y_top), 0)
        area1, area2 = bbox1[2] * bbox1[3], bbox2[2] * bbox2[3]
        iou = intersection / (area1 + area2 - intersection)
        return round(iou, 2)

    @staticmethod
    def get_bbox_from_tag(tag_dict):
        return [int(float(x)) for x in tag_dict['bbox']]


def IoU(bbox1, bbox2):
    """each bbox much be of shape (x_left, y_up, width, height)"""
    assert bbox1[2] * bbox1[3] * bbox2[2] * bbox2[3] > 0
    x_left, x_right = max(bbox1[0], bbox2[0]), min(bbox1[0] + bbox1[2], bbox2[0] + bbox2[2])
    y_top, y_bottom = max(bbox1[1], bbox2[1]), min(bbox1[1] + bbox1[3], bbox2[1] + bbox2[3])
    intersection = max((x_right - x_left), 0) * max((y_bottom - y_top), 0)
    area1, area2 = bbox1[2] * bbox1[3], bbox2[2] * bbox2[3]
    iou = intersection / (area1 + area2 - intersection)
    return round(iou, 2)


def is_same_action(annot1, annot2):
    return 1 if annot1['attributes']['action'] == annot2['attributes']['action'] and \
                IoU(annot1['bbox'], annot2['bbox']) > 0.5 and \
                abs(annot1['image_id'] - annot2['image_id']) == 1 else 0


def get_next_video_id(frame_list_csv):
    if os.path.exists(frame_list_csv):
        frame_ls = pd.read_csv(frame_list_csv, sep=' ')
        return frame_ls['video_id'].iloc[-1] if len(frame_ls) > 0 else 0
    else:
        pd.DataFrame([], columns=START_LINE.split()).to_csv(frame_list_csv, index=False, header=None, sep=' ')
        return 0


def build_frame_list_csv(video_names, frame_dir, output_csv):
    frames = []
    start_index = get_next_video_id(output_csv)
    for index, video in enumerate(video_names):
        video_index = start_index + index
        video = video.split('.mp4')[0]
        frame_path = os.path.join(frame_dir, video)
        if os.path.exists(frame_path):
            video_frames = os.listdir(frame_path)
            for frame_index, frame in enumerate(video_frames):
                path = video + '/' + frame
                row = [video, video_index, frame_index, path, "''"]
                frames.append(row)
        else:
            logging.warning("no video {} in {} folder".format(video, frame_dir))
    frame_df = pd.DataFrame(frames)
    return frame_df


def build_df(annotation_files, is_opened=False):
    csv_file = []
    for file in annotation_files:
        my_annotation = DrillAnnotation(file) if not is_opened else DrillAnnotation(my_file=file)
        my_annotation.parse_actions()
        for actions in my_annotation.actions:
            for action in actions:
                label = action['attributes']['action']
                if label in CLASS_MAP:
                    video, start, x1, y1, x2, y2, confidence = my_annotation.format_row(action)
                    if int(start) == start:
                        csv_file.append([video, int(start), x1, y1, x2, y2, CLASS_MAP[label], confidence])
        for hand in my_annotation.hand_touch:
            annot = my_annotation.find_hand_owner(hand)
            if annot is not None:
                video, start, x1, y1, x2, y2, confidence = my_annotation.format_row(annot)
                label = CLASS_MAP['ts']
                if int(start) == start:
                    csv_file.append([video, int(start), x1, y1, x2, y2, label, confidence])
            else:
                pass
                # print(file, video, hand)
    return pd.DataFrame(csv_file, columns=['video_name', 'sec', 'x1', 'y1', 'x2', 'y2', 'label', 'score'])


def extract_frames_ava(video_path, output_path, step=1):
    """video path: full path to video (with mp4/avi extension)"""
    cap = cv2.VideoCapture(video_path)
    if cap.isOpened():
        video_name = os.path.split(video_path)[1].split('.')[0]
        frame_folder = os.path.join(output_path, video_name)
        if os.path.exists(frame_folder):
            logging.warning("folder with name {} already exists, stops extraction".format(video_name))
            return 0
        os.makedirs(frame_folder)
        logging.info("created folder {}, starts frame extraction".format(frame_folder))
        flag, img = cap.read()
        frame_number = 0
        while flag:
            cv2.imwrite(os.path.join(frame_folder, '{}_{:06d}.jpg'.format(video_name, frame_number)), img)
            frame_number += step
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            flag, img = cap.read()
    else:
        logging.warning("video {} doesnt exist".format(video_path))
        return -1
    cap.release()
    return 0


def get_args():
    parser = argparse.ArgumentParser(description='Extract and save all frmaes from a video in a folder called '
                                                 'on video name')
    parser.add_argument('-vp', '--video_path', required=True, type=str, help='path to video')
    parser.add_argument('-op', '--output_path', required=True, type=str, help='folder destination, folder with video '
                                                                              'name is created at thi location')
    parser.add_argument('--step', required=False, type=int, default=1, help='iteration size on frames')
    return parser.parse_args()


def main():
    args = get_args()
    extract_frames_ava(args.video_path, args.output_path, args.step)


if __name__ == "__main__":
    main()
