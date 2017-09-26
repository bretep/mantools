#!/usr/bin/env python
import StringIO
import io
import pprint
import urllib

import httplib2
import os
import sys
import base64
import email

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
import markdown
import BeautifulSoup
import html2text


def _create_argument_parser():

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
    parser.add_argument('--get_reports', default=False,
                        action='store_true', help='Get reports will display all undread emails in a gmail label.')
    parser.add_argument('--skip_email', default=False,
                        action='store_true', help='Skip sesnding the email.')
    return parser

argument_parser = _create_argument_parser()

try:
    flags = argparse.ArgumentParser(parents=[argument_parser, tools.argparser]).parse_args()
except:
    flags = None
    raise

try:
    with open(flags.config_file, 'r') as yaml_file:
        cfg = yaml.load(yaml_file)
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
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.appdata',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'https://www.googleapis.com/auth/admin.directory.user',
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


def is_white_space(line=''):
    return line.startswith(' ') or line.startswith('#') or line.startswith('[')


def is_alt_text(line=''):
    return line.startswith('!') or not line


def is_number_item(line=''):
    return line.startswith('# ')

# Load jinja template
PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, 'templates')),
    trim_blocks=False)
TEMPLATE_ENVIRONMENT.filters['isBulletItem'] = is_bullet_item
TEMPLATE_ENVIRONMENT.filters['isWhiteSpace'] = is_white_space
TEMPLATE_ENVIRONMENT.filters['isNumberItem'] = is_number_item
TEMPLATE_ENVIRONMENT.filters['isAltText'] = is_alt_text
md_template = TEMPLATE_ENVIRONMENT.get_template('report_md.tpl')
html_template = TEMPLATE_ENVIRONMENT.get_template('report_html.tpl')


def get_credentials(cred_scope, file_name):
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
                                   file_name)

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, cred_scope)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)

        # Needed only for compatibility with Python 2.6
        else:
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_files_in_folder(file_service, folder_id):
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

    return existing_files


def download_file_as_base64(file_service, image_files, file_name):
    file_id = image_files[file_name].get('id')
    if not file_id:
        return None
    test_req = file_service.files().get_media(fileId=file_id)
    output = StringIO.StringIO()
    media_request = http.MediaIoBaseDownload(output, test_req)
    while True:
        try:
            download_progress, done = media_request.next_chunk()
        except errors.HttpError, error:
            print 'An error occurred: %s' % error
            return None
        if download_progress:
            print 'Download Progress [{0}]: {1:d}%'.format(file_name, int(download_progress.progress() * 100))
        if done:
            print 'Download Complete'
            break

    contents = output.getvalue()
    output.close()
    return base64.b64encode(contents)


def filter_img_tags(file_service, image_files, image_store, document, image_alt_text=''):
    soup = BeautifulSoup.BeautifulSoup(document)

    for img in soup.findAll('img'):
        image_name = img['src']
        if image_name not in image_files:
            continue

        if int(image_files[image_name].get('quotaBytesUsed')) > 69000:
            if not image_files[image_name].get('image_size_override', False):
                image_size_override = raw_input('''
{0} is {1} bytes: The size of this image is larger than 69000 bytes.
This image will clobber the gmail web/phone client with base64 encoding.
Would you like to continue [N/y]? '''.format(image_name, image_files[image_name].get('quotaBytesUsed')))

                print(image_size_override.lower())
                if image_size_override.lower() in ['yes', 'y']:
                    image_files[image_name]['image_size_override'] = True
                else:
                    print('Exiting...')
                    exit(1)

        if image_name not in image_store:
            try:
                b64img = download_file_as_base64(file_service, image_files, image_name)
                image_store[image_name] = {
                    'mimeType': image_files[image_name].get('mimeType'),
                    'base64': b64img,
                }
            except:
                continue

        img['src'] = 'data:{mimeType};base64,{base64}'.format(**image_store[image_name])
        if not img['alt']:
            img['alt'] = image_alt_text

    return soup


