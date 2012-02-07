import urllib
import re
from math import floor
from django import template
from django.template.base import Node
from django.template.defaultfilters import stringfilter
from django.utils.encoding import force_unicode, smart_str
from django.utils.safestring import mark_safe
from django.utils.html import urlize

register = template.Library()

# ---- FILTERS

@register.filter
def even(value):
    return int(value) % 2 == 0

@register.filter
def odd(value):
    return not even(value)

@register.filter
@stringfilter
def split(value, character):

    """
    Simply calls built-in .split() method on the string, splitting it by the passed-in character

    Example

    list = 'Hey, there, dudes
    {{ list|split:',' }} yields ['Hey', 'there', 'dudes']
    """

    return [bit.strip() for bit in value.split(character)]

def urlquote_plus(url, safe='/'):
    
    """
    Copy of Django's django.utils.http.urlquote function, but using urllib.quote_plus() instead of quote()
    """
    
    return force_unicode(urllib.quote_plus(smart_str(url), smart_str(safe)))

@register.filter
@stringfilter
def urlencode_plus(value, safe=None):
    
    """
    URL encode method using '+' instead of spaces
    """
    
    kwargs = {}
    if safe is not None:
        kwargs['safe'] = safe
    return urlquote_plus(value, **kwargs)

@register.filter
@stringfilter
def possessive(value):
    
    """
    Possessive template filter. Takes a name and appends "'s" or "'" to the end
    depending on whether or not the name ends with an 's'
    
    Example:
    
    name = 'Sally'
    {{ name|possessive }} yields "Sally's"
    
    name = 'Chris'
    {{ name|possessive }} yields "Chris'"
    
    """
    
    return "%s'%s" % (value, '' if value.rstrip()[-1] == 's' else 's')

@register.filter
@stringfilter
def make_paragraphlist(value):
    
    """
    Takes a string and breaks it apart by newline/return characters and returns a list
    of paragraphs
    
    Example:
    
    'Hello there,
    
    My name is $horty'
    
    would yield:
    
    ['Hello there,', 'My name is $horty']
    
    """
    
    value = re.sub(r'[ \t]*(\r\n|\r|\n)[ \t]*', '\n', force_unicode(value)) # normalize newlines
    return re.split('\n{2,}', value)

@register.filter
@stringfilter
def twitterize(value):

    """
    Replace Twitter @ and # references with links to the user/hashtag
    """

    value = urlize(value)
    value = re.sub(r'(\s+|\A)@([a-zA-Z0-9\-_]*)\b',r'\1<a href="http://twitter.com/\2">@\2</a>', value)
    value = re.sub(r'(\s+|\A)#([a-zA-Z0-9\-_]*)\b',r'\1<a href="http://search.twitter.com/search?q=%23\2">#\2</a>',value)
    return mark_safe(value.replace('<a ', '<a target="_blank" '))

# ---- TAGS

# Regex for token keyword arguments

kwarg_re = re.compile(r"(?:(\w+\[?\]?\+?\-?)=)?(.+)")

def token_kwargs(bits, parser, support_legacy=False):
    
    """
    This is an exact copy of django.template.defaulttags.token_kwargs but
    with kwarg_re modified to accept params with brackets, like {% sometag hey[]='yo' %},
    and add/remove mofidiers, like {% sometag hey[]+='dude' %}
    """
    
    if not bits:
        return {}
    match = kwarg_re.match(bits[0])
    kwarg_format = match and match.group(1)
    if not kwarg_format:
        if not support_legacy:
            return {}
        if len(bits) < 3 or bits[1] != 'as':
            return {}

    kwargs = {}
    while bits:
        if kwarg_format: 
            match = kwarg_re.match(bits[0])
            if not match or not match.group(1):
                return kwargs
            key, value = match.groups()
            del bits[:1]
        else:
            if len(bits) < 3 or bits[1] != 'as':
                return kwargs
            key, value = bits[2], bits[0]
            del bits[:3]
        kwargs[key] = parser.compile_filter(value)
        if bits and not kwarg_format:
            if bits[0] != 'and':
                return kwargs
            del bits[:1]
    return kwargs

