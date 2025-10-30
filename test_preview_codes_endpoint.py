#!/usr/bin/env python3
"""
Test script for the preview codes list endpoint
"""
import requests
import json

# Your deployed endpoint URL
BASE_URL = "https://1task-backend-api-gse0fsgngtfxhjc6.southcentralus-01.azurewebsites.net"
ENDPOINT = f"{BASE_URL}/api/admin/preview-codes/list"

def test_preview_codes_list():
    """Test the admin preview codes list endpoint"""
    print(f"Testing endpoint: {ENDPOINT}")
    
    try:
        # Make GET request
        response = requests.get(ENDPOINT)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            
            if data.get('success'):
                codes = data.get('codes', [])
                print(f"Total codes returned: {len(codes)}")
                
                # Show first few codes as sample
                for i, code in enumerate(codes[:5]):
                    print(f"Code {i+1}: {code}")
                
                if len(codes) > 5:
                    print(f"... and {len(codes) - 5} more codes")
                    
                # Show usage statistics
                used_count = sum(1 for code in codes if code.get('is_used', False))
                unused_count = len(codes) - used_count
                print(f"\nUsage Statistics:")
                print(f"  Total: {len(codes)}")
                print(f"  Used: {used_count}")
                print(f"  Unused: {unused_count}")
                print(f"  Usage Rate: {(used_count / len(codes) * 100):.1f}%" if codes else "N/A")
            else:
                print(f"API returned success=false")
                if 'error' in data:
                    print(f"Error: {data['error']}")
        else:
            print(f"HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_preview_codes_list()
