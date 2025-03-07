import requests
import json

# Your credentials
access_token = "1000.e40f111017811a8c91c2377f8e4c5a3e.087d97073708c9e9bad6c65b06b95311"
refresh_token = "1000.11cb3306200b6f2e828b3fb7074b5889.6a2da955b9de85f2a71116e92079f2cc"
client_id = "1000.5P2BPAULRG6LY7C6UA6PQOT2EYDE6W"
client_secret = "1818af3fb5f952d7e77e7e89c2e208cb1051407ac8"

# First, let's get your organization ID
def get_organizations():
    url = "https://www.zohoapis.in/books/v3/organizations"  # Updated domain
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    return response.json()

# Get customers to create an invoice for
def get_customers(organization_id):
    url = "https://www.zohoapis.in/books/v3/contacts"  # Updated domain
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "organization_id": organization_id
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# Get items to add to the invoice
def get_items(organization_id):
    url = "https://www.zohoapis.in/books/v3/items"  # Updated domain
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "organization_id": organization_id
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# Create a test invoice
def create_invoice(organization_id, customer_id, item_id):
    url = "https://www.zohoapis.in/books/v3/invoices"  # Updated domain
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "customer_id": customer_id,
        "date": "2023-11-15",
        "line_items": [
            {
                "item_id": item_id,
                "quantity": 1,
                "rate": 100
            }
        ]
    }
    
    params = {
        "organization_id": organization_id
    }
    
    response = requests.post(url, headers=headers, params=params, data=json.dumps(data))
    return response.json()

# Main test function
def test_zohobooks_api():
    print("Testing ZohoBooks API...")
    
    # Step 1: Get organizations
    print("\nFetching organizations...")
    orgs_response = get_organizations()
    print(json.dumps(orgs_response, indent=2))
    
    if 'organizations' in orgs_response and len(orgs_response['organizations']) > 0:
        organization_id = orgs_response['organizations'][0]['organization_id']
        print(f"\nUsing organization ID: {organization_id}")
        
        # Step 2: Get customers
        print("\nFetching customers...")
        customers_response = get_customers(organization_id)
        print(json.dumps(customers_response, indent=2))
        
        # Step 3: Get items
        print("\nFetching items...")
        items_response = get_items(organization_id)
        print(json.dumps(items_response, indent=2))
        
        # Step 4: Create invoice if we have customers and items
        if 'contacts' in customers_response and len(customers_response['contacts']) > 0 and \
           'items' in items_response and len(items_response['items']) > 0:
            
            customer_id = customers_response['contacts'][0]['contact_id']
            item_id = items_response['items'][0]['item_id']
            
            print(f"\nCreating invoice for customer ID: {customer_id} with item ID: {item_id}")
            invoice_response = create_invoice(organization_id, customer_id, item_id)
            print(json.dumps(invoice_response, indent=2))
        else:
            print("\nCannot create invoice: No customers or items found")
    else:
        print("\nNo organizations found")

# Run the test
if __name__ == "__main__":
    test_zohobooks_api()