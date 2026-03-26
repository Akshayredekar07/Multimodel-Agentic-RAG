from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Document
from dotenv import load_dotenv
import os 

load_dotenv()

client = QdrantClient(
    url=os.getenv("QUADRANT_CLUSTER_URL", ""),
    api_key=os.getenv("QUADRANT_API_KEY", ""),
    cloud_inference=True,
)

points = [
    PointStruct(
        id=1,
        payload={"topic": "cooking", "type": "dessert"},
        vector=Document(
            text="Recipe for baking chocolate chip cookies requires flour, sugar, eggs, and chocolate chips.",
            model="sentence-transformers/all-minilm-l6-v2"
        )
    )
]

client.upsert(collection_name="", points=points)

points = client.query_points(collection_name="", query=Document(
    text="Recipe for baking chocolate chip cookies requires flour",
    model="sentence-transformers/all-minilm-l6-v2"
))

print(points)