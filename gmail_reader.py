import os.path
import base64
import sqlite3
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from datetime import date
from bs4 import BeautifulSoup

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

CREDENTIALS_PATH = "credentials/credentials.json"
TOKEN_PATH = "credentials/token.json"
DB_PATH = "jobs.db"

ARCHIVE_EMAILS = True
SKIP_ONSITE = True

def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH,
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service

def parse_linkedin_subject(subject):

    # parses LinkedIn alert subject lines into individual fields

    # using regex to group alert name 1, company 2, job title 3, posted date 4. 
    # () represents a new group, then, .+? captures the text within each section
    pattern_with_alert = r'“(.+?)”:\s(.+?)\s-\s(.+?)\sposted on\s(.+)'

    # Example: “Data insights analyst”: Walgreens - Data Analytics Analyst posted on 7/3/26
    # asks regex to search the subject for that pattern
    match = re.search(pattern_with_alert, subject)

    # extract the groups if matched format
    if match:
        return {
            "alert_name": match.group(1),
            "company": match.group(2),
            "job_title": match.group(3),
            "posted_date": match.group(4),
            "raw_subject": subject
        }
    
    # Example: Systems Analyst - Business Intelligence at Griffith Foods
    # used for linkedin emails that use a simpler format
    pattern_simple = r'(.+?)\sat\s(.+)'

    match = re.search(pattern_simple, subject)

    if match:
        return {
            "alert_name": "",
            "company": match.group(2),
            "job_title": match.group(1),
            "posted_date": "",
            "raw_subject": subject
        }

    # if neither format matches, return blank fields while preserving original subject for troubleshooting
    return {
        "alert_name": "",
        "company": "",
        "job_title": "",
        "posted_date": "",
        "raw_subject": subject
    }


def extract_linkedin_job_links(payload):
    # extract individual job postings from the HTML of an email

    # empty string to hold email's HTML
    html_body = ""

    # gives the payload containing potentially nested pieces in gmail until we find text/html, then decodes
    def walk_parts(part):
        nonlocal html_body

        # if this part of the email has HTML, extract and decode
        if part.get("mimeType") == "text/html":
            data = part.get("body", {}).get("data", "")
            if data:
                # decode base64 data in HTML and add it to html_body
                decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                html_body += decoded

        # check for additional nested email parts and run on each one
        for child in part.get("parts", []):
            walk_parts(child)

    # start walking through gmail payload
    walk_parts(payload)

    # if no HTML, no jobs to extract
    if not html_body:
        return []

    # beautifulsoup takes raw HTML into objects to search for html tags, ie <a> or <p>
    soup = BeautifulSoup(html_body, "html.parser")

    # store extracted data
    job_links = []
    # track URLs so same job is not found
    seen_urls = set()

    # find every a tag in the email that contains an href link
    for tag in soup.find_all("a", href=True):
        href = tag["href"]

        if "/jobs/view/" not in href:
            continue 

        # Remove tracking/query parameters from the URL.
        # Example: linkedin.com/jobs/view/12345?trackingETC... becomes: linkedin.com/jobs/view/12345
        clean_url = href.split("?")[0]

        # skip if job URL has been processed
        if clean_url in seen_urls:
            continue

        # use classes to identify linkedin alert emails
        job_title_tag = tag.find("a", class_="font-bold")
        company_location_tag = tag.find("p", class_="text-system-gray-100")

        if not job_title_tag or not company_location_tag:
            continue

        # extract text from HTML elements
        job_title = job_title_tag.get_text(" ", strip=True)
        company_location = company_location_tag.get_text(" ", strip=True)

        # linkedin uses centered dots to separate company and location, if it's not there, skip posting
        if " · " not in company_location:
            continue

        # split left side company, right side location
        company, location = company_location.split(" · ", 1)

        # mark as processed so dupes are ignored
        seen_urls.add(clean_url)

        # add clean info to the list
        job_links.append({
            "job_title": job_title,
            "company": company.strip(),
            "location": location.strip(),
            "linkedin_url": clean_url
        })
        
    return job_links

