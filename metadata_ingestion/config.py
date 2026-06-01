import os
import boto3

AWS_REGION = (
    os.environ.get("AWS_REGION")
    or boto3.session.Session().region_name
)

SPOTIFY_SECRET_NAME = os.environ.get(
    "SPOTIFY_SECRET_NAME",
    "music-analytics/spotify-api"
)