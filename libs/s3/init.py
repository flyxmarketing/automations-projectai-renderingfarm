import boto3
from botocore.exceptions import NoCredentialsError, ClientError

def uploadFile(remoteFile, localFile):
    bucket = "renderfarm"
    session = boto3.session.Session()
    client = session.client(
        's3',
        endpoint_url='https://0a4e9dcd03b76f1d49958d8467da33ea.eu.r2.cloudflarestorage.com',
        aws_access_key_id="0e8778aeccbed0a52467557956e16d0b",
        aws_secret_access_key="d5f869dd7fa6f1ed277312eb0a2a9c93b1f856dc09a7024fe0877b121778b4cf"
    )
    try:
        client.put_object(Bucket=bucket, Key=remoteFile, Body=open(localFile, 'rb'), ACL='public-read')
        return True
    except FileNotFoundError:
        raise Exception(f"The file {localFile} was not found.")
    except NoCredentialsError:
        raise Exception("Invalid credentials")
    except ClientError as e:
        raise Exception(f"Error ocurred {e}")
