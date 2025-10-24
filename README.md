# allure-grpc-client

A tiny helper library to send gRPC requests dynamically (via server reflection) and attach full request/response data to Allure reports. It lets you call any unary-unary gRPC method without generated stubs by providing service/method names and a JSON payload.

Key points:
- Works with Python 3.11
- Requires server reflection on the target gRPC service
- Supports insecure and TLS-secured channels
- Attaches request and response as Allure attachments


## Installation

Using pip:

```bash
pip install allure-grpc-client
```

Using Poetry:

```bash
poetry add allure-grpc-client
```


## Requirements
- Python 3.11
- A gRPC service with reflection enabled
- Optional: Allure reporting stack to view attachments
  - allure-pytest (provided as a dependency)
  - Allure CLI to open reports


## Quick start

```python
from grpc_client import GRPClient

# Insecure channel example
client = GRPClient(address="localhost:50051")

# Secure channel example (server CA certificate path)
# client = GRPClient(address="my.secure.host:443", cert_path="/path/to/ca.crt")

# Prepare payload as a Python dict that matches the input protobuf message
payload = {
    "user_id": "12345"
}

# Optional request metadata as a sequence of (key, value)
metadata = [("authorization", "Bearer <token>")]

# Call: <package.ServiceName>/<MethodName>
response = client.send_request(
    service_name="my.package.UserService",
    method_name="GetUser",
    payload=payload,
    metadata=metadata,
)

# On success, `response` is a pretty-printed JSON string of the protobuf response.
print(response)
```

When run under pytest with Allure enabled, the library adds two attachments:
- "gRPC Request" — includes an example grpcurl command and JSON payload
- "gRPC Response" — the JSON response body


## How it works
- Uses gRPC server reflection to discover message and method descriptors at runtime.
- Builds request/response message classes dynamically (`google.protobuf`).
- Calls the method via a unary-unary channel.
- Reports details to Allure using `allure.attach`.


## Running with Allure
1) Run your tests and generate Allure results:

```bash
pytest --alluredir=./allure-results
```

2) Serve or open the report via Allure CLI:

```bash
allure serve ./allure-results
# or
allure generate ./allure-results -o ./allure-report --clean
```


## Examples

- Insecure connection:
```python
from grpc_client import GRPClient
client = GRPClient("localhost:50051")
print(client.send_request("demo.Greeter", "SayHello", {"name": "World"}))
```

- TLS with custom CA certificate:
```python
client = GRPClient("greeter.example.com:443", cert_path="/etc/ssl/certs/greeter_ca.crt")
print(client.send_request("demo.Greeter", "SayHello", {"name": "Alice"}))
```

- With metadata:
```python
meta = [("authorization", "Bearer <token>"), ("x-request-id", "abc-123")]
client = GRPClient("localhost:50051")
print(client.send_request("demo.Greeter", "SayHello", {"name": "Bob"}, metadata=meta))
```


## Troubleshooting
- Reflection errors: Ensure the target service has gRPC reflection enabled.
- SSL/TLS issues: Provide the correct root CA at `cert_path`. For self-signed endpoints, point to the issuing CA cert.
- UNAVAILABLE / connection refused: Verify `address` is reachable and ports are open.
- PERMISSION_DENIED / UNAUTHENTICATED: Check your metadata/credentials.


## API

Only one public class is currently exposed:

- grpc_client.GRPClient(address: str, cert_path: str | None = None)
  - Creates an insecure channel if `cert_path` is None, otherwise a secure channel with the provided root certs.
  - .send_request(service_name: str, method_name: str, payload: dict, metadata: Sequence[tuple[str, str]] | None = None) -> grpc.RpcError | str
    - Returns pretty JSON string on success or the `grpc.RpcError` instance on failure.

Note: Only unary-unary RPCs are supported at the moment.


## Development
- Python 3.11
- Manage dependencies with Poetry
- Linting/formatting/tests are not enforced here; feel free to adapt for your project


## License

This project is licensed under the terms of the MIT License. See the LICENSE file for details.