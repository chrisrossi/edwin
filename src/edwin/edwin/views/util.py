import datetime
from happy.acl import effective_principals

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

def format_month(year, month):
    return datetime.date(year, month, 1).strftime('%B %Y')

def format_date(date):
    return date.strftime("%B %d, %Y")

def format_date_range(date_range):
    start, end = date_range
    if start == end:
        return format_date(start)
    elif start.year == end.year and start.month == end.month:
        return "%s-%s, %s" % (start.strftime('%B %d'),
                              end.strftime('%d'),
                              start.strftime('%Y'))
    elif start.year == end.year:
        return "%s - %s" % (start.strftime("%B %d"), end.strftime("%B %d, %Y"))
    return "%s - %s" % (format_date(start), format_date(end))