def main():
    print("Running profile: {0}".format(PROFILE))
    # Setup auth
    credentials = get_credentials(SCOPES,'weekly-report.json')
    http_auth = credentials.authorize(httplib2.Http())

    # Setup email read auth
    # Must do this because you can't search with a metadata scope in email
    # email_credentials = get_credentials(EMAIL_SCOPES,'weekly-report-email.json')
    # email_http_auth = email_credentials.authorize(httplib2.Http())

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

    # User information
    user_service = discovery.build('admin', 'directory_v1', http=http_auth)

    if flags.get_reports:
        label_response = email_service.users().labels().list(userId='me').execute()
        labels = label_response['labels']
        label_id = None
        for label in labels:
            if label.get('name') == '0 - Weekly Status':
                label_id = label.get('id')

        msg_list_response = email_service.users().messages().list(userId='me',
                                                                  q='is:unread',
                                                                  labelIds=label_id).execute()

        messages = []
        if 'messages' in msg_list_response:
            messages.extend(msg_list_response['messages'])

            while 'nextPageToken' in msg_list_response:
                msg_page_token = msg_list_response['nextPageToken']
                msg_list_response = email_service.users().messages().list(userId='me',
                                                                          labelIds=label_id,
                                                                          q='is:unread',
                                                                          pageToken=msg_page_token).execute()
                messages.extend(msg_list_response['messages'])

        for mail_msg in messages:
            mail_payload = None
            mail_date = None
            mail_week = None
            mail_id = mail_msg.get('id')
            sender_name = None
            mail_response = email_service.users().messages().get(userId='me',
                                                                format='raw',
                                                                id=mail_id).execute()
            mail_msg_str = base64.urlsafe_b64decode(mail_response['raw'].encode('ASCII'))
            mail_mime_msg = email.message_from_string(mail_msg_str)
            mail_date = mail_response.get('internalDate')
            if mail_date:
                mail_date = float(mail_date) / 1000
                mail_week = datetime.datetime.fromtimestamp(mail_date).strftime('%V')

            sender_email = mail_mime_msg['X-Original-Sender']

            user_response = user_service.users().get(userKey=sender_email).execute()

            if user_response.get('name'):
                sender_name = user_response.get('name').get('fullName', sender_email)

            if mail_mime_msg.is_multipart():
                for msg_part in mail_mime_msg.walk():
                    if msg_part.get_content_maintype() == 'text':
                        mail_payload = msg_part.get_payload(decode=True)
            else:
                mail_payload = msg_part.get_payload(decode=True)

            try:
                print(u'''
---------------------------------------------------------------
Name: {0}
Week: {1}

Report:
{2}
---------------------------------------------------------------''').format(sender_name,
                                                                           mail_week,
                                                                           html2text.html2text(urllib.unquote(
                                                                               mail_payload.decode("utf8")
                                                                           )))
                msg_labels={'addLabelIds': ['Label_9'],
                            'removeLabelIds': ['UNREAD'],
                            }
                email_service.users().messages().modify(userId='me',
                                                        id=mail_id,
                                                        body=msg_labels).execute()
            except UnicodeEncodeError:
                print('{0}\'s report could not be displayed: UnicodeEncodeError'.format(sender_name))

        sys.exit(0)

    folder_id = PROFILES[PROFILE]['folder']
    image_folder_id = PROFILES[PROFILE].get('image_folder')
    image_alt_text = PROFILES[PROFILE].get('image_alt_text')

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

        existing_files = get_files_in_folder(file_service, folder_id)
        if image_folder_id:
            image_files = get_files_in_folder(file_service, image_folder_id)
        else:
            image_files = {}
        image_store = {}

        for year in REPORTS:
            for week in REPORTS[year]:
                week_date = '{0}-W{1}'.format(year, week)
                start = datetime.datetime.strptime(week_date + '-0', "%Y-W%W-%w") - datetime.timedelta(days=7)
                end = datetime.datetime.strptime(week_date + '-0', "%Y-W%W-%w")
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

                file_name = week_of
                if file_name not in existing_files:

                    shortcut_metadata = {
                        'name': file_name,
                        'parents': [folder_id],
                        'mimeType': 'application/vnd.google-apps.document',
                    }
                    document = ''
                    try:
                        document = TEMPLATE_ENVIRONMENT.get_template(md_template).render(context)
                    except Exception as e:
                        print('Failed to render doc jinja: {0}', e)
                        pass

                    html_document = markdown.markdown(document, extensions=['markdown.extensions.codehilite',
                                                                            'markdown.extensions.tables',
                                                                            'markdown.extensions.fenced_code'])

                    try:
                        document = TEMPLATE_ENVIRONMENT.get_template(html_template).render({'html': html_document})
                    except Exception as e:
                        print('Failed to render doc jinja: {0}', e)
                        pass
                    document = filter_img_tags(file_service, image_files, image_store, document, image_alt_text)
                    document = io.BytesIO(str(document))

                    document_media = http.MediaIoBaseUpload(document, mimetype='text/html')
                    file_created = file_service.files().create(body=shortcut_metadata, media_body=document_media).execute()

                    print('Created file {0}'.format(file_name))
                    context['link'] = file_created['id']

                    if not flags.skip_email:
                        email_document = ''

                        try:
                            email_document = TEMPLATE_ENVIRONMENT.get_template(md_template).render(context)
                        except Exception as e:
                            print('Failed to render email jinja: {0}', e)
                            pass

                        html_email_document = markdown.markdown(email_document, extensions=[
                            'markdown.extensions.codehilite',
                            'markdown.extensions.tables',
                            'markdown.extensions.fenced_code'])
                        try:
                            email_document = TEMPLATE_ENVIRONMENT.get_template(html_template).render(
                                {'html': html_email_document}
                            )
                        except Exception as e:
                            print('Failed to render doc jinja: {0}', e)
                            pass

                        email_document = filter_img_tags(file_service, image_files, image_store, email_document, image_alt_text)
                        email_document = str(email_document)

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
