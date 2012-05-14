from django import template
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def dv_unorderedlist(list_, autoescape=None):
    """
    This entire function was adapted from the unordered_list function
    in "django/template/defaultfilters.py
    """
    if autoescape:
        from django.utils.html import conditional_escape
        escaper = conditional_escape
    else:
        escaper = lambda x: x

    def _helper(list_, tabs=1):

        indent = u'\t' * tabs
        output = []

        list_length = len(list_)
        i = 0
        while i < list_length:
            title = list_[i]
            sublist = ''
            sublist_item = None
            if isinstance(title, (list, tuple)):
                sublist_item = title
                title = ''
            elif i < list_length - 1:
                next_item = list_[i+1]
                if next_item and isinstance(next_item, (list, tuple)):
                    # The next item is a sub-list.
                    sublist_item = next_item
                    # We've processed the next item now too.
                    i += 1

            if sublist_item:
                sublist = _helper(sublist_item, tabs+1)
                sublist = '\n%s<ul>\n%s\n%s</ul>\n%s' % (indent, sublist, indent, indent)

            #####
            # Add an anchor to each list item.  Set the data in the anchor to the
            # view's readable name.  Set the href to the api name of the view.
            #####
            if type(title) == dict:
                a = '<a href="#%s">%s</a>' % (force_unicode(title['name']), force_unicode(title['read_name']))
                output.append('%s<li>%s%s</li>' % (indent, escaper(a), sublist))
            elif title:
                output.append('%s<li>%s%s</li>' % (indent, escaper('<a href="#">' + force_unicode(title) + '</a>'), sublist))
            else:
                output.append('%s<li>%s%s</li>' % (indent, escaper(force_unicode(title)), sublist))
            i += 1
        return '\n'.join(output)

    return mark_safe( _helper(list_) )
