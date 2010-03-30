import datetime
import re

from happy.acl import effective_principals
from happy.traversal import model_url

def get_months(request):
    app_context = request.app_context
    routes = app_context.routes
    month_route = routes['month']
    months = []
    for month in app_context.catalog.months(effective_principals(request)):
        y, m = month.split('-')
        label = format_month(int(y), int(m))
        url = month_route.url(
            request, year=y, month=m
        )
        months.append(dict(label=label, url=url))
    return months

def brain_url(request, brain):
    return '/'.join((request.application_url, brain.path))

def _title_or_path(brain):
    if not brain.title:
        return brain.path
    return brain.title

def get_new_albums(request, catalog=None):
    catalog = request.app_context.catalog
    return [dict(label=_title_or_path(a), url=brain_url(request, a)) for a in
            catalog.new_albums(effective_principals(request))]

STRIP_LEADING_ZEROS_RE = re.compile(
    '(?P<pre>\D)'
    '(?P<zeros>0+)(?P<number>\d+)'
)

def strip_leading_zeros(s):
    def repl(match):
        d = match.groupdict()
        return ''.join((d['pre'], d['number']))
    return STRIP_LEADING_ZEROS_RE.sub(repl, s)

def format_month(year, month):
    return datetime.date(year, month, 1).strftime('%B %Y')

def format_date(date):
    if date is None:
        return ''
    formatted = date.strftime("%B %d, %Y")
    return strip_leading_zeros(formatted)

def format_date_range(date_range):
    if date_range is None:
        return ''
    start, end = date_range
    if start == end:
        return format_date(start)
    elif start.year == end.year and start.month == end.month:
        formatted = "%s-%s, %s" % (start.strftime('%B %d'),
                                   end.strftime('%d'),
                                   start.strftime('%Y'))
        return strip_leading_zeros(formatted)
    elif start.year == end.year:
        formatted = "%s - %s" % (start.strftime("%B %d"),
                                 end.strftime("%B %d, %Y"))
        return strip_leading_zeros(formatted)
    formatted = "%s - %s" % (format_date(start), format_date(end))
    return strip_leading_zeros(formatted)

