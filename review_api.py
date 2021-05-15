"""
Model-data interface for the Review model.
"""

import json

import model_api_ABC
import review

# todo seems better to name them "ModelnameModelInterface" not "...API..."

class ReviewAPI (model_api_ABC.ModelAPI):

    def __init__(self, json_map_filename=None):
        self._model = "review"
        if json_map_filename:
            super().__init__(json_map_filename)
        else:
            super().__init__()
        self._valid_model_fields = ["datespot_id", "text"]
    
    def create_review(self, json_str: str) -> str:
        self._read_json()
        json_dict = json.loads(json_str)

        self._validate_json_fields(json_dict) # Validate fields

        new_obj = review.Review( # Instantiate a model object
            datespot_id = json_dict["datespot_id"],
            text = json_dict["text"]
        )
        new_obj_id = new_obj.id # Get object's id hash string
        self._data[new_obj_id] = new_obj.serialize() # Save with that id as the key
        self._write_json()
        return new_obj_id
            