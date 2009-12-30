import sys

from edwin.config import ApplicationContext

def main(args=sys.argv[1:], context=None):
    # XXX User should be allowed to pass in config file
    if context is None:
        context = ApplicationContext()
    context.catalog.scan()
