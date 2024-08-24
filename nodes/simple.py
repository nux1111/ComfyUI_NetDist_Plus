from ..core.fetch import fetch_from_remote, fetch_from_remote_with_extras
from ..core.utils import clean_url, get_client_id, get_new_job_id
from ..core.dispatch import dispatch_to_remote, clear_remote_queue

class FetchRemote():
	"""
	Try to retrieve the final output image from the remote client.
	On the remote client, this is replaced with a preview image node.
	I.e. remote_info can be none, but the node shouldn't exist at that point
	"""
	def __init__(self):
		pass

	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"final_image": ("IMAGE",),
				"remote_info": ("REMINFO",),
			},
		}

	RETURN_TYPES = ("IMAGE",)
	FUNCTION = "fetch"
	CATEGORY = "remote"
	TITLE = "Fetch from remote"

	def fetch(self, final_image, remote_info):
		out = fetch_from_remote(
			remote_url = remote_info.get("remote_url"),
			job_id     = remote_info.get("job_id"),
		)
		if out is None:
			out = final_image[:1] * 0.0 # black image
		return (out,)

#with extras returns, the image, remote latent and conditioning if there are any
class FetchRemoteWithExtras():
    """
    Try to retrieve the final output image from the remote client.
    On the remote client, this is replaced with a preview image node.
    I.e. remote_info can be none, but the node shouldn't exist at that point
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "final_image": ("IMAGE",),
                "remote_info": ("REMINFO",),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("IMAGE", "latent_base64", "conditioning_base64")
    FUNCTION = "fetch"
    CATEGORY = "remote"
    TITLE = "Fetch from remote"

    def fetch(self, final_image, remote_info):
        out, metadata = fetch_from_remote_with_extras(
            remote_url = remote_info.get("remote_url"),
            job_id     = remote_info.get("job_id"),
        )
        if out is None:
            out = final_image[:1] * 0.0 # black image
        
        latent = metadata.get("latent_base64", None)
        conditioning = metadata.get("conditioning_base64", None)
        
        return (out, latent, conditioning)

import ast

#v2 of remote queue to prevent to fix ui mess
class RemoteQueueSimpleNux():
    """
    This is a "simplified" version with additional optional parameters for remote execution.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "remote_url": ("STRING", {
                    "multiline": False,
                    "default": "http://127.0.0.1:8288/",
                }),
                "batch_local": ("INT", {"default": 1, "min": 1, "max": 8}),
                "batch_remote": ("INT", {"default": 1, "min": 1, "max": 8}),
                "trigger": (["on_change", "always"],),
                "enabled": (["true", "false", "remote"],{"default": "true"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            },
            "optional": {
				"remoteapply1": ("REMOTEAPPLY",),
				"remoteapply2": ("REMOTEAPPLY",),
				"remoteapply3": ("REMOTEAPPLY",),
				"remoteapply4": ("REMOTEAPPLY",),
				"remoteapply5": ("REMOTEAPPLY",),
				"remoteapply6": ("REMOTEAPPLY",),
				"remoteapply7": ("REMOTEAPPLY",),
				"remoteapply8": ("REMOTEAPPLY",),
				"remoteapply9": ("REMOTEAPPLY",),
				"remoteapply10": ("REMOTEAPPLY",),
            },
            "hidden": {
                "prompt": "PROMPT",
            },
        }

    RETURN_TYPES = ("INT", "INT", "REMINFO",)
    RETURN_NAMES = ("seed", "batch", "remote_info",)
    FUNCTION = "queue"
    CATEGORY = "remote"
    TITLE = "Queue on remote (single)"

    def parse_value(self, value, value_type):
        """Parse the value string to the specified type."""
        if value_type == "INT":
            return int(value)
        elif value_type == "FLOAT":
            return float(value)
        elif value_type == "BOOL":
            return value.lower() == "true"
        else:  # STRING or any other type
            return value

    def queue(self, remote_url, batch_local, batch_remote, trigger, enabled, seed, prompt, 
		remoteapply1=None, remoteapply2=None, remoteapply3=None, remoteapply4=None,
		remoteapply5=None, remoteapply6=None, remoteapply7=None, remoteapply8=None,
		remoteapply9=None, remoteapply10=None):
        if enabled == "false":
            return (seed, batch_local, {})
        if enabled == "remote":
            return (seed+batch_local, batch_remote, {})
        
        job_id = get_new_job_id()
        remote_url = clean_url(remote_url)
        clear_remote_queue(remote_url)
        
        # Prepare remote parameters
        remote_params = []
        for remoteapply in [remoteapply1, remoteapply2, remoteapply3, remoteapply4,
                            remoteapply5, remoteapply6, remoteapply7, remoteapply8,
                            remoteapply9, remoteapply10]:
            if remoteapply:
                nodetitle, param, value, value_type = remoteapply
                if param and value:
                    remote_params.append((param, self.parse_value(value, value_type), nodetitle))
        
        dispatch_to_remote(remote_url, prompt, job_id, remote_params)
        remote_info = {
            "remote_url" : remote_url,
            "job_id"     : job_id,
        }
        return (seed, batch_local, remote_info)

    @classmethod
    def IS_CHANGED(self, remote_url, batch_local, batch_remote, trigger, enabled, seed, prompt, 
                   remoteapply1=None, remoteapply2=None, remoteapply3=None, remoteapply4=None,
                   remoteapply5=None, remoteapply6=None, remoteapply7=None, remoteapply8=None,
                   remoteapply9=None, remoteapply10=None):
        uuid = f"W:{remote_url},B1:{batch_local},B2:{batch_remote},S:{seed},E:{enabled}"
        for i, remoteapply in enumerate([remoteapply1, remoteapply2, remoteapply3, remoteapply4,
                                         remoteapply5, remoteapply6, remoteapply7, remoteapply8,
                                         remoteapply9, remoteapply10], start=1):
            if remoteapply:
                param, value, value_type, nodetitle = remoteapply
                uuid += f",RP{i}:{param}:{value}:{value_type}:{nodetitle}"
        return uuid if trigger == "on_change" else str(time.time())

