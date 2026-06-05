# KeyInfo

Response model for key information.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**created_at** | **str** |  | 
**expires_at** | **str** |  | 
**id** | **str** |  | 
**is_active** | **bool** |  | 
**key_name** | **str** |  | 
**last_used_at** | **str** |  | 
**metadata** | **Dict[str, object]** |  | 
**user_id** | **str** |  | 

## Example

```python
from otari_control_plane.models.key_info import KeyInfo

# TODO update the JSON string below
json = "{}"
# create an instance of KeyInfo from a JSON string
key_info_instance = KeyInfo.from_json(json)
# print the JSON string representation of the object
print(KeyInfo.to_json())

# convert the object into a dict
key_info_dict = key_info_instance.to_dict()
# create an instance of KeyInfo from a dict
key_info_from_dict = KeyInfo.from_dict(key_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