class QueryStringNode(Node):
    
    """
    Handle querystring tag parsing
    """
    
    def __init__(self, query_string, arguments={}, append=False):
        
        """
        Query string init
        
            `query_string`  (dict)  The variable containing the original query string we are analyzing/modifying
            `arguments`     (dict)  Token arguments dictionary -- variable names to be replaced with specified values
            `append`        (bool)  Boolean to determine whether the resulting query string starts with a '?' or a '&'
        
        """
        
        self.query_string_var = query_string
        self.query_string_data = template.Variable(self.query_string_var)
        self.arguments = arguments
        self.append = append
    
    def render(self, context):
        
        """
        Render query string
        """
        
        from copy import deepcopy
        
        # Grab query string context var
        
        try:
            query_string_data = deepcopy(self.query_string_data.resolve(context))
            if type(query_string_data) != dict:
                raise Exception()
        except:
            # Default to an empty query string dict
            query_string_data = {}
        
        # Sort through arguments and update query string data accordingly
        
        if self.arguments:
            for var, filter_expression in self.arguments.items():
                value = filter_expression.resolve(context, True)
                
                append = var[-1] == '+'
                remove = var[-1] == '-'
                if append or remove: var = var[0:-1]
                
                if query_string_data.has_key(var):
                    if type(query_string_data[var]) is list and (append or remove):
                        if remove:
                            try:
                                ind = query_string_data[var].index(value)
                                del query_string_data[var][ind]
                            except:
                                pass
                        else:
                            query_string_data[var].append(value)
                    elif value == None:
                        del query_string_data[var]
                    elif value:
                        query_string_data[var] = value
                elif value:
                    query_string_data[var] = [value] if append else value
        
        # Preparse for encoding
        
        query_string_data_list = []
        
        for key in query_string_data.keys():
            value = query_string_data[key]
            if type(value) in [list, tuple]:
                key = str(key).rstrip('[]') + '[]'
                for item in value:
                    query_string_data_list.append((key, str(item),))
            else:
                query_string_data_list.append((key, str(value),))
        
        # Build and return query string
        
        if query_string_data:
            return '%s%s' % ('&' if self.append else '?', urllib.urlencode(query_string_data_list))
        else:
            return ''

@register.tag(name='querystring')
def do_querystring(parser, token):
    
    """
    Query string tag: use a base query string dictionary, pass in arguments to replace particular query string variables.
    Returns a parsed out query string with the variables, like: ?foo=bar&filter=date
    
    Usage:
    
        base_query_string = {'foo': 'bar'}
        {% querystring base_query_string %}
        '?foo=bar'
    
        base_query_string = {'foo': 'bar', 'dude': 'hello'}
        {% querystring base_query_string %}
        '?foo=bar&dude=hello'
    
        base_query_string = {'foo': 'bar', 'dude': 'hello'}
        {% querystring base_query_string dude='smelly' %}
        '?foo=bar&dude=smelly'
    
    Pass 'append' keyword as the last argument for the query string to start with a '&' instead of a '?'
    
    See tests.py for more examples
    
    """
    
    bits = token.split_contents()
    tag = bits[0]
    arguments = {}
    append = False
    
    # Get base query string dict
    
    try:
        query_string_data = bits[1]
    except:
        raise template.TemplateSyntaxError('%s tag requires at least one argument: a base query string dictionary')
    
    # Check for arguments
    
    remaining_bits = bits[2:]
    
    if remaining_bits:
        
        # Check for 'append'
        
        if 'append' in remaining_bits:
            append = True
            remaining_bits.remove('append')
        
        # Parse remaining arguments
        
        try:
            arguments = token_kwargs(remaining_bits, parser)
        except:
            arguments = {}
    
    return QueryStringNode(query_string_data, arguments, append)

class ColumnizeNode(Node):
    
    
    """
    Handle 'columnize' tag parsing
    """
    
    def __init__(self, expression, target, columns, stacked=False):
        
        """
        Columnize init
        
            `expression`    The FilterExpression instance for the source to columnize from
            `target`        The target context variable for the resulting, sorted/columnized data
            `columns`       The number of columns to sort the source data into
            `stacked`       Whether the data should be sorted in a stacked manner or not. By default
                            the data is sorted into columns by alternating through the source, setting
                            this to True would break the contents of the source into columns, maintaining
                            its initial order.
        
        """
        
        self.expression = expression
        self.target = target
        self.columns = columns
        self.stacked = stacked
    
    def render(self, context):
        
        source_list = self.expression.resolve(context, True)
        
        if not source_list:
            context[self.target] = []
            return ''
        
        out = [[] for i in range(self.columns)]
        lengths = [0 for i in range(self.columns)]
        
        # Figure out how long each column should be
        
        if self.stacked:
            total = len(source_list)
            rem = total % self.columns
            
            if total > self.columns:
                lengths = [int(floor(float(total) / float(self.columns)))] * self.columns
            
            if rem:
                i = 0
                while rem:
                    lengths[i] += 1
                    rem -= 1
                    i += 1
            
        # Sort into columns
        
        i = 0
        column = 0
        
        for item in source_list:
            
            out[column].append(item)
            i += 1
            
            if self.stacked:
                if len(out[column]) == lengths[column]:
                    column += 1
            else:
                column = i % self.columns
        
        context[self.target] = out
        
        return ''

