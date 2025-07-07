# Product Management Internship Scraper

A Python-based web scraper that monitors the [jobright-ai/2025-Product-Management-Internship](https://github.com/jobright-ai/2025-Product-Management-Internship) GitHub repository for new internship listings and sends email notifications when new opportunities are discovered.

## Features

- 🔍 **Automated Monitoring**: Continuously monitors the GitHub repository for new internship listings
- 📧 **Email Notifications**: Sends HTML-formatted email alerts when new listings are found
- 🔄 **Duplicate Detection**: Tracks previously seen listings to avoid duplicate notifications
- 🔗 **Link Extraction**: Automatically extracts application links from listings
- 📊 **Structured Data**: Parses company names, positions, locations, and application links

## Prerequisites

- Python 3.6+
- Gmail account with App Password enabled
- GitHub Personal Access Token (optional, for higher rate limits)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd pm-internship-scraper
```

2. Install required dependencies:
```bash
pip install requests html2text
```

## Configuration

Set up the following environment variables:

```bash
# Gmail Configuration (Required for email notifications)
export GMAIL_USERNAME="your-gmail@gmail.com"
export GMAIL_APP_PASSWORD="your-app-password"
export RECIPIENT_EMAIL="recipient@example.com"

# GitHub Configuration (Optional, for higher API rate limits)
export GITHUB_TOKEN="your-github-token"
```

### Setting up Gmail App Password

1. Enable 2-Factor Authentication on your Gmail account
2. Go to [Google Account Settings](https://myaccount.google.com/)
3. Navigate to Security → App passwords
4. Generate a new app password for "Mail"
5. Use this password in the `GMAIL_APP_PASSWORD` environment variable

## Usage

Run the scraper:

```bash
python scraper.py
```

The scraper will:
1. Fetch the latest README from the target repository
2. Parse internship listings
3. Compare with previously saved listings
4. Send email notifications for new listings
5. Save current listings for future comparison

## Scheduling

To run the scraper automatically, you can use cron (Linux/macOS) or Task Scheduler (Windows):

### Using Cron (Linux/macOS)

```bash
# Run every hour
0 * * * * /usr/bin/python3 /path/to/scraper.py

# Run every 6 hours
0 */6 * * * /usr/bin/python3 /path/to/scraper.py
```

### Using GitHub Actions

You can also deploy this as a GitHub Action to run on a schedule. Create `.github/workflows/scraper.yml`:

```yaml
name: Internship Scraper
on:
  schedule:
    - cron: '0 */6 * * *'  # Run every 6 hours
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install requests html2text
      - name: Run scraper
        env:
          GMAIL_USERNAME: ${{ secrets.GMAIL_USERNAME }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python scraper.py
```

## File Structure

```
pm-internship-scraper/
├── scraper.py              # Main scraper script
├── previous_listings.json  # Stores previously found listings
└── README.md              # This file
```

## How It Works

1. **Fetching Data**: The scraper fetches the README.md file from the target GitHub repository
2. **Parsing**: It parses the markdown content to extract internship listings using regex patterns
3. **Comparison**: New listings are identified by comparing with previously saved data
4. **Notification**: HTML email notifications are sent for new listings
5. **Storage**: Current listings are saved to `previous_listings.json` for future comparisons

## Customization

### Targeting Different Repositories

To monitor a different repository, modify these variables in `scraper.py`:

```python
self.repo_url = "https://api.github.com/repos/your-username/your-repo"
self.raw_readme_url = "https://raw.githubusercontent.com/your-username/your-repo/master/README.md"
```

### Adjusting Parsing Logic

The scraper expects listings in this format:
```
* Company Name - Position Title - Location
```

To modify the parsing logic, update the `parse_internship_listings` method.

## Troubleshooting

### Common Issues

1. **No email notifications**: Check Gmail credentials and app password
2. **API rate limits**: Add a GitHub personal access token
3. **Parsing errors**: Verify the target repository's README format
4. **SSL/TLS errors**: Ensure your system certificates are up to date

### Debug Mode

Add print statements or logging to debug parsing issues:

```python
print(f"Parsed {len(listings)} listings")
for listing in listings:
    print(f"  - {listing['company']}: {listing['position']}")
```

## License

This project is open source and available under the [MIT License](LICENSE).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Disclaimer

This tool is for educational and personal use only. Please respect the terms of service of the repositories you're monitoring and email service providers you're using.