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
        
        lines = readme_content.split('\n')
        in_table = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for table start marker
            if 'TABLE_START' in line or (line.startswith('| Company') and 'Job Title' in line):
                in_table = True
                continue
            
            # Look for table end marker
            if 'TABLE_END' in line:
                in_table = False
                break
            
            # Skip header separator line
            if line.startswith('| -') or line.startswith('|--'):
                continue
            
            # Parse table rows when in table section
            if in_table and line.startswith('|') and line.endswith('|') and line.count('|') >= 5:
                try:
                    # Split by | and clean up
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last elements
                    
                    if len(cells) >= 5:  # Company, Job Title, Location, Work Model, Date Posted
                        company_cell = cells[0]
                        job_title_cell = cells[1]
                        location = cells[2]
                        work_model = cells[3]
                        date_posted = cells[4]
                        
                        # Extract company name and URL
                        company_info = self.extract_company_info(company_cell)
                        job_info = self.extract_job_info(job_title_cell)
                        
                        # Skip if essential info is missing
                        if not company_info['name'] or not job_info['title']:
                            continue
                        
                        # Skip separator rows with arrows (↳)
                        if company_info['name'] == '↳' or company_info['name'] == '':
                            # This is a continuation row, use previous company
                            if listings:
                                company_info['name'] = listings[-1]['company']
                            else:
                                continue
                        
                        listing = {
                            'company': company_info['name'],
                            'position': job_info['title'],
                            'location': location,
                            'work_model': work_model,
                            'date_posted': date_posted,
                            'apply_link': job_info['link'],
                            'company_url': company_info['url'],
                            'found_date': datetime.now().isoformat()
                        }
                        listings.append(listing)
                        
                except Exception as e:
                    print(f"Error parsing line: {line[:50]}... - {e}")
                    continue
        
        return listings
    
    def extract_company_info(self, company_cell: str) -> Dict[str, str]:
        """Extract company name and URL from cell like **[TikTok](https://www.tiktok.com)**"""
        import re
        
        # Remove bold formatting
        cell = company_cell.replace('**', '')
        
        # Extract markdown link [Company Name](URL)
        link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', cell)
        if link_match:
            return {
                'name': link_match.group(1).strip(),
                'url': link_match.group(2).strip()
            }
        else:
            # No link, just plain text
            return {
                'name': cell.strip(),
                'url': ''
            }
    
    def extract_job_info(self, job_cell: str) -> Dict[str, str]:
        """Extract job title and application URL from job cell"""
        import re
        
        # Remove bold formatting
        cell = job_cell.replace('**', '')
        
        # Extract markdown link [Job Title](URL)
        link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', cell)
        if link_match:
            return {
                'title': link_match.group(1).strip(),
                'link': link_match.group(2).strip()
            }
        else:
            # No link, just plain text
            return {
                'title': cell.strip(),
                'link': ''
            }
    
    def clean_cell_content(self, cell: str) -> str:
        """Clean markdown formatting from table cell content"""
        # Remove markdown links but keep the text
        import re
        # Remove [text](link) format but keep text
        cell = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cell)
        # Remove **bold** formatting
        cell = re.sub(r'\*\*([^*]+)\*\*', r'\1', cell)
        # Remove other markdown formatting
        cell = cell.replace('**', '').replace('*', '').replace('`', '')
        return cell.strip()
    
    def extract_link_from_cells(self, cells: List[str]) -> str:
        """Extract application link from table cells"""
        import re
        for cell in cells:
            # Look for markdown links
            link_match = re.search(r'\[([^\]]*)\]\(([^)]+)\)', cell)
            if link_match:
                link_text = link_match.group(1).lower()
                link_url = link_match.group(2)
                # Check if it's an application link
                if 'apply' in link_text or 'job' in link_text or link_url.startswith('http'):
                    return link_url
        return ""
    
    def parse_alternative_format(self, readme_content: str) -> List[Dict]:
        """Alternative parsing for different formats"""
        listings = []
        lines = readme_content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for lines that mention companies and positions
            if ('intern' in line.lower() and 
                ('|' in line or '-' in line) and 
                len(line) > 20 and
                not line.startswith('#')):
                
                # Try to extract company and position info
                parts = []
                if '|' in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                elif ' - ' in line:
                    parts = [p.strip() for p in line.split(' - ') if p.strip()]
                
                if len(parts) >= 2:
                    company = self.clean_cell_content(parts[0])
                    position = self.clean_cell_content(parts[1])
                    location = self.clean_cell_content(parts[2]) if len(parts) > 2 else "Not specified"
                    
                    if company and position and len(company) > 1 and len(position) > 5:
                        listing = {
                            'company': company,
                            'position': position,
                            'location': location,
                            'apply_link': self.extract_link_from_cells(parts),
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
                <div class="company">
                    {f'<a href="{listing["company_url"]}" target="_blank">{listing["company"]}</a>' if listing.get("company_url") else listing['company']}
                </div>
                <div class="position">{listing['position']}</div>
                <div class="location">📍 {listing['location']} • {listing.get('work_model', '')} • Posted: {listing.get('date_posted', '')}</div>
                {f'<a href="{listing["apply_link"]}" class="apply-btn" target="_blank">Apply Now</a>' if listing.get('apply_link') else ''}
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
            text_body += f"  Location: {listing['location']} ({listing.get('work_model', 'N/A')})\n"
            text_body += f"  Posted: {listing.get('date_posted', 'N/A')}\n"
            if listing.get('apply_link'):
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
        
        print(f"README content length: {len(readme_content)} characters")
        print("First 500 characters of README:")
        print("-" * 50)
        print(readme_content[:500])
        print("-" * 50)
        
        # Parse current listings
        current_listings = self.parse_internship_listings(readme_content)
        print(f"Found {len(current_listings)} total listings")
        
        # Debug: Show some sample listings
        if current_listings:
            print("Sample listings found:")
            for i, listing in enumerate(current_listings[:3]):  # Show first 3
                print(f"  {i+1}. {listing['company']} - {listing['position']}")
        
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