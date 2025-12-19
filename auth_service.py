from authlib.integrations.requests_client import OAuth2Session

def create_oauth_session(client_id, client_secret, redirect_uri, scope=None):
    return OAuth2Session(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope
    )

def get_authorization_url(oauth_session, auth_url):
    return oauth_session.create_authorization_url(auth_url)

def fetch_token(oauth_session, token_url, code, client_id, client_secret):
    return oauth_session.fetch_token(
        url=token_url,
        code=code,
        client_id=client_id,
        client_secret=client_secret
    )

def get_user_info(oauth_session, userinfo_url):
    return oauth_session.get(userinfo_url).json()
