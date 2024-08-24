from ..core.utils import clean_url, get_client_id, get_new_job_id
from ..core.dispatch import dispatch_to_remote, clear_remote_queue

import copy

class RemoteApplyValues:
    """Apply values to remote nodes"""
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "nodeid": ("STRING", {"default": ""}),
                "param": ("STRING", {"default": ""}),
                "value": ("STRING", {"default": ""}),
                "type": (["STRING", "INT", "FLOAT", "BOOL"], {"default": "STRING"}),
            }
        }

    RETURN_TYPES = ("REMOTEAPPLY",)
    RETURN_NAMES = ("remote_apply",)
    FUNCTION = "apply_values"
    CATEGORY = "remote/advanced"
    TITLE = "Apply Values to Remote Nodes"

    def apply_values(self, nodeid, param, value, type):
        return ((nodeid, param, value, type),)

class RemoteApplyValuesMulti:
    """Apply values to remote nodes"""
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "nodeid": ("STRING", {"default": ""}),
                "param": ("STRING", {"default": ""}),
                "value": ("STRING", {"default": ""}),
                "type": ("STRING", {"default": "STRING"}),
            }
        }

    RETURN_TYPES = ("REMOTEAPPLY",)
    RETURN_NAMES = ("remote_apply",)
    FUNCTION = "apply_values"
    CATEGORY = "remote/advanced"
    TITLE = "Apply Values to Remote Nodes"

    def apply_values(self, nodeid, param, value, type):
        nodeids = [id.strip() for id in nodeid.split(",")]
        params = [p.strip() for p in param.split(",")]
        values = [v.strip() for v in value.split(",")]
        types = type.split(",")  # Split the types string into a list

        # If only one type is provided, apply it to all values
        if len(types) == 1:
            types = types * len(nodeids)
        else:
            types = [t.strip() for t in types]  # Strip whitespace from each type

        if len(nodeids) != len(params) or len(nodeids) != len(values) or len(nodeids) != len(types):
            raise ValueError("Number of nodeids, params, values, and types must be equal")

        remote_values = tuple(zip(nodeids, params, values, types))
        return (remote_values,)

class RemoteChainStartNux:
	"""Merge required attributes into one [REMCHAIN]"""
	def __init__(self):
		pass
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"workflow": ("JSON",),
				"trigger": (["on_change", "always"],),
				"batch": ("INT", {"default": 1, "min": 1, "max": 8}),
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
            }
		}

	RETURN_TYPES = ("REMCHAIN",)
	RETURN_NAMES = ("remote_chain",)
	FUNCTION = "chain_start"
	CATEGORY = "remote/advanced"
	TITLE = "Queue on remote (start of chain)"

	def chain_start(self, workflow, trigger, batch, seed,
		remoteapply1=None, remoteapply2=None, remoteapply3=None, remoteapply4=None,
		remoteapply5=None, remoteapply6=None, remoteapply7=None, remoteapply8=None,
		remoteapply9=None, remoteapply10=None):

		# Make a deep copy of the workflow to avoid retaining state between calls
		workflow = copy.deepcopy(workflow)

		remote_params = {}
		for remoteapply in [remoteapply1, remoteapply2, remoteapply3, remoteapply4,
							remoteapply5, remoteapply6, remoteapply7, remoteapply8,
							remoteapply9, remoteapply10]:
			print("**"+str(remoteapply6)+str(type(remoteapply6))+"**")
			if remoteapply:
				if isinstance(remoteapply[0], tuple):  # Check if it's a tuple of tuples (multi)
					for nodeid, param, value, value_type in remoteapply:
						if param and value:
							
							remote_params[(nodeid, param)] = self.parse_value(value, value_type)
				else:  # Single tuple
					nodeid, param, value, value_type = remoteapply
					if param and value:
						remote_params[(nodeid, param)] = self.parse_value(value, value_type)

		remote_params[("", "seed")] = self.parse_value(seed, "INT")  # Add seed to remote_params

		# Apply remote parameters to the prompt
		for (nodeid, param), value in remote_params.items():
			truncated_value = str(value)[:30] + '...' if len(str(value)) > 30 else str(value)  # Truncate value for display
			print(f"Applying param: {param}, value: {truncated_value}, nodeid: {nodeid}")  # Debug statement
			if nodeid:
				if nodeid in workflow:
					if param in workflow[nodeid].get("inputs", {}):
						workflow[nodeid]["inputs"][param] = value
						print(f"Updated node {nodeid} param {param} with value {truncated_value}")  # Debug statement
					else:
						print(f"Param {param} not found in node {nodeid} inputs")  # Debug statement
				else:
					print(f"Node {nodeid} not found in workflow")  # Debug statement
			else:
				for node_key, node_data in workflow.items():
					if param in node_data.get("inputs", {}):
						workflow[node_key]["inputs"][param] = value
						print(f"Updated node {node_key} param {param} with value {truncated_value}")  # Debug statement
						break
					else:
						print(f"Param {param} not found in node {node_key} inputs")  # Debug statement

		remote_chain = {
			"seed": seed,
			"batch": batch,
			"prompt": workflow,
			"seed_offset": batch,
			"job_id": get_new_job_id(),
		}
		return(remote_chain,)

	@classmethod
	def IS_CHANGED(self, workflow, trigger, batch, seed, prompt):
		uuid = f"W:{workflow},B:{batch},S:{seed}"
		return uuid if trigger == "on_change" else str(time.time())

	def parse_value(self, value, value_type):
		"""Parse the value string to the specified type."""
		if value_type == "INT":
			return int(value)
		elif value_type == "FLOAT":
			return float(value)
		elif value_type == "BOOL":
			return value.lower() == "true"
		else:  # STRING or any other type
			return value.replace("\\", "\\\\")

