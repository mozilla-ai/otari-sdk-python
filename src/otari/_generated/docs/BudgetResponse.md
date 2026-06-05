# BudgetResponse

Response model for budget information.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**budget_duration_sec** | **int** |  | 
**budget_id** | **str** |  | 
**created_at** | **str** |  | 
**max_budget** | **float** |  | 
**updated_at** | **str** |  | 

## Example

```python
from otari_control_plane.models.budget_response import BudgetResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BudgetResponse from a JSON string
budget_response_instance = BudgetResponse.from_json(json)
# print the JSON string representation of the object
print(BudgetResponse.to_json())

# convert the object into a dict
budget_response_dict = budget_response_instance.to_dict()
# create an instance of BudgetResponse from a dict
budget_response_from_dict = BudgetResponse.from_dict(budget_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


