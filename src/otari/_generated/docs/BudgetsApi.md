# otari_control_plane.BudgetsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_budget_v1_budgets_post**](BudgetsApi.md#create_budget_v1_budgets_post) | **POST** /v1/budgets | Create Budget
[**delete_budget_v1_budgets_budget_id_delete**](BudgetsApi.md#delete_budget_v1_budgets_budget_id_delete) | **DELETE** /v1/budgets/{budget_id} | Delete Budget
[**get_budget_v1_budgets_budget_id_get**](BudgetsApi.md#get_budget_v1_budgets_budget_id_get) | **GET** /v1/budgets/{budget_id} | Get Budget
[**list_budgets_v1_budgets_get**](BudgetsApi.md#list_budgets_v1_budgets_get) | **GET** /v1/budgets | List Budgets
[**update_budget_v1_budgets_budget_id_patch**](BudgetsApi.md#update_budget_v1_budgets_budget_id_patch) | **PATCH** /v1/budgets/{budget_id} | Update Budget


# **create_budget_v1_budgets_post**
> BudgetResponse create_budget_v1_budgets_post(create_budget_request)

Create Budget

Create a new budget.

### Example


```python
import otari_control_plane
from otari_control_plane.models.budget_response import BudgetResponse
from otari_control_plane.models.create_budget_request import CreateBudgetRequest
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
    api_instance = otari_control_plane.BudgetsApi(api_client)
    create_budget_request = otari_control_plane.CreateBudgetRequest() # CreateBudgetRequest | 

    try:
        # Create Budget
        api_response = api_instance.create_budget_v1_budgets_post(create_budget_request)
        print("The response of BudgetsApi->create_budget_v1_budgets_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BudgetsApi->create_budget_v1_budgets_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_budget_request** | [**CreateBudgetRequest**](CreateBudgetRequest.md)|  | 

### Return type

[**BudgetResponse**](BudgetResponse.md)

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

# **delete_budget_v1_budgets_budget_id_delete**
> delete_budget_v1_budgets_budget_id_delete(budget_id)

Delete Budget

Delete a budget.

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
    api_instance = otari_control_plane.BudgetsApi(api_client)
    budget_id = 'budget_id_example' # str | 

    try:
        # Delete Budget
        api_instance.delete_budget_v1_budgets_budget_id_delete(budget_id)
    except Exception as e:
        print("Exception when calling BudgetsApi->delete_budget_v1_budgets_budget_id_delete: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **budget_id** | **str**|  | 

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

# **get_budget_v1_budgets_budget_id_get**
> BudgetResponse get_budget_v1_budgets_budget_id_get(budget_id)

Get Budget

Get details of a specific budget.

### Example


```python
import otari_control_plane
from otari_control_plane.models.budget_response import BudgetResponse
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
    api_instance = otari_control_plane.BudgetsApi(api_client)
    budget_id = 'budget_id_example' # str | 

    try:
        # Get Budget
        api_response = api_instance.get_budget_v1_budgets_budget_id_get(budget_id)
        print("The response of BudgetsApi->get_budget_v1_budgets_budget_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BudgetsApi->get_budget_v1_budgets_budget_id_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **budget_id** | **str**|  | 

### Return type

[**BudgetResponse**](BudgetResponse.md)

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

# **list_budgets_v1_budgets_get**
> List[BudgetResponse] list_budgets_v1_budgets_get(skip=skip, limit=limit)

List Budgets

List all budgets with pagination.

### Example


```python
import otari_control_plane
from otari_control_plane.models.budget_response import BudgetResponse
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
    api_instance = otari_control_plane.BudgetsApi(api_client)
    skip = 0 # int |  (optional) (default to 0)
    limit = 100 # int |  (optional) (default to 100)

    try:
        # List Budgets
        api_response = api_instance.list_budgets_v1_budgets_get(skip=skip, limit=limit)
        print("The response of BudgetsApi->list_budgets_v1_budgets_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BudgetsApi->list_budgets_v1_budgets_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **skip** | **int**|  | [optional] [default to 0]
 **limit** | **int**|  | [optional] [default to 100]

### Return type

[**List[BudgetResponse]**](BudgetResponse.md)

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

# **update_budget_v1_budgets_budget_id_patch**
> BudgetResponse update_budget_v1_budgets_budget_id_patch(budget_id, update_budget_request)

Update Budget

Update a budget.

### Example


```python
import otari_control_plane
from otari_control_plane.models.budget_response import BudgetResponse
from otari_control_plane.models.update_budget_request import UpdateBudgetRequest
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
    api_instance = otari_control_plane.BudgetsApi(api_client)
    budget_id = 'budget_id_example' # str | 
    update_budget_request = otari_control_plane.UpdateBudgetRequest() # UpdateBudgetRequest | 

    try:
        # Update Budget
        api_response = api_instance.update_budget_v1_budgets_budget_id_patch(budget_id, update_budget_request)
        print("The response of BudgetsApi->update_budget_v1_budgets_budget_id_patch:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BudgetsApi->update_budget_v1_budgets_budget_id_patch: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **budget_id** | **str**|  | 
 **update_budget_request** | [**UpdateBudgetRequest**](UpdateBudgetRequest.md)|  | 

### Return type

[**BudgetResponse**](BudgetResponse.md)

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

