import os
import smtplib
import requests
# from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import groq
import pinecone
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import time
import random
from email.mime.image import MIMEImage
import argparse
import base64
import pandas as pd  # Add pandas for Excel processing

# Load environment variables
load_dotenv()

# SMTP Configuration
smtp_server = "smtp.hostinger.com"
port = 587  
sender_email = "rebecca@sensiq.ae"
password = os.getenv("EMAIL_PASSWORD")  # Store securely

if not password:
    raise ValueError("EMAIL_PASSWORD environment variable is not set")

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = groq.Groq(api_key=GROQ_API_KEY)

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("Pinecone API key not set")

# Initialize Pinecone with new syntax
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
index_name = "components-db"

# Define country_specific dictionary at module level
country_specific = {
    'UAE': {
        'context': 'supporting UAE Vision 2030 and smart city initiatives',
        'regulations': 'UAE environmental standards and sustainability goals',
        'initiatives': ['UAE Vision 2030', 'Smart Dubai', 'UAE Net Zero 2050']
    },
    'KSA': {
        'context': 'aligning with Saudi Vision 2030 and smart city development',
        'regulations': 'Saudi environmental regulations and waste management standards',
        'initiatives': ['Saudi Vision 2030', 'NEOM', 'Smart City Initiatives']
    },
    'Kingdom of Saudi Arabia': {  # Alternative name mapping to KSA
        'context': 'aligning with Saudi Vision 2030 and smart city development',
        'regulations': 'Saudi environmental regulations and waste management standards',
        'initiatives': ['Saudi Vision 2030', 'NEOM', 'Smart City Initiatives']
    },
    'India': {
        'context': 'supporting Swachh Bharat Mission and Smart Cities Mission',
        'regulations': 'Indian solid waste management rules and guidelines',
        'initiatives': ['Swachh Bharat Mission', 'Smart Cities Mission', 'National Clean Air Programme']
    }
}

def initialize_vector_database():
    """Initialize the vector database if it doesn't already exist"""
    try:
        # Check if index exists
        if index_name not in pc.list_indexes().names():
            print("Creating new vector database...")
            pc.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
            return True
        return False
    except Exception as e:
        print(f"Error initializing vector database: {e}")
        return False

# Initialize the index after ensuring it exists
initialize_vector_database()
index = pc.Index(index_name)

# Initialize sentence transformer model for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

def check_vectors_exist():
    """Check if vectors already exist in the database"""
    try:
        # Query for any vector to check if database is populated
        results = index.query(
            vector=[0.0] * 384,  # Dummy vector
            top_k=1,
            include_metadata=True
        )
        return len(results['matches']) > 0
    except Exception as e:
        print(f"Error checking vectors: {e}")
        return False

def create_vector_database():
    """Create and populate the vector database if needed"""
    try:
        print("Reading components.txt...")
        with open('components.txt', 'r') as file:
            content = file.read()
        
        print("\nSplitting content into chunks...")
        # Split by double newlines and keep section headers together with their content
        chunks = []
        current_chunk = []
        
        for line in content.split('\n'):
            if line.strip():
                current_chunk.append(line)
            elif current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        
        print(f"\nFound {len(chunks)} chunks")
        print("\nFirst few chunks:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk {i}:")
            print(chunk)
            print("-" * 50)
        
        # Generate embeddings for each chunk
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i}...")
            embedding = model.encode(chunk)
            index.upsert(vectors=[
                {
                    'id': f'chunk_{i}',
                    'values': embedding.tolist(),
                    'metadata': {'text': chunk}
                }
            ])
        
        print(f"Successfully created vector database with {len(chunks)} entries")
        return True
        
    except Exception as e:
        print(f"Error creating vector database: {e}")
        return False

def delete_and_recreate_database():
    """Delete existing index and create a new one with updated data"""
    try:
        # Delete existing index if it exists
        if index_name in pc.list_indexes().names():
            pc.delete_index(index_name)
            print("Deleted existing index")
        
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
        
        # Populate with updated data
        with open('components.txt', 'r') as file:
            content = file.read()
        
        chunks = content.split('\n\n')
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        
        # Generate embeddings for each chunk
        for i, chunk in enumerate(chunks):
            embedding = model.encode(chunk)
            index.upsert(vectors=[
                {
                    'id': f'chunk_{i}',
                    'values': embedding.tolist(),
                    'metadata': {'text': chunk}
                }
            ])
        
        print(f"Successfully recreated database with {len(chunks)} entries")
        return True
        
    except Exception as e:
        print(f"Error recreating database: {e}")
        return False

def update_database():
    """Update existing vectors with new content"""
    try:
        print("Reading components.txt...")
        with open('components.txt', 'r') as file:
            content = file.read()
        
        print("Splitting content into chunks...")
        chunks = content.split('\n\n')
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        print(f"Found {len(chunks)} chunks")
        
        print("\nFirst few chunks:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk {i}:")
            print(chunk)
            print("-" * 50)
        
        # Generate embeddings and update vectors
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i}...")
            embedding = model.encode(chunk)
            index.upsert(vectors=[
                {
                    'id': f'chunk_{i}',
                    'values': embedding.tolist(),
                    'metadata': {'text': chunk}
                }
            ])
        
        print(f"Successfully updated database with {len(chunks)} entries")
        return True
        
    except Exception as e:
        print(f"Error updating database: {e}")
        return False

def setup_database():
    """Main function to handle database setup"""
    # First initialize the index if needed
    is_new = initialize_vector_database()
    
    # If it's a new index or if we need to populate existing one
    if is_new:
        create_vector_database()
    else:
        # Update existing database with new content
        update_database()

