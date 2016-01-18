from django.db import models
from distutils.version import StrictVersion
from django import get_version
from django.conf import settings

if StrictVersion(get_version()) >= StrictVersion('1.9.0'):
    from django.db.models.query import ModelIterable
else:
    ModelIterable = object  # just mocking it


class TranslationMixin(object):
    TRANSLATIONS_DEFAULT = getattr(settings, 'TRANSLATIONS_DEFAULT', 'en_us')
    TRANSLATIONS_MAP = getattr(settings, 'TRANSLATIONS_MAP', {'en': 'en_us'})
    _default_language_code = TRANSLATIONS_DEFAULT

    def get_language_key(self, language_code):
        return self.TRANSLATIONS_MAP.get(language_code, language_code)

    def is_default_language(self, language_code):
        language_code = self.get_language_key(language_code)
        return language_code == self.TRANSLATIONS_DEFAULT


class TranslationModelIterable(ModelIterable):
    def __iter__(self):
        for obj in super(TranslationModelIterable, self).__iter__():
            if self.queryset._language_code:
                obj.language(self.queryset._language_code)
            yield obj


class TranslationQuerySet(models.QuerySet, TranslationMixin):
    _language_code = None

    def __init__(self, model=None, query=None, using=None, hints=None):
        super(TranslationQuerySet, self).__init__(model, query, using, hints)
        self._iterable_class = TranslationModelIterable

    def language(self, language_code):
        self._language_code = language_code
        return self

    def _clone(self, **kwargs):
        clone = super(TranslationQuerySet, self)._clone(**kwargs)
        clone._language_code = self._language_code
        return clone

    def iterator(self):
        for obj in super(TranslationQuerySet, self).iterator():
            if self._language_code:
                obj.language(self._language_code)
            yield obj


class TranslationManager(models.Manager, TranslationMixin):
    def get_queryset(self):
        qs = TranslationQuerySet(self.model, using=self.db, hints=self._hints)
        return qs

    def language_or_default(self, language_code):
        language_code = self.get_language_key(language_code)
        qs = self.get_queryset()
        qs._language_code = language_code
        if self.is_default_language(language_code):
            return qs
        return qs.language(language_code)

    def language(self, language_code):
        language_code = self.get_language_key(language_code)
        return self.language_or_default(language_code).filter(
            translations__has_key=(language_code))
