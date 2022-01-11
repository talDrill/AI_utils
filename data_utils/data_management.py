from datetime import datetime
import argparse
import glob
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
import logging
from datetime import datetime
from utils.sql_utils import execute_sql_query
from frame_extraction import build_df, extract_frames_ava, build_frame_list_csv
from frame_creation_from_cvat import extract_frames_demographic, extract_frame_shelf_seg
from tqdm import tqdm


BASE_DIRECTORY = "/media/data/StoragePath/Datasets"


def get_datetime(task):
    return datetime.strptime(task['completed_date'].split('.')[0], "%Y-%m-%dT%H:%M:%S")


def start_and_end_date(cvat_annotation):
    dates = [get_datetime(task) for task in cvat_annotation['tasks']]
    return min(dates), max(dates)


def min_and_max_dates(json_list):
    bounding_dates = [start_and_end_date(json.load(open(path))) for path in json_list]
    starts, ends = zip(*bounding_dates)
    return {'earliest_date': min(starts), 'latest_date': max(ends)}


def get_latest_update(annotation_class):
    latest_update = execute_sql_query("select end from data_management where class='{}'".format(annotation_class))
    return latest_update[0][0]


def get_all_latest_updates():
    data_updates = execute_sql_query("select class, end from data_management")
    return {x[0]: x[1] for x in data_updates}


def update_last_update(class_name, date):
    last_update_date = get_latest_update(class_name)
    if date > last_update_date:
        logging.info("last update date for class {}: {}".format(class_name, date))
        execute_sql_query("update data_management set end='{}' where class='{}'".format(date, class_name))


def filter_annotation_on_tasks(annotation, task_ids):
    filtered_images = [img for img in annotation['images'] if img['task_id'] in task_ids]
    image_ids = [img['id'] for img in filtered_images]
    filtered_annotations = [annot for annot in annotation['annotations'] if annot['image_id'] in image_ids]
    filtered_annotation = {'tasks': [t for t in annotation['tasks'] if t['id'] in task_ids],
                           'images': filtered_images, 'annotations': filtered_annotations,
                           'categories': annotation['categories']}
    return filtered_annotation


def filter_annotation_on_dates(annotation, from_date):
    recent_task_ids = [task['id'] for task in annotation['tasks'] if get_datetime(task) > from_date]
    return filter_annotation_on_tasks(annotation, recent_task_ids)


def append_to_json(data: dict, path):
    if os.path.exists(path):
        with open(path, 'r') as fp:
            previous = json.load(fp)
        data.update(previous)
    with open(path, 'w') as fp:
        json.dump(data, fp)


def demographic_pipe(annotations, video_dir, frame_dir, csv_folder):
    for annotation in annotations:
        extract_frames_demographic(annotation, video_dir, frame_dir, csv_folder)


def action_pipe(annotations, video_dir, frame_dir, csv_folder):
    for annotation in annotations:
        for task in tqdm(annotation['tasks']):
            logging.info('process on task: {}'.format(task['task_id']))
            annot = filter_annotation_on_tasks(annotation, [task['id']])
            action_df = build_df([annot], is_opened=True)
            if len(action_df) > 0:
                video_path = os.path.join(video_dir, task['video'])
                rc = extract_frames_ava(video_path, frame_dir, step=20)
                if rc == 0:
                    logging.info("writing {} new actions to csv action_labels".format(len(action_df)))
                    action_df.to_csv(os.path.join(csv_folder, "action_labels.csv"), index=False, header=None, mode='a')
                    frame_list_name = os.path.join(csv_folder, "frame_list.csv")
                    frame_list = build_frame_list_csv([task['video']], frame_dir, frame_list_name)
                    logging.info("writing {} new lines to csv frame list csv".format(len(frame_list)))
                    frame_list.to_csv(frame_list_name, index=False, mode="a", header=None, sep=' ')


def seg_pipe(jsons_annot, video_dir, frame_dir, json_folder):
    """
    This function creates a data for shelf segmetation.
    Inputs:
    jsons_annot: dictionary contains json annotations
    video_dir: root folder of videos directory
    frame_dir: frame output directory
    csv_folder: output directory to store json file
    """
    for j in jsons_annot:
        j_dict = {}
        shelf_sections_ids = []
        for cat in j["categories"]:
            if cat["name"] == "shelf_sections":
                shelf_sections_ids.append(cat['id'])
        for annot in tqdm(j["annotations"]):
            if int(annot["category_id"]) in shelf_sections_ids:
                img_inst = [img for img in j["images"] if img['id'] == annot["image_id"]][0]
                video_path = os.path.join(video_dir, img_inst['video'])
                frame_num = int(img_inst['file_name'].split('.')[0].split('_')[-1])
                new_image_name = "{}_{}.png".format(img_inst['video'].replace('.mp4', ''), frame_num)
                if new_image_name not in j_dict.keys():
                    j_dict[new_image_name] = []
                annot_json = {}
                annot_json['bbox'] = annot['bbox']
                annot_json['label'] = annot['attributes']['shelf_name']
                annot_json['height'] = annot['attributes']['shelf_height']
                saving_indicator = extract_frame_shelf_seg(video_path, frame_num,
                                                           os.path.join(frame_dir, new_image_name))
                if saving_indicator:
                    j_dict[new_image_name].append(annot_json)
        append_to_json(j_dict, os.path.join(json_folder, 'shelf_segmentation_labels.json'))
                
        
def pipe(class_name, arguments):
    logging.info("runing pipe for {} class".format(class_name))
    if class_name == 'demographic':
        demographic_pipe(*arguments)
    elif class_name == 'action':
        action_pipe(*arguments)
    elif class_name == 'shelf_segmentation':
        seg_pipe(*arguments)


def get_args():
    desc = "Data management from CVAT"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-lu", "--last_updates", action="store_true", default=False,
                        help='if you wants to get last time data was downloaded, without running script')
    required = '-lu' not in sys.argv and '--last_updates' not in sys.argv
    parser.add_argument("--class_name", type=str, choices=['action', 'demographic', 'shelf_segmentation'],
                        required=required)
    parser.add_argument("--video_dir", type=str, default="/media/data/small_video/small_video_upload_annotation")
    parser.add_argument("--input_dir", type=str, required=required,
                        help="folder with json annotation to runs on")
    return parser.parse_args()


def main():
    args = get_args()
    last_updates = get_all_latest_updates()
    if args.last_updates:
        logging.info("last updates: {}".format(last_updates))
        return last_updates

    json_list = glob.glob(args.input_dir + "/*.json")
    logging.info("Total jsons: {}".format(len(json_list)))
    most_recent_date = min_and_max_dates(json_list)['latest_date']
    from_date = last_updates[args.class_name]
    logging.info("last update was on {}, starting from this date".format(from_date))
    cvat_dicts = [json.load(open(js)) for js in json_list]
    for cvat_dict in cvat_dicts:
        cvat_dict['annotations'] = [annot for annot in cvat_dict['annotations'] if annot['attributes'] is not None]
    cvat_dicts = [filter_annotation_on_dates(annot, from_date) for annot in cvat_dicts]
    logging.info("annotation per file: " + ", ".join([str(len(cvat['annotations'])) for cvat in cvat_dicts]))

    label_directory = os.path.join(BASE_DIRECTORY, args.class_name, "labels")
    frame_directory = os.path.join(BASE_DIRECTORY, args.class_name, "frames")
    pipe(args.class_name, [cvat_dicts, args.video_dir, frame_directory, label_directory])
    update_last_update(args.class_name, most_recent_date)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
