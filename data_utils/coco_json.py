from detectron2.data.datasets.coco import load_coco_json
from PIL import Image, ImageDraw
from pycocotools.coco import COCO
import numpy as np
import matplotlib.pyplot as plt
import json
import os

class COCO_annotation(COCO):
    def __init__(self, json_path, data_path='', dataset_name=None) -> None:
        super().__init__(json_path)
        self.coco_annot = load_coco_json(json_file=json_path, image_root=data_path, dataset_name=dataset_name, extra_annotation_keys=["attributes", "area"])

    def create_planogram_mask_from_annotations(self, img_idx=0):
        """
        This method creates a mask of the shelf categories, and a map between the values in the mask and the categories' names.
        Input: An index of the frame that the planogram was marked.
        
        """
        planogram_cls = [n['id'] for n in self.cats.values() if n['name'] == 'shelf_sections'][0]
        img_dict = self.coco_annot[img_idx]
        planogram_mask = Image.new('L', (img_dict['width'], img_dict['height']), 0)
        shelf_names_ids_dict = {}
        shelf_name_id = 1
        for annot in img_dict['annotations']:
            if annot['category_id'] == planogram_cls:
                poly = [int(a) for a in annot['segmentation'][0]]
                ImageDraw.Draw(planogram_mask).polygon(poly, outline=shelf_name_id, fill=shelf_name_id)
                shelf_names_ids_dict[shelf_name_id] = annot['attributes']['shelf_name']
                shelf_name_id += 1
        return np.array(planogram_mask), shelf_names_ids_dict
    
    def create_planogram_file_from_annotations(self, output_path, img_idx=0):
        planogram_cls = [n['id'] for n in self.cats.values() if n['name'] == 'shelf_sections'][0]
        name_to_poly_dict = {}
        img_dict = self.coco_annot[img_idx]
        other = 1
        for annot in img_dict['annotations']:
            if annot['category_id'] == str(planogram_cls):
                poly = [int(a) for a in annot['bbox']]
                if annot["attributes"]["shelf_name"] == 'other':
                    k = annot["attributes"]["shelf_name"] + '_{}'.format(other)
                    other += 1
                else:
                    k = annot["attributes"]["shelf_name"]
                name_to_poly_dict[k] = poly
        img_size_dict = {'width': img_dict['width'], 'height': img_dict['height']}
        output_dict = {'img_size': img_size_dict, 'planogram': name_to_poly_dict}
        with open(output_path, 'w') as f:
            json.dump(output_dict, f)

    
    @staticmethod
    def create_planogram_mask_from_planogram_file(plan_file, debug=False):
        planogram_dict = json.load(open(plan_file))
        planogram_mask = Image.new('L', (planogram_dict['img_size']['width'], planogram_dict['img_size']['height']), 0)
        id_to_name_dict = {0: None}
        
        for shelf_name_id, (name, poly) in enumerate(planogram_dict['planogram'].items()):
            ImageDraw.Draw(planogram_mask).polygon(poly, outline=shelf_name_id, fill=shelf_name_id)
            id_to_name_dict[shelf_name_id + 1] = name
        
        if debug:
            plt.imsave(os.path.join(os.path.dirname(plan_file), 'planogram_mask.png'), np.array(planogram_mask))
        
        return np.array(planogram_mask), id_to_name_dict
