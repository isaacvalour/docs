#!/usr/bin/env python3
"""
Script to regenerate all API documentation from the OpenAPI specification
"""

import json
import os
import re
from pathlib import Path

def load_openapi_spec():
    """Load the OpenAPI specification"""
    with open('api-reference/openapi.json', 'r') as f:
        return json.load(f)

def clean_filename(path, method):
    """Convert API path to clean filename"""
    # Remove leading slash and replace slashes with hyphens
    clean_path = path.lstrip('/').replace('/', '-')
    # Add method prefix
    filename = f"{method.lower()}-{clean_path}.mdx"
    return filename

def generate_mdx_content(path, method, operation):
    """Generate MDX content for an API endpoint"""
    title = operation.get('summary', f"{method.upper()} {path}")
    description = operation.get('description', f"API endpoint: {method.upper()} {path}")
    
    # Extract parameters
    parameters = operation.get('parameters', [])
    request_body = operation.get('requestBody', {})
    
    # Generate request fields
    request_fields = ""
    if request_body and 'content' in request_body:
        content = request_body['content']
        if 'application/json' in content:
            schema = content['application/json'].get('schema', {})
            if '$ref' in schema:
                # Extract schema name from reference
                schema_name = schema['$ref'].split('/')[-1]
                request_fields = f"<ParamField body=\"data\" type=\"object\" required>\n  Request body data ({schema_name})\n</ParamField>\n\n"
            else:
                request_fields = f"<ParamField body=\"data\" type=\"object\" required>\n  Request body data\n</ParamField>\n\n"
    
    # Add path parameters
    for param in parameters:
        if param.get('in') == 'path':
            param_name = param.get('name', '')
            param_type = param.get('schema', {}).get('type', 'string')
            required = 'required' if param.get('required', False) else ''
            description = param.get('description', f'{param_name} parameter')
            request_fields += f'<ParamField path="{param_name}" type="{param_type}" {required}>\n  {description}\n</ParamField>\n\n'
    
    # Add query parameters
    for param in parameters:
        if param.get('in') == 'query':
            param_name = param.get('name', '')
            param_type = param.get('schema', {}).get('type', 'string')
            required = 'required' if param.get('required', False) else ''
            description = param.get('description', f'{param_name} parameter')
            request_fields += f'<ParamField query="{param_name}" type="{param_type}" {required}>\n  {description}\n</ParamField>\n\n'
    
    # Generate responses
    responses = operation.get('responses', {})
    success_response = responses.get('200', {})
    error_responses = {k: v for k, v in responses.items() if k.startswith('4') or k.startswith('5')}
    
    # Generate response fields
    response_fields = ""
    if success_response:
        response_fields += "### Success Responses\n\n"
        response_fields += f'<ResponseField name="status" type="number">\n  HTTP status code: 200\n</ResponseField>\n\n'
        response_fields += f'<ResponseField name="message" type="string">\n  Success message\n</ResponseField>\n\n'
        response_fields += f'<ResponseField name="data" type="object">\n  Response data\n</ResponseField>\n\n'
    
    if error_responses:
        response_fields += "### Error Responses\n\n"
        for status_code, response in error_responses.items():
            response_fields += f'<ResponseField name="status" type="number">\n  HTTP status code: {status_code}\n</ResponseField>\n\n'
            response_fields += f'<ResponseField name="message" type="string">\n  Error message\n</ResponseField>\n\n'
            response_fields += f'<ResponseField name="error" type="object">\n  Error details\n</ResponseField>\n\n'
    
    # Generate example requests
    example_requests = f"""## Example Request

<CodeGroup>

```bash cURL
curl -X {method.upper()} \\
  '{path}' \\
  -H 'Content-Type: application/json' \\
  -H 'Authorization: Bearer YOUR_TOKEN'
```

```javascript JavaScript
const response = await fetch('{path}', {{
  method: '{method.upper()}',
  headers: {{
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  }},
  body: JSON.stringify({{
    // Request body data
  }})
}});

const data = await response.json();
console.log(data);
```

```python Python
import requests

url = '{path}'
headers = {{
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
}}
data = {{
    # Request body data
}}

response = requests.{method.lower()}(url, headers=headers, json=data)
result = response.json()
print(result)
```

</CodeGroup>

## Example Response

### Success Response

```json
{{
  "status": 200,
  "message": "Success",
  "data": {{
    "key": "value"
  }}
}}
```

### Error Response

```json
{{
  "status": 400,
  "message": "Bad Request",
  "error": {{
    "code": "VALIDATION_ERROR",
    "details": "Invalid input data"
  }}
}}
```"""

    # Check if authentication is required
    security = operation.get('security', [])
    auth_note = ""
    if security:
        auth_note = """<Note>
This endpoint requires authentication. Include your API key in the `X-API-Key` header or use Bearer token authentication.
</Note>

"""

    # Generate complete MDX content
    mdx_content = f"""---
title: "{title}"
api: "{method.upper()} {path}"
description: "{description}"
---

## Overview

{description}

{auth_note}## Request

{request_fields}## Response Codes

{response_fields}{example_requests}"""
    
    return mdx_content

def regenerate_all_docs():
    """Regenerate all API documentation files"""
    spec = load_openapi_spec()
    paths = spec.get('paths', {})
    
    # Clear existing API files
    api_dir = Path('api')
    if api_dir.exists():
        import shutil
        shutil.rmtree(api_dir)
    
    # Create new API directory
    api_dir.mkdir(exist_ok=True)
    
    generated_count = 0
    
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
                # Generate filename
                filename = clean_filename(path, method)
                filepath = api_dir / filename
                
                # Generate content
                content = generate_mdx_content(path, method, operation)
                
                # Write file
                with open(filepath, 'w') as f:
                    f.write(content)
                
                generated_count += 1
                print(f"Generated: {filepath}")
    
    print(f"\nGenerated {generated_count} API documentation files")

if __name__ == "__main__":
    regenerate_all_docs()
