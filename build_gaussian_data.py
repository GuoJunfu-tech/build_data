import os
import shutil
import zipfile
import json
import re
from PIL import Image


def unpack_zip_files(address, start_name):
    """
    Extracts the contents of ZIP files in a given address and creates new directories with the same names.

    Args:
        address (str): The directory containing the ZIP files.

    Raises:
        OSError: If an error occurs while creating directories or extracting files.
    """

    for filename in os.listdir(address):
        if filename.endswith(".zip") and filename.startswith(start_name):
            zip_filepath = os.path.join(address, filename)
            try:
                # Create a directory with the same name as the ZIP file (without extension)
                directory_name = os.path.splitext(filename)[0]
                new_directory = os.path.join(address, directory_name)
                os.makedirs(
                    new_directory, exist_ok=True
                )  # Handle pre-existing directories

                with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
                    zip_ref.extractall(new_directory)
                    print(f"Extracted '{filename}' to '{new_directory}'")
            except (OSError, zipfile.BadZipFile) as e:
                print(f"Error extracting '{filename}': {e}")


def rename_images(file_list, target_address):
    """
    Renames images in a directory structure according to the sequence of document names.

    Args:
        address (str): The base directory containing the datasets.
    """

    image_counter = 1
    for filename in file_list:
        filename_train = os.path.join(filename, "train")
        image_list = get_file_list_ref_to_the_end_number("", ".png", filename_train)

        print(f"\n\n processing file [{filename_train}]")

        # Counter for image sequence within this dataset
        for image_name in image_list:
            if image_name.endswith(".png"):
                print(f"copying file: [{image_name}]")
                # Construct the new image name with padding
                new_name = f"{(image_counter):04d}.png"

                # Create the full path to the new image
                new_path = os.path.join(target_address, new_name)

                # copy the image
                shutil.copy(os.path.join(filename, image_name), new_path)
                print(f"to: [{new_path}]")

                image_counter += 1


def generate_transform_json(
    file_list: list[str], target_address: str, test_or_train: str = "test"
) -> None:
    sequence_number = 1
    time = 0
    # print(file_list, "\n", target_address)
    # time_steps = count_files_with_start_name(root_address, "dataset-") - 1
    time_steps = len(file_list) - 1
    print(f"time_steps:{time_steps}")
    time_step = 1.0 / time_steps

    camera_angle_x, camera_angle_y = None, None

    new_data = {}
    new_frames = []
    for filename in file_list:

        print(f"processing file {filename}")

        json_file = os.path.join(filename, f"transforms_train.json")

        with open(json_file, "r") as f:
            origin_data = json.load(f)
            if sequence_number == 1:
                camera_angle_x = origin_data["camera_angle_x"]
                camera_angle_y = origin_data["camera_angle_y"]

            for frame in origin_data["frames"]:
                new_frame = dict()
                new_frame["time"] = time
                print(f"write time: {time}")
                # print(f"sequence_number: {sequence_number}")
                file_path = f"./{test_or_train}/{(sequence_number):04d}"
                # print(f"file_path: {file_path}")
                new_frame["file_path"] = file_path
                new_frame["transform_matrix"] = frame["transform_matrix"]

                new_frames.append(new_frame)

                sequence_number += 1

        time += time_step

    new_data["camera_angle_x"] = camera_angle_x
    new_data["camera_angle_y"] = camera_angle_y
    new_data["frames"] = new_frames

    output_json_file = os.path.join(target_address, f"transforms_{test_or_train}.json")
    with open(output_json_file, "w") as output_file:
        json.dump(new_data, output_file, indent=4)


def count_files_with_start_name(address, start_name, end_name=".zip"):
    count = 0
    for filename in os.listdir(address):
        if filename.endswith(end_name):
            continue
        if filename.startswith(start_name):
            count += 1
    return count


def get_file_list_ref_to_the_end_number(start_name="", end_name="", address=""):
    # return the file names according to the number at the end of the file name, ignore the .zip files
    # e.g. [data-01, data-09, data-19, data-20, data-21]
    # pattern = r"^dataset-(\d+)$"  # Match only "data-" followed by digits
    pattern = rf"^{start_name}(\d+){end_name}$"  # Match only "data-" followed by digits
    filenames = [f for f in os.listdir(address) if re.match(pattern, f)]
    filenames.sort(key=lambda filename: int(re.match(pattern, filename).group(1)))
    output_files = []
    for file in filenames:
        output_files.append(os.path.join(address, file))
    return output_files


def crop_image_and_lowen_resolution(image_path, output_path, resolution=(800, 800)):
    """
    Reads an image, crops it to a square in the center, resizes it to 800x800, and saves it.

    Args:
        image_path: Path to the input image file.
        output_path: Path to save the processed image file.
    """
    try:
        # Open the image
        img = Image.open(image_path)

        # Get image width and height
        width, height = img.size

        # Calculate the minimum dimension for square cropping
        min_dim = min(width, height)

        # Calculate starting coordinates for center square crop
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2

        # Crop the image to a square
        cropped_img = img.crop((left, top, left + min_dim, top + min_dim))

        # Resize the cropped image to 800x800
        resized_img = cropped_img.resize((800, 800))

        # Save the processed image
        resized_img.save(output_path)

        print(f"Image processed successfully! Saved to: {output_path}")
    except Exception as e:
        print(f"Error processing image: {e}")


if __name__ == "__main__":
    # Replace 'path/to/your/directory' with the actual directory containing ZIP files
    address = "/home/guojunfu/Documents/articulated_gaussian/build_data/"
    unpack_zip_files(address, start_name="test-")
    file_list = get_file_list_ref_to_the_end_number("test-", "", address)

    target_address = os.path.join(address, "test")
    os.makedirs(target_address, exist_ok=True)

    rename_images(file_list, target_address)
    generate_transform_json(file_list, address, test_or_train="test")
