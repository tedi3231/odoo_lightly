# -*- coding: utf-8 -*-
# ----------------------------------------------------------
# OpenERP Session layer
# ----------------------------------------------------------
from werkzeug.contrib.sessions import SessionStore
import cPickle
import logging

ONE_WEEK_IN_SECONDS = 60 * 60 * 24 * 7
_logger = logging.getLogger(__name__)


class RedisSessionStore(SessionStore):
    def __init__(self, redis_client, salt, *args, **kwargs):
        self.redis = redis_client
        self.generate_salt = salt
        self.key_template = 'session:%s'
        super(RedisSessionStore, self).__init__(*args, **kwargs)

    def new(self):
        return self.session_class({}, self.generate_key(self.generate_salt), True)

    def get_session_key(self, sid):
        if isinstance(sid, unicode):
            sid = sid.encode('utf-8')
        return self.key_template % sid

    def save(self, session):
        data = cPickle.dumps(dict(session))
        key = self.get_session_key(session.sid)
        try:
            return self.redis.setex(key, ONE_WEEK_IN_SECONDS, data)
        except Exception as ex:
            _logger.error("Error on setting session data", exc_info=ex)

    def delete(self, session):
        try:
            key = self.get_session_key(session.sid)
            return self.redis.delete(key)
        except Exception as ex:
            _logger.error("Error on deleting session data", exc_info=ex)

    def get(self, sid):
        if not self.is_valid_key(sid):
            return self.new()

        key = self.get_session_key(sid)
        try:
            saved = self.redis.get(key)
            data = cPickle.loads(saved) if saved else {}
        except Exception as ex:
            _logger.error("Error on getting session data", exc_info=ex)
            data = {}
        return self.session_class(data, sid, False)
