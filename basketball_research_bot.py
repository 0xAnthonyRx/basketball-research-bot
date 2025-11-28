#!/usr/bin/env python3
"""
Basketball Research Automation Bot
Randomly samples basketball articles from 70 target journals.
Runs: Tuesdays & Thursdays at 11 AM EST
"""

import os
import json
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import time
import random

# ============================================================================
# CONFIGURATION
# ============================================================================

# Email Configuration
SENDER_EMAIL = "madutony20@gmail.com"
RECIPIENT_EMAIL = "rockthedoc94@gmail.com"

# API Keys
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

# Gmail API Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Target Journals (70 reputable sources)
TARGET_JOURNALS = [
    "J Bone Joint Surg Am",
    "Am J Sports Med",
    "J Bone Miner Res",
    "Br J Sports Med",
    "Bone Joint J",
    "Clin Orthop Relat Res",
    "Sports Med",
    "Osteoarthritis Cartilage",
    "Spine J",
    "Spine",
    "J Arthroplasty",
    "Bone",
    "Arthroscopy",
    "J Shoulder Elbow Surg",
    "Knee Surg Sports Traumatol Arthrosc",
    "J Am Acad Orthop Surg",
    "Eur Spine J",
    "J Orthop Res",
    "Int Orthop",
    "Acta Orthop",
    "Sports Health",
    "EFORT Open Rev",
    "J Orthop Surg Res",
    "Injury",
    "Orthop J Sports Med",
    "Foot Ankle Int",
    "BMC Musculoskelet Disord",
    "Arch Orthop Trauma Surg",
    "J Hand Surg Am",
    "World J Orthop",
    "Orthop Traumatol Surg Res",
    "Musculoskelet Sci Pract",
    "Hand",
    "J Back Musculoskelet Rehabil",
    "J Pediatr Orthop",
    "Bone Res",
    "J Orthop Sports Phys Ther",
    "Scand J Med Sci Sports",
    "Phys Ther Sport",
    "Curr Rev Musculoskelet Med",
    "Gait Posture",
    "J Biomech",
    "J Athl Train",
    "J Exp Orthop",
    "Clin Biomech",
    "J Sport Rehabil",
    "Front Surg",
    "Orthop Rev",
    "Tech Orthop",
    "Int J Surg",
    "Med Sci Sports Exerc",
    "Sports Med Health Sci",
    "J Sports Sci Med",
    "J Sports Med Allied Health Sci",
    "Int J Sports Phys Ther",
    "Res Sports Med",
    "J Sci Med Sport"
]

# Full journal names for better searching
JOURNAL_FULL_NAMES = [
    "Journal of Bone and Joint Surgery American",
    "American Journal of Sports Medicine",
    "Journal of Bone and Mineral Research",
    "British Journal of Sports Medicine",
    "Bone Joint Journal",
    "Clinical Orthopaedics and Related Research",
    "Sports Medicine",
    "Osteoarthritis and Cartilage",
    "Spine Journal",
    "Spine",
    "Journal of Arthroplasty",
    "Bone",
    "Arthroscopy",
    "Journal of Shoulder and Elbow Surgery",
    "Knee Surgery Sports Traumatology Arthroscopy",
    "Journal of the American Academy of Orthopaedic Surgeons",
    "European Spine Journal",
    "Journal of Orthopaedic Research",
    "International Orthopaedics",
    "Acta Orthopaedica",
    "Sports Health",
    "EFORT Open Reviews",
    "Journal of Orthopaedic Surgery and Research",
    "Injury",
    "Orthopaedic Journal of Sports Medicine",
    "Foot and Ankle International",
    "BMC Musculoskeletal Disorders",
    "Archives of Orthopaedic and Trauma Surgery",
    "Journal of Hand Surgery American",
    "World Journal of Orthopedics",
    "Orthopaedics Traumatology Surgery Research",
    "Musculoskeletal Science and Practice",
    "Hand",
    "Journal of Back and Musculoskeletal Rehabilitation",
    "Journal of Pediatric Orthopaedics",
    "Bone Research",
    "Journal of Orthopaedic Sports Physical Therapy",
    "Scandinavian Journal of Medicine Science in Sports",
    "Physical Therapy in Sport",
    "Current Reviews in Musculoskeletal Medicine",
    "Gait Posture",
    "Journal of Biomechanics",
    "Journal of Athletic Training",
    "Journal of Experimental Orthopaedics",
    "Clinical Biomechanics",
    "Journal of Sport Rehabilitation",
    "Frontiers in Surgery Orthopedic Surgery",
    "Orthopedic Reviews",
    "Techniques in Orthopaedics",
    "International Journal of Surgery",
    "Medicine Science in Sports Exercise",
    "Sports Medicine and Health Science",
    "Journal of Sports Science and Medicine",
    "Journal of Sports Medicine and Allied Health Sciences",
    "International Journal of Sports Physical Therapy",
    "Research in Sports Medicine",
    "Journal of Science and Medicine in Sport"
]

