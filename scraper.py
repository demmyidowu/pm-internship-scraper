#!/usr/bin/env python3
"""
Product Management Internship Scraper
Monitors jobright-ai/2025-Product-Management-Internship repository for new listings
"""

import os
import json
import smtplib
import requests
import re
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Set
import html2text

class InternshipScraper:
    def __init__(self):
        self.repo_url = "https://api.github.com/repos/jobright-ai/2025-Product-Management-Internship"
        self.raw_readme_url = "https://raw.githubusercontent.com/jobright-ai/2025-Product-Management-Internship/master/README.md"
        self.data_file = "previous_listings.json"
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.headers = {
            'Authorization': f'token {self.github_token}' if self.github_token else None,
            'Accept': 'application/vnd.github.v3+json'
        }
        
    def fetch_readme_content(self) -> str:
        """Fetch the current README content from the repository"""
        try:
            response = requests.get(self.raw_readme_url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching README: {e}")
            return ""
    
    def parse_internship_listings(self, readme_content: str) -> List[Dict]:
        """Parse internship listings from README content"""
        listings = []
        
        # Convert markdown to text for easier parsing
        h = html2text.HTML2Text()
        h.ignore_links = False
        text_content = h.handle(readme_content)
        
        # Look for company names and positions
        # This regex pattern looks for lines that contain company names and positions
        # Format typically: "Company Name - Position Title - Location"
        pattern = r'^\*\s+(.+?)\s+-\s+(.+?)(?:\s+-\s+(.+?))?$'
        
        lines = text_content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('*') and ' - ' in line:
                # Extract company and position info
                parts = line[1:].strip().split(' - ')
                if len(parts) >= 2:
                    company = parts[0].strip()
                    position = parts[1].strip()
                    location = parts[2].strip() if len(parts) > 2 else "Not specified"
                    
                    # Look for application links in the surrounding context
                    apply_link = self.find_apply_link(line, readme_content)
                    
                    listing = {
                        'company': company,
                        'position': position,
                        'location': location,
                        'apply_link': apply_link,
                        'found_date': datetime.now().isoformat()
                    }
                    listings.append(listing)
        
        return listings
    
    def find_apply_link(self, line: str, content: str) -> str:
        """Find application link associated with a listing"""
        # Look for "Apply" links in markdown format
        apply_patterns = [
            r'\[Apply\]\((https?://[^\)]+)\)',
            r'\[apply\]\((https?://[^\)]+)\)',
            r'\[APPLY\]\((https?://[^\)]+)\)'
        ]
        
        # Check the line itself first
        for pattern in apply_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        
        # If not found in line, look in surrounding context
        lines = content.split('\n')
        for i, content_line in enumerate(lines):
            if line.strip() in content_line:
                # Check next few lines for apply link
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    for pattern in apply_patterns:
                        match = re.search(pattern, lines[j])
                        if match:
                            return match.group(1)
        
        return ""
    
    def load_previous_listings(self) -> List[Dict]:
        """Load previously found listings from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def save_listings(self, listings: List[Dict]):
        """Save current listings to file"""
        with open(self.data_file, 'w') as f:
            json.dump(listings, f, indent=2)
    
    def find_new_listings(self, current_listings: List[Dict], previous_listings: List[Dict]) -> List[Dict]:
        """Find new listings by comparing current with previous"""
        # Create sets of unique identifiers for comparison
        previous_ids = {
            f"{listing['company']}||{listing['position']}"
            for listing in previous_listings
        }
        
        new_listings = []
        for listing in current_listings:
            listing_id = f"{listing['company']}||{listing['position']}"
            if listing_id not in previous_ids:
                new_listings.append(listing)
        
        return new_listings
    
    def send_email_notification(self, new_listings: List[Dict]):
        """Send email notification about new listings"""
        if not new_listings:
            return
        
        gmail_username = os.getenv('GMAIL_USERNAME')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        recipient_email = os.getenv('RECIPIENT_EMAIL')
        
        if not all([gmail_username, gmail_password, recipient_email]):
            print("Email credentials not configured")
            return
        
        # Create email content
        subject = f"[Internship Alert] {len(new_listings)} new listing(s)"
        
        # Create HTML email body
        html_body = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; }
                .listing { margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .company { font-weight: bold; font-size: 16px; color: #333; }
                .position { font-size: 14px; color: #666; margin: 5px 0; }
                .location { font-size: 12px; color: #888; }
                .apply-btn { 
                    background-color: #007bff; 
                    color: white; 
                    padding: 8px 16px; 
                    text-decoration: none; 
                    border-radius: 3px; 
                    display: inline-block;
                    margin-top: 10px;
                }
                .footer { margin-top: 20px; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚀 New Product Management Internship Listings</h2>
                <p>Found {count} new internship opportunity(ies)!</p>
            </div>
        """.format(count=len(new_listings))
        
        for listing in new_listings:
            html_body += f"""
            <div class="listing">
                <div class="company">{listing['company']}</div>
                <div class="position">{listing['position']}</div>
                <div class="location">📍 {listing['location']}</div>
                {f'<a href="{listing["apply_link"]}" class="apply-btn">Apply</a>' if listing['apply_link'] else ''}
            </div>
            """
        
        html_body += """
            <div class="footer">
                <p>Source: <a href="https://github.com/jobright-ai/2025-Product-Management-Internship">GitHub Repository</a></p>
                <p>This alert was generated automatically.</p>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        text_body = f"New Product Management Internship Listings ({len(new_listings)} found):\n\n"
        for listing in new_listings:
            text_body += f"• {listing['company']} - {listing['position']}\n"
            text_body += f"  Location: {listing['location']}\n"
            if listing['apply_link']:
                text_body += f"  Apply: {listing['apply_link']}\n"
            text_body += "\n"
        
        # Send email
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = gmail_username
            msg['To'] = recipient_email
            
            # Add text and HTML parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send via Gmail SMTP
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(gmail_username, gmail_password)
                server.send_message(msg)
            
            print(f"Email sent successfully! Found {len(new_listings)} new listings.")
            
        except Exception as e:
            print(f"Error sending email: {e}")
    
    def run(self):
        """Main execution function"""
        print(f"Starting scraper at {datetime.now()}")
        
        # Fetch current README content
        readme_content = self.fetch_readme_content()
        if not readme_content:
            print("Failed to fetch README content")
            return
        
        # Parse current listings
        current_listings = self.parse_internship_listings(readme_content)
        print(f"Found {len(current_listings)} total listings")
        
        # Load previous listings
        previous_listings = self.load_previous_listings()
        print(f"Previously had {len(previous_listings)} listings")
        
        # Find new listings
        new_listings = self.find_new_listings(current_listings, previous_listings)
        
        if new_listings:
            print(f"Found {len(new_listings)} new listings!")
            for listing in new_listings:
                print(f"  - {listing['company']}: {listing['position']}")
            
            # Send email notification
            self.send_email_notification(new_listings)
        else:
            print("No new listings found")
        
        # Save current listings
        self.save_listings(current_listings)
        print("Scraper completed successfully")

if __name__ == "__main__":
    scraper = InternshipScraper()
    scraper.run()