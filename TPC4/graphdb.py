import requests
from tabulate import tabulate

def query_graphdb(endpoint_url, sparql_query):
    headers = {
        'Accept': 'application/json',  
    }
    
    response = requests.get(endpoint_url, params={'query': sparql_query}, headers=headers)
    
    if response.status_code == 200:
        return response.json() 
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")
