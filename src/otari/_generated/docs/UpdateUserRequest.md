# UpdateUserRequest

Request model for updating a user.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**alias** | **str** |  | [optional] 
**blocked** | **bool** |  | [optional] 
**budget_id** | **str** |  | [optional] 
**metadata** | **Dict[str, object]** |  | [optional] 

## Example

```python
from otari_control_plane.models.update_user_request import UpdateUserRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateUserRequest from a JSON string
update_user_request_instance = UpdateUserRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateUserRequest.to_json())

# convert the object into a dict
update_user_request_dict = update_user_request_instance.to_dict()
# create an instance of UpdateUserRequest from a dict
update_user_request_from_dict = UpdateUserRequest.from_dict(update_user_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


