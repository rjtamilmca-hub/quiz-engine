import os

from google.oauth2.credentials import Credentials

from google_auth_oauthlib.flow import InstalledAppFlow

from google.auth.transport.requests import Request

from googleapiclient.discovery import build

from googleapiclient.http import MediaFileUpload

from config import PARENT_FOLDER_ID


SCOPES = [
    "https://www.googleapis.com/auth/drive"
]


def get_drive_service():

    creds = None

    if os.path.exists("token.json"):

        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:

            creds.refresh(Request())

        else:

            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:

            token.write(creds.to_json())

    service = build(
        "drive",
        "v3",
        credentials=creds
    )

    return service


service = get_drive_service()


# GET ALL SUBJECT FOLDERS
def get_subject_folders():

    query = f"""
    '{PARENT_FOLDER_ID}' in parents
    and mimeType='application/vnd.google-apps.folder'
    and trashed=false
    """

    response = service.files().list(
        q=query,
        fields="files(id,name)"
    ).execute()

    return response.get("files", [])


# GET OR CREATE SUBJECT FOLDER
def get_or_create_subject_folder(subject_name):

    query = f"""
    name='{subject_name}'
    and mimeType='application/vnd.google-apps.folder'
    and '{PARENT_FOLDER_ID}' in parents
    and trashed=false
    """

    response = service.files().list(
        q=query,
        fields="files(id,name)"
    ).execute()

    folders = response.get("files", [])

    if folders:

        return folders[0]["id"]

    metadata = {
        "name": subject_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [PARENT_FOLDER_ID]
    }

    folder = service.files().create(
        body=metadata,
        fields="id"
    ).execute()

    return folder["id"]


# UPLOAD FILE
def upload_file(file_path, folder_id):

    file_name = os.path.basename(
        file_path
    )

    metadata = {
        "name": file_name,
        "parents": [folder_id]
    }

    media = MediaFileUpload(
        file_path,
        mimetype="text/csv",
        resumable=True
    )

    uploaded = service.files().create(
        body=metadata,
        media_body=media,
        fields="id"
    ).execute()

    return uploaded["id"]