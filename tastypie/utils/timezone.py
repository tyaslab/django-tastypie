from __future__ import unicode_literals
import datetime, operator, pytz
from django.utils import datetime_safe
from django.conf import settings
from ..constants import TIME_ZONE_OFFSET
import re

try:
    from django.utils import timezone

    def make_aware(value):
        if getattr(settings, "USE_TZ", False) and timezone.is_naive(value):
            default_tz = timezone.get_default_timezone()
            value = timezone.make_aware(value, default_tz)
        return value

    def make_naive(value):
        if getattr(settings, "USE_TZ", False) and timezone.is_aware(value):
            default_tz = timezone.get_default_timezone()
            value = timezone.make_naive(value, default_tz)
        return value

    def now():
        d = timezone.now()

        if d.tzinfo:
            return timezone.localtime(timezone.now())

        return d
except ImportError:
    now = datetime.datetime.now
    make_aware = make_naive = lambda x: x


def aware_date(*args, **kwargs):
    return make_aware(datetime.date(*args, **kwargs))


def aware_datetime(*args, **kwargs):
    return make_aware(datetime.datetime(*args, **kwargs))


def json_to_datetime(json_datetime, time_zone=None):
    # get default time zone
    if settings.USE_TZ and time_zone is None:
        time_zone = pytz.timezone(settings.TIME_ZONE)
    else:
        time_zone = pytz.utc

    DATETIME_REGEX = re.compile(r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})(T|\s+)(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}(\.\d+)?)(?P<tz>(Z|[\-\+]\d{4}))?$')

    match = DATETIME_REGEX.search(json_datetime)

    if not match:
        raise ValueError

    data = match.groupdict()
    second_split = data['second'].split('.')
    second = int(second_split[0])
    millisecond = 0

    if len(second_split) > 1:
        millisecond = int(second_split[1])

    result = datetime_safe.datetime(
        int(data['year']),
        int(data['month']),
        int(data['day']),
        int(data['hour']),
        int(data['minute']),
        second,
        millisecond
    )

    tz = data.get('tz', None)

    if tz != 'Z':
        sign, hour_offset, minute_offset = tz[0], int(tz[1:3]), int(tz[3:5])
        if sign == '-':
            sign = operator.add
        else:
            sign = operator.sub

        seconds = (hour_offset * 60 * 60) + (minute_offset * 60)
        result = sign(result, timezone.timedelta(seconds=seconds))

    result = time_zone.localize(result)

    return result


def datetime_to_json(date_time, time_zone=None):
    # get default time zone
    if settings.USE_TZ and time_zone is None:
        time_zone = pytz.timezone(settings.TIME_ZONE)
    else:
        time_zone = pytz.utc

    # change to aware
    if date_time.tzinfo is None:
        date_time = time_zone.localize(date_time)
    elif date_time.tzinfo.zone != time_zone.zone:
        date_time = date_time.astimezone(time_zone)

    # for json data
    if time_zone.zone == 'UTC':
        tz = 'Z'
    else:
        tz = TIME_ZONE_OFFSET[time_zone.zone]

    # TODO: ROUND THE MICROSECOND
    if date_time.microsecond:
        sm = '%s.%s' % (
            '%02d' % date_time.second,
            date_time.microsecond
        )
    else:
        sm = '%02d' % date_time.second

    result = '%04d-%02d-%02dT%02d:%02d:%s%s' % (
        date_time.year,
        date_time.month,
        date_time.day,
        date_time.hour,
        date_time.minute,
        sm,
        tz
    )

    return result
