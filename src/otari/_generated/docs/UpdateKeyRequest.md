# UpdateKeyRequest

Request model for updating a key.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**expires_at** | **datetime** |  | [optional] 
**is_active** | **bool** |  | [optional] 
**key_name** | **str** |  | [optional] 
**metadata** | **Dict[str, object]** |  | [optional] 

## Example

```python
from otari_control_plane.models.update_key_request import UpdateKeyRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateKeyRequest from a JSON string
update_key_request_instance = UpdateKeyRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateKeyRequest.to_json())

# convert the object into a dict
update_key_request_dict = update_key_request_instance.to_dict()
# create an instance of UpdateKeyRequest from a dict
update_key_request_from_dict = UpdateKeyRequest.from_dict(update_key_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


