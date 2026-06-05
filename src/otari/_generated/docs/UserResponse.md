# UserResponse

Response model for user information.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**alias** | **str** |  | 
**blocked** | **bool** |  | 
**budget_id** | **str** |  | 
**budget_started_at** | **str** |  | 
**created_at** | **str** |  | 
**metadata** | **Dict[str, object]** |  | 
**next_budget_reset_at** | **str** |  | 
**reserved** | **float** |  | 
**spend** | **float** |  | 
**updated_at** | **str** |  | 
**user_id** | **str** |  | 

## Example

```python
from otari_control_plane.models.user_response import UserResponse

# TODO update the JSON string below
json = "{}"
# create an instance of UserResponse from a JSON string
user_response_instance = UserResponse.from_json(json)
# print the JSON string representation of the object
print(UserResponse.to_json())

# convert the object into a dict
user_response_dict = user_response_instance.to_dict()
# create an instance of UserResponse from a dict
user_response_from_dict = UserResponse.from_dict(user_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


