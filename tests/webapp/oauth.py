import json
import time
import urllib

import oauth2 as oauth


def oauth_signed(ptm, path, data):
    """Return params dict for OAuth-signed form-encoded POST request."""
    ds = ptm.sources["objectstore"].datasource
    uri = "http://localhost:80%s" % path
    user = ptm.project
    oauth_key = ds.oauth_consumer_key
    oauth_secret = ds.oauth_consumer_secret

    params = {
        'oauth_version': "1.0",
        'oauth_nonce': oauth.generate_nonce(),
        'oauth_timestamp': int(time.time()),
        'user': user,
        'data': urllib.quote(json.dumps(data)),
    }

    #There is no requirement for the token in two-legged
    #OAuth but we still need the token object.
    token = oauth.Token(key="", secret="")
    consumer = oauth.Consumer(key=oauth_key, secret=oauth_secret)

    params['oauth_token'] = token.key
    params['oauth_consumer_key'] = consumer.key

    req = oauth.Request(method="POST", url=uri, parameters=params)

    #Set the signature
    signature_method = oauth.SignatureMethod_HMAC_SHA1()

    #Sign the request
    req.sign_request(signature_method, consumer, token)

    return req
