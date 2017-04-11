#!/usr/bin/env python

import httplib2
import os
import sys
import base64

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import discovery, errors
from apiclient import http
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from jinja2 import Environment, FileSystemLoader
import datetime
import yaml
import argparse


def _createargumentparser():

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--config_file', default='config.yaml',
                        help='Weekly report configuration file.')
    parser.add_argument('--profile', default=None,
                        help='Name of the profile to run defined in the configuration file.')
    parser.add_argument('--year', default=datetime.datetime.now().strftime("%Y"),
                        help='Year the weekly report is in.')
    parser.add_argument('--week', default=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%W"),
                        help='Week number of report.')
    parser.add_argument('--all_reports', default=False,
                        action='store_true', help='Generate all reports.')
    return parser

argparser = _createargumentparser()

try:
    flags = argparse.ArgumentParser(parents=[argparser, tools.argparser]).parse_args()
except:
    flags = None
    raise

try:
    with open('config.yaml', 'r') as yamlfile:
        cfg = yaml.load(yamlfile)
except:
    raise

if not flags.profile:
    print('No profile selected. Select a profile using --profile')
    sys.exit(1)

# Set Profile
PROFILE = flags.profile

# Load Profiles
PROFILES = cfg.get('profiles', None)

if not PROFILES or len(PROFILES) < 1:
    print('No profiles defined in configuration. Please add a profiles section to the configuration.')
    sys.exit(1)

print('Loaded profiles:')
for profile in PROFILES:
    print('  {0}'.format(profile))

if PROFILE not in PROFILES:
    print('Profile: "{0}" not in configuration.'.format(PROFILE))
    sys.exit(1)

# TODO: Pull order from spreadsheet. This should be done per week not globally.
REPORTS_ORDER = cfg.get('reports', [])

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/weekly-report.json
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.appdata',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    ]
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Weekly Report Script'
REPORTS = {}


def report_filter(year=None, week=None):
    if flags.all_reports:
        return True
    if year == flags.year and week == flags.week:
        return True
    return False


def is_bullet_item(line=''):
    return line.startswith('- ')


def is_number_item(line=''):
    return line.startswith('# ')

# Load jinja template
PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, 'templates')),
    trim_blocks=False)
TEMPLATE_ENVIRONMENT.filters['isBulletItem'] = is_bullet_item
TEMPLATE_ENVIRONMENT.filters['isNumberItem'] = is_number_item
template = TEMPLATE_ENVIRONMENT.get_template('report.tpl')


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'weekly-report.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)

        # Needed only for compatibility with Python 2.6
        else:
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def main():
    print("Running profile: {0}".format(PROFILE))
    # Setup auth
    credentials = get_credentials()
    http_auth = credentials.authorize(httplib2.Http())

    # Google sheets
    sheet_discovery_url = ('https://sheets.googleapis.com/$discovery/rest?' 'version=v4')
    sheet_service = discovery.build('sheets', 'v4', http=http_auth, discoveryServiceUrl=sheet_discovery_url)

    spreadsheet_id = PROFILES[PROFILE]['spreadsheet']
    range_name = 'Sheet1!A2:F'
    result = sheet_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])

    # Google docs
    file_service = discovery.build('drive', 'v3', http=http_auth)
    email_service = discovery.build('gmail', 'v1', http=http_auth)

    folder_id = PROFILES[PROFILE]['folder']

    if not values:
        print('No data found.')
    else:
        # For each row
        for row in values:
            # If length is 6, then it contains rollup data
            if len(row) == 6 and report_filter(year=row[0], week=row[1]):
                # Add the year if it is not already in the REPORTS dictionary
                if row[0] not in REPORTS:
                    REPORTS[row[0]] = {}
                # Add the week if it is not already in the year
                if row[1] not in REPORTS[row[0]]:
                    REPORTS[row[0]][row[1]] = {}
                # Add the Project if it's not in the week
                if row[3] not in REPORTS[row[0]][row[1]]:
                    REPORTS[row[0]][row[1]][row[3]] = []
                # Add the rollup item to the Project
                for item in row[5].split('\n'):
                    REPORTS[row[0]][row[1]][row[3]].append(item)
        result = []
        page_token = None
        while True:
            try:
                param = {
                    'q': "'{0}' in parents".format(folder_id),
                    'fields': 'files',
                    'spaces': 'drive',
                }
                if page_token:
                    param['pageToken'] = page_token
                files = file_service.files().list(**param).execute()
                result.extend(files['files'])
                page_token = files.get('nextPageToken')
                if not page_token:
                    break
            except errors.HttpError, error:
                print 'An error occurred: %s' % error
                break
        existing_files = {}
        for name in result:
            doc_name = name.get('name')
            doc_info = name
            if doc_name not in existing_files:
                if not doc_info.get('trashed'):
                    existing_files[doc_name] = doc_info

        for year in REPORTS:
            for week in REPORTS[year]:
                weekdate = '{0}-W{1}'.format(year, week)
                start = datetime.datetime.strptime(weekdate + '-0', "%Y-W%W-%w") - datetime.timedelta(days=7)
                end = datetime.datetime.strptime(weekdate + '-0', "%Y-W%W-%w")
                week_of = '{0} - {1}'.format(
                    start.strftime("%Y-%m-%d"),
                    end.strftime("%Y-%m-%d"),
                )
                reports = REPORTS[year][week]
                reports_ordered = []
                for key in REPORTS_ORDER:
                    p_report = reports.pop(key, None)
                    if p_report:
                        reports_ordered.append({key: p_report})
                for k, v in reports.iteritems():
                    reports_ordered.append({k: v})

                context = {
                    'week_of': week_of,
                    'reports': reports_ordered,
                    'link': None,
                }

                # file_name = ''.join(week_of.split())
                file_name = week_of
                if file_name not in existing_files:

                    shortcut_metadata = {
                        'name': file_name,
                        'parents': [folder_id],
                        'mimeType': 'application/vnd.google-apps.document',
                    }
                    document = ''
                    try:
                        document = TEMPLATE_ENVIRONMENT.get_template(template).render(context)
                    except Exception as e:
                        print('Failed to render doc jinja: {0}', e)
                        pass

                    document_media = http.MediaInMemoryUpload(document, 'text/html')
                    file_created = file_service.files().create(body=shortcut_metadata, media_body=document_media)\
                        .execute()
                    print('Created file {0}'.format(file_name))
                    context['link'] = file_created['id']

                    email_document = ''
                    try:
                        email_document = TEMPLATE_ENVIRONMENT.get_template(template).render(context)
                    except Exception as e:
                        print('Failed to render email jinja: {0}', e)
                        pass

                    msg = MIMEMultipart()
                    msg['Subject'] = 'Infrastructure: Week of {0}'.format(file_name)
                    msg['From'] = PROFILES[PROFILE]['from']
                    msg['To'] = PROFILES[PROFILE].get('to', '')
                    msg['Cc'] = PROFILES[PROFILE].get('cc', '')
                    msg['Bcc'] = PROFILES[PROFILE].get('bcc', '')

                    part1 = MIMEText(email_document, 'html', 'UTF-8')
                    msg.attach(part1)

                    final_msg = {'raw': base64.urlsafe_b64encode(msg.as_string())}
                    message = (email_service.users().messages().send(userId='me', body=final_msg).execute())
                    print('Sent email message id: {0}'.format(message['id']))

                else:
                    print('File {0} exists. Skipping...'.format(file_name))

if __name__ == '__main__':
    main()