def get_linkedin_job_alerts(max_results=50):

    # assign function connecting to gmail service as service
    service = get_gmail_service()

    # only seach emails in inbox newer than 30 days
    query = 'from:jobalerts-noreply@linkedin.com in:inbox newer_than:30d'

    # send gmail search request, max results to limit total at 50
    results = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results
    ).execute()

    # results is gmail API response, assign that to messages, if no messages return empty list
    # messages is a list of emails
    messages = results.get("messages", [])

    # stop function if no linkedin emails found
    if not messages:
        print("No LinkedIn emails found.")
        return

    print(f"Found {len(messages)} LinkedIn emails:\n")

    # store all jobs extracted from emails, jobs is all postings extracted from emails
    jobs = []
    # store email ids so they can be archived later
    processed_message_ids = []

    # process one email at a time
    for message in messages:
        msg = service.users().messages().get(
            userId="me",
            id=message["id"],
            format="full"
        ).execute()

        # get email headers, including subject
        headers = msg.get("payload", {}).get("headers", [])
        subject = ""

        # find subject header and save
        for header in headers:
            if header["name"] == "Subject":
                subject = header["value"]

        # skip linkedin emails that aren't job alerts
        if subject.startswith("Brad:"):
            continue

        # find alert name
        parsed = parse_linkedin_subject(subject)
        job_links = extract_linkedin_job_links(msg.get("payload", {}))

        # emails contain multiple job postings, combines alert name and job details
        for job_link in job_links:
            row = {
                "alert_name": parsed.get("alert_name", ""),
                "job_title": job_link["job_title"],
                "company": job_link["company"],
                "location": job_link["location"],
                "job_link": job_link["linkedin_url"]
            }
            # add to jobs list
            jobs.append(row)

        processed_message_ids.append(message["id"])

    # open connection to database
    conn = sqlite3.connect(DB_PATH)

    # track new vs skipped jobs
    new_jobs = 0
    skipped_jobs = 0
    onsite_jobs_skipped = 0

    # check whether job link already is in database
    for job in jobs:

        if SKIP_ONSITE and "on-site" in job["location"].lower():
            onsite_jobs_skipped += 1
            continue

        existing_job = conn.execute("""
            SELECT id
            FROM jobs
            WHERE job_link = ?;
        """, (job["job_link"],)).fetchone()

        # if job link exists, skip
        if existing_job:
            skipped_jobs +=1
            continue

        # insert new job data into database, manual fields (interested, applied, interview) are blank
        conn.execute("""
            INSERT INTO jobs (
                date_added,
                alert_name,
                job_title,
                company,
                location,
                job_link
            )
            VALUES (?, ?, ?, ?, ?, ?);
        """, (
            date.today().isoformat(),
            job["alert_name"],
            job["job_title"],
            job["company"],
            job["location"],
            job["job_link"]
        ))

        new_jobs +=1

    conn.execute("""
        INSERT OR IGNORE INTO companies (company)
        SELECT DISTINCT company
        FROM jobs
        WHERE company IS NOT NULL
            AND company != '';
    """)

    # save all insert operations
    conn.commit()

    # count total jobs(rows) in database
    total_jobs = conn.execute("""
        SELECT COUNT(*)
        FROM jobs;
    """).fetchone()[0]

    conn.close()

    print(f"\nNew jobs added: {new_jobs}")
    print(f"Existing jobs skipped: {skipped_jobs}")
    print(f"On-site jobs skipped: {onsite_jobs_skipped} ")
    print(f"Total jobs now: {total_jobs}")

    # archive processed emails by removing inbox label
    if ARCHIVE_EMAILS:
        for message_id in processed_message_ids:
            service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["INBOX"]}
            ).execute()

        print(f"\nArchived {len(processed_message_ids)} LinkedIn emails.")
    else:
        print("\nArchive skipped. ARCHIVE_EMAILS is set to False.")

# run only when this file is executed directly
if __name__ == "__main__":
    get_linkedin_job_alerts()
