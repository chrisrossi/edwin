from code import interact
import sys

from edwin.config import ApplicationContext

def main(argv=sys.argv):
    context = ApplicationContext() # XXX pass config on command line
    script = None # XXX

    if script is None:
        cprt = ('"catalog" is the photos catalog.  "photos" is the photos  '
                'repository.')
        banner = "Python %s on %s\n%s" % (sys.version, sys.platform, cprt)
        interact(banner, local={'catalog': context.catalog,
                                'photos': context.photos})
    else:
        code = compile(open(script).read(), script, 'exec')
        exec code in {'root': root}

