import boto3
from botocore.exceptions import NoCredentialsError, ClientError

def uploadFile(remoteFile, localFile):
    bucket = "renderfarm"
    session = boto3.session.Session()
    client = session.client(
        's3',
        endpoint_url='https://0a4e9dcd03b76f1d49958d8467da33ea.eu.r2.cloudflarestorage.com',
        aws_access_key_id="13a5b3cf0ad4b6c550342cef7f4ca524",
        aws_secret_access_key="b2e6b106d48c325e8d0ef6eeb1e92bfb409e257c9c0d840d62f3576ef3621324"
    )
    try:
        client.put_object(Bucket=bucket, Key=remoteFile, Body=open(localFile, 'rb'))
        return True
    except FileNotFoundError:
        raise Exception(f"The file {localFile} was not found.")
    except NoCredentialsError:
        raise Exception("Invalid credentials")
    except ClientError as e:
        raise Exception(f"Error ocurred {e}")
