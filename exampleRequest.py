# -*- coding: utf-8 -*-
import requests

r = requests.post(
    'http://127.0.0.1:5000/api/search',
    json={
        'arabicText': u'محمد',
        'translation': 'en-hilali',
    },
)

print r.json()
