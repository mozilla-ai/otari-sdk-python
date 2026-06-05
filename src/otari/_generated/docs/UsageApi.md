# otari_control_plane.UsageApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**list_usage_v1_usage_get**](UsageApi.md#list_usage_v1_usage_get) | **GET** /v1/usage | List Usage


# **list_usage_v1_usage_get**
> List[UsageEntry] list_usage_v1_usage_get(start_date=start_date, end_date=end_date, user_id=user_id, skip=skip, limit=limit)

List Usage

List usage logs ordered by timestamp (most recent first).

Supports optional filters for time range and user. Paginated via skip/limit.
Timestamps accept either ISO 8601 strings or Unix epoch seconds (numeric).

### Example


```python
import otari_control_plane
from otari_control_plane.models.usage_entry import UsageEntry
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
    api_instance = otari_control_plane.UsageApi(api_client)
    start_date = '2013-10-20T19:20:30+01:00' # datetime | Return logs with timestamp >= start_date (ISO 8601 or Unix epoch seconds) (optional)
    end_date = '2013-10-20T19:20:30+01:00' # datetime | Return logs with timestamp < end_date (ISO 8601 or Unix epoch seconds) (optional)
    user_id = 'user_id_example' # str | Filter to a single user (optional)
    skip = 0 # int |  (optional) (default to 0)
    limit = 100 # int |  (optional) (default to 100)

    try:
        # List Usage
        api_response = api_instance.list_usage_v1_usage_get(start_date=start_date, end_date=end_date, user_id=user_id, skip=skip, limit=limit)
        print("The response of UsageApi->list_usage_v1_usage_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UsageApi->list_usage_v1_usage_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **start_date** | **datetime**| Return logs with timestamp &gt;&#x3D; start_date (ISO 8601 or Unix epoch seconds) | [optional] 
 **end_date** | **datetime**| Return logs with timestamp &lt; end_date (ISO 8601 or Unix epoch seconds) | [optional] 
 **user_id** | **str**| Filter to a single user | [optional] 
 **skip** | **int**|  | [optional] [default to 0]
 **limit** | **int**|  | [optional] [default to 100]

### Return type

[**List[UsageEntry]**](UsageEntry.md)

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