class RemoteQueueSimple():
    """
    This is a "simplified" version with additional optional parameters for remote execution.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "remote_url": ("STRING", {
                    "multiline": False,
                    "default": "http://127.0.0.1:8288/",
                }),
                "batch_local": ("INT", {"default": 1, "min": 1, "max": 8}),
                "batch_remote": ("INT", {"default": 1, "min": 1, "max": 8}),
                "trigger": (["on_change", "always"],),
                "enabled": (["true", "false", "remote"],{"default": "true"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            },
            #init idea for entering settings for the remote workflow.
            "optional": {
                "remote_param1": ("STRING", {"default": ""}),
                "remote_value1": ("STRING", {"default": ""}),
                "remote_type1": (["STRING", "INT", "FLOAT", "BOOL"], {"default": "STRING"}),
                "remote_nodetitle1": ("STRING", {"default": ""}),  # Added nodetitle
                "remote_param2": ("STRING", {"default": ""}),
                "remote_value2": ("STRING", {"default": ""}),
                "remote_type2": (["STRING", "INT", "FLOAT", "BOOL"], {"default": "STRING"}),
                "remote_nodetitle2": ("STRING", {"default": ""}),  # Added nodetitle
                "remote_param3": ("STRING", {"default": ""}),
                "remote_value3": ("STRING", {"default": ""}),
                "remote_type3": (["STRING", "INT", "FLOAT", "BOOL"], {"default": "STRING"}),
                "remote_nodetitle3": ("STRING", {"default": ""}),  # Added nodetitle
                "remote_param4": ("STRING", {"default": ""}),
                "remote_value4": ("STRING", {"default": ""}),
                "remote_type4": (["STRING", "INT", "FLOAT", "BOOL"], {"default": "STRING"}),
                "remote_nodetitle4": ("STRING", {"default": ""}),  # Added nodetitle
            },
            "hidden": {
                "prompt": "PROMPT",
            },
        }

    RETURN_TYPES = ("INT", "INT", "REMINFO",)
    RETURN_NAMES = ("seed", "batch", "remote_info",)
    FUNCTION = "queue"
    CATEGORY = "remote"
    TITLE = "Queue on remote (single)"

    def parse_value(self, value, value_type):
        """Parse the value string to the specified type."""
        if value_type == "INT":
            return int(value)
        elif value_type == "FLOAT":
            return float(value)
        elif value_type == "BOOL":
            return value.lower() == "true"
        else:  # STRING or any other type
            return value

    def queue(self, remote_url, batch_local, batch_remote, trigger, enabled, seed, prompt, 
              remote_param1="", remote_value1="", remote_type1="STRING", remote_nodetitle1="",
              remote_param2="", remote_value2="", remote_type2="STRING", remote_nodetitle2="",
              remote_param3="", remote_value3="", remote_type3="STRING", remote_nodetitle3="",
              remote_param4="", remote_value4="", remote_type4="STRING", remote_nodetitle4=""):
        if enabled == "false":
            return (seed, batch_local, {})
        if enabled == "remote":
            return (seed+batch_local, batch_remote, {})
        
        job_id = get_new_job_id()
        remote_url = clean_url(remote_url)
        clear_remote_queue(remote_url)
        
        # Prepare remote parameters
        remote_params = []
        for param, value, value_type, nodetitle in [
            (remote_param1, remote_value1, remote_type1, remote_nodetitle1),
            (remote_param2, remote_value2, remote_type2, remote_nodetitle2),
            (remote_param3, remote_value3, remote_type3, remote_nodetitle3),
            (remote_param4, remote_value4, remote_type4, remote_nodetitle4)
        ]:
            if param and value:
                remote_params.append((param, self.parse_value(value, value_type), nodetitle))
        
        dispatch_to_remote(remote_url, prompt, job_id, remote_params)
        remote_info = {
            "remote_url" : remote_url,
            "job_id"     : job_id,
        }
        return (seed, batch_local, remote_info)

    @classmethod
    def IS_CHANGED(self, remote_url, batch_local, batch_remote, trigger, enabled, seed, prompt, 
                   remote_param1="", remote_value1="", remote_type1="STRING", remote_nodetitle1="",
                   remote_param2="", remote_value2="", remote_type2="STRING", remote_nodetitle2="",
                   remote_param3="", remote_value3="", remote_type3="STRING", remote_nodetitle3="",
                   remote_param4="", remote_value4="", remote_type4="STRING", remote_nodetitle4=""):
        uuid = f"W:{remote_url},B1:{batch_local},B2:{batch_remote},S:{seed},E:{enabled}"
        uuid += f",RP1:{remote_param1}:{remote_value1}:{remote_type1}:{remote_nodetitle1}"
        uuid += f",RP2:{remote_param2}:{remote_value2}:{remote_type2}:{remote_nodetitle2}"
        uuid += f",RP3:{remote_param3}:{remote_value3}:{remote_type3}:{remote_nodetitle3}"
        uuid += f",RP4:{remote_param4}:{remote_value4}:{remote_type4}:{remote_nodetitle4}"
        return uuid if trigger == "on_change" else str(time.time())

NODE_CLASS_MAPPINGS = {
    "RemoteQueueSimple(Nux)" : RemoteQueueSimpleNux,
	"RemoteQueueSimple" : RemoteQueueSimple,
	"FetchRemote"       : FetchRemote,
    "FetchRemoteWithExtras(Nux)": FetchRemoteWithExtras,
}
