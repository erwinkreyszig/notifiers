from django.conf import settings


def get_database_uri(using: str = "default") -> str:
    db_config = settings.DATABASES[using]
    db_name = db_config["NAME"]
    db_user = db_config["USER"]
    db_password = db_config["PASSWORD"]
    db_host = db_config["HOST"]
    db_port = db_config["PORT"]
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
