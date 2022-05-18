# Helper function for determining if request is for csv serialization.
# startswith because browsableapi is sending 'text/csv;q=0.8'
from datetime import datetime

from pytz import timezone


def is_csv_request(request):
    return request.accepted_media_type.startswith('text/csv')


def get_utc_now() -> datetime:
    t = datetime.utcnow()  # Note: despite the method name, this returns a timezone unaware timestamp, hence the conversion below
    tz = timezone('UTC')
    return tz.localize(t)
