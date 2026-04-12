import weaviate

from parking_assistant.config import settings


def get_client():
    return weaviate.connect_to_local(
        host=settings.weaviate_host,
        port=settings.weaviate_http_port,
        grpc_port=settings.weaviate_grpc_port,
    )


def get_collection(client):
    return client.collections.get("ParkingKnowledge")