def query_vector_database(query, top_k=3):
    # Generate embedding for the query
    query_embedding = model.encode(query)
    
    # Query Pinecone
    results = index.query(
        vector=query_embedding.tolist(),
        top_k=top_k,
        include_metadata=True
    )
    
    # Extract and return the relevant texts
    return [match['metadata']['text'] for match in results['matches']]

def extract_name_from_email(email):
    """Extract and format a name from an email address"""
    try:
        # Remove everything after @ and split by common separators
        local_part = email.split('@')[0]
        
        # Split by common separators and remove numbers
        parts = ''.join(char for char in local_part if not char.isdigit())
        parts = parts.replace('.', ' ').replace('_', ' ').replace('-', ' ')
        
        # Capitalize each word and filter out empty strings
        words = [word.capitalize() for word in parts.split() if word]
        
        if not words:
            return "Valued Professional"
            
        # If we have at least two words, use them as first and last name
        if len(words) >= 2:
            return f"{words[0]} {words[1]}"
        
        # If we only have one word, use it as first name
        return words[0]
        
    except Exception as e:
        print(f"Error extracting name from email {email}: {e}")
        return "Valued Professional"

def get_random_queries():
    """Generate random variations of queries for different components"""
    company_queries = [
        "SensIQ company information contact details",
        "SensIQ company overview background mission",
        "SensIQ business description expertise",
        "SensIQ company profile and specialization"
    ]
    
    solution_queries = [
        "Smart waste management solutions features benefits",
        "Waste management technology advantages implementation",
        "SensIQ waste management innovation benefits",
        "Waste optimization solutions key features"
    ]
    
    product_queries = [
        "SensIQ products SN10 RFID specifications",
        "SN10 sensor system capabilities features",
        "RFID waste management technology details",
        "Smart waste sensor technical advantages"
    ]
    
    return {
        'company': random.choice(company_queries),
        'solution': random.choice(solution_queries),
        'product': random.choice(product_queries)
    }

