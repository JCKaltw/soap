import logging
import argparse
import json
from pathlib import Path
from zeep import Client
from zeep.transports import Transport
from requests import Session
from requests_oauthlib import OAuth1

# Import credentials
from config import ACCOUNT_ID, CONSUMER_KEY, CONSUMER_SECRET, TOKEN, TOKEN_SECRET

# Set up argument parsing
parser = argparse.ArgumentParser(
    description='Fetch a list of customer internal IDs using SOAP API with TBA.')
parser.add_argument('--masked', action='store_true',
                    help='Mask sensitive data in the log output')
args = parser.parse_args()

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# NetSuite WSDL URL for 2023.2 version
wsdl_url = 'https://webservices.netsuite.com/wsdl/v2023_2_0/netsuite.wsdl'

# OAuth setup for TBA
oauth = OAuth1(
    client_key=CONSUMER_KEY,
    client_secret=CONSUMER_SECRET,
    resource_owner_key=TOKEN,
    resource_owner_secret=TOKEN_SECRET,
    signature_method='HMAC-SHA256',
    realm=ACCOUNT_ID
)

# Create a SOAP client with OAuth
session = Session()
session.auth = oauth
transport = Transport(session=session)
client = Client(wsdl_url, transport=transport)

# Search Preferences
search_preferences = {
    'pageSize': 1000,
    'returnSearchColumns': True,
    'bodyFieldsOnly': False
}

# Define the search criteria for active customers
search_criteria = client.get_type('ns0:SearchBooleanField')(searchValue=False)
customer_search = client.get_type(
    'ns0:CustomerSearchBasic')(isInactive=search_criteria)


def get_customers():
    try:
        # Execute the search
        response = client.service.search(customer_search, _soapheaders={
                                         'searchPreferences': search_preferences})
        if response.status.isSuccess:
            # Process the response
            customers = response.searchResult.recordList.record
            return customers
        else:
            logger.error("Error in SOAP response: " +
                         response.status.statusDetail[0].message)
    except Exception as e:
        logger.error("Exception occurred: " + str(e))


def write_json_to_file(json_data, file_name):
    if json_data:
        project_root = Path(__file__).parent.parent
        log_dir = project_root / "log"
        log_dir.mkdir(exist_ok=True)
        file_path = log_dir / f"{file_name}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
            print(f"Data written to {file_path}")


# Main script logic
customers = get_customers()
if customers:
    write_json_to_file(customers, "customer_list_soap")
else:
    logger.error("Failed to fetch customer list.")
