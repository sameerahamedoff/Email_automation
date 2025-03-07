import os
from dotenv import load_dotenv
import pinecone
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import time

# Load environment variables
load_dotenv()

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("Pinecone API key not set")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "components-db"

# SN10 product details chunk
sn10_chunk = """11. SensIQ Product Details
- Title: SN10
- Subtitle: Smart IoT Solution for Real-time Waste Management
- Sections:
  * Product Overview
  * Features
  * Technical Specifications:
    - Sensor: Ultrasonic with 20-400 cm range, ±2 cm accuracy
    - Connectivity: 
      > LTE CAT-1 (B1, B3, B5, B8, B20, B28)
      > Fallback: 2G/3G/NB-IoT
      > SIM: eSIM/4FF Nano SIM with multi-carrier roaming
    - Power:
      > Battery: 2 x Li-ion (10000 mAh)
      > Sleep Current: <10 μA
      > Battery Life: 2+ years (1 update/hour)
    - Communication:
      > Update Interval: Configurable (5 mins-24 hrs)
      > Protocols: MQTT, HTTPS, TCP/UDP
    - Environmental:
      > Operating Temperature: -20°C to +70°C
      > IP Rating: IP67 (dust/waterproof)
    - Physical:
      > Dimensions: 130 x 130 x 50 mm
      > Weight: 150 g
  * Key Features:
    - Adaptive reporting based on fill rate and motion
    - Tamper detection alerts
    - Weatherproof design
    - Long battery life
  * Integration & Security"""

def manual_index():
    try:
        # Delete existing index if it exists
        if index_name in pc.list_indexes().names():
            pc.delete_index(index_name)
            print("Deleted existing index")
            time.sleep(2)
        
        # Create new index
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        print("Created new index")
        time.sleep(2)
        
        # Initialize the index
        index = pc.Index(index_name)
        
        # Initialize sentence transformer model
        print("Loading model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Generate embedding for SN10 chunk
        print("\nGenerating embedding for SN10 chunk...")
        embedding = model.encode(sn10_chunk)
        
        # Index the chunk
        print("Indexing SN10 chunk...")
        index.upsert(vectors=[{
            'id': 'sn10_details',
            'values': embedding.tolist(),
            'metadata': {
                'text': sn10_chunk,
                'type': 'product_info'
            }
        }])
        
        # Verify the chunk was indexed
        print("\nVerifying indexed content...")
        verify_results = index.query(
            vector=embedding.tolist(),
            top_k=1,
            include_metadata=True
        )
        
        if verify_results['matches']:
            print("Success: SN10 content was properly indexed")
            print(f"Score: {verify_results['matches'][0]['score']}")
            print("\nStored content:")
            print(verify_results['matches'][0]['metadata']['text'])
        else:
            print("Warning: SN10 content may not be properly indexed")
        
        # Test some queries
        test_queries = [
            "SN10",
            "SensIQ Product Details",
            "Technical Specifications",
            "Smart IoT Solution"
        ]
        
        print("\nTesting queries...")
        for query in test_queries:
            print(f"\nQuerying: '{query}'")
            query_embedding = model.encode(query)
            results = index.query(
                vector=query_embedding.tolist(),
                top_k=1,
                include_metadata=True
            )
            
            if results['matches']:
                print(f"Found match with score: {results['matches'][0]['score']}")
            else:
                print("No matches found")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Starting manual indexing of SN10 product details...")
    success = manual_index()
    if success:
        print("\nManual indexing completed successfully")
    else:
        print("\nManual indexing failed") 