def generate_base_email_content(recipient_type='municipality', country='UAE', language='English'):
    """Generate base email content with randomized variations"""
    print(f"Generating email for recipient_type: {recipient_type}, country: {country}, language: {language}")
    
    # Validate country and get country info
    if country == 'Kingdom of Saudi Arabia':
        country = 'KSA'
    
    if country not in country_specific:
        print(f"Warning: Invalid country: {country}, defaulting to UAE")
        country = 'UAE'
    
    country_info = country_specific[country]
    
    # Get random queries for each component
    queries = get_random_queries()
    
    # Get relevant components from vector database with randomized queries
    company_info = query_vector_database(queries['company'], top_k=1)
    solutions = query_vector_database(queries['solution'], top_k=random.randint(1, 2))
    products = query_vector_database(queries['product'], top_k=random.randint(1, 2))
    
    context = {
        'company': company_info[0] if company_info else "",
        'solutions': "\n".join(solutions) if solutions else "",
        'products': "\n".join(products) if products else ""
    }

    # Recipient type specific content
    recipient_specific = {
        'municipality': {
            'focus': f'smart city initiatives and public waste management, {country_info["context"]}',
            'benefits': [
                'Smart City Integration',
                'Cost Optimization',
                'Public Service Enhancement',
                'Data-Driven Decisions',
                f'Alignment with {country_info["initiatives"][0]}'
            ]
        },
        'charity': {
            'focus': f'sustainable waste management for charitable organizations, {country_info["context"]}',
            'benefits': [
                'Cost-Effective Operations',
                'Environmental Impact',
                'Community Engagement',
                'Resource Optimization',
                f'Support for {country_info["initiatives"][0]}'
            ]
        },
        'waste_management': {
            'focus': f'efficient waste management operations, {country_info["context"]}',
            'benefits': [
                'Operational Efficiency',
                'Cost Reduction',
                'Route Optimization',
                'Regulatory Compliance',
                f'Support for {country_info["regulations"]}'
            ]
        },
        'property_management': {
            'focus': f'modern property management and sustainability, {country_info["context"]}',
            'benefits': [
                'Property Value Enhancement',
                'Tenant Satisfaction',
                'Service Optimization',
                'Cost Control',
                'Regulatory Compliance'
            ]
        }
    }

    # Validate recipient type
    if recipient_type not in ['municipality', 'charity', 'waste_management', 'property_management']:
        print(f"Warning: Invalid recipient_type: {recipient_type}, defaulting to municipality")
        recipient_type = 'municipality'

    prompt = f"""Generate a professional cold email for a {recipient_type} in {country}, focusing on {recipient_specific[recipient_type]['focus']}.
    The email should follow this EXACT template (only replace the introduction paragraph):

    Subject: Smart ESG Waste Management – Get a Free Demo & Trial

    Hi [recipient_name],

    [GENERATE A COMPELLING 2-3 SENTENCE INTRODUCTION FOCUSING ON:
    - {recipient_specific[recipient_type]['benefits'][0]}
    - {recipient_specific[recipient_type]['benefits'][1]}
    - {country_info['context']}
    - Mention {country_info['initiatives'][0]} if relevant]

    Why SN10 for {recipient_type.replace('_', ' ').title()} Waste Management?

    ✅ {recipient_specific[recipient_type]['benefits'][0]} – Real-time monitoring and optimization
    ✅ {recipient_specific[recipient_type]['benefits'][1]} – Reduce operational costs by up to 30%
    ✅ {recipient_specific[recipient_type]['benefits'][2]} – Enhance service quality and impact
    ✅ {recipient_specific[recipient_type]['benefits'][3]} – Advanced analytics and reporting
    ✅ {recipient_specific[recipient_type]['benefits'][4]} – Support {country_info['regulations']}

    🚀 Get Started with a Free Trial!

    We make it easy to evaluate our solution:

    📅 Schedule a Demo: https://calendly.com/sameer-sensiq/30min
    📱 WhatsApp or Call Us: https://wa.me/971528004558
    🎟 Request a Trial Project: https://www.sensiq.ae/trial

    You can also visit our website for more details: https://www.sensiq.ae

    Looking forward to helping you modernize waste management and achieve your sustainability targets!

    Best regards,
    Rebecca
    Business Development Representative
    SensIQ
    📞 <a href="tel:+97152800455" style="color: #9ba6b7; text-decoration: none;">+971 52 800 4558</a> | 🌐 <a href="https://www.sensiq.ae" style="color: #9ba6b7; text-decoration: none;">www.sensiq.ae</a>
    📲 WhatsApp: +971 528004558

    IMPORTANT: DO NOT write "Rest of the email remains the same" or any similar placeholder. Include the complete email as shown above.
    """

    try:
        completion = groq_client.chat.completions.create(
            model="DeepSeek-R1-Distill-Llama-70B",
            messages=[
                {"role": "system", "content": "You are a professional email writer. Generate only the email content exactly as requested, with no additional commentary or placeholders."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        email_content = completion.choices[0].message.content.strip()
        
        # Extract subject and body
        lines = email_content.split('\n')
        subject = ""
        body_lines = []
        content_started = False
        
        for line in lines:
            line = line.strip()
            if line.startswith("Subject:"):
                subject = line.replace("Subject:", "").strip()
                content_started = True
            elif content_started:
                # Skip any line that looks like a placeholder or instruction
                if not any(marker in line.lower() for marker in [
                    "[generate", "[your", "[insert", "[intro", "[close",
                    "ok, i'll", "ok, i need", "okay,", "copy the"
                ]):
                    body_lines.append(line)
        
        body = "\n".join(body_lines)
        
        # Convert the plain text to HTML
        html_body = create_html_email(body)
        return subject, html_body
        
    except Exception as e:
        print(f"Error generating email content: {e}")
        return "Smart ESG Waste Management – Get a Free Demo & Trial", create_html_email("Error generating email content. Please try again.")

def create_html_email(body_text):
    """Create HTML email with modern design and emoji support"""
    paragraphs = [p.strip() for p in body_text.split('\n') if p.strip()]
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #e9eef4;
                background-color: #0c1117;
                margin: 0;
                padding: 0;
            }
            
            .container {
                max-width: 600px;
                margin: 0 auto;
                background-color: #0c1117;
            }
            
            .header {
                background-color: #1a1f26;
                padding: 25px 20px;
                text-align: center;
            }
            
            .logo {
                max-width: 150px;
                height: auto;
            }
            
            .hero {
                background-color: #131820;
                padding: 40px 20px;
                text-align: center;
            }
            
            .hero-image {
                width: 100%;
                max-width: 500px;
                height: auto;
                margin-bottom: 20px;
                border-radius: 8px;
            }
            
            .hero-title, .greeting {
                color: #0ef0a1;
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 15px;
                background: linear-gradient(135deg, #0ef0a1 0%, #00f5c4 100%);
                -webkit-background-clip: text;
                background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .hero-subtitle {
                color: #9ba6b7;
                font-size: 16px;
                margin-bottom: 30px;
            }
            
            .content-section {
                padding: 30px 20px;
                background-color: #1a1f26;
            }
            
            .feature-card {
                background-color: #131820;
                border: 1px solid #0ef0a1;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .cta-button {
                display: inline-block;
                background: #05a67b;
                color: white;
                text-decoration: none;
                padding: 14px 30px;
                border-radius: 50px;
                font-weight: 600;
                font-size: 15px;
            }
            
            .stats-section {
                display: flex;
                justify-content: center;
                gap: 30px;
                padding: 40px 20px;
                flex-wrap: wrap;
                margin-top: 30px;
            }
            
            .stat-circle {
                width: 120px;
                height: 120px;
                border-radius: 50%;
                background: linear-gradient(135deg, #131820 0%, #1a1f26 100%);
                border: 2px solid #0ef0a1;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 15px;
                transition: all 0.3s ease;
            }
            
            .stat-circle:hover {
                transform: scale(1.05);
                box-shadow: 0 0 20px rgba(14, 240, 161, 0.2);
            }
            
            .stat-number {
                color: #0ef0a1;
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 5px;
                background: linear-gradient(135deg, #0ef0a1 0%, #00f5c4 100%);
                -webkit-background-clip: text;
                background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .stat-label {
                color: #9ba6b7;
                font-size: 12px;
                text-align: center;
                line-height: 1.2;
            }
            
            .eco-badge {
                background-color: #1a1f26;
                border: 1px solid #05a67b;
                border-radius: 12px;
                padding: 20px;
                margin: 20px;
                text-align: center;
            }
            
            .signature {
                padding: 20px;
                border-top: 1px solid #1a1f26;
                color: #9ba6b7;
            }
            
            .footer {
                background-color: #0c1117;
                color: #9ba6b7;
                padding: 30px 20px;
                text-align: center;
            }
            
            @media screen and (max-width: 480px) {
                .stats-section {
                    flex-direction: row;
                    justify-content: space-around;
                }
                
                .stat-item {
                    flex: 0 0 33.33%;
                    padding: 10px 5px;
                }
                
                .stat-number {
                    font-size: 24px;
                }
                
                .stat-label {
                    font-size: 12px;
                }
            }
            
            .greeting {
                font-size: 20px;
                margin: 20px 0;
                padding: 10px 0;
            }
            
            .content-text {
                color: #e9eef4;
                font-size: 16px;
                line-height: 1.8;
                margin-bottom: 15px;
            }
            
            .highlight-text {
                color: #0ef0a1;
                font-weight: 500;
            }
            
            .address-footer {
                background-color: #131820;
                padding: 20px;
                margin-top: 20px;
                border-top: 1px solid rgba(255,255,255,0.05);
                text-align: center;
            }
            
            .contact-info {
                margin-bottom: 15px;
            }
            
            .contact-info a:hover {
                color: #0ef0a1 !important;
                transition: color 0.3s ease;
            }
            
            .address {
                font-size: 14px;
                line-height: 1.6;
            }
            
            .feature-list {
                background-color: #131820;
                border: 1px solid #0ef0a1;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }
            
            .feature-item {
                color: #e9eef4;
                margin: 10px 0;
                padding: 8px 0;
                font-size: 15px;
                line-height: 1.6;
            }
            
            .cta-section {
                background-color: #131820;
                border: 1px solid #0ef0a1;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }
            
            .contact-link {
                display: block;
                color: #0ef0a1;
                text-decoration: none;
                margin: 10px 0;
                padding: 8px 0;
            }
            
            .contact-link:hover {
                color: #05a67b;
            }
            
            .emoji {
                font-size: 18px;
                margin-right: 8px;
            }
            
            .cta-buttons {
                display: flex;
                justify-content: center;
                gap: 20px;
                flex-wrap: wrap;
                margin: 30px 0;
            }
            
            .cta-button {
                display: flex;
                flex-direction: column;
                align-items: center;
                text-decoration: none;
                background: linear-gradient(135deg, #131820 0%, #1a1f26 100%);
                border: 2px solid #0ef0a1;
                border-radius: 15px;
                padding: 20px;
                width: 160px;
                transition: all 0.3s ease;
            }
            
            .cta-button:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(14, 240, 161, 0.2);
                background: linear-gradient(135deg, #1a1f26 0%, #131820 100%);
            }
            
            .cta-icon {
                font-size: 32px;
                margin-bottom: 10px;
            }
            
            .cta-label {
                color: #e9eef4;
                font-size: 14px;
                text-align: center;
                line-height: 1.4;
            }
            
            .divider {
                width: 40px;
                height: 2px;
                background: #0ef0a1;
                margin: 8px auto;
            }
            
            .website-link-container {
                text-align: center;
                margin: 30px 0;
                padding: 20px;
            }
            
            .website-link {
                display: inline-block;
                padding: 10px 20px;
                background: linear-gradient(135deg, #131820 0%, #1a1f26 100%);
                border: 2px solid #0ef0a1;
                border-radius: 12px;
                transition: all 0.3s ease;
            }
            
            .website-link:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(14, 240, 161, 0.2);
                background: linear-gradient(135deg, #1a1f26 0%, #131820 100%);
            }
            
            .website-logo {
                max-width: 150px;
                height: auto;
            }
            
            .visit-text {
                color: #9ba6b7;
                font-size: 14px;
                margin-bottom: 15px;
            }
            
            .product-showcase {
                text-align: center;
                margin: 40px 0;
                padding: 30px;
                background: linear-gradient(135deg, #131820 0%, #1a1f26 100%);
                border: 2px solid #0ef0a1;
                border-radius: 15px;
            }
            
            .product-image {
                max-width: 300px;
                height: auto;
                margin: 20px auto;
                filter: drop-shadow(0 0 20px rgba(14, 240, 161, 0.3));
                transition: transform 0.3s ease;
            }
            
            .product-image:hover {
                transform: scale(1.05);
            }
            
            .product-title {
                color: #0ef0a1;
                font-size: 24px;
                margin: 20px 0 10px 0;
            }
            
            .product-description {
                color: #9ba6b7;
                font-size: 16px;
                margin: 10px 0;
            }
            
            .feature-box {
                background: linear-gradient(135deg, #131820 0%, #1a1f26 100%);
                border: 2px solid #0ef0a1;
                border-radius: 15px;
                padding: 25px;
                margin: 30px 0;
            }
            
            .feature-box h3 {
                color: #0ef0a1;
                margin-top: 0;
                margin-bottom: 20px;
                font-size: 24px;
                text-align: center;
            }
            
            .feature-item {
                color: #e9eef4;
                margin: 15px 0;
                padding: 15px;
                border-left: 3px solid #0ef0a1;
                background: rgba(14, 240, 161, 0.05);
                border-radius: 0 10px 10px 0;
            }
            
            .cta-container {
                background: linear-gradient(135deg, #131820 0%, #1a1f26 100%);
                border: 2px solid #0ef0a1;
                border-radius: 15px;
                padding: 25px;
                margin: 30px 0;
            }
            
            .cta-title {
                color: #0ef0a1;
                text-align: center;
                margin-bottom: 20px;
                font-size: 20px;
            }
            
            .cta-buttons {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .cta-link {
                display: flex;
                align-items: center;
                padding: 15px 25px;
                background: rgba(14, 240, 161, 0.05);
                border: 1px solid #0ef0a1;
                border-radius: 10px;
                color: #e9eef4;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            
            .cta-link:hover {
                transform: translateX(10px);
                background: rgba(14, 240, 161, 0.1);
                box-shadow: 0 0 20px rgba(14, 240, 161, 0.2);
            }
            
            .cta-emoji {
                font-size: 24px;
                margin-right: 15px;
                min-width: 30px;
                text-align: center;
            }
            
            .info-box {
                background: linear-gradient(135deg, #131820 0%, #1a1f26 100%);
                border: 2px solid #0ef0a1;
                border-radius: 15px;
                padding: 25px;
                margin: 30px 0;
            }
            
            .info-box-title {
                color: #0ef0a1;
                font-size: 20px;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .info-box-content {
                color: #e9eef4;
                line-height: 1.6;
            }
            
            .contact-info {
                background: rgba(14, 240, 161, 0.05);
                border-left: 3px solid #0ef0a1;
                padding: 15px;
                margin: 20px 0;
                border-radius: 0 10px 10px 0;
            }
            
            .signature-box {
                border-top: 2px solid #0ef0a1;
                margin-top: 30px;
                padding-top: 20px;
                color: #9ba6b7;
            }
            
            .website-box {
                text-align: center;
                margin: 30px 0;
                padding: 20px;
                background: linear-gradient(135deg, #131820 0%, #1a1f26 100%);
                border: 2px solid #0ef0a1;
                border-radius: 15px;
            }
            
            .website-text {
                color: #9ba6b7;
                margin-bottom: 15px;
                font-size: 16px;
            }
            
            .logo-link {
                display: inline-block;
                padding: 15px 30px;
                transition: all 0.3s ease;
            }
            
            .logo-link:hover {
                transform: translateY(-5px);
            }
            
            .website-logo {
                max-width: 120px;  /* Reduced size */
                height: auto;
                filter: drop-shadow(0 0 10px rgba(14, 240, 161, 0.3));
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="cid:logo" alt="SensIQ" class="logo">
            </div>
            
            <div class="hero">
                <img src="cid:cover" alt="Smart Waste Management" class="hero-image">
                <h1 class="hero-title">Smart Waste Management Solutions</h1>
                <p class="hero-subtitle">Transform your operations with IoT-powered efficiency</p>
            </div>
            
            <div class="content-section">
    """
    
    # Process paragraphs with new styling
    parts = []
    for p in paragraphs:
        if "Hi [recipient_name]" in p or "Hi {{recipient_name}}" in p or "Hi " in p:
            parts.append(f'<div class="content-text">{p}</div>')
            # Add product showcase after greeting
            parts.append("""
            <div class="product-showcase">
                <img src="cid:product" alt="SN10 Smart Sensor" class="product-image">
                <h2 style="color: #0ef0a1; margin: 20px 0 10px 0;">SN10 Smart Waste Sensor</h2>
                <p style="color: #9ba6b7; margin: 10px 0;">Advanced IoT-powered waste management solution</p>
            </div>
            """)
        elif "Why SensIQ?" in p:
            parts.append("""
            <div class="info-box">
                <div class="info-box-title">Why SensIQ?</div>
                <div class="info-box-content">
            """)
        elif p.startswith("✅"):
            parts.append(f'<div class="feature-item">{p}</div>')
        elif "We make it easy" in p:
            if "info-box" in "".join(parts):
                parts.append("</div></div>")  # Close info box
            parts.append("""
            <div class="info-box">
                <div class="info-box-title">Get Started with a Free Demo or Trial!</div>
                <div class="info-box-content">
                    <p>We make it easy for you to explore how our solution fits your needs:</p>
                    <div class="cta-buttons">
                        <a href="https://calendly.com/rebecca-sensiq/30min" class="cta-link" target="_blank">
                            <span class="cta-emoji">📅</span>
                            <span>Schedule a Meeting/Demo</span>
                        </a>
                        <a href="https://wa.me/971528004558" class="cta-link" target="_blank">
                            <span class="cta-emoji">📱</span>
                            <span>WhatsApp or Call Us</span>
                        </a>
                        <a href="https://www.sensiq.ae/trial" class="cta-link" target="_blank">
                            <span class="cta-emoji">🎟</span>
                            <span>Request a Free Trial</span>
                        </a>
                </div>
                </div>
                </div>
            """)
        elif "Looking forward" in p:
            parts.append("""
            <div class="signature-box">
                <div class="contact-info">
            """)
            parts.append(f'<div class="content-text">{p}</div>')
            parts.append("</div></div>")
        elif "visit our website" in p.lower():
            parts.append("""
            <div class="website-box">
                <div class="website-text">You can also visit our website for more details:</div>
                <a href="https://www.sensiq.ae" class="logo-link" target="_blank">
                    <img src="cid:logo" alt="SensIQ Website" class="website-logo">
                </a>
            </div>
            """)
        elif not any(p.startswith(icon) for icon in ["📅", "📱", "🎟"]):
            parts.append(f'<div class="content-text">{p}</div>')
    
    html_content += "\n".join(parts)
    return html_content

def send_email(receiver_email, subject, body, images=None):
    """Send email with images"""
    print(f"\n--- DEBUG: Starting send_email to {receiver_email} ---")
    try:
        # Create a multipart message with the correct structure for inline images
        message = MIMEMultipart('alternative')
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        # Debug: Check if product image is referenced in the body
        if 'cid:product' in body:
            print("DEBUG: Product image is referenced in the body")
        else:
            print("WARNING: Product image reference (cid:product) not found in the body")
            
        # Create HTML part
        html_part = MIMEText(body, "html")
        
        # Create related part to hold the HTML and inline images
        related = MIMEMultipart('related')
        related.attach(html_part)
        
        # Get current directory for absolute paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Default image paths with absolute paths
        default_images = {
            'logo': os.path.join(current_dir, 'assets', 'logo.png'),
            'cover': os.path.join(current_dir, 'assets', 'Cover.png'),
            'product': os.path.join(current_dir, 'assets', 'SN10.jpg')
        }

        # Use provided image paths if available, otherwise use defaults
        image_paths = images if images else default_images
        print(f"DEBUG: Using image paths: {image_paths}")

        # Attach images
        for cid, path in image_paths.items():
            try:
                # Check if path exists
                if not os.path.exists(path):
                    print(f"WARNING: Image path does not exist: {path}")
                    # Try alternative path
                    alt_path = os.path.join(current_dir, 'assets', os.path.basename(path))
                    if os.path.exists(alt_path):
                        print(f"DEBUG: Using alternative path for {cid}: {alt_path}")
                        path = alt_path
                    else:
                        print(f"ERROR: Could not find image for {cid}")
                        continue
                
                with open(path, 'rb') as f:
                    img_data = f.read()
                    img = MIMEImage(img_data)
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(path))
                    related.attach(img)
                    print(f"DEBUG: Successfully attached image: {cid} from {path} ({len(img_data)} bytes)")
            except Exception as e:
                print(f"ERROR: Error attaching image {cid} from {path}: {e}")
                # Continue with other images even if one fails

        # Attach the related part to the message
        message.attach(related)
        
        # Debug: Print message structure
        print(f"DEBUG: Message structure: {message.as_string()[:500]}...")

        # Send the email
        try:
            with smtplib.SMTP(smtp_server, port) as server:
                server.set_debuglevel(1)  # Enable debug output
                print(f"DEBUG: Connecting to SMTP server {smtp_server}:{port}")
                server.starttls()
                print(f"DEBUG: Logging in as {sender_email}")
                server.login(sender_email, password)
                print(f"DEBUG: Sending message to {receiver_email}")
                server.send_message(message)
                print(f"DEBUG: Email sent to {receiver_email}")
                return True
        except Exception as e:
            print(f"ERROR: SMTP error while sending email: {e}")
            return False
    except Exception as e:
        print(f"ERROR: General error in send_email: {e}")
        return False

def get_sn10_product_info():
    """Fetch SN10 product information from components database"""
    # Query for SN10 product details
    results = query_vector_database("SensIQ Product Details SN10", top_k=1)
    
    # Print debug information
    print("\nDebug: Vector Database Query Results")
    print("Query:", "SensIQ Product Details SN10")
    print("Results:", results)
    
    # Always return the hardcoded info for now
    sn10_info = {
        'name': 'SN10',
        'subtitle': 'Smart IoT Solution for Real-time Waste Management',
        'technical_specs': {
            'sensor': {
                'type': 'Ultrasonic',
                'range': '20-400 cm',
                'accuracy': '±2 cm'
            },
            'connectivity': {
                'primary': 'LTE CAT-1 (B1, B3, B5, B8, B20, B28)',
                'fallback': '2G/3G/NB-IoT',
                'sim': 'eSIM/4FF Nano SIM with multi-carrier roaming'
            },
            'power': {
                'battery': '2 x Li-ion (10000 mAh)',
                'sleep_current': '<10 μA',
                'battery_life': '2+ years (1 update/hour)'
            },
            'communication': {
                'update_interval': 'Configurable (5 mins-24 hrs)',
                'protocols': 'MQTT, HTTPS, TCP/UDP'
            },
            'environmental': {
                'operating_temp': '-20°C to +70°C',
                'ip_rating': 'IP67 (dust/waterproof)'
            },
            'physical': {
                'dimensions': '130 x 130 x 50 mm',
                'weight': '150 g'
            }
        },
        'key_features': [
            'Adaptive reporting based on fill rate and motion',
            'Tamper detection alerts',
            'Weatherproof design',
            'Long battery life'
        ]
    }
    return sn10_info

def send_sn10_product_email(recipient_email, subject, images=None):
    """Send SN10 product email using the new template"""
    print(f"\n--- DEBUG: Starting send_sn10_product_email to {recipient_email} ---")
    sn10_info = get_sn10_product_info()
    
    # Get the absolute path to the templates directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(current_dir, 'templates', 'product_template.html')
    
    print(f"DEBUG: Looking for template at: {template_path}")
    
    # Read the HTML template with UTF-8 encoding
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            template = file.read()
        print("DEBUG: Successfully read product template file")
    except Exception as e:
        print(f"ERROR: Error reading template file: {e}")
        # Try alternative path (relative to frontend directory)
        try:
            frontend_dir = os.path.join(current_dir, 'frontend')
            alt_template_path = os.path.join(frontend_dir, '..', 'templates', 'product_template.html')
            print(f"DEBUG: Trying alternative template path: {alt_template_path}")
            with open(alt_template_path, 'r', encoding='utf-8') as file:
                template = file.read()
            print("DEBUG: Successfully read product template file from alternative path")
        except Exception as e2:
            print(f"ERROR: Error reading template file from alternative path: {e2}")
            return False
    
    # Replace placeholders with SN10 information
    try:
        email_content = template.replace('{{product_name}}', sn10_info['name'])
        email_content = email_content.replace('{{product_subtitle}}', sn10_info['subtitle'])
        email_content = email_content.replace('{{product_image}}', 'cid:product')
        
        # Format technical specifications
        specs_html = ''
        for category, details in sn10_info['technical_specs'].items():
            specs_html += f'<div class="content-text"><h3 style="color: #0ef0a1;">{category.title()}</h3><ul style="list-style: none; padding-left: 0;">'
            for key, value in details.items():
                specs_html += f'<li style="margin-bottom: 8px;"><strong style="color: #9ba6b7;">{key.replace("_", " ").title()}:</strong> {value}</li>'
            specs_html += '</ul></div>'
        
        email_content = email_content.replace('{{technical_specs}}', specs_html)
        
        # Format key features
        features_html = '<ul style="list-style: none; padding-left: 0;">'
        for feature in sn10_info['key_features']:
            features_html += f'<li style="margin-bottom: 8px; color: #9ba6b7;">• {feature}</li>'
        features_html += '</ul>'
        email_content = email_content.replace('{{key_features}}', features_html)
        print("DEBUG: Successfully prepared email content")
    except Exception as e:
        print(f"ERROR: Error preparing email content: {e}")
        return False
    
    # Define default images dictionary if none provided
    if images is None:
        # Use absolute paths for images
        current_dir = os.path.dirname(os.path.abspath(__file__))
        images = {
            'logo': os.path.join(current_dir, 'assets', 'logo.png'),
            'cover': os.path.join(current_dir, 'assets', 'Cover.png'),
            'product': os.path.join(current_dir, 'assets', 'SN10.jpg')
        }
    
    # Verify image files exist
    for img_id, img_path in images.items():
        if not os.path.exists(img_path):
            print(f"ERROR: Image file not found: {img_path}")
            # Try to find the file in the assets directory
            alt_path = os.path.join(current_dir, 'assets', os.path.basename(img_path))
            if os.path.exists(alt_path):
                print(f"DEBUG: Found image at alternate path: {alt_path}")
                images[img_id] = alt_path
            else:
                print(f"ERROR: Could not find image {img_id} at any path")
    
    # Send email with all required images
    try:
        result = send_email(recipient_email, subject, email_content, images=images)
        if result:
            print(f"DEBUG: Product email successfully sent to {recipient_email}")
            return True
        else:
            print(f"ERROR: Failed to send product email to {recipient_email}")
            return False
    except Exception as e:
        print(f"ERROR: Exception while sending product email: {e}")
        return False

def test_database_content():
    """Test if the database contains the correct content"""
    # Test query for SN10 details
    results = query_vector_database("SensIQ Product Details SN10", top_k=1)
    print("\nTesting database content:")
    print("Query result:", results[0] if results else "No results found")
    
    # Get product info
    product_info = get_sn10_product_info()
    print("\nProduct info:", product_info)

def preview_raw_email():
    """Preview the raw email content for debugging"""
    try:
        # Get SN10 product info
        sn10_info = get_sn10_product_info()
        
        # Get the absolute path to the templates directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, 'templates', 'product_template.html')
        
        # Read the HTML template
        with open(template_path, 'r', encoding='utf-8') as file:
            template = file.read()
        
        # Replace placeholders with SN10 information
        email_content = template.replace('{{product_name}}', sn10_info['name'])
        email_content = email_content.replace('{{product_subtitle}}', sn10_info['subtitle'])
        email_content = email_content.replace('{{product_image}}', 'cid:product')
        
        # Format technical specifications
        specs_html = ''
        for category, details in sn10_info['technical_specs'].items():
            specs_html += f'<div class="content-text"><h3 style="color: #0ef0a1;">{category.title()}</h3><ul style="list-style: none; padding-left: 0;">'
            for key, value in details.items():
                specs_html += f'<li style="margin-bottom: 8px;"><strong style="color: #9ba6b7;">{key.replace("_", " ").title()}:</strong> {value}</li>'
            specs_html += '</ul></div>'
        
        email_content = email_content.replace('{{technical_specs}}', specs_html)
        
        # Format key features
        features_html = '<ul style="list-style: none; padding-left: 0;">'
        for feature in sn10_info['key_features']:
            features_html += f'<li style="margin-bottom: 8px; color: #9ba6b7;">• {feature}</li>'
        features_html += '</ul>'
        email_content = email_content.replace('{{key_features}}', features_html)
        
        # Create a test email message
        message = MIMEMultipart('alternative')
        message["From"] = sender_email
        message["To"] = "test@example.com"
        message["Subject"] = "Test Product Email"
        
        # Create HTML part
        html_part = MIMEText(email_content, "html")
        
        # Create related part to hold the HTML and inline images
        related = MIMEMultipart('related')
        related.attach(html_part)
        
        # Get image paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        images = {
            'logo': os.path.join(current_dir, 'assets', 'logo.png'),
            'cover': os.path.join(current_dir, 'assets', 'Cover.png'),
            'product': os.path.join(current_dir, 'assets', 'SN10.jpg')
        }
        
        # Attach images
        for cid, path in images.items():
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(path))
                    related.attach(img)
            else:
                print(f"Warning: Image not found: {path}")
        
        # Attach the related part to the message
        message.attach(related)
        
        # Print the raw email content
        print(message.as_string())
        return True
    except Exception as e:
        print(f"Error previewing email: {e}")
        return False

def send_followup_email(recipient_email, country, recipient_type, followup_stage):
    """
    Send a follow-up email using country and recipient type specific templates.
    
    Args:
        recipient_email (str): Email address of the recipient
        country (str): Country code ('UAE', 'KSA', 'India')
        recipient_type (str): Type of recipient ('municipality', 'charity')
        followup_stage (str): Stage of follow-up ('first', 'second', 'third')
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    print(f"\n--- DEBUG: Starting follow-up email to {recipient_email} ---")
    
    # Validate recipient type
    if recipient_type not in ['municipality', 'charity']:
        print(f"ERROR: Invalid recipient_type: {recipient_type}, defaulting to municipality")
        recipient_type = 'municipality'
    
    # Validate follow-up stage
    valid_stages = ['first', 'second', 'third']
    if followup_stage not in valid_stages:
        print(f"ERROR: Invalid follow-up stage '{followup_stage}'. Must be one of {valid_stages}")
        return False
    
    # Get recipient name
    recipient_name = extract_name_from_email(recipient_email)
    
    # Get the follow-up content
    try:
        from templates.followup_content import get_followup_content
        content = get_followup_content(country, recipient_type, followup_stage)
    except Exception as e:
        print(f"ERROR: Failed to get follow-up content: {e}")
        return False
    
    # Read the follow-up template
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, 'templates', 'followup_template.html')
        
        print(f"DEBUG: Looking for template at: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as file:
            template = file.read()
        print("DEBUG: Successfully read follow-up template file")
        
        # Replace placeholders with content
        email_content = template.replace('{{recipient_name}}', recipient_name)
        email_content = email_content.replace('{{followup_intro}}', content['followup_intro'])
        email_content = email_content.replace('{{country_specific_content}}', content['country_specific_content'])
        email_content = email_content.replace('{{main_content}}', content['main_content'])
        email_content = email_content.replace('{{cta_message}}', content['cta_message'])
        
        # Generate subject line based on follow-up stage
        subject_prefixes = {
            'first': "Following up: ",
            'second': "Re: ",
            'third': "Final follow-up: "
        }
        subject = f"{subject_prefixes[followup_stage]}Smart Waste Management Solution for {country}"
        
        # Prepare images
        images = {
            'logo': os.path.join(current_dir, 'assets', 'logo.png'),
            'cover': os.path.join(current_dir, 'assets', 'Cover.png'),
            'product': os.path.join(current_dir, 'assets', 'SN10.jpg')
        }
        
        # Send the email with images
        result = send_email(recipient_email, subject, email_content, images=images)
        if result:
            print(f"DEBUG: Follow-up email successfully sent to {recipient_email}")
            return True
        else:
            print(f"ERROR: Failed to send follow-up email to {recipient_email}")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception while sending follow-up email: {e}")
        return False

def process_excel_file(file_path, email_column, additional_columns=None):
    """
    Process an Excel file to extract email addresses and additional data.
    
    Args:
        file_path (str): Path to the Excel file
        email_column (str): Name of the column containing email addresses
        additional_columns (list, optional): List of additional column names to extract
        
    Returns:
        list: List of dictionaries with email and additional data
    """
    try:
        # Read the Excel file
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            raise ValueError("Unsupported file format. Please use .xlsx, .xls, or .csv")
        
        # Validate that the email column exists
        if email_column not in df.columns:
            raise ValueError(f"Email column '{email_column}' not found in the file")
        
        # Validate additional columns if provided
        if additional_columns:
            for col in additional_columns:
                if col not in df.columns:
                    raise ValueError(f"Column '{col}' not found in the file")
        
        # Extract data
        result = []
        for _, row in df.iterrows():
            email = row[email_column]
            # Skip rows with empty email addresses
            if pd.isna(email) or not email:
                continue
                
            data = {'email': email}
            
            # Add additional column data if requested
            if additional_columns:
                for col in additional_columns:
                    data[col] = row[col] if not pd.isna(row[col]) else ''
            
            result.append(data)
        
        return result
    except Exception as e:
        raise Exception(f"Error processing Excel file: {str(e)}")

def send_bulk_emails(email_data, email_type, recipient_type, country, language, followup_stage=None):
    """
    Send emails to multiple recipients from an Excel file.
    
    Args:
        email_data (list): List of dictionaries with email and additional data
        email_type (str): Type of email to send (regular, product, followup)
        recipient_type (str): Type of recipient (municipality, charity)
        country (str): Target country
        language (str): Email language
        followup_stage (str, optional): Stage of followup for followup emails
        
    Returns:
        dict: Results of the bulk email operation
    """
    results = {
        'total': len(email_data),
        'sent': 0,
        'failed': 0,
        'errors': []
    }
    
    for i, data in enumerate(email_data):
        try:
            email_address = data['email']
            
            # Determine which send function to use based on email_type
            if email_type == 'regular':
                success = send_email(recipient_type, country, language, email_address)
            elif email_type == 'product':
                success = send_sn10_product_email(recipient_type, country, language, email_address)
            elif email_type == 'followup':
                if not followup_stage:
                    raise ValueError("Followup stage is required for followup emails")
                success = send_followup_email(recipient_type, country, language, email_address, followup_stage)
            else:
                raise ValueError(f"Unsupported email type: {email_type}")
            
            if success:
                results['sent'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'email': email_address,
                    'error': 'Failed to send email'
                })
                
            # Add a small delay between emails to avoid rate limiting
            time.sleep(1)
            
            # Calculate progress percentage
            progress = (i + 1) / len(email_data) * 100
            
            # You could implement a callback or other mechanism here to report progress
            
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'email': data['email'],
                'error': str(e)
            })
    
    return results

# List of recipients - example of how to structure larger list
recipients = [
    #{"email": "sameerahamedoff3@gmail.com"},
    #{"email": "riyas@mirobsinnovations.com"}
    {"email": "Sameer@mirobsinnovations.com"}

]

# Modified main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--force-update', action='store_true', help='Force update the vector database')
    parser.add_argument('--test', action='store_true', help='Test database content')
    parser.add_argument('--preview', action='store_true', help='Preview email without sending')
    args = parser.parse_args()
    
    if args.force_update:
        delete_and_recreate_database()
    else:
        setup_database()
    
    if args.test:
        test_database_content()
        exit()
        
    if args.preview:
        preview_raw_email()
        exit()
    
    # Send personalized emails
    for recipient in recipients:
        # Generate name from email
        recipient_name = extract_name_from_email(recipient["email"])
        
        # Randomly decide whether to send product email or regular email
        if random.random() < 1:  # 50% chance of sending product email
            subject = f"Introducing {get_sn10_product_info()['name']}: Advanced Waste Management Solution"
            send_sn10_product_email(recipient["email"], subject)
        else:
            # Generate regular email content
            subject, body_template = generate_base_email_content()
            personalized_body = body_template.replace("[recipient_name]", recipient_name)
            send_email(recipient["email"], subject, personalized_body)
        
        # Add a small delay between emails
        time.sleep(1)
