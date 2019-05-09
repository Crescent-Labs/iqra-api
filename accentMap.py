# -*- coding: utf-8 -*-
from whoosh.compat import iteritems


accent_map = {
    u'آ': u'ا',
    u'ٱ': u'ا',
    u'أ': u'ا',
    u'إ': u'ا',
    u'ى': u'ي',
    u'ؤ': u'ء',
    u'ئ': u'ء',
    u'ه': u'ة',
}

accent_map = dict((ord(k), v) for k, v in iteritems(accent_map))