# ============================================================================
# GMAIL AUTHENTICATION
# ============================================================================

def authenticate_gmail():
    """Authenticate with Gmail API using OAuth2."""
    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)

# ============================================================================
# SEARCH FUNCTIONS - SAMPLE FROM EACH JOURNAL
# ============================================================================

def search_journal_basketball_articles(journal_name, min_articles=5, max_articles=15):
    """
    Search for basketball articles from a specific journal.
    Returns random sample of 5-15 articles.
    """
    # Random number of articles to fetch from this journal
    target_count = random.randint(min_articles, max_articles)
    
    print(f"  📖 {journal_name}: targeting {target_count} articles...")
    
    # Try multiple search strategies
    articles = []
    
    # Strategy 1: PubMed search
    pubmed_articles = search_pubmed_by_journal(journal_name, max_results=50)
    articles.extend(pubmed_articles)
    
    # Strategy 2: Europe PMC search (if PubMed didn't get enough)
    if len(articles) < target_count:
        europepmc_articles = search_europepmc_by_journal(journal_name, max_results=50)
        articles.extend(europepmc_articles)
    
    # Strategy 3: CrossRef search
    if len(articles) < target_count:
        crossref_articles = search_crossref_by_journal(journal_name, max_results=50)
        articles.extend(crossref_articles)
    
    # Remove duplicates
    articles = remove_duplicates(articles)
    
    # Randomly sample
    if len(articles) > target_count:
        articles = random.sample(articles, target_count)
    
    print(f"     ✅ Found {len(articles)} articles")
    
    return articles