class RemoteChainStart:
	"""Merge required attributes into one [REMCHAIN]"""
	def __init__(self):
		pass
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"workflow": ("JSON",),
				"trigger": (["on_change", "always"],),
				"batch": ("INT", {"default": 1, "min": 1, "max": 8}),
				"seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
			},
            "optional": {
				"remote_nodeid1": ("STRING", {"default": ""}),
                "remote_param1": ("STRING", {"default": ""}),
                "remote_value1": ("STRING", {"default": ""}),
                "remote_type1": (["STRING", "INT", "FLOAT", "BOOL"], {"default": "STRING"}),
				"remote_nodeid2": ("STRING", {"default": ""}),
                "remote_param2": ("STRING", {"default": ""}),
                "remote_value2": ("STRING", {"default": ""}),
                "remote_type2": (["STRING", "INT", "FLOAT", "BOOL"], {"default": "STRING"}),
				"remote_nodeid3": ("STRING", {"default": ""}),
                "remote_param3": ("STRING", {"default": ""}),
                "remote_value3": ("STRING", {"default": ""}),
                "remote_type3": (["STRING", "INT", "FLOAT", "BOOL"], {"default": "STRING"}),
				"remote_nodeid4": ("STRING", {"default": ""}),
                "remote_param4": ("STRING", {"default": ""}),
                "remote_value4": ("STRING", {"default": ""}),
                "remote_type4": (["STRING", "INT", "FLOAT", "BOOL"], {"default": "STRING"}),
            }
		}

	RETURN_TYPES = ("REMCHAIN",)
	RETURN_NAMES = ("remote_chain",)
	FUNCTION = "chain_start"
	CATEGORY = "remote/advanced"
	TITLE = "Queue on remote (start of chain)"

	def chain_start(self, workflow, trigger, batch, seed,
		remote_nodeid1="", remote_param1="", remote_value1="", remote_type1="STRING",
		remote_nodeid2="", remote_param2="", remote_value2="", remote_type2="STRING",
		remote_nodeid3="", remote_param3="", remote_value3="", remote_type3="STRING", 
		remote_nodeid4="", remote_param4="", remote_value4="", remote_type4="STRING"):

		# Make a deep copy of the workflow to avoid retaining state between calls
		workflow = copy.deepcopy(workflow)

		remote_params = {}
		for nodeid, param, value, value_type in [
			(remote_nodeid1, remote_param1, remote_value1, remote_type1),
			(remote_nodeid2, remote_param2, remote_value2, remote_type2),
			(remote_nodeid3, remote_param3, remote_value3, remote_type3),
			(remote_nodeid4, remote_param4, remote_value4, remote_type4),
			("", "seed", seed, "INT")
		]:
			if param and value:
				remote_params[(nodeid, param)] = self.parse_value(value, value_type)
		
		# Apply remote parameters to the prompt
		for (nodeid, param), value in remote_params.items():
			truncated_value = str(value)[:30] + '...' if len(str(value)) > 30 else str(value)  # Truncate value for display
			print(f"Applying param: {param}, value: {truncated_value}, nodeid: {nodeid}")  # Debug statement
			if nodeid:
				if nodeid in workflow:
					if param in workflow[nodeid].get("inputs", {}):
						workflow[nodeid]["inputs"][param] = value
						print(f"Updated node {nodeid} param {param} with value {truncated_value}")  # Debug statement
					else:
						print(f"Param {param} not found in node {nodeid} inputs")  # Debug statement
				else:
					print(f"Node {nodeid} not found in workflow")  # Debug statement
			else:
				for node_key, node_data in workflow.items():
					if param in node_data.get("inputs", {}):
						workflow[node_key]["inputs"][param] = value
						print(f"Updated node {node_key} param {param} with value {truncated_value}")  # Debug statement
						break
					else:
						print(f"Param {param} not found in node {node_key} inputs")  # Debug statement

		remote_chain = {
			"seed": seed,
			"batch": batch,
			"prompt": workflow,
			"seed_offset": batch,
			"job_id": get_new_job_id(),
		}
		return(remote_chain,)

	@classmethod
	def IS_CHANGED(self, workflow, trigger, batch, seed, prompt):
		uuid = f"W:{workflow},B:{batch},S:{seed}"
		return uuid if trigger == "on_change" else str(time.time())

	def parse_value(self, value, value_type):
		"""Parse the value string to the specified type."""
		if value_type == "INT":
			return int(value)
		elif value_type == "FLOAT":
			return float(value)
		elif value_type == "BOOL":
			return value.lower() == "true"
		else:  # STRING or any other type
			return value.replace("\\", "\\\\")

