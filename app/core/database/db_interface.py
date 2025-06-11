import pymysql
import os
from app.core.app_config import get_config
from .connection_handler import DatabaseConnection
import app.core.secret_handler as secrets
from app.core.utils.utils import set_logger

logger = set_logger(name=__name__)
secret_config = secrets.get_config()

app_config = get_config()


class Table:
    def __init__(self, name: str, columns: dict[str, str] = None):
        self.name = name
        self.columns: dict[str, str] = columns

    def set_columns(self, columns: dict[str, str]):
        self.columns = columns

    def get_json_columns(self):
        return [col for col, dtype in self.columns.items() if dtype == "json"]


class DatabaseInterface:
    def __init__(
        self,
        host: str = os.getenv("MYSQL_HOST"),
        port: int = os.getenv("MYSQL_PORT"),
        user: str = os.getenv("MYSQL_USERNAME"),
        password: str = os.getenv("MYSQL_KEY"),
        database: str = os.getenv("MYSQL_DBNAME"),
        is_ssh_tunnel: bool = False,
        connection_timeout: int = 10
    ):
        self.set_db_config(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            is_ssh_tunnel=is_ssh_tunnel,
            connection_timeout=connection_timeout
        )
        self.database_name = database
        self.tables = {
            "reddit_posts": Table(
                    app_config.get('mysql').get('tables').get('reddit_posts'),
                    ),
            "portfolios": Table(
                app_config.get('mysql').get('tables').get('portfolios'),
            ),
            "purchases": Table(
                app_config.get('mysql').get('tables').get('purchases'),
            ),
            "crypto_currency_prices": Table(
                app_config.get('mysql').get('tables').get(
                        'crypto_currency_prices'),
            ),
            "crypto_assets": Table(
                app_config.get('mysql').get('tables').get(
                        'crypto_assets')
            )
        }
        self.prepare_tables()

    def set_db_config(
            self,
            host: str = None,
            port: int = None,
            user: str = None,
            password: str = None,
            database: str = None,
            is_ssh_tunnel: bool = False,
            connection_timeout: int = 10):
        db_config = {
            'db_host': host,
            'db_port': int(port),
            'db_username': user,
            'db_password': password,
            'database': database,
            'is_ssh_tunnel': is_ssh_tunnel,
            'connection_timeout': connection_timeout,
        }
        if is_ssh_tunnel:
            db_config.update({
                'ssh_host': secret_config.get('DROPLET_SSH_HOST'),
                'ssh_port': int(secret_config.get('SSH_TUNNEL_PORT')),
                'ssh_private_key_path': secret_config.get(
                    'SSH_PRIVATE_KEY_PATH'),
                'ssh_user': secret_config.get('DROPLET_SSH_USER'),
            })
        self.db_config = db_config
        
    def prepare_tables(self):
        # Logic unchanged, relies on get_column_name_and_datatype_from_table
        for key, table in self.tables.items():
            column_info = self.get_column_name_and_datatype_from_table(
                self.tables[key].name
            )
            if column_info:
                self.tables[key].set_columns(column_info)
            else:
                logger.error(f"""Could not prepare table
                {self.tables[key].name}
                due to missing column info.""")

    def execute_query(
            self,
            query: str,
            params: tuple = None,
            dictionary_cursor: bool = False
    ):
        try:
            with DatabaseConnection(
                self.db_config,
                dictionary_cursor=dictionary_cursor
            ) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except pymysql.Error as err:
            logger.error(f"Error executing query: {err} (PyMySQL)")
            raise

    def get_column_name_and_datatype_from_table(self, table_name):
        # Query remains the same
        query = """
            SELECT
                COLUMN_NAME,
                COLUMN_TYPE
            FROM
                INFORMATION_SCHEMA.COLUMNS
            WHERE
                TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
            ORDER BY
                ORDINAL_POSITION;
            """

        column_info = {}
        try:
            with DatabaseConnection(self.db_config, dictionary_cursor=False)\
                    as cursor:
                logger.info(
                    f"""Executing schema query for table:
                    {self.database_name}.{table_name} (PyMySQL)""")
                # %s placeholder is standard for PyMySQL too
                cursor.execute(query, (self.database_name, table_name))
                results = cursor.fetchall()

                if results:
                    # Access results by index for default cursor
                    for row in results:
                        column_info[row[0]] = row[1]
                    logger.info(
                        f"""Fetched {len(results)}
                        columns for table {table_name}.""")
                else:
                    logger.warning(
                        f"""No columns found for table
                        '{self.database_name}.{table_name}'.""")

        # Changed: Catch PyMySQL specific errors
        except pymysql.Error as e:
            logger.error(f"""DB Error retrieving column
            info for {table_name} (PyMySQL): {e}""")
            return None
        except Exception as ex:
            logger.error(
                f"Non-DB error retrieving column info for {table_name}: {ex}")
            return None
        return column_info

    def get_datatype_of_column(
        self,
        tablename: str,
        column_name: str
    ):
        query = """
            SELECT DATA_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
            """
        try:
            # Use context manager, request dictionary cursor for easy access
            with DatabaseConnection(
                    self.db_config, dictionary_cursor=True) as cursor:
                cursor.execute(
                    query, (self.database_name, tablename, column_name))
                result = cursor.fetchone()
            if result:
                # Access result by key 'DATA_TYPE' because of DictCursor
                data_type = result['DATA_TYPE']
                logger.info(f"Data type of column {column_name}: {data_type}")
                return data_type
            else:
                logger.warning(
                    f"No data type found for column {column_name}.")
                return None
        # Changed: Catch general PyMySQL errors
        except pymysql.Error as e:
            logger.error(
                f"""Error getting data type for
                column {column_name} (PyMySQL): {e}""")
            raise
        except Exception as e:
            logger.error(
                f"""Non-DB error getting
                data type for column {column_name}: {e}""")
            raise

    def get_values_from_column(
            self,
            table_name: str,
            column_name: str,
            limit: int = None) -> list:
        query = f"""
            SELECT {column_name}
            FROM {table_name}
            WHERE {column_name} IS NOT NULL
            """
        if limit:
            query += f" LIMIT {limit}"
        query += ";"

        try:
            with DatabaseConnection(self.db_config) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                if results:
                    logger.info(
                        f"""Fetched {len(results)} values from
                        column {column_name} in table {table_name}.""")
                    return [row[0] for row in results]
                else:
                    logger.warning(
                        f"""No values found in column {column_name}
                        of table {table_name}.""")
                    return []
        except pymysql.Error as err:
            logger.error(
                f"Error executing query: {query}, Error: {err} (PyMySQL)")
            raise
        except Exception as e:
            logger.error(
                f"Non-DB error executing query: {query}, Error: {e}")
            raise
