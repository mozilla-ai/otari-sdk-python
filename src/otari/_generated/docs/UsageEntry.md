# UsageEntry

A single usage log entry.

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
from otari_control_plane.models.usage_entry import UsageEntry

# TODO update the JSON string below
json = "{}"
# create an instance of UsageEntry from a JSON string
usage_entry_instance = UsageEntry.from_json(json)
# print the JSON string representation of the object
print(UsageEntry.to_json())

# convert the object into a dict
usage_entry_dict = usage_entry_instance.to_dict()
# create an instance of UsageEntry from a dict
usage_entry_from_dict = UsageEntry.from_dict(usage_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


