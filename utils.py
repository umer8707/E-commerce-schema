import logging
import logging.handlers

SENSITIVE_FIELDS = {"password", "token", "email", "authorization", "credit_card", "cvv"}

_fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
logging.basicConfig(handlers=[], level=logging.DEBUG)

_fileHandler = logging.FileHandler("app.log")
_fileHandler.setLevel(logging.DEBUG)
_fileHandler.setFormatter(logging.Formatter(_fmt))
logging.getLogger().addHandler(_fileHandler)

logger = logging.getLogger(__name__)


def maskSensitive(data):
    if isinstance(data, dict):
        return {
            k: "***" if k.lower() in SENSITIVE_FIELDS else maskSensitive(v)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [maskSensitive(i) for i in data]
    return data


def logRequest(action, data=None):
    masked = maskSensitive(data) if data else {}
    logger.info("action=%s data=%s", action, masked)


def logWarning(action, reason, data=None):
    masked = maskSensitive(data) if data else {}
    logger.warning("action=%s reason=%s data=%s", action, reason, masked)


def logError(action, error):
    logger.error("action=%s error=%s", action, type(error).__name__)


def logDbError(action, error):
    logger.error("action=%s db_error_type=%s db_error_detail=%s", action, type(error).__name__, str(error))
