# SetPricingRequest

Request model for setting model pricing.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**effective_at** | **datetime** | ISO 8601 datetime from which this price applies. Defaults to now if omitted. | [optional] 
**input_price_per_million** | **float** | Price per 1M input tokens | 
**model_key** | **str** | Model identifier in format &#39;provider:model&#39; | 
**output_price_per_million** | **float** | Price per 1M output tokens | 

## Example

```python
from otari_control_plane.models.set_pricing_request import SetPricingRequest

# TODO update the JSON string below
json = "{}"
# create an instance of SetPricingRequest from a JSON string
set_pricing_request_instance = SetPricingRequest.from_json(json)
# print the JSON string representation of the object
print(SetPricingRequest.to_json())

# convert the object into a dict
set_pricing_request_dict = set_pricing_request_instance.to_dict()
# create an instance of SetPricingRequest from a dict
set_pricing_request_from_dict = SetPricingRequest.from_dict(set_pricing_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


