import simplejson
import webob

class JSONResponse(webob.Response):
    def __init__(self, payload):
        encoded = simplejson.dumps(payload)
        super(JSONResponse, self).__init__(
            encoded,
            content_type='application/json'
        )