def search_pubmed_by_journal(journal_name, max_results=50):
    """Search PubMed for basketball articles in specific journal."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    # Build query: basketball AND journal
    search_query = f'basketball AND "{journal_name}"[Journal]'
    
    # Search for IDs
    search_url = f"{base_url}esearch.fcgi"
    search_params = {
        'db': 'pubmed',
        'term': search_query,
        'retmax': max_results,
        'retmode': 'json',
        'sort': 'relevance'
    }
    
    try:
        search_response = requests.get(search_url, params=search_params, timeout=30)
        search_data = search_response.json()
        
        id_list = search_data.get('esearchresult', {}).get('idlist', [])
        
        if not id_list:
            return []
        
        # Fetch article details
        fetch_url = f"{base_url}efetch.fcgi"
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(id_list),
            'retmode': 'xml'
        }
        
        fetch_response = requests.get(fetch_url, params=fetch_params, timeout=30)
        articles = parse_pubmed_xml(fetch_response.text)
        
        return articles
        
    except Exception as e:
        return []


def search_europepmc_by_journal(journal_name, max_results=50):
    """Search Europe PMC for basketball articles in specific journal."""
    base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    params = {
        'query': f'basketball AND JOURNAL:"{journal_name}"',
        'format': 'json',
        'pageSize': max_results,
        'resultType': 'core'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('resultList', {}).get('result', [])
            
            articles = []
            for result in results:
                article = {
                    'pmid': result.get('pmid', result.get('id', 'N/A')),
                    'title': result.get('title', 'No title'),
                    'abstract': result.get('abstractText', 'No abstract available'),
                    'journal': result.get('journalTitle', journal_name),
                    'authors': format_authors(result.get('authorString', 'Unknown')),
                    'pub_date': result.get('firstPublicationDate', 'N/A'),
                    'url': f"https://europepmc.org/article/MED/{result.get('pmid', result.get('id', ''))}"
                }
                articles.append(article)
            
            return articles
            
    except Exception as e:
        return []
    
    return []


def search_crossref_by_journal(journal_name, max_results=50):
    """Search CrossRef for basketball articles in specific journal."""
    base_url = "https://api.crossref.org/works"
    
    params = {
        'query': 'basketball',
        'query.container-title': journal_name,
        'rows': max_results,
        'select': 'DOI,title,abstract,container-title,author,published'
    }
    
    headers = {
        'User-Agent': 'BasketballResearchBot/1.0 (mailto:madutony20@gmail.com)'
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('message', {}).get('items', [])
            
            articles = []
            for result in results:
                title = ' '.join(result.get('title', ['']))
                abstract = result.get('abstract', 'No abstract available')
                
                # Format authors
                authors_list = result.get('author', [])
                authors = ', '.join([
                    f"{a.get('given', '')} {a.get('family', '')}"
                    for a in authors_list[:3]
                ])
                if len(authors_list) > 3:
                    authors += ' et al.'
                
                # Get publication date
                pub_date_parts = result.get('published', {}).get('date-parts', [[]])
                pub_date = '-'.join(map(str, pub_date_parts[0])) if pub_date_parts else 'N/A'
                
                article = {
                    'pmid': result.get('DOI', 'N/A'),
                    'title': title,
                    'abstract': abstract,
                    'journal': ' '.join(result.get('container-title', [journal_name])),
                    'authors': authors if authors else 'Unknown',
                    'pub_date': pub_date,
                    'url': f"https://doi.org/{result.get('DOI', '')}"
                }
                articles.append(article)
            
            return articles
            
    except Exception as e:
        return []
    
    return []


def format_authors(author_string):
    """Helper function to format author strings."""
    if not author_string or author_string == 'Unknown':
        return 'Unknown'
    
    authors = author_string.replace(';', ',').split(',')
    authors = [a.strip() for a in authors if a.strip()]
    
    if len(authors) > 3:
        return ', '.join(authors[:3]) + ' et al.'
    return ', '.join(authors)


def parse_pubmed_xml(xml_text):
    """Parse PubMed XML response into article dictionaries."""
    from xml.etree import ElementTree as ET
    
    articles = []
    
    try:
        root = ET.fromstring(xml_text)
        
        for article_elem in root.findall('.//PubmedArticle'):
            try:
                pmid_elem = article_elem.find('.//PMID')
                pmid = pmid_elem.text if pmid_elem is not None else 'N/A'
                
                title_elem = article_elem.find('.//ArticleTitle')
                title = title_elem.text if title_elem is not None else 'No title'
                
                abstract_parts = article_elem.findall('.//AbstractText')
                abstract = ' '.join([part.text for part in abstract_parts if part.text])
                if not abstract:
                    abstract = 'No abstract available'
                
                journal_elem = article_elem.find('.//Journal/Title')
                journal = journal_elem.text if journal_elem is not None else 'Unknown Journal'
                
                authors = []
                for author_elem in article_elem.findall('.//Author'):
                    lastname = author_elem.find('LastName')
                    forename = author_elem.find('ForeName')
                    if lastname is not None:
                        name = lastname.text
                        if forename is not None:
                            name = f"{forename.text} {name}"
                        authors.append(name)
                
                authors_str = ', '.join(authors[:3])
                if len(authors) > 3:
                    authors_str += ' et al.'
                
                pub_date_elem = article_elem.find('.//PubDate')
                pub_year = pub_date_elem.find('Year')
                pub_month = pub_date_elem.find('Month')
                
                pub_date = ''
                if pub_year is not None:
                    pub_date = pub_year.text
                    if pub_month is not None:
                        pub_date = f"{pub_month.text} {pub_date}"
                
                article = {
                    'pmid': pmid,
                    'title': title,
                    'abstract': abstract,
                    'journal': journal,
                    'authors': authors_str if authors_str else 'Unknown',
                    'pub_date': pub_date,
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                }
                
                articles.append(article)
                
            except Exception as e:
                continue
        
    except Exception as e:
        pass
    
    return articles


def remove_duplicates(articles):
    """Remove duplicate articles based on title similarity."""
    if not articles:
        return []
    
    unique = []
    seen_titles = []
    
    for article in articles:
        title = article['title'].lower().strip()
        
        is_duplicate = False
        for seen_title in seen_titles:
            if title == seen_title or (
                len(title) > 20 and 
                title[:50] == seen_title[:50]
            ):
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique.append(article)
            seen_titles.append(title)
    
    return unique


def search_all_journals(journals_to_sample=None, min_per_journal=5, max_per_journal=15):
    """
    Search basketball articles from all target journals.
    Randomly samples articles from each journal.
    """
    print("=" * 70)
    print("🔍 SAMPLING BASKETBALL ARTICLES FROM TARGET JOURNALS")
    print("=" * 70)
    print(f"Strategy: {min_per_journal}-{max_per_journal} random articles per journal")
    print(f"Total journals: {len(JOURNAL_FULL_NAMES)}")
    print()
    
    # Randomly select journals to search if not specified
    if journals_to_sample is None:
        # Sample 15-25 random journals each run for variety
        num_journals = random.randint(15, 25)
        journals_to_search = random.sample(JOURNAL_FULL_NAMES, min(num_journals, len(JOURNAL_FULL_NAMES)))
    else:
        journals_to_search = journals_to_sample
    
    print(f"📚 Sampling from {len(journals_to_search)} journals this run:")
    print()
    
    all_articles = []
    
    for i, journal in enumerate(journals_to_search, 1):
        print(f"[{i}/{len(journals_to_search)}] {journal}")
        
        articles = search_journal_basketball_articles(
            journal, 
            min_articles=min_per_journal,
            max_articles=max_per_journal
        )
        
        all_articles.extend(articles)
        
        # Be nice to APIs
        time.sleep(2)
    
    print()
    print("=" * 70)
    print(f"📊 Total articles collected: {len(all_articles)}")
    
    # Final deduplication
    unique_articles = remove_duplicates(all_articles)
    print(f"📊 Unique articles after deduplication: {len(unique_articles)}")
    
    # Randomly select final set for email (max 20 articles per email)
    if len(unique_articles) > 10:
        final_articles = random.sample(unique_articles, 10)
        print(f"📊 Randomly selected {len(final_articles)} for this digest")
    else:
        final_articles = unique_articles
    
    print("=" * 70)
    
    return final_articles

# ============================================================================
# AI SUMMARY GENERATION (GROQ)
# ============================================================================

def generate_summary(article, max_retries=3):
    """Generate plain-language summary using Groq API (FREE)."""
    groq_key = os.environ.get('GROQ_API_KEY', '')
    
    if not groq_key:
        print("   ⚠️  No GROQ_API_KEY found, using fallback")
        words = article['abstract'].split()[:150]
        return ' '.join(words) + '...'
    
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Explain this basketball research in simple terms (3-4 sentences):

Title: {article['title']}
Abstract: {article['abstract'][:2000]}

Write a clear, plain-language summary that anyone can understand. Avoid medical jargon:"""
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a medical research translator who explains complex studies in simple terms."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 350,
        "temperature": 0.3
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                summary = result['choices'][0]['message']['content'].strip()
                
                if len(summary) > 30:
                    print(f"   ✅ Summary generated!")
                    return summary
                    
            elif response.status_code == 429:
                print(f"   ⏳ Rate limited, waiting...")
                time.sleep(10)
                continue
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5)
    
    # Fallback
    words = article['abstract'].split()[:150]
    return ' '.join(words) + '...'

