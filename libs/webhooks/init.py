import requests

def renderReportStatus(archive_id, item_id, status):
    try:
        webhook_url = "https://automations.flyxmarketing.com/api/v1/webhooks/Wu2THyojY4nBkFw3kFZSO"
        body = {
            "archive_id": archive_id,
            "item_id": item_id,
            "status": status
        }
        requests.post(webhook_url, json=body)
    except Exception as e:
        print(e)

def renderReportFinished(archive_id, item_id):
    try:
        webhook_url = "https://automations.flyxmarketing.com/api/v1/webhooks/imI7XJaffmV9Q7qYNfFBH"
        item_url_original = f"https://rf-storage.flyxmarketing.com/{archive_id}/{item_id}/original.mp4"
        item_url_rendered = f"https://rf-storage.flyxmarketing.com/{archive_id}/{item_id}/render.mp4"
        item_url_rendered_thumbnail = f"https://rf-storage.flyxmarketing.com/{archive_id}/{item_id}/thumbnail.jpg"
        body = {
            "archive_id": archive_id,
            "item_id": item_id,
            "item_url_original": item_url_original,
            "item_url_rendered": item_url_rendered,
            "item_url_rendered_thumbnail": item_url_rendered_thumbnail
        }
        requests.post(webhook_url, json=body)
    except Exception as e:
        print(e)
