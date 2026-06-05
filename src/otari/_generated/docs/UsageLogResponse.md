# UsageLogResponse

Response model for usage log.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**api_key_id** | **str** |  | 
**completion_tokens** | **int** |  | 
**cost** | **float** |  | 
**endpoint** | **str** |  | 
**error_message** | **str** |  | 
**id** | **str** |  | 
**model** | **str** |  | 
**prompt_tokens** | **int** |  | 
**provider** | **str** |  | 
**status** | **str** |  | 
**timestamp** | **str** |  | 
**total_tokens** | **int** |  | 
**user_id** | **str** |  | 

## Example

```python
from otari_control_plane.models.usage_log_response import UsageLogResponse

# TODO update the JSON string below
json = "{}"
# create an instance of UsageLogResponse from a JSON string
usage_log_response_instance = UsageLogResponse.from_json(json)
# print the JSON string representation of the object
print(UsageLogResponse.to_json())

# convert the object into a dict
usage_log_response_dict = usage_log_response_instance.to_dict()
# create an instance of UsageLogResponse from a dict
usage_log_response_from_dict = UsageLogResponse.from_dict(usage_log_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


