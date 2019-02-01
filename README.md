# SMM posting script

The script posts articles and/or photos to VK public, Telegram chat and FB group. Posting shedule
get from Google Sheets and texts and images - from Google Drive.

For approve user should:
* tag his friend(s)
* like the post
* subscribe to the orginizer account


### How to install

1. Python3 should be already installed. Then use `pip` (or `pip3`) to install dependencies:
```
pip install -r requirements.txt
```

2. Enable Google Sheets API according [instructions](https://developers.google.com/sheets/api/quickstart/python) 
spreadsheet_id variable contains the ID of shedule table (see the [sample](https://docs.google.com/spreadsheets/d/17r4QRW_m0clut772bRnUL-U1-JiazImiZMm43SkgS9Q/edit#gid=0))

3. Enable Google Drive API accordin [instructions](https://gsuitedevs.github.io/PyDrive/docs/build/html/quickstart.html#authentication) 

4. Create VK public, Telegram chat and FB group for posting and put all necessary parameters to .env

```
LOGIN_VK=your_phone_number_in_vk
PASSWORD_VK=your_vk_password
GROUP_ID_VK=v_public_id
ALBUM_ID_VK=vk_album_id
TOKEN_VK=vk_token

CHAT_ID_TEL=telegram_chat_id
TOKEN_TEL=telegram_token

TOKEN_FB=fb_token
FB_ID=fb_user_id
GROUP_ID_FB=fb_group_id
```


### Quickstart

Just run **main.py**, it will be check shedule every 5 minutes. Or, if you want to add script to cron,
edit `while True:` loop.


### Project Goals

The code is written for educational purposes on online-course for web-developers [dvmn.org](https://dvmn.org/).

