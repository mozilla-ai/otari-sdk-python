# CreateBudgetRequest

Request model for creating a new budget.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**budget_duration_sec** | **int** | Budget duration in seconds (e.g., 86400 for daily, 604800 for weekly) | [optional] 
**max_budget** | **float** | Maximum spending limit | [optional] 

## Example

```python
from otari_control_plane.models.create_budget_request import CreateBudgetRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateBudgetRequest from a JSON string
create_budget_request_instance = CreateBudgetRequest.from_json(json)
# print the JSON string representation of the object
print(CreateBudgetRequest.to_json())

# convert the object into a dict
create_budget_request_dict = create_budget_request_instance.to_dict()
# create an instance of CreateBudgetRequest from a dict
create_budget_request_from_dict = CreateBudgetRequest.from_dict(create_budget_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


