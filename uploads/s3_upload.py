import logging
import boto3
from botocore.exceptions import ClientError
import os
import argparse
import glob
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if not object_name:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def get_args():
    parser = argparse.ArgumentParser("SDG Utils")
    parser.add_argument('-sd', '--source_directory', required=False, help='Path to source folder to copy.')
    parser.add_argument('-f', '--format_to_copy', required=False, help='Format of files to match and upload, can be left empty for a single file.')
    parser.add_argument('-dd', '--destination_directory', required=False, help='Destination folder in S3 folder.')
    parser.add_argument('-sf', '--source_file', required=False, help='Path to source file to copy.')
    parser.add_argument('-df', '--destination_file', required=False, help='Destination file in S3 folder')
    parser.add_argument('-b', '--bucket', required=True, help='S3 bucket to copy data to.')
    args = parser.parse_args()
    return args

def main():
    args = get_args()

    logging.info("")
    # Folder copy variables
    source_directory = args.source_directory
    destination_directory = args.destination_directory
    format_to_copy = args.format_to_copy
    source_file = args.source_file
    destination_file = args.destination_file
    bucket = args.bucket



    if source_directory:
        if os.path.isdir(source_directory):
            files = glob.glob("{}/**/*.{}".format(source_directory, format_to_copy),recursive=True)
            logging.info("Total files to copy - {}".format(len(files)))
            for file in files:
                logging.info("Copying file {}".format(file))
                file_name = os.path.basename(file)
                destination_object = None
                if destination_directory:
                    destination_object = destination_directory + "/" + file_name
                upload_file(file, bucket, destination_object)
        else:
            logging.error("Invalid source_directory passed.")

    if source_file:
        if os.path.isfile(source_file):
            logging.info("Copying file {}".format(source_file))
            upload_file(source_file, bucket, destination_file)
        else:
            logging.error("Invalid source_file passed.")


if __name__ == "__main__":
    main()