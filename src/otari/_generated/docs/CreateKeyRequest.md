# CreateKeyRequest

Request model for creating a new API key.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**expires_at** | **datetime** | Optional expiration timestamp | [optional] 
**key_name** | **str** | Optional name for the key | [optional] 
**metadata** | **Dict[str, object]** | Optional metadata | [optional] 
**user_id** | **str** | Optional user ID to associate with this key | [optional] 

## Example

```python
from otari_control_plane.models.create_key_request import CreateKeyRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateKeyRequest from a JSON string
create_key_request_instance = CreateKeyRequest.from_json(json)
# print the JSON string representation of the object
print(CreateKeyRequest.to_json())

# convert the object into a dict
create_key_request_dict = create_key_request_instance.to_dict()
# create an instance of CreateKeyRequest from a dict
create_key_request_from_dict = CreateKeyRequest.from_dict(create_key_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


