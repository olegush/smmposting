from __future__ import print_function
import time
from datetime import datetime
import pickle
import os
import os.path
from urllib.parse import urlparse, parse_qs

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from urlextract import URLExtract
import requests
from dotenv import load_dotenv, find_dotenv
import vk_api
import telegram


def auth_google_sheet(token_file, creds_file, scopes):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token, encoding='bytes')

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
            creds = flow.run_local_server()

        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    return build('sheets', 'v4', credentials=creds)


def get_google_sheet(service, spreadsheet_id, range_name):
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueRenderOption='FORMULA'
    ).execute()
    return result.get('values', [])


def get_googledrive_id(cell):
    try:
        extractor = URLExtract()
        urls = extractor.find_urls(cell)
        query = urlparse(urls[0])[4]
        googledrive_id = parse_qs(query)['id'][0]
    except (IndexError, KeyError):
        return False
    else:
        return googledrive_id


def get_data_for_posts(article_id, img_id):
    if article_id:
        article_title = get_googledrive_content(article_id, type='text/plain')
        with open(article_title) as file:
            text = file.read()
    else:
        text = ''

    if img_id:
        img_title = get_googledrive_content(img_id, type=None)
    else:
        img_title = None

    return text, img_title


def get_googledrive_content(id, type):
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)
    content = drive.CreateFile({'id': id})
    content.GetContentFile(content['title'], mimetype=type)
    return content['title']


def post_to_vk(vk, vk_session, filepath, text, group_id, album_id):
    if filepath:
        upload = vk_api.upload.VkUpload(vk_session)
        photo = upload.photo(filepath, album_id=album_id, group_id=group_id)
        photo_name = 'photo-{}_{}'.format(group_id_vk, photo[0]['id'])
    else:
        photo_name = ''
    vk.wall.post(
        owner_id=-int(group_id),
        from_group=1,
        message=text,
        attachments=photo_name
    )


def post_to_telegram(bot, filepath, text, chat):
    if filepath:
        with open(filepath, 'rb') as img:
            bot.send_photo(chat_id=chat, photo=img, caption=text)
    else:
        bot.send_message(chat_id=chat, text=text)


def post_to_facebook(filepath, text, token, group_id):
    if filepath:
        url = 'https://graph.facebook.com/{}/photos'.format(group_id)
        with open(filepath, 'rb') as photo:
            payload = {'caption': text, 'access_token': token, 'source': photo}
            response = requests.post(url, params=payload)
    else:
        url = 'https://graph.facebook.com/{}/feed'.format(group_id)
        payload = {'message': text, 'access_token': token}
        response = requests.post(url, params=payload)


def update_google_sheet(row, num, spreadsheet_id):
    row_new = row[:-1]
    row_new.append('да')
    values = [row_new]
    body = {'values': values}
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='A{}'.format(num),
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    result.get('updatedCells')


if __name__ == '__main__':
    # If modifying these scopes, delete the file token.pickle.
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    token_file = 'token.pickle'
    creds_file = 'credentials.json'

    # The ID and range of a sample spreadsheet.
    spreadsheet_id = '17hMOmQkpdTUqUbnDmKOpCOLNuJ53DvmAmapDz2eg-bs'
    start_row = 3
    range_name = 'Лист1!A{}:H'.format(start_row)

    weekdays = [
        'понедельник', 'вторник', 'среда',
        'четверг', 'пятница', 'суббота', 'воскресенье'
    ]
    delay = 5*60

    load_dotenv()
    login_vk = os.getenv('LOGIN_VK')
    password_vk = os.getenv('PASSWORD_VK')
    group_id_vk = os.getenv('GROUP_ID_VK')
    album_id_vk = os.getenv('ALBUM_ID_VK')
    token_tel = os.getenv('TOKEN_TEL')
    chat_id_tel = os.getenv('CHAT_ID_TEL')
    group_id_fb = os.getenv('GROUP_ID_FB')
    token_fb = os.getenv('TOKEN_FB')

    while True:
        current_datetime = datetime.now().timetuple()
        current_hour = current_datetime[3]
        current_weekday = weekdays[current_datetime[6]]

        service = auth_google_sheet(token_file, creds_file, scopes)
        sheet_data = get_google_sheet(service, spreadsheet_id, range_name)

        if not sheet_data:
            print('No data found.')
        else:
            for num, row in enumerate(sheet_data, start_row):
                vk_flag, tel_flag, fb_flag, weekday, hour, article_link, img_link, status = row

                if current_weekday == weekday and current_hour == hour and status == 'нет':
                    article_id = get_googledrive_id(article_link)
                    img_id = get_googledrive_id(img_link)
                    text, img_title = get_data_for_posts(article_id, img_id)

                    if text or img_title:

                        if vk_flag == 'да':
                            vk_session = vk_api.VkApi(login_vk, password_vk)
                            vk_session.auth()
                            vk = vk_session.get_api()
                            post_to_vk(
                                vk,
                                vk_session,
                                img_title,
                                text,
                                group_id_vk,
                                album_id_vk
                            )
                        if tel_flag == 'да':
                            bot = telegram.Bot(token=token_tel)
                            post_to_telegram(
                                bot,
                                img_title,
                                text,
                                chat_id_tel
                            )
                        if fb_flag == 'да':
                            post_to_facebook(
                                img_title,
                                text,
                                token_fb,
                                group_id_fb
                            )
                        update_google_sheet(row, num, spreadsheet_id)
        time.sleep(delay)
