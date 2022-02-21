"""
Flow Aggregation Service

Both the Read API and Write API have the same message specification: A JSON array with
any number of flow-log objects, where a flow-log object has these fields
● src_app - string
● dest_app - string
● vpc_id - string
● bytes_tx - int
● bytes_rx - int
● hour - int

Example Message

[
{"src_app": "foo", "dest_app": "bar", "vpc_id": "vpc-0", "bytes_tx": 100, "bytes_rx": 500, "hour": 1},
{"src_app": "foo", "dest_app": "bar", "vpc_id": "vpc-0", "bytes_tx": 200, "bytes_rx": 1000, "hour": 1}
]

Only GET and POST methods are supported

POST /flows

GET /flows?hour=<value>

"""

import json

from http import HTTPStatus

from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse

from fas.models import Flowlog

# Setting limits. Chosen arbitrarily for now.
MAX_INTVAL = 2**31-1
MAX_APP_LEN = 20
MAX_RECORDS = 10000

message_fields = ('src_app', 'dest_app', 'vpc_id', 'bytes_tx', 'bytes_rx', 'hour')


def check_intval(value):
    """
    Check if value is an integer, and is in the accepted range
    """
    return isinstance(value, int) and value >= 0 and value <= MAX_INTVAL


def check_slen(stringval):
    """
    Check if string length is valid
    """
    return 0 < len(stringval) <= MAX_APP_LEN


def index(request):
    """
    Handle Request for index
    """
    return HttpResponse("Hello, world. You're at the fas index.")


def parse_row(row):
    """
    Extract values from input dict and check if they are valid
    """
    if not all(key in row for key in message_fields):
        return None

    src_app = row['src_app']
    dest_app = row['dest_app']
    vpc_id = row['vpc_id']
    bytes_tx = row['bytes_tx']
    bytes_rx = row['bytes_rx']
    hour = row['hour']

    if not (check_slen(src_app) and check_slen(dest_app) and check_slen(vpc_id)):
        return None

    if not (check_intval(bytes_tx) and check_intval(bytes_rx) and check_intval(hour)):
        return None

    return (src_app, dest_app, vpc_id, bytes_tx, bytes_rx, hour)


def sum_safe(val1, val2):
    """
    Sum integer values, but clamp it to MAX_INTVAL
    """
    return min(MAX_INTVAL, val1+val2)


def flows_get(request):
    """
     Handle a GET Request
    """
    hour = request.GET.get('hour', None)
    if not hour or not str.isdigit(hour) or not check_intval(int(hour)):
        return HttpResponse(status=HTTPStatus.BAD_REQUEST)
    hour = int(hour)

    # Get all objects matching the hour value.
    # We exclude the 'hashkey' column from the QuerySet because it is not a message field
    qset = Flowlog.objects.filter(hour=hour).values('src_app', 'dest_app', 'vpc_id', 'bytes_tx', 'bytes_rx', 'hour')

    return JsonResponse(list(qset), safe=False)


def flows_post(request):
    """
    Handle a POST Request
    """
    # From the request body, extract the bytestring, and convert to a dict
    bss = request.body
    try:
        values = json.loads(bss)
    except ValueError:
        return HttpResponse("Error in decoding JSON", status=HTTPStatus.BAD_REQUEST)

    for row in values:
        parsed_values = parse_row(row)
        if parsed_values is None:
            continue  # ignore this row

        src_app, dest_app, vpc_id, bytes_tx, bytes_rx, hour = parsed_values

        # We use the tuple (src_app, dest_app, vpc_id, hour) as the primary key
        # Django does not support multi-column keys
        # Hence, create a hashkey by concatenating the fields
        #
        hashkey = src_app + dest_app + vpc_id + str(hour)
        try:
            obj = Flowlog.objects.get(hashkey=hashkey)
            # update the existing object
            obj.bytes_tx = sum_safe(bytes_tx, obj.bytes_tx)
            obj.bytes_rx = sum_safe(bytes_rx, obj.bytes_rx)
        except Flowlog.DoesNotExist:
            # create a new object, if table is not full
            if Flowlog.objects.count() > MAX_RECORDS:
                return HttpResponse(status=HTTPStatus.INSUFFICIENT_STORAGE)
            obj = Flowlog(hashkey=hashkey, src_app=src_app, dest_app=dest_app, vpc_id=vpc_id,
                          bytes_tx=bytes_tx, bytes_rx=bytes_rx, hour=hour)
        obj.save()

    return HttpResponse()


def flows(request):
    """
    Entry point, to call handlers for GET and POST Requests
    """
    if request.method == 'GET':
        ret = flows_get(request)
    elif request.method == 'POST':
        ret = flows_post(request)
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

    return ret
