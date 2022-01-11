import logging
import os
import sys
import cv2
import json
import glob
import argparse
import pandas as pd
from tqdm import tqdm


def extract_frames_from_path(json_list, video_dir, output_dir):
    for json_path in json_list:
        file = open(json_path)
        data = json.load(file)
        print("images in current jon: ", len(data["images"]))
        print("annotations in current json: ", len(data["annotations"]))
        extract_frames_demographic(data, video_dir, output_dir)


def extract_frame_shelf_seg(video_path, frame_index, output_path):
    if not os.path.isfile(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        cap.release()
        if frame is not None:
            # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cv2.imwrite(output_path, frame)
            return True
        else:
            return False
    else:
        return True
        

def extract_frames_demographic(data, video_dir, output_dir, output_csv=None):
    filename_list = []
    age_list = []
    gender_list = []

    data['annotations'] = [x for x in data['annotations'] if x.get('attributes', {}).get('gender', -1) != -1]
    for annotation in tqdm(data["annotations"]):
        if "age" not in annotation["attributes"] or "gender" not in annotation["attributes"]:
            continue

        image_id = annotation["image_id"]
        logging.info('\nimage_id: {}'.format(image_id))
        item = [img for img in data["images"] if img['id'] == image_id][0]
        image_filename = item["file_name"]
        image_title = os.path.splitext(image_filename)[0]
        frame_index = int(image_title.split("_")[1])

        video_filename = item["video"]
        logging.info('video: {}'.format(video_filename))
        path = os.path.join(video_dir, video_filename)
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            logging.warning("video {} not in folder {}".format(video_filename, video_dir))
            continue
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

        if frame_index < 0 or frame_index > total_frames:
            continue
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        bbox = [int(x) for x in annotation["bbox"]]
        ret, frame = cap.read()
        if frame is not None:
            temp_name = os.path.basename(video_filename)
            video_title = os.path.splitext(temp_name)[0]
            dst_filename = f'{video_title}_{frame_index}_{bbox[0]}_{bbox[1]}.jpg'

            filename_list.append(dst_filename)
            age_list.append(annotation['attributes']["age"])
            gender_list.append(annotation['attributes']["gender"])

            save_img = frame[bbox[1]:bbox[1] + bbox[3], bbox[0]:bbox[0]+bbox[2]]
            cv2.imwrite(os.path.join(output_dir, dst_filename), save_img)

    df = pd.DataFrame({'filename': filename_list, 'age': age_list, 'gender': gender_list})
    csv_path = os.path.join(output_dir, 'demographic_labels.csv') if output_csv is None \
        else os.path.join(output_csv, 'demographic_labels.csv')
    df.to_csv(csv_path, mode='a', header=None, index=False)


if __name__ == '__main__':
    desc = "Dataset Preparation for age estimation"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--input_dir", type=str, default="")
    parser.add_argument("--video_dir", type=str, default="/media/data/small_video/small_video_upload_annotation")
    parser.add_argument("--output_dir", type=str,
                        default="")

    args = parser.parse_args()

    json_list = glob.glob(args.input_dir + "/*.json")
    print("Total jsons: ", len(json_list))

    extract_frames_from_path(json_list, args.video_dir, args.output_dir)
