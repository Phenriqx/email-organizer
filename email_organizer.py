from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.utils import parseaddr
import os 
import pickle

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class EmailAuth:
    def get_email_service():
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                
        # If no valid credentials -> authenticate user
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return build('gmail', 'v1', credentials=creds)

class EmailConditions:   
    @staticmethod
    def get_email_sender(from_header):
        _, email = parseaddr(from_header)
        return email
    
    @staticmethod
    def condition_college(msg):
        """Check if email is from work domain --> This is the same for all the other condition functions, example: college, friend, etc.
        Args:
            msg (dict): The email message object containing payload and headers

        Returns:
            bool: True if the sender's domain is 'college.com', False otherwise
        """
        from_header = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'From'), None)
        if from_header:
            email = EmailConditions.get_email_sender(from_header)
            domain = email.split('@')[-1] if '@' in email else None
            # Enter the email address after the @ of your university
            return domain == 'college.com'
        
        return False
    
    @staticmethod
    def condition_work(msg):
        from_header = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'From'), None)
        if from_header:
            email = EmailConditions.get_email_sender(from_header)
            domain = email.split('@')[-1] if '@' in email else None
            
            # Enter the email address of your work, for instance: google.com or microsoft.com, etc.
            return domain == 'work.com' 
        
        return False
    
    @staticmethod 
    def multiple_conditions(msg):
        """You may want to alter the name of this function to match a certain criteria or category/label.
           Here I named multiple_conditions() just to be general, but you can just modify the domains inside the domains list below.
        """
        from_header = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'From'), None)
        if from_header:
            email = EmailConditions.get_email_sender(from_header)
            domains = ['leetcode.com', 'linkedin.com', 'udemymail.com']
            domain = email.split('@')[-1] if '@' in email else None
            return domain in domains
            
        return False

    
    
rules = [
    (EmailConditions.condition_work, 'Work'),
    (EmailConditions.condition_college, 'College'),
    (EmailConditions.multiple_conditionsm, 'Conditions')
]   
service = EmailAuth.get_email_service()