from __future__ import absolute_import

from timeago import setting


def locale_module(mod, locale):
    try:
        return getattr(getattr(getattr(mod, 'locales'), locale), 'LOCALE')
    except:
        raise


def timeago_template(locale, index, ago_in):
    '''
    simple locale implement
    '''
    try:
        LOCALE = __import__('timeago.locales.' + locale)
        LOCALE = locale_module(LOCALE, locale)
    except:
        locale = setting.DEFAULT_LOCALE
        LOCALE = __import__('timeago.locales.' + locale)
        LOCALE = locale_module(LOCALE, locale)

    return LOCALE[index][ago_in]
