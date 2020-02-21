import logging
from datetime import datetime
from pytz import timezone, utc
import os


def custom_time(*args):
    utc_dt = utc.localize(datetime.utcnow())
    my_tz = timezone("Europe/Kiev")
    converted = utc_dt.astimezone(my_tz)
    return converted.timetuple()


def log_msg(update):
    return f'id: {update.effective_user.id} ' \
           f'name: {update.effective_user.full_name} ' \
           f'usrnm: {update.effective_user.username}'


log = logging.getLogger('MainLogger')
# TODO: set custom timezone for logging
logging.Formatter.converter = custom_time
fh = logging.FileHandler('logfile.log', encoding='utf-8')
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter('{asctime} {message} {funcName}',
                                  datefmt='%y.%m.%d %H:%M:%S', style='{'))
log.addHandler(fh)
log.setLevel(logging.INFO)

log_chat = logging.getLogger('ChatLogger')
logging.Formatter.converter = custom_time
fh = logging.FileHandler(os.path.join('logfiles', 'log_chat.log'),
                         encoding='utf-8')
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter('{asctime} {message}',
                                  datefmt='%y.%m.%d %H:%M:%S', style='{'))
log_chat.addHandler(fh)
log_chat.setLevel(logging.INFO)
