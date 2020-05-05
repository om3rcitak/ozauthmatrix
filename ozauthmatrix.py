import argparse
import sys
import requests
import re
from terminaltables import AsciiTable

# Argument Parser
parser = argparse.ArgumentParser('ozauthmatrix', 'IDOR Finder')
parser.add_argument('-u', '--url', type=str, required=True, help='Target')
parser.add_argument('-l', '--loginurl', type=str, required=True, help='Login URL')
parser.add_argument('-s', '--successurl', type=str, required=True, help='Success URL For login')
parser.add_argument('-c', '--credentials', action='append', required=True, help='Credentials. Format: id:email:password')
args = parser.parse_args()

# Colors
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

# Validation
if len(args.credentials) < 2:
    print(FAIL + 'Required min 2 credentials' + ENDC)
    sys.exit()

# Variables
sessions = {}
urls = set()
results = []

print('')


def parse_credentials():
    for cred in args.credentials:
        creds = cred.split(':')
        sessions[creds[0]] = {
            'email': creds[1],
            'password': creds[2]
        }


def login():
    print(HEADER + '[*] Login' + ENDC)
    for k, v in sessions.items():
        response = requests.post(args.loginurl, data={'email': v['email'], 'password': v['password']}, allow_redirects=False)
        if response.headers['Location'] == args.successurl:
            print(OKGREEN + '[+] Login OK: ' + str(v) + ENDC)
            cookie = response.headers['Set-cookie'].split(';')[0]
            sessions[k]['cookie'] = {
                cookie.split('=')[0]: cookie.split('=')[1]
            }
        else:
            print(FAIL + '[-] Login Error: ' + str(v) + ENDC)
            sys.exit()
    print('')


def crawl_urls():
    print(HEADER + '[*] Crawling' + ENDC)
    for k, v in sessions.items():
        response = requests.get(args.successurl, cookies=v['cookie'])
        crawled_urls = re.findall('''<a\s+(?:[^>]*?\s+)?href="([^"]*)"''', response.content.decode('utf-8'))
        for url in crawled_urls:
            if url.startswith(args.url):
                urls.add(url)
                print(OKGREEN + '[+] Detected: ' + url + ENDC)
            else:
                print(WARNING + '[-] Detected: ' + url + ' (Out-of-scope)' + ENDC)
    print('')


def idorbaba():
    print(HEADER + '[*] IDOR Testing' + ENDC)
    for url in urls:
        row = [url]
        for k, v in sessions.items():
            response = requests.get(url, cookies=v['cookie'])
            row.append('status_code: ' + str(response.status_code) + '   content_length: ' + str(len(response.content)))
        results.append(row)
        #print(OKGREEN + '[+] Test finished for this user: ' + v['email'] + ENDC)
    print('')


def generate_table():
    print(HEADER + '[*] Results: ' + ENDC)

    head_line = ['']
    for k, v in sessions.items():
        head_line.append(str(k) + ' - ' + str(v['email']))

    table_data = [head_line]
    table_data.extend(results)

    table = AsciiTable(table_data)
    print(OKBLUE + table.table + ENDC)


parse_credentials()
login()
crawl_urls()
idorbaba()
generate_table()
