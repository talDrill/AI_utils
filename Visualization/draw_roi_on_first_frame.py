import os
import argparse
import cv2
import logging
import json
from PIL import Image, ImageDraw
import logging


def get_args():
    parser = argparse.ArgumentParser(
        "This script gets video and roi_points.json files, and draw the roi on the first frame of the video. It is a visulization tool."
    )
    parser.add_argument("--input_video", help="Path to a video to extract.")
    parser.add_argument(
        "-rp", "--roi_points_file", help="Path to roi_points.json file."
    )
    parser.add_argument("-cn", "--camera_number", help="Camera number.")
    parser.add_argument(
        "--output_folder",
        help="Folder for outputs. The output frame will be saved in this folder with the name <video name>_roi_points.png",
    )
    return parser.parse_known_args()


def main(input_video, roi_points_file, camera_number, output_folder):
    """
    The main function is the only function we have in this script.
    It takes the first frame from the video and draw the planogram on it.
    The output is a png image of the first frame, that the planogram was drawed on it.
    """
    # Read the video with cv2.VideoCapture and extract the first frame
    cap = cv2.VideoCapture(input_video)
    if cap.isOpened():
        logging.info("\n video {} opened".format(input_video))
    else:
        logging.info("\n cannot open video {}".format(input_video))
        exit(1)
    frame = cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2RGB)
    cap.release()
    del cap
    # Parse roi_points.json and extract the roi for the specified camera.
    with open(roi_points_file, "r") as fp:
        roi_points = json.load(fp)
    camera = "camera_{}".format(camera_number)
    roi = roi_points[list(roi_points.keys())[0]][
        list(roi_points[list(roi_points.keys())[0]].keys())[0]
    ][camera]
    # Draw polygon on first frame
    my_points = [(roi[key][0], roi[key][1]) for key in ["A", "B", "C", "D"]]
    img_PIL = Image.fromarray(frame).convert("RGBA")
    poly = Image.new("RGBA", img_PIL.size)
    img_draw = ImageDraw.Draw(poly)
    img_draw.polygon(my_points, fill=(255, 0, 0, 127), outline=(255, 255, 255, 255))
    img_PIL.paste(poly, mask=poly)
    # # Save output
    os.makedirs(output_folder, exist_ok=True)
    output_file_name = (
        os.path.basename(input_video).split(".mp4")[0] + "_roi_points.png"
    )
    img_PIL.save(os.path.join(output_folder, output_file_name))


if __name__ == "__main__":
    # Get args and run main function
    args, _ = get_args()
    logging.info(args)
    main(args.input_video, args.roi_points_file, args.camera_number, args.output_folder)
