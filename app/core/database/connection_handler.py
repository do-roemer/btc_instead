import pymysql
import pymysql.cursors
import logging
import os
from sshtunnel import SSHTunnelForwarder

import app.core.secret_handler as secrets
from app.core.utils.utils import set_logger
from app.core.app_config import get_config

app_config = get_config()
logger = set_logger(__name__)
secrets_config = secrets.get_config()


class DatabaseConnection:
    def __init__(
            self,
            config,
            dictionary_cursor=False
    ):
        self.db_config = config
        self.dictionary_cursor = dictionary_cursor
        self.connection = None
        self.cursor = None
        self.tunnel = None

        logging.info(
            "DatabaseConnection context manager initialized (PyMySQL).")

    def _start_tunnel(self):
        """Starts the SSH tunnel if not already active."""
        if self.tunnel and self.tunnel.is_active:
            logging.debug("SSH tunnel already active.")
            return True

        logging.info("Attempting to start SSH tunnel...")
        required_ssh_keys = [
            'ssh_host',
            'ssh_port',
            'ssh_private_key_path',
            'ssh_user']
        if not all(k in self.db_config for k in required_ssh_keys):
            logging.error("Missing required SSH configuration keys for tunnel.")
            return False

        try:
            ssh_key_path = os.path.expanduser(
                    self.db_config['ssh_private_key_path'])
            if not os.path.exists(ssh_key_path):
                logging.error(
                        f"SSH private key not found at: {ssh_key_path}")
                return False

            self.tunnel = SSHTunnelForwarder(
                ssh_address_or_host=(
                        self.db_config['ssh_host'],
                        int(self.db_config.get('ssh_port', 22))),
                ssh_username=self.db_config['ssh_user'],
                ssh_pkey=ssh_key_path,
                remote_bind_address=(
                        self.db_config['db_host'],
                        int(self.db_config.get('db_port', 3306))),
                local_bind_address=('127.0.0.1', 0)
            )
            self.tunnel.start()
            logging.info(
                f"""SSH tunnel established.
                Local bind port: {self.tunnel.local_bind_port}""")
            return True
        except Exception as e:
            logging.error(f"Failed to start SSH tunnel: {e}")
            self.tunnel = None
            return False

    def __enter__(self):

        pymysql_connection_args = {}
        db_target_name = self.db_config.get('database', 'N/A')

        try:
            if self.db_config.get('is_ssh_tunnel', False):
                # --- SSH Tunnel Connection ---
                logging.info(
                    f"Attempting SSH tunnel setup for DB:"
                    f" {db_target_name} (PyMySQL)"
                )
                if not self._start_tunnel():
                    # If tunnel fails to start, raise an error
                    raise ConnectionError("Failed to establish SSH tunnel.")

                # Connect PyMySQL to the local end of the tunnel
                pymysql_connection_args = {
                    'host': self.db_config.get('db_host'),
                    'port': self.tunnel.local_bind_port,
                    'user': self.db_config.get('db_username'),
                    'password': self.db_config.get('db_password'),
                    'database': self.db_config.get('database'),
                    'charset': self.db_config.get('charset', 'utf8mb4'),
                    'connect_timeout': self.db_config.get('connect_timeout', 10)
                }
                logging.info(
                    f"Attempting to connect PyMySQL to local tunnel endpoint "
                    f"({self.db_config.get('db_host')}:{self.tunnel.local_bind_port}) for DB:"
                    f" {db_target_name}"
                )

            else:
                # --- Direct Connection ---
                logging.info(
                    f"Attempting direct connection to DB: {db_target_name} (PyMySQL)")
                pymysql_connection_args = {
                    'host': self.db_config.get('db_host'),
                    'port': self.db_config.get('db_port', 3306),
                    'user': self.db_config.get('db_username'),
                    'password': self.db_config.get('db_password'),
                    'database': self.db_config.get('database'),
                    'charset': self.db_config.get('charset', 'utf8mb4'),
                    'connect_timeout': self.db_config.get('connect_timeout', 10)
                }
            self.connection = pymysql.connect(**pymysql_connection_args)
            logging.info(f"Connected to DB: {db_target_name} (PyMySQL).")

            # Determine cursor type based on flag
            cursor_type = pymysql.cursors.DictCursor if \
                self.dictionary_cursor else pymysql.cursors.Cursor
            self.cursor = self.connection.cursor(cursor_type)
            logging.info(" -> Connection established, cursor created (PyMySQL).")
            return self.cursor

        except (pymysql.Error, ConnectionError, ValueError, Exception) as e: # Catch potential errors
            logging.error(f"Error during database connection setup (PyMySQL): {e}")
            # Ensure cleanup happens even if __enter__ fails partially
            self.__exit__(type(e), e, e.__traceback__)
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        log_prefix = "SSH Tunnel" if self.db_config.get('is_ssh_tunnel', False) else "Direct"
        logging.info(
            f"Exiting DatabaseConnection context ({log_prefix}). Exception Type: {exc_type}."
        )
        if self.connection:
            try:
                if self.cursor:
                    try:
                        self.cursor.close()
                        logging.info(" -> Cursor closed (PyMySQL).")
                    except pymysql.Error as e_cur:
                        logging.error(f"Error closing cursor (PyMySQL): {e_cur}")
                if exc_type:
                    logging.warning(
                        f"""Rolling back transaction due
                        to error: {exc_val} (PyMySQL)""")
                    self.connection.rollback()
                else:
                    logging.info("Committing transaction (PyMySQL).")
                    self.connection.commit()

            except pymysql.Error as e_cr:
                logging.error(f"Error during commit/rollback (PyMySQL): {e_cr}")
            finally:
                try:
                    self.connection.close()
                    logging.info(" -> Connection closed (PyMySQL).")
                except pymysql.Error as e_con:
                    logging.error(f"Error closing connection (PyMySQL): {e_con}")
                finally:
                    self.connection = None
                    self.cursor = None
        if self.tunnel and self.tunnel.is_active:
            logging.info("Stopping SSH tunnel...")
            try:
                self.tunnel.stop()
                logging.info(" -> SSH tunnel stopped.")
            except Exception as e_tun:
                logging.error(f"Error stopping SSH tunnel: {e_tun}")
            finally:
                self.tunnel = None
        return False