class RemoteChainEnd:
	"""Split [REMCHAIN] into local seed/batch"""
	def __init__(self):
		pass
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"remote_chain": ("REMCHAIN",)
			}
		}

	RETURN_TYPES = ("INT", "INT")
	RETURN_NAMES = ("seed", "batch")
	FUNCTION = "chain_end"
	CATEGORY = "remote/advanced"
	TITLE = "Queue on remote (end of chain)"

	def chain_end(self, remote_chain):
		seed = remote_chain["seed"]
		batch = remote_chain["batch"]
		return(seed,batch)

class RemoteQueueWorker:
    """Start job on remote worker"""
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "remote_chain": ("REMCHAIN",),
                "remote_url": ("STRING", {
                    "multiline": False,
                    "default": "http://127.0.0.1:8288/",
                }),
                "batch_override": ("INT", {"default": 0, "min": 0, "max": 8}),
                "enabled": (["true", "false", "remote"],{"default": "true"}),
                "outputs": (["final_image", "any"],{"default":"final_image"}),
            },
        }

    RETURN_TYPES = ("REMCHAIN", "REMINFO")
    RETURN_NAMES = ("remote_chain", "remote_info")
    FUNCTION = "queue"
    CATEGORY = "remote/advanced"
    TITLE = "Queue on remote (worker)"

    def queue(self, remote_chain, remote_url, batch_override, enabled, outputs,
	):
        current_offset = remote_chain["seed_offset"]
        remote_chain["seed_offset"] += 1 if batch_override == 0 else batch_override
        if enabled == "false":
            return (remote_chain, {})
        if enabled == "remote":
            # apply offset from previous nodes in chain
            remote_chain["seed"] += current_offset
            if batch_override > 0:
                remote_chain["batch"] = batch_override
            return (remote_chain, {})

        remote_url = clean_url(remote_url)
        clear_remote_queue(remote_url)
        
        # Prepare remote parameters
        remote_params = {}

        dispatch_to_remote(
            remote_url,
            remote_chain["prompt"],
            remote_chain["job_id"],
            remote_params,
            outputs,
        )
        remote_info = {
            "remote_url" : remote_url,
            "job_id"     : remote_chain["job_id"],
        }
        return (remote_chain, remote_info)

NODE_CLASS_MAPPINGS = {
	"RemoteApplyValues(Nux)": RemoteApplyValues, 
	"RemoteChainStart(Nux)": RemoteChainStartNux,
	"RemoteChainStart"  : RemoteChainStart,
	"RemoteQueueWorker" : RemoteQueueWorker,
	"RemoteChainEnd"    : RemoteChainEnd,
	"RemoteApplyValuesMulti(Nux)": RemoteApplyValuesMulti,
}
