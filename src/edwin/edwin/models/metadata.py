from __future__ import with_statement

from jpeg import jpeg
import os
import simplejson

#
# Class for representing our custom metadata for jpeg photos.  Metadata is
# stored in the comments section of jpeg files following our own format
#
BEGIN_TAG = '<photometa>'
END_TAG = '</photometa>'

# States for our finite state machine parser
STATE_SCANNING=0
STATE_INTAGNAME=1
STATE_INTAGBODY=2

import re
COMMENT_RE = re.compile('<!--.+-->')

class OldMetadata(dict):
    """Class for representing our custom metadata for jpeg photos.  Metadata is
       stored in the comments section of jpeg files following our own format."""

    def __init__( self, fname ):
        self.fname = fname
        self._load()

    def _load( self ):
        """Loads photo metadata from file comments."""

        # load comments from file
        c = jpeg.getComments( self.fname )

        # look for our semaphore
        i = c.find( BEGIN_TAG )
        if i == -1:
            # if it is not present, then we haven't tagged this file yet
            return

        # start parsing after semaphore
        i += len( BEGIN_TAG )
        state = STATE_SCANNING
        tagname = None
        iTagname = -1
        iTagbody = -1
        closingTag = None

        while(True):
            if state==STATE_SCANNING:
                # Check for begin of tag name
                if c[i] == '<':
                    # Check for end of tags
                    if c[i:i+len(END_TAG)] == END_TAG:
                        break

                    # Start parsing tag name
                    state = STATE_INTAGNAME
                    iTagname = i+1

                # else ignore
                i += 1

            elif state==STATE_INTAGNAME:
                # Check for end of tag name
                if c[i] == '>':
                    # Get tag name
                    tagname = c[iTagname:i]
                    closingTag = '</%s>' % tagname

                    # Start parsing tag body
                    state = STATE_INTAGBODY
                    iTagbody = i+1

                # else just keep trucking on the tag name
                i += 1

            elif state==STATE_INTAGBODY:
                # Check for closing tag
                if c[i:i+len(closingTag)] == closingTag:
                    # Store tag in metadata
                    tagbody = c[iTagbody:i]
                    tagbody = COMMENT_RE.sub('', tagbody)
                    self[tagname] = tagbody
                    state = STATE_SCANNING
                    i += len(closingTag)

                # else keep on trucking on tag body
                else:
                    i += 1

            assert i < len(c), "Bad metadata"

    def save( self ):
        """Writes metadata out to photo comments."""

        # load existing comments
        c = jpeg.getComments( self.fname )

        # Find previous metadata and get comments that precede and follow
        # our metadata (so we don't nuke somebody else's comments).
        before = ''
        after = ''
        i = c.find( BEGIN_TAG )
        if i == -1:
            # No previous tags
            before = c

        else:
            # Get before
            before = c[:i]

            # And get after
            i = c.find( END_TAG )
            assert i != -1, "Bad metadata"
            after = c[i+len( END_TAG ):]

        # Generate metadata block
        meta = BEGIN_TAG
        for ( name, value ) in self.items():
            meta = '%s<%s>%s</%s>' % ( meta, name, value, name )
        meta = '%s%s' % ( meta, END_TAG )

        # Write comments back out
        jpeg.setComments( '%s%s%s' % ( before, meta, after ), self.fname )

class Metadata(dict):
    def __init__(self, path):
        dirname, fname = os.path.split(path)
        metadata_fname = '.%s.metadata' % fname
        metadata_path = os.path.join(dirname, metadata_fname)
        self._file = metadata_path
        if not os.path.exists(metadata_path):
            self._convert(path)
        else:
            self.update(simplejson.load(open(metadata_path)))

    def _save(self):
        with open(self._file, 'w') as f:
            simplejson.dump(self, f, indent=4)

    def __setitem__(self, name, value):
        super(Metadata, self).__setitem__(name, value)
        self._save()

    def __delitem__(self, name):
        super(Metadata, self).__delitem__(name)
        self._save()

    def _convert(self, path):
        self.update(OldMetadata(path))
        if 'published' in self:
            published = self['published'] == 'True'
            super(Metadata, self).__setitem__('published', published)
        self._save()