@register.tag(name='columnize')
def do_columnize(parser, token):
    
    """
    
    Take an iterable and sort the contents into the specified number of columns/buckets.
    By default, the contents are sorted by alternating columns, but the 'stacked' keyword 
    can be used to break the contents into columns in the order that they appear in the 
    iterable. So for example, the default behavior would look like this:
        
        mylist = [1, 2, 3, 4, 5]
        
        {% columnize mylist into 3 %}
        ...
        mylist = [[1, 4], [2, 5], [3]]
    
    Using the 'stacked' keyword looks like this:
        
        mylist = [1, 2, 3, 4, 5]
        
        {% columnize mylist into 3 stacked %}
        ...
        mylist = [[1, 2], [3, 4], [5]]
    
    Usage:
    
        Separate the contents of 'some_var' into 3 columns
        
        {% columnize some_var into 3 %}
        
        Separate the contents of 'my_var' into 4 columns and store as 'columnated'
        
        {% columnize my_var into 4 as columnated %}
        
        Separate the contents of 'rad_var' into 5 columns in its original order (stacked)
        
        {% columnize rad_var into 5 stacked %}
        
        Separate the contents of 'yay_var' into 8 columns in its original order (stacked) and store as 'yay_columns'
        
        {% columnize yay_var into 8 stacked as yay_columns %}
    
    """
    
    bits = token.contents.split()
    bits.pop(0) # Pop off 'columnize' bit
    
    if len(bits) < 3:
        raise template.TemplateSyntaxError("'columnize' template tag takes at least 3 arguments")
    
    source = bits.pop(0) # Store first argument as the 'source' variable
    
    # Validate 'into #' portion
    
    if bits[0] != 'into':
        raise template.TemplateSyntaxError("The 2nd argument for 'columnize' must be 'into', followed by the number of columns you want to divide into")
    
    bits.pop(0)
    
    try:
        columns = int(bits.pop(0))
    except:
        raise template.TemplateSyntaxError("The 3rd argument for 'columnize' must be numeric, indicating how many columns you want your variable divied into")
    
    # Validate optional 'stacked' keyword
    
    stacked = False
    
    if bits and bits[0] == 'stacked':
        stacked = True
        bits.pop(0)
    
    if bits:
        if len(bits) == 2 and bits[-2] == 'as':
            target = bits[-1]
        else:
            raise template.TemplateSyntaxError("The last 2 arguments of 'columnize' must be empty, or 'as' followed by the variable name you want the resulting columnized data stored into")
    else:
        target = source
    
    # Compile source expresion
    
    expression = parser.compile_filter(source)
    
    return ColumnizeNode(expression, target, columns, stacked)

class TruncateStringNode(Node):
    
    """
    Handle truncatestring tag parsing
    """
    
    def __init__(self, expression, length, end_text=''):
        self.expression = expression
        self.length = length
        self.end_text = end_text
    
    def render(self, context):
        
        value = self.expression.resolve(context, True)
        length = int(self.length.resolve(context, True))
        
        if len(value) <= length:
            return value
        
        # See if there's a custom string to append, otherwise use '...' by default
        
        try:
            end_text = str(self.end_text.resolve(context, True))
        except:
            end_text = '...'
        
        trunc = value[0:length].rstrip()
        if not trunc.endswith(end_text): trunc += end_text
        
        return trunc
        

@register.tag(name='truncatestring')
def do_truncatestring(parser, token):
    
    """
    Simple string truncation tag. This was made as a tag rather than a filter because filters only take 1 argument
    and we're allowing the flexibility to change the appended string if you want to.
    
    Usage:
        
        somevar = 'Hello'
        {% truncatestring somevar 3 %}
        'Hel...'
        
        somevar = 'Hello'
        {% truncatestring somevar 3 '!' %}
        'Hel!'
    
    """
    
    bits = token.contents.split()
    bits.pop(0) # Pop off 'truncatestring' bit
    
    try:
        var = bits.pop(0)
    except:
        raise template.TemplateSyntaxError("The 1st argument for 'truncatestring' must be the string or variable to truncate")
    
    try:
        length = bits.pop(0)
    except:
        raise template.TemplateSyntaxError("The 2nd argument for 'truncatestring' must be a number for the maximum length of the resulting string")
    
    end_text = bits.pop(0) if bits else None
    
    expression = parser.compile_filter(var)
    length = parser.compile_filter(length)
    if end_text: end_text = parser.compile_filter(end_text)
    
    return TruncateStringNode(expression, length, end_text)