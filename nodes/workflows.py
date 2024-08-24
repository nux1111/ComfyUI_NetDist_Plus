import os
import json
import hashlib
import folder_paths

class SaveDiskWorkflowJSON:
	"""Save workflow to disk"""
	def __init__(self):
		self.output_dir = folder_paths.get_output_directory()

	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"workflow": ("JSON", ),
				"filename_prefix": ("STRING", {"default": "workflow/ComfyUI"}),
			}
		}

	RETURN_TYPES = ()
	FUNCTION = "save_workflow"
	OUTPUT_NODE = True
	CATEGORY = "remote/advanced"
	TITLE = "Save workflow (disk)"

	def save_workflow(self, workflow, filename_prefix):
		full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir)

		json_path = os.path.join(full_output_folder, f"{filename}_{counter:05}_.json")
		with open(json_path, "w") as f:
			f.write(json.dumps(workflow, indent=2))
		return {}

class LoadDiskWorkflowJSON:
	"""Load workflow JSON from disk"""
	def __init__(self):
		pass

	@classmethod
	def INPUT_TYPES(s):
		input_dir = folder_paths.get_input_directory()
		files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f)) and f.endswith(".json")]
		return {
			"required": {
				"workflow": [sorted(files),],
			}
		}

	RETURN_TYPES = ("JSON",)
	RETURN_NAMES = ("Workflow JSON",)
	FUNCTION = "load_workflow"
	CATEGORY = "remote/advanced"
	TITLE = "Load workflow (disk)"

	def load_workflow(self, workflow):
		json_path = folder_paths.get_annotated_filepath(workflow)
		with open(json_path) as f:
			data = json.loads(f.read())
		return (data,)

	@classmethod
	def IS_CHANGED(s, workflow):
		json_path = folder_paths.get_annotated_filepath(workflow)
		m = hashlib.sha256()
		with open(json_path, 'rb') as f:
			m.update(f.read())
		return m.digest().hex()

	@classmethod
	def VALIDATE_INPUTS(s, workflow):
		if not folder_paths.exists_annotated_filepath(workflow):
			return "Invalid JSON file: {}".format(workflow)
		json_path = folder_paths.get_annotated_filepath(workflow)
		with open(json_path) as f:
			try: json.loads(f.read())
			except:
				return "Failed to read JSON file: {}".format(workflow)
		return True

class LoadCurrentWorkflowJSON:
	"""Fetch the current workflow/prompt as an API compatible JSON"""
	def __init__(self):
		pass

	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {},
			"hidden": {
				"prompt": "PROMPT",
			},
		}
	
	RETURN_TYPES = ("JSON",)
	RETURN_NAMES = ("Workflow JSON",)
	FUNCTION = "load_workflow"
	CATEGORY = "remote/advanced"
	TITLE = "Load workflow (current)"

	def load_workflow(self, prompt):
		return (prompt,)

	@classmethod
	def IS_CHANGED(s, prompt):
		return hashlib.sha256(json.dumps(prompt)).digest().hex()

import os
import json
import hashlib
import folder_paths
from PIL import Image
import piexif


class LoadWorkflowJSON:
    """Load workflow JSON from disk or image upload"""
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True}),
            }
        }

    RETURN_TYPES = ("JSON",)
    RETURN_NAMES = ("Workflow JSON",)
    FUNCTION = "load_workflow"
    CATEGORY = "remote/advanced"
    TITLE = "Load workflow (image upload)"

    def load_workflow(self, image):
        try:
            image_path = folder_paths.get_annotated_filepath(image)
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            with Image.open(image_path) as img:
                # Try to get the EXIF data
                exif_data = img.info.get("exif")
                if not exif_data:
                    raise ValueError("No EXIF data found in the image")

                exif_dict = piexif.load(exif_data)
                user_comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                if not user_comment:
                    raise ValueError("No UserComment found in EXIF data")

                metadata = json.loads(user_comment.decode("utf-8"))
                workflow_json = metadata.get("prompt")
                if not workflow_json:
                    raise ValueError("No 'prompt' field found in UserComment data")

                # Parse the JSON string into a Python object
                workflow_data = json.loads(workflow_json)
                return (workflow_data,)

        except Exception as e:
            print(f"Error loading workflow from image: {str(e)}")
            return ({},)  # Return an empty JSON object in case of error

    @classmethod
    def IS_CHANGED(s, image):
        try:
            image_path = folder_paths.get_annotated_filepath(image)
            if not os.path.exists(image_path):
                return "FILE_NOT_FOUND"
            
            m = hashlib.sha256()
            with open(image_path, 'rb') as f:
                m.update(f.read())
            return m.digest().hex()
        except Exception as e:
            print(f"Error in IS_CHANGED: {str(e)}")
            return "ERROR"

    @classmethod
    def VALIDATE_INPUTS(s, image):
        try:
            image_path = folder_paths.get_annotated_filepath(image)
            if not os.path.exists(image_path):
                return f"Image file not found: {image_path}"

            with Image.open(image_path) as img:
                exif_data = img.info.get("exif")
                if not exif_data:
                    return f"No EXIF data found in image: {image}"

                exif_dict = piexif.load(exif_data)
                user_comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                if not user_comment:
                    return f"No UserComment found in EXIF data: {image}"

                metadata = json.loads(user_comment.decode("utf-8"))
                if "prompt" not in metadata:
                    return f"No 'prompt' field found in UserComment data: {image}"

            return True
        except Exception as e:
            return f"Error validating image: {image}. Error: {str(e)}"

NODE_CLASS_MAPPINGS = {
	"SaveDiskWorkflowJSON":    SaveDiskWorkflowJSON,
	"LoadDiskWorkflowJSON":    LoadDiskWorkflowJSON,
	"LoadCurrentWorkflowJSON": LoadCurrentWorkflowJSON,
	"LoadWorkflowJSON":    LoadWorkflowJSON,
}
