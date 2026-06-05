# CreateUserRequest

Request model for creating a new user.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**alias** | **str** | Optional admin-facing alias | [optional] 
**blocked** | **bool** | Whether user is blocked | [optional] [default to False]
**budget_id** | **str** | Optional budget ID | [optional] 
**metadata** | **Dict[str, object]** | Optional metadata | [optional] 
**user_id** | **str** | Unique user identifier | 

## Example

```python
from otari_control_plane.models.create_user_request import CreateUserRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateUserRequest from a JSON string
create_user_request_instance = CreateUserRequest.from_json(json)
# print the JSON string representation of the object
print(CreateUserRequest.to_json())

# convert the object into a dict
create_user_request_dict = create_user_request_instance.to_dict()
# create an instance of CreateUserRequest from a dict
create_user_request_from_dict = CreateUserRequest.from_dict(create_user_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


