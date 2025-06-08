import logging
import app.core.app_config as app_config

config = app_config.get_config()


def set_logger(name):
    logging.basicConfig(
        level=logging.DEBUG if config["debug"]["print_debug"] else logging.INFO,
        format=config["logging"]["format"],
        handlers=[
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    return logger
