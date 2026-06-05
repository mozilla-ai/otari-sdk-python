# otari_control_plane.KeysApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_key_v1_keys_post**](KeysApi.md#create_key_v1_keys_post) | **POST** /v1/keys | Create Key
[**delete_key_v1_keys_key_id_delete**](KeysApi.md#delete_key_v1_keys_key_id_delete) | **DELETE** /v1/keys/{key_id} | Delete Key
[**get_key_v1_keys_key_id_get**](KeysApi.md#get_key_v1_keys_key_id_get) | **GET** /v1/keys/{key_id} | Get Key
[**list_keys_v1_keys_get**](KeysApi.md#list_keys_v1_keys_get) | **GET** /v1/keys | List Keys
[**update_key_v1_keys_key_id_patch**](KeysApi.md#update_key_v1_keys_key_id_patch) | **PATCH** /v1/keys/{key_id} | Update Key


# **create_key_v1_keys_post**
> CreateKeyResponse create_key_v1_keys_post(create_key_request)

Create Key

Create a new API key.

Requires master key authentication.

If user_id is provided, the key will be associated with that user (creates user if it doesn't exist).
If user_id is not provided, a new user will be created automatically and the key will be associated with it.

### Example


```python
import otari_control_plane
from otari_control_plane.models.create_key_request import CreateKeyRequest
from otari_control_plane.models.create_key_response import CreateKeyResponse
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
    api_instance = otari_control_plane.KeysApi(api_client)
    create_key_request = otari_control_plane.CreateKeyRequest() # CreateKeyRequest | 

    try:
        # Create Key
        api_response = api_instance.create_key_v1_keys_post(create_key_request)
        print("The response of KeysApi->create_key_v1_keys_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling KeysApi->create_key_v1_keys_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_key_request** | [**CreateKeyRequest**](CreateKeyRequest.md)|  | 

### Return type

[**CreateKeyResponse**](CreateKeyResponse.md)

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

# **delete_key_v1_keys_key_id_delete**
> delete_key_v1_keys_key_id_delete(key_id)

Delete Key

Delete (revoke) an API key.

Requires master key authentication.

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
    api_instance = otari_control_plane.KeysApi(api_client)
    key_id = 'key_id_example' # str | 

    try:
        # Delete Key
        api_instance.delete_key_v1_keys_key_id_delete(key_id)
    except Exception as e:
        print("Exception when calling KeysApi->delete_key_v1_keys_key_id_delete: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **key_id** | **str**|  | 

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

# **get_key_v1_keys_key_id_get**
> KeyInfo get_key_v1_keys_key_id_get(key_id)

Get Key

Get details of a specific API key.

Requires master key authentication.

### Example


```python
import otari_control_plane
from otari_control_plane.models.key_info import KeyInfo
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
    api_instance = otari_control_plane.KeysApi(api_client)
    key_id = 'key_id_example' # str | 

    try:
        # Get Key
        api_response = api_instance.get_key_v1_keys_key_id_get(key_id)
        print("The response of KeysApi->get_key_v1_keys_key_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling KeysApi->get_key_v1_keys_key_id_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **key_id** | **str**|  | 

### Return type

[**KeyInfo**](KeyInfo.md)

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

# **list_keys_v1_keys_get**
> List[KeyInfo] list_keys_v1_keys_get(skip=skip, limit=limit)

List Keys

List all API keys.

Requires master key authentication.

### Example


```python
import otari_control_plane
from otari_control_plane.models.key_info import KeyInfo
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
    api_instance = otari_control_plane.KeysApi(api_client)
    skip = 0 # int |  (optional) (default to 0)
    limit = 100 # int |  (optional) (default to 100)

    try:
        # List Keys
        api_response = api_instance.list_keys_v1_keys_get(skip=skip, limit=limit)
        print("The response of KeysApi->list_keys_v1_keys_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling KeysApi->list_keys_v1_keys_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **skip** | **int**|  | [optional] [default to 0]
 **limit** | **int**|  | [optional] [default to 100]

### Return type

[**List[KeyInfo]**](KeyInfo.md)

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

# **update_key_v1_keys_key_id_patch**
> KeyInfo update_key_v1_keys_key_id_patch(key_id, update_key_request)

Update Key

Update an API key.

Requires master key authentication.

### Example


```python
import otari_control_plane
from otari_control_plane.models.key_info import KeyInfo
from otari_control_plane.models.update_key_request import UpdateKeyRequest
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
    api_instance = otari_control_plane.KeysApi(api_client)
    key_id = 'key_id_example' # str | 
    update_key_request = otari_control_plane.UpdateKeyRequest() # UpdateKeyRequest | 

    try:
        # Update Key
        api_response = api_instance.update_key_v1_keys_key_id_patch(key_id, update_key_request)
        print("The response of KeysApi->update_key_v1_keys_key_id_patch:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling KeysApi->update_key_v1_keys_key_id_patch: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **key_id** | **str**|  | 
 **update_key_request** | [**UpdateKeyRequest**](UpdateKeyRequest.md)|  | 

### Return type

[**KeyInfo**](KeyInfo.md)

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

