import googleapiclient
from googleapiclient.discovery import build
from googleapiclient.http import BatchHttpRequest
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
        if 'payload' not in msg or 'headers' not in msg['payload']:
            return False
        
        from_header = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'From'), None)
        if from_header:
            email = EmailConditions.get_email_sender(from_header)
            domain = email.split('@')[-1] if '@' in email else None
            # Enter the email address after the @ of your university
            return domain == 'college.com'
        
        return False
    
    @staticmethod
    def condition_work(msg):
        if 'payload' not in msg or 'headers' not in msg['payload']:
            return False
        
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
        if 'payload' not in msg or 'headers' not in msg['payload']:
            return False
        
        from_header = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'From'), None)
        if from_header:
            email = EmailConditions.get_email_sender(from_header)
            domains = ['leetcode.com', 'linkedin.com', 'udemymail.com']
            domain = email.split('@')[-1] if '@' in email else None
            return domain in domains
            
        return False
    
class EmailHandler:
    @staticmethod
    def ensure_labels(service, label_names):
        """
        Ensure all specified labels exist and return a name-to-ID mapping.

        label_dict maps label names (e.g., "Work") to their Gmail API IDs (e.g., "Label_123").
        """
        existing_labels = service.users().labels().list(userId='me').execute()['labels']
        label_dict = {label['name']: label['id'] for label in existing_labels}
        for name in label_names:
            if name not in label_dict:
                label_body = {
                    'name': name,
                    'labelListVisibility': 'labelShow',
                    'messageListVisibility': 'show'
                }
                created_label = service.users().labels().create(userId='me', body=label_body).execute()
                label_dict[name] = created_label['id']
                
        return label_dict
    
    @staticmethod
    def get_recent_emails(service, max_emails=250):
        """Fetch and yield the most recent emails."""
        try:
            response = service.users().messages().list(
                userId='me',
                maxResults=max_emails  # Limit to 150 recent emails
            ).execute()
            message_ids = [msg['id'] for msg in response.get('messages', [])]

            # Fetch full details for each message individually
            for msg_id in message_ids:
                try:
                    full_msg = service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='metadata',
                        fields='id,payload/headers'
                    ).execute()
                    yield full_msg
                except googleapiclient.errors.HttpError as e:
                    print(f"Error fetching message {msg_id}: {e}")
                    continue  # Skip failed fetches
                
        except googleapiclient.errors.HttpError as e:
            print(f"HTTP error fetching messages: {e}")
        except Exception as e:
            print(f"Unexpected error fetching messages: {type(e).__name__}: {e}")
            
    @staticmethod
    def organize_emails(service, rules, label_dict, max_emails=150):
        """Process all emails and apply labels based on rules."""
        processed_count = 0
        skipped_count = 0
        for msg in EmailHandler.get_recent_emails(service, max_emails):
            try:
                if 'payload' not in msg:
                    print(f"Skipping message {msg['id']}: No payload available")
                    skipped_count += 1
                    continue
                
                labels_to_add = [label for condition, label in rules if condition(msg)]
                if labels_to_add:
                    label_ids = [label_dict[label] for label in labels_to_add]
                    service.users().messages().modify(
                        userId='me',
                        id=msg['id'],
                        body={'addLabelIds': label_ids}
                    ).execute()
                    
                processed_count += 1
                if processed_count % 10 == 0:
                    print(f"Processed {processed_count} emails, skipped {skipped_count}")
                    
            except Exception as e:
                print(f"Error processing message {msg['id']}: {type(e).__name__}: {e}")
                
        print(f"Total emails processed: {processed_count}, skipped: {skipped_count}")

def main():
    
    service = EmailAuth.get_email_service()
    rules = [
        (EmailConditions.condition_work, 'Work'),
        (EmailConditions.condition_college, 'College')
        (EmailConditions.multiple_conditions, 'Conditions')
    ]
    label_names = set(rule[1] for rule in rules)
    label_dict = EmailHandler.ensure_labels(service, label_names)
    EmailHandler.organize_emails(service, rules, label_dict, max_emails=150)
    
    print('Email organization complete!')  
    
if __name__ == '__main__':
    main()