# ============================================================================
# EMAIL GENERATION
# ============================================================================

def generate_html_email(articles):
    """Generate beautiful HTML email with articles and summaries."""
    
    if not articles:
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #FF6600;">🏀 Basketball Research Digest</h1>
            <p style="color: #666; font-size: 14px;">{datetime.now().strftime('%B %d, %Y')}</p>
            <div style="background-color: #FFF3CD; border-left: 4px solid #FFC107; padding: 15px; margin: 20px 0;">
                <p><strong>No articles found this time.</strong></p>
                <p>Check back next time for the latest basketball research!</p>
            </div>
        </body>
        </html>
        """
        return html
    
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                background: linear-gradient(135deg, #FF6600 0%, #FF8C00 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 32px;
            }}
            .article {{
                background-color: white;
                border-radius: 8px;
                padding: 25px;
                margin-bottom: 25px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .article-title {{
                color: #2C3E50;
                font-size: 22px;
                font-weight: bold;
                margin-bottom: 10px;
                line-height: 1.4;
            }}
            .article-meta {{
                color: #7F8C8D;
                font-size: 14px;
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 2px solid #ECF0F1;
            }}
            .journal {{
                color: #FF6600;
                font-weight: bold;
            }}
            .summary-label {{
                background-color: #3498DB;
                color: white;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                display: inline-block;
                margin-bottom: 10px;
            }}
            .summary {{
                color: #34495E;
                line-height: 1.8;
                font-size: 16px;
                margin-bottom: 15px;
            }}
            .abstract-label {{
                background-color: #95A5A6;
                color: white;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                display: inline-block;
                margin-bottom: 10px;
            }}
            .abstract {{
                color: #5D6D7E;
                line-height: 1.6;
                font-size: 14px;
                background-color: #F8F9FA;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 15px;
            }}
            .read-more {{
                display: inline-block;
                background-color: #FF6600;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                color: #7F8C8D;
                font-size: 12px;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #BDC3C7;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏀 Basketball Research Digest</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px;">{datetime.now().strftime('%B %d, %Y')}</p>
            <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">{len(articles)} Curated Article{'s' if len(articles) != 1 else ''}</p>
        </div>
    """
    
    for i, article in enumerate(articles, 1):
        abstract_preview = article['abstract'][:500] if len(article['abstract']) > 500 else article['abstract']
        if len(article['abstract']) > 500:
            abstract_preview += '...'
        
        html += f"""
        <div class="article">
            <div class="article-title">{i}. {article['title']}</div>
            <div class="article-meta">
                <span class="journal">{article['journal']}</span><br>
                <strong>Authors:</strong> {article['authors']}<br>
                <strong>Published:</strong> {article['pub_date']}
                {f"({article['pub_date'].split('-')[0]})" if '-' in article['pub_date'] else ''}
            </div>
            
            <span class="summary-label">📝 PLAIN LANGUAGE SUMMARY</span>
            <div class="summary">{article.get('summary', 'Summary not available')}</div>
            
            <span class="abstract-label">🔬 TECHNICAL ABSTRACT</span>
            <div class="abstract">{abstract_preview}</div>
            
            <a href="{article['url']}" class="read-more" target="_blank">Read Full Article →</a>
        </div>
        """
    
    html += f"""
        <div class="footer">
            <p><strong>Basketball Research Automation Bot</strong><br>
            Randomly curated from 70 top journals</p>
            <p style="margin-top: 10px; font-size: 11px;">
            Delivered every Tuesday and Thursday at 11 AM EST</p>
        </div>
    </body>
    </html>
    """
    
    return html

# ============================================================================
# EMAIL SENDING
# ============================================================================

def send_email(service, subject, html_content):
    """Send email via Gmail API."""
    try:
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = SENDER_EMAIL
        message['To'] = RECIPIENT_EMAIL
        
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"✅ Email sent successfully! Message ID: {send_message['id']}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    print("=" * 70)
    print("🏀 BASKETBALL RESEARCH AUTOMATION BOT")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Sample articles from journals
    articles = search_all_journals(min_per_journal=5, max_per_journal=10)
    
    if not articles:
        print("\n⚠️  No articles found. Sending notification email...")
    
    # Step 2: Generate summaries
    print(f"\n📝 Generating AI summaries for {len(articles)} articles...")
    for i, article in enumerate(articles, 1):
        print(f"   [{i}/{len(articles)}] {article['title'][:60]}...")
        article['summary'] = generate_summary(article)
        time.sleep(2)
    
    # Step 3: Generate email
    print("\n📧 Generating email...")
    subject = f"🏀 Basketball Research Digest - {datetime.now().strftime('%B %d, %Y')} ({len(articles)} Articles)"
    html_email = generate_html_email(articles)
    
    # Step 4: Authenticate Gmail
    print("\n🔐 Authenticating with Gmail...")
    gmail_service = authenticate_gmail()
    
    # Step 5: Send email
    print(f"\n📬 Sending email to {RECIPIENT_EMAIL}...")
    success = send_email(gmail_service, subject, html_email)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ SUCCESS! Email delivered successfully.")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ FAILED! Email could not be delivered.")
        print("=" * 70)
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
