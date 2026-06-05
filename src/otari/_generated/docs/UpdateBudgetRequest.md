# UpdateBudgetRequest

Request model for updating a budget.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**budget_duration_sec** | **int** |  | [optional] 
**max_budget** | **float** |  | [optional] 

## Example

```python
from otari_control_plane.models.update_budget_request import UpdateBudgetRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateBudgetRequest from a JSON string
update_budget_request_instance = UpdateBudgetRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateBudgetRequest.to_json())

# convert the object into a dict
update_budget_request_dict = update_budget_request_instance.to_dict()
# create an instance of UpdateBudgetRequest from a dict
update_budget_request_from_dict = UpdateBudgetRequest.from_dict(update_budget_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


