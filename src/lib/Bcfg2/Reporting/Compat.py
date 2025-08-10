""" Compatibility imports for Django. """

from django import VERSION
from django.db import transaction
from django.urls import re_path

# Django 1.6 deprecated commit_on_success() and introduced atomic() with
# similar semantics.
if VERSION[0] == 1 and VERSION[1] < 6:
    transaction.atomic = transaction.commit_on_success

try:
    from django.conf.urls import patterns
except:
    # Django > 1.10
    def patterns(_prefix, *urls):
        url_list = list()
        for u in urls:
            if isinstance(u, (list, tuple)):
                u = re_path(*u)
            url_list.append(u)
        return url_list
