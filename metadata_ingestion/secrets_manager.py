import boto3

def get_secret(secret_name: str, region_name: str) -> str:
    """
    Retrieve a secret from AWS Secrets Manager.
    """
    client = boto3.client(
        service_name="secretsmanager",
        region_name=region_name
    )

    response = client.get_secret_value(
        SecretId=secret_name
    )

    return response["SecretString"]