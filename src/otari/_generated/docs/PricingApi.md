# otari_control_plane.PricingApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**delete_pricing_v1_pricing_model_key_delete**](PricingApi.md#delete_pricing_v1_pricing_model_key_delete) | **DELETE** /v1/pricing/{model_key} | Delete Pricing
[**get_pricing_history_v1_pricing_model_key_history_get**](PricingApi.md#get_pricing_history_v1_pricing_model_key_history_get) | **GET** /v1/pricing/{model_key}/history | Get Pricing History
[**get_pricing_v1_pricing_model_key_get**](PricingApi.md#get_pricing_v1_pricing_model_key_get) | **GET** /v1/pricing/{model_key} | Get Pricing
[**list_pricing_v1_pricing_get**](PricingApi.md#list_pricing_v1_pricing_get) | **GET** /v1/pricing | List Pricing
[**set_pricing_v1_pricing_post**](PricingApi.md#set_pricing_v1_pricing_post) | **POST** /v1/pricing | Set Pricing


# **delete_pricing_v1_pricing_model_key_delete**
> delete_pricing_v1_pricing_model_key_delete(model_key, effective_at=effective_at)

Delete Pricing

Delete pricing entries for a model.

### Example


```python
import otari_control_plane
from otari_control_plane.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = otari_control_plane.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with otari_control_plane.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = otari_control_plane.PricingApi(api_client)
    model_key = 'model_key_example' # str | 
    effective_at = '2013-10-20T19:20:30+01:00' # datetime | ISO datetime identifying a specific pricing row to delete (optional)

    try:
        # Delete Pricing
        api_instance.delete_pricing_v1_pricing_model_key_delete(model_key, effective_at=effective_at)
    except Exception as e:
        print("Exception when calling PricingApi->delete_pricing_v1_pricing_model_key_delete: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_key** | **str**|  | 
 **effective_at** | **datetime**| ISO datetime identifying a specific pricing row to delete | [optional] 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_pricing_history_v1_pricing_model_key_history_get**
> List[PricingResponse] get_pricing_history_v1_pricing_model_key_history_get(model_key)

Get Pricing History

Return the full pricing history for a model.

### Example


```python
import otari_control_plane
from otari_control_plane.models.pricing_response import PricingResponse
from otari_control_plane.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = otari_control_plane.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with otari_control_plane.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = otari_control_plane.PricingApi(api_client)
    model_key = 'model_key_example' # str | 

    try:
        # Get Pricing History
        api_response = api_instance.get_pricing_history_v1_pricing_model_key_history_get(model_key)
        print("The response of PricingApi->get_pricing_history_v1_pricing_model_key_history_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PricingApi->get_pricing_history_v1_pricing_model_key_history_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_key** | **str**|  | 

### Return type

[**List[PricingResponse]**](PricingResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_pricing_v1_pricing_model_key_get**
> PricingResponse get_pricing_v1_pricing_model_key_get(model_key, as_of=as_of)

Get Pricing

Get pricing for a specific model as of a timestamp.

### Example


```python
import otari_control_plane
from otari_control_plane.models.pricing_response import PricingResponse
from otari_control_plane.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = otari_control_plane.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with otari_control_plane.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = otari_control_plane.PricingApi(api_client)
    model_key = 'model_key_example' # str | 
    as_of = '2013-10-20T19:20:30+01:00' # datetime | ISO datetime for effective lookup (optional)

    try:
        # Get Pricing
        api_response = api_instance.get_pricing_v1_pricing_model_key_get(model_key, as_of=as_of)
        print("The response of PricingApi->get_pricing_v1_pricing_model_key_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PricingApi->get_pricing_v1_pricing_model_key_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_key** | **str**|  | 
 **as_of** | **datetime**| ISO datetime for effective lookup | [optional] 

### Return type

[**PricingResponse**](PricingResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_pricing_v1_pricing_get**
> List[PricingResponse] list_pricing_v1_pricing_get(skip=skip, limit=limit)

List Pricing

List all model pricing.

### Example


```python
import otari_control_plane
from otari_control_plane.models.pricing_response import PricingResponse
from otari_control_plane.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = otari_control_plane.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with otari_control_plane.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = otari_control_plane.PricingApi(api_client)
    skip = 0 # int |  (optional) (default to 0)
    limit = 100 # int |  (optional) (default to 100)

    try:
        # List Pricing
        api_response = api_instance.list_pricing_v1_pricing_get(skip=skip, limit=limit)
        print("The response of PricingApi->list_pricing_v1_pricing_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PricingApi->list_pricing_v1_pricing_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **skip** | **int**|  | [optional] [default to 0]
 **limit** | **int**|  | [optional] [default to 100]

### Return type

[**List[PricingResponse]**](PricingResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_pricing_v1_pricing_post**
> PricingResponse set_pricing_v1_pricing_post(set_pricing_request)

Set Pricing

Set or update pricing for a model.

### Example


```python
import otari_control_plane
from otari_control_plane.models.pricing_response import PricingResponse
from otari_control_plane.models.set_pricing_request import SetPricingRequest
from otari_control_plane.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = otari_control_plane.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with otari_control_plane.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = otari_control_plane.PricingApi(api_client)
    set_pricing_request = otari_control_plane.SetPricingRequest() # SetPricingRequest | 

    try:
        # Set Pricing
        api_response = api_instance.set_pricing_v1_pricing_post(set_pricing_request)
        print("The response of PricingApi->set_pricing_v1_pricing_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PricingApi->set_pricing_v1_pricing_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **set_pricing_request** | [**SetPricingRequest**](SetPricingRequest.md)|  | 

### Return type

[**PricingResponse**](PricingResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

