# otari_control_plane.UsersApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_user_v1_users_post**](UsersApi.md#create_user_v1_users_post) | **POST** /v1/users | Create User
[**delete_user_v1_users_user_id_delete**](UsersApi.md#delete_user_v1_users_user_id_delete) | **DELETE** /v1/users/{user_id} | Delete User
[**get_user_usage_v1_users_user_id_usage_get**](UsersApi.md#get_user_usage_v1_users_user_id_usage_get) | **GET** /v1/users/{user_id}/usage | Get User Usage
[**get_user_v1_users_user_id_get**](UsersApi.md#get_user_v1_users_user_id_get) | **GET** /v1/users/{user_id} | Get User
[**list_users_v1_users_get**](UsersApi.md#list_users_v1_users_get) | **GET** /v1/users | List Users
[**update_user_v1_users_user_id_patch**](UsersApi.md#update_user_v1_users_user_id_patch) | **PATCH** /v1/users/{user_id} | Update User


# **create_user_v1_users_post**
> UserResponse create_user_v1_users_post(create_user_request)

Create User

Create a new user.

### Example


```python
import otari_control_plane
from otari_control_plane.models.create_user_request import CreateUserRequest
from otari_control_plane.models.user_response import UserResponse
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
    api_instance = otari_control_plane.UsersApi(api_client)
    create_user_request = otari_control_plane.CreateUserRequest() # CreateUserRequest | 

    try:
        # Create User
        api_response = api_instance.create_user_v1_users_post(create_user_request)
        print("The response of UsersApi->create_user_v1_users_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UsersApi->create_user_v1_users_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_user_request** | [**CreateUserRequest**](CreateUserRequest.md)|  | 

### Return type

[**UserResponse**](UserResponse.md)

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

# **delete_user_v1_users_user_id_delete**
> delete_user_v1_users_user_id_delete(user_id)

Delete User

Delete a user.

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
    api_instance = otari_control_plane.UsersApi(api_client)
    user_id = 'user_id_example' # str | 

    try:
        # Delete User
        api_instance.delete_user_v1_users_user_id_delete(user_id)
    except Exception as e:
        print("Exception when calling UsersApi->delete_user_v1_users_user_id_delete: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_id** | **str**|  | 

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

# **get_user_usage_v1_users_user_id_usage_get**
> List[UsageLogResponse] get_user_usage_v1_users_user_id_usage_get(user_id, skip=skip, limit=limit)

Get User Usage

Get usage history for a specific user.

### Example


```python
import otari_control_plane
from otari_control_plane.models.usage_log_response import UsageLogResponse
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
    api_instance = otari_control_plane.UsersApi(api_client)
    user_id = 'user_id_example' # str | 
    skip = 0 # int |  (optional) (default to 0)
    limit = 100 # int |  (optional) (default to 100)

    try:
        # Get User Usage
        api_response = api_instance.get_user_usage_v1_users_user_id_usage_get(user_id, skip=skip, limit=limit)
        print("The response of UsersApi->get_user_usage_v1_users_user_id_usage_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UsersApi->get_user_usage_v1_users_user_id_usage_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_id** | **str**|  | 
 **skip** | **int**|  | [optional] [default to 0]
 **limit** | **int**|  | [optional] [default to 100]

### Return type

[**List[UsageLogResponse]**](UsageLogResponse.md)

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

# **get_user_v1_users_user_id_get**
> UserResponse get_user_v1_users_user_id_get(user_id)

Get User

Get details of a specific user.

### Example


```python
import otari_control_plane
from otari_control_plane.models.user_response import UserResponse
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
    api_instance = otari_control_plane.UsersApi(api_client)
    user_id = 'user_id_example' # str | 

    try:
        # Get User
        api_response = api_instance.get_user_v1_users_user_id_get(user_id)
        print("The response of UsersApi->get_user_v1_users_user_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UsersApi->get_user_v1_users_user_id_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_id** | **str**|  | 

### Return type

[**UserResponse**](UserResponse.md)

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

# **list_users_v1_users_get**
> List[UserResponse] list_users_v1_users_get(skip=skip, limit=limit)

List Users

List all users with pagination.

### Example


```python
import otari_control_plane
from otari_control_plane.models.user_response import UserResponse
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
    api_instance = otari_control_plane.UsersApi(api_client)
    skip = 0 # int |  (optional) (default to 0)
    limit = 100 # int |  (optional) (default to 100)

    try:
        # List Users
        api_response = api_instance.list_users_v1_users_get(skip=skip, limit=limit)
        print("The response of UsersApi->list_users_v1_users_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UsersApi->list_users_v1_users_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **skip** | **int**|  | [optional] [default to 0]
 **limit** | **int**|  | [optional] [default to 100]

### Return type

[**List[UserResponse]**](UserResponse.md)

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

# **update_user_v1_users_user_id_patch**
> UserResponse update_user_v1_users_user_id_patch(user_id, update_user_request)

Update User

Update a user.

### Example


```python
import otari_control_plane
from otari_control_plane.models.update_user_request import UpdateUserRequest
from otari_control_plane.models.user_response import UserResponse
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
    api_instance = otari_control_plane.UsersApi(api_client)
    user_id = 'user_id_example' # str | 
    update_user_request = otari_control_plane.UpdateUserRequest() # UpdateUserRequest | 

    try:
        # Update User
        api_response = api_instance.update_user_v1_users_user_id_patch(user_id, update_user_request)
        print("The response of UsersApi->update_user_v1_users_user_id_patch:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UsersApi->update_user_v1_users_user_id_patch: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_id** | **str**|  | 
 **update_user_request** | [**UpdateUserRequest**](UpdateUserRequest.md)|  | 

### Return type

[**UserResponse**](UserResponse.md)

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

