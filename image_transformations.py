def cut_bbox_image(img, bbox):
    if sum([x < 1 for x in bbox]) > 0:
        bbox = to_absolute_values(bbox, img.shape[0], img.shape[1])
    return img[bbox[1]:bbox[3], bbox[0]:bbox[2], :]


def to_relative_values(bbox, height, width):
    height, width = float(height), float(width)
    return [bbox[0]/width, bbox[1]/height, bbox[2]/width, bbox[3]/height]


def to_absolute_values(bbox, height, width):
    return [int(bbox[0]*width), int(bbox[1]*height), int(bbox[2]*width), int(bbox[3]*height)]
