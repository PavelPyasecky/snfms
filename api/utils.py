# Helper function for determining if request is for csv serialization.
# startswith because browsableapi is sending 'text/csv;q=0.8'
def is_csv_request(request):
    return request.accepted_media_type.startswith('text/csv')
