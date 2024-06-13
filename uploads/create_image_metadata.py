'''
Script for generating image metadatafile 'image.json' from calibration file.

The image.json file generated follows the schema required by the rtls app.
'''

import json
import os
import argparse

image_metadata_file_name = "imageMetadata.json"
metadata_dict = {"images": [{"place": "", "view": "plan-view", "fileName": "Top.png"}]}

def generate_image_metadata(calibration_file_path, output_folder_path = None):
    calibration_json = None
    with open(calibration_file_path) as calibration_json_file:
        calibration_json = json.load(calibration_json_file)

    location_string = '/'.join(["{}={}".format(item['name'], item['value']) for item in calibration_json["sensors"][0]['place']])
    
    if not location_string:
        print("Could not construct {} file from calibration file {}.".format(image_metadata_file_name, calibration_file_path))
        return

    metadata_dict["images"][0]["place"] = location_string

    # Write output to file
    if output_folder_path:
        output_file_path = os.path.join(output_folder_path, image_metadata_file_name)
    else:
        curr_dir = os.getcwd()
        output_file_path = os.path.join(curr_dir, image_metadata_file_name)

    with open(output_file_path, "w") as outfile: 
        json.dump(metadata_dict, outfile)

def get_args():
    parser = argparse.ArgumentParser("Image Metadata Parser")
    parser.add_argument('-c', '--calibration_file_path', required=True, help='Path of calibration file to read metadata information from.')
    parser.add_argument('-d', '--destination_folder', required=False, help='Destination folder to write to.')
    args = parser.parse_args()
    return args

def main():
    args = get_args()
    generate_image_metadata(args.calibration_file_path, args.destination_folder)

if __name__ == "__main__":
    main()
