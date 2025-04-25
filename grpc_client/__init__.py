import json
from collections.abc import Sequence
from typing import Any

import allure
import grpc
from google.protobuf import json_format
from google.protobuf.descriptor_pool import DescriptorPool
from google.protobuf.message_factory import MessageFactory
from grpc_reflection.v1alpha.proto_reflection_descriptor_database import ProtoReflectionDescriptorDatabase


class GRPClient:
    def __init__(self, address: str, cert_path: str | None = None) -> None:
        self.cert_path = cert_path
        if self.cert_path is None:
            self.channel = grpc.insecure_channel(target=address)
        else:
            with open(self.cert_path, 'rb') as f:
                root_certificates = f.read()
            credentials = grpc.ssl_channel_credentials(root_certificates=root_certificates)
            self.channel = grpc.secure_channel(target=address, credentials=credentials)
        self.address = address
        self._descriptor_pool = DescriptorPool(ProtoReflectionDescriptorDatabase(channel=self.channel))
        self._message_factory = MessageFactory(self._descriptor_pool)

    def _get_method_descriptor(self, service_name: str, method_name: str):
        service_desc = self._descriptor_pool.FindServiceByName(service_name)
        if service_desc is None:
            raise RuntimeError(f"Service {service_name} not found.")
        for method in service_desc.methods:
            if method.name == method_name:
                return method
        raise RuntimeError(f"Method {method_name} not found in service {service_name}.")

    def send_request(self, service_name: str, method_name: str, payload: dict,
                     metadata: Sequence[tuple[str, str]] | None = None) -> tuple[Any, Any] | str:
        try:
            with allure.step(f'gRPC Request -> {self.address}'):
                method_desc = self._get_method_descriptor(service_name, method_name)
                input_type, output_type = method_desc.input_type, method_desc.output_type
                request_msg_class = self._message_factory.GetPrototype(input_type)
                request_msg = request_msg_class()
                json_format.ParseDict(payload, request_msg)
                full_rpc_name = f"/{service_name}/{method_name}"
                req = (f"grpcurl -d '{json.dumps(payload)}' -cacert {self.cert_path} {self.address} "
                       f"{service_name}/{method_name}")
                print(req)
                allure.attach(str(req), name='gRPC Request', attachment_type=allure.attachment_type.TEXT)
                unary_call = self.channel.unary_unary(
                    full_rpc_name,
                    request_serializer=lambda msg: msg.SerializeToString(),
                    response_deserializer=lambda data: self._message_factory.GetPrototype(output_type)().FromString(data),
                )
                response_msg = unary_call(request_msg, metadata=metadata)
                response_json = json_format.MessageToDict(response_msg)
                response = json.dumps(response_json, indent=2, ensure_ascii=False)
                allure.attach(str(response), name='gRPC Response', attachment_type=allure.attachment_type.TEXT)
                print(response)
                return response
        except grpc.RpcError as error:
            print(f"[gRPC Error] Code: {error.code().name}, Details: {error.details()}")
            return error.code().name, error.details()
