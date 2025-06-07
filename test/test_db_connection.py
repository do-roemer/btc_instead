from database.db_interface import DatabaseInterface
from src.app_config import get_config
import src.secret_handler as secrets

secret_config = secrets.get_config()
app_config = get_config()


def test_database_connection():
    db_interface = DatabaseInterface(
        host=secret_config.get("AWS_RDS_HOST"),
        user=secret_config.get("AWS_RDS_USERNAME"),
        password=secret_config.get("AWS_RDS_KEY"),
        database=secret_config.get("AWS_RDS_DBNAME"),
        ssh_host=secret_config.get("SSH_HOST_RDS_BASTION"),
        ssh_port=secret_config.get("SSH_PORT_RDS_BASTION"),
        ssh_user=secret_config.get("SSH_USER_RDS_BASTION"),
        ssh_private_key_path=secret_config.get("SSH_KEY_PATH_RDS_BASTION")
    )
    post = db_interface.get_reddit_posts(["1jn1zkh"])
    assert post is not None, "Failed to fetch post from the database"
