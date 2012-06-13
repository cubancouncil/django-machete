from pprint import pprint
from urlparse import parse_qs
from django.test import TestCase
from django.template import Context, Template
from google_maps import find_geo, find_geo_point
from paginator import WindowPaginator, WindowPage

# ---- UTILITY

class BaseTestCase(TestCase):
    
    """
    Base TestCase with some simple template rendering helper functions
    """
    
    default_template_string = '' # Template string to include with all renders
    
    def render_template(self, template, context={}):
        
        """
        Simple helper function that returns a rendered template of the passed in
        template/context vars
        
        template - String or list/tuple of strings to act as a template
        context - Context variables to render into template
        
        """
        
        rendered, context = self.render(template, context)
        return rendered
    
    def render(self, template, context={}):
        
        strings = [self.default_template_string]
        
        if type(template) in (list, tuple):
            strings.extend(list(template))
        else:
            strings.append(template)
        
        template = ''.join(strings)
        
        rendered = Template(template).render(Context(context))
        
        return rendered, context
    
    def nice_form_errors(self, form):

        """
        Format form errors into a nice comma separated list like:

            field_name1: error1, error2, field_name2: error1, error2

        ...for easier-to-read reporting
        """

        if form.errors:
            return ', '.join(['%s: %s' % (row[0], ', '.join(row[1])) for row in form.errors.items()])
        return ''

# ---- TEST CASES

class GoogleMapsTestCase(TestCase):
    
    """
    Test case for google_maps.py
    """
    
    def test_find_geo(self):
        
        # Valid locations
        
        locations = [
            '7719 N. McKenna Ave., Portland, OR',
            'Los Angeles, CA',
            '90210'
        ]
        
        for location in locations:
            self.assertIsInstance(find_geo(location), dict, "Valid address doesn't return a dict object: %s" % location)
        
        # Invalid locations
        
        self.assertFalse(find_geo(''), "Blank location doesn't return false")

class WindowPaginatorTestCase(TestCase):
    
    """
    Test case for WindowPaginator
    """
    
    def test_window_paginator(self):

        items = range(0, 86)
        pager = WindowPaginator(items, 5) # 86 objects, 18 pages

        # ---- Odd window

        window = 5
        page = pager.page(1, 5)

        self.assertIsInstance(page, WindowPage)

        # Test sets by window size, then a tuple: index 0 is pages that should equate to the page range in index 1

        test_sets = {
            4: (
                ([1,2], [1, 2, 3, 4, 5, None, 18],), # Lower end
                ([6], [1, None, 5, 6, 7, 8, None, 18],), # Middle
                ([16, 17, 18], [1, None, 14, 15, 16, 17, 18],), # Higher
            ),
            5: (
                ([1, 2, 3], [1, 2, 3, 4, 5, 6, None, 18],), # Lower end
                ([5], [1, None, 3, 4, 5, 6, 7, None, 18],), # Middle
                ([16, 17, 18], [1, None, 13, 14, 15, 16, 17, 18]) # Higher
            ),
            18: (
                (range(1, 19), range(1, 19),),
            )
        }

        for window in test_sets.keys():
            for test in test_sets[window]:
                for num in test[0]:
                    page = pager.page(num, window=window)
                    self.assertIsInstance(page, WindowPage, 'Instance is not a `WindowPage` object')
                    self.assertEqual(page.page_range, test[1], 'Window %d, page %d page range incorrect' % (window, num))

# ---- TEMPLATE TAGS

class MacheteFiltersTestCase(BaseTestCase):
    
    default_template_string = '{% load machete %}'
    
    def test_even(self):
        evens = [0, 2, 4, 6, 8, 10, 12, 24.0, -4, '100']
        for num in evens:
            self.assertTrue(self.render_template('{{ num|even }}', {'num': num}))
    
    def test_odd(self):
        odds = [1, 3, 5, 21.0, -7, '5']
        for num in odds:
            self.assertTrue(self.render_template('{{ num|odd }}', {'num': num}))
        

class QueryStringTagTestCase(BaseTestCase):
    
    """
    Test case for 'querystring' template tag
    """
    
    default_template_string = '{% load machete %}'
    
    def test_querystring(self):
        
        # Empty
        
        rendered = self.render_template(
            '{% querystring qs %}',
            {'qs': {}}
        )
        
        self.assertEqual(rendered, '', "Empty query string doesn't return an empty string")
        
        # Simple
        
        qs = {'page': 1}
        rendered = self.render_template(
            '{% querystring qs %}',
            {'qs': qs}
        )
        
        self.assertEqual(rendered[0], '?')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('page=1'), "Simple query string is incorrect: %s" % qs)
        
        # Multiple
        
        qs = {'page': 2, 'artist': 57}
        rendered = self.render_template(
            '{% querystring qs %}',
            {'qs': qs}
        )
        
        self.assertEqual(rendered[0], '?')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('page=2&artist=57'), "Multiple query string is incorrect: %s" % qs)
        
        qs = {'page': 3, 'artist': 14, 'sort': 'DESC'}
        rendered = self.render_template(
            '{% querystring qs %}',
            {'qs': qs}
        )
        
        self.assertEqual(rendered[0], '?')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('page=3&artist=14&sort=DESC'), "Multiple query string is incorrect: %s" % qs)
        
        # Inline var addition
        
        qs = {'page': 1}
        expr = "{% querystring qs year='2011' %}"
        rendered = self.render_template(
            expr,
            {'qs': qs}
        )
        
        self.assertEqual(rendered[0], '?')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('page=1&year=2011'), "Inline addition query string is incorrect: %s, %s" % (qs, expr))
    
    def test_querystring_inlineargs(self):
        
        qs = {'page': 1}
        expr = "{% querystring qs year=2011 title=title %}"
        rendered = self.render_template(
            expr,
            {'qs': qs, 'title': 'Some Title'}
        )
        
        self.assertEqual(rendered[0], '?')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('page=1&year=2011&title=Some+Title'), "Inline addition query string with context variable is incorrect: %s, %s" % (qs, expr))
    
    def test_querystring_inline_unset(self):
        
        # Inline variable un-setting
        
        qs = {'page': 1}
        expr = "{% querystring qs page=None %}",
        rendered = self.render_template(
            expr,
            {'qs': qs}
        )
        
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs(''), "Inline variable un-setting is incorrect: %s, %s" % (qs, expr))
    
    def test_querystring_inline_context_var(self):
        
        # Inline addition with context variable
        
        qs = {'page': 1, 'title': 'Some Title'}
        expr = "{% querystring qs year='2011' title=title %}"
        rendered = self.render_template(
            expr,
            {'qs': qs, 'title': 'Some Context Title'}
        )
        
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('page=1&year=2011&title=Some+Context+Title'), "Inline addition query string with context variable is incorrect: %s, %s" % (qs, expr))
        
        # Inline addition with nonexistent context variable
        
        qs = {'page': 1}
        expr = "{% querystring qs year='2011' title=title %}"
        rendered = self.render_template(
            expr,
            {'qs': qs}
        )
        
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('page=1&year=2011'), "Inline addition query string with nonexistent context variable is incorrect: %s, %s" % (qs, expr))
    
    def test_querystring_append(self):
        
        # Inline 'append' keyword
        
        qs = {'page': 1}
        expr = "{% querystring qs year='2010' append %}"
        rendered = self.render_template(
            expr,
            {'qs': qs}
        )
        
        self.assertEqual(rendered[0], '&')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('&page=1&year=2010'), "Inline 'append' keyword is incorrect: %s, %s" % (qs, expr))
    
    def test_querystring_mix(self):
        
        # Mix and match 1
        
        qs = {'page': 1, 'filter': 'date'}
        expr = "{% querystring qs page=None sort='ASC' %}"
        rendered = self.render_template(
            expr,
            {'qs': qs}
        )
        
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('filter=date&sort=ASC'), "Mix and match 1 is incorrect: %s, %s" % (qs, expr))
        
        # Mix and match 2
        
        qs = {'page': 40, 'artist': 50, 'title': 'Some Title'}
        expr = "{% querystring qs artist=current_artist foo='bar' %}"
        rendered = self.render_template(
            expr,
            {
                'qs': qs,
                'current_artist': 'Tom Waits'
            }
        )
        
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('page=40&artist=Tom+Waits&title=Some+Title&foo=bar'), "Mix and match 2 is incorrect: %s, %s" % (qs, expr))
        
        # Mix and match 3
        
        qs = {'page': 40, 'artist': 50, 'title': 'Some Title'}
        expr = "{% querystring qs artist=current_artist title=None append %}"
        rendered = self.render_template(
            expr,
            {
                'qs': qs,
                'current_artist': 'Tom Waits'
            }
        )
        
        self.assertEqual(rendered[0], '&')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('&page=40&artist=Tom+Waits'), "Mix and match 3 is incorrect: %s, %s" % (qs, expr))
    
    def test_querystring_array(self):
        
        """
        Test array style GET vars, e.g. ?artists[]=40&artists[]=50
        """
        
        # Simple
        
        qs = {'page': 40, 'artists': [50, 60, 70], 'title': 'Some Title'}
        expr = "{% querystring qs %}"
        rendered = self.render_template(
            expr,
            {'qs': qs}
        )
        
        self.assertEqual(rendered[0], '?')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('&page=40&artists[]=50&artists[]=60&artists[]=70&title=Some+Title'), "Array query string test incorrect: %s, %s" % (qs, expr))
        
        # Inline
        
        qs = {'page': 1, 'artists[]': [40, 50]}
        expr = "{% querystring qs artists[]='30' %}"
        rendered = self.render_template(
            expr,
            {'qs': qs}
        )
        
        self.assertEqual(rendered[0], '?')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('&page=1&artists[]=30'), "Array inline query string test incorrect: %s, %s" % (qs, expr))
        
        # Variable argument
        
        qs = {'page': 1, 'artists[]': [40, 50]}
        expr = "{% querystring qs artists[]=somenum type='Rad' %}"
        rendered = self.render_template(
            expr,
            {
                'qs': qs,
                'somenum': 30
            }
        )
        
        self.assertEqual(rendered[0], '?')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('&page=1&artists[]=30&type=Rad'), "Array variable argument query string test incorrect: %s, %s" % (qs, expr))
    
    def test_querystring_array_append(self):
    
        # Array append syntax
        
        qs = {'page': 40, 'artists[]': [50, 60, 70], 'title': 'Some Title'}
        expr = "{% querystring qs artists[]+=80 %}"
        rendered = self.render_template(
            expr,
            {'qs': qs}
        )
        
        self.assertEqual(rendered[0], '?')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('&page=40&artists[]=50&artists[]=60&artists[]=70&artists[]=80&title=Some+Title'), "Array append query string test incorrect: %s, %s" % (qs, expr))
        
        # Array append syntax 2
        
        qs = {'page': 40, 'artists[]': [50, 60, 70], 'title': 'Some Title'}
        expr = "{% querystring qs artists[]+=80 %}"
        rendered = self.render_template(
            expr,
            {'qs': qs}
        )
        
        self.assertEqual(rendered[0], '?')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('&page=40&artists[]=50&artists[]=60&artists[]=70&artists[]=80&title=Some+Title'), "Array append query string test incorrect: %s, %s" % (qs, expr))
    
    def test_querystring_array_remove(self):

        # Array remove syntax

        qs = {'page': 40, 'artists[]': [50, 60, 70], 'title': 'Some Title'}
        expr = "{% querystring qs artists[]-=60 %}"
        rendered = self.render_template(
            expr,
            {'qs': qs}
        )

        self.assertEqual(rendered[0], '?')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('&page=40&artists[]=50&artists[]=70&title=Some+Title'), "Array remove query string test incorrect: %s, %s" % (qs, expr))

        # Array remove syntax 2

        qs = {'page': 40, 'artists[]': [50, 60, 70], 'title': 'Some Title'}
        expr = "{% querystring qs artists[]-=80 %}"
        rendered = self.render_template(
            expr,
            {'qs': qs}
        )

        self.assertEqual(rendered[0], '?')
        self.assertEqual(parse_qs(rendered.lstrip('?')), parse_qs('&page=40&artists[]=50&artists[]=60&artists[]=70&title=Some+Title'), "Array remove non-existent query string test incorrect: %s, %s" % (qs, expr))

class ColumnizeTagTestCase(BaseTestCase):
    
    """
    Tests for 'columnize' template tag
    """
    
    default_template_string = '{% load machete %}'
    
    def test_basic(self):
        
        # Basic
        
        mylist = ['hello', 'there', 'dude']
        expr = '{% columnize mylist into 3 %}'
        rendered, context = self.render(expr, {'mylist': mylist})
        
        self.assertEqual(len(context['mylist']), 3, "The length of 'mylist' in the resulting context is not 3")
        
        self.assertEqual(len(context['mylist'][0]), 1, "The first column's length is not equal to 1")
        self.assertEqual(context['mylist'][0][0], 'hello', "'hello' was not properly sorted into the first column")
        
        self.assertEqual(len(context['mylist'][1]), 1, "The second column's length is not equal to 1")
        self.assertEqual(context['mylist'][1][0], 'there', "'there' was not properly sorted into the second column")
        
        self.assertEqual(len(context['mylist'][2]), 1, "The third column's length is not equal to 1")
        self.assertEqual(context['mylist'][2][0], 'dude', "'dude' was not properly sorted into the third column")
        
        # Unequal column distribution
        
        mylist = ['hello', 'there', 'dude']
        expr = '{% columnize mylist into 2 %}'
        rendered, context = self.render(expr, {'mylist': mylist})
        
        self.assertEqual(len(context['mylist']), 2, "The length of 'mylist' in the resulting context is not 2")
        
        self.assertEqual(len(context['mylist'][0]), 2, "The first column's length is not equal to 2")
        self.assertEqual(context['mylist'][0][0], 'hello', "'hello' was not properly sorted into the first column")
        self.assertEqual(context['mylist'][0][1], 'dude', "'dude' was not properly sorted into the first column")
        
        self.assertEqual(len(context['mylist'][1]), 1, "The second column's length is not equal to 1")
        self.assertEqual(context['mylist'][1][0], 'there', "'there' was not properly sorted into the second column")
    
    def test_as_keyword(self):
        
        mylist = ['some', 'test', 'list', 'dude']
        expr = '{% columnize mylist into 3 as differentlist %}'
        rendered, context = self.render(expr, {'mylist': mylist})
        
        self.assertEqual(context['mylist'], mylist, "The original 'mylist' differs from the context's 'mylist'")
        self.assertEqual(len(context['differentlist']), 3, "The length of 'differentlist' in the resulting context is not 3")
        
        self.assertEqual(len(context['differentlist'][0]), 2, "The first column's length is not equal to 2")
        self.assertEqual(context['differentlist'][0][0], 'some', "'some' was not properly sorted into the first column")
        self.assertEqual(context['differentlist'][0][1], 'dude', "'dude' was not properly sorted into the first column")
        
        self.assertEqual(len(context['differentlist'][1]), 1, "The second column's length is not equal to 1")
        self.assertEqual(context['differentlist'][1][0], 'test', "'test' was not properly sorted into the second column")
        
        self.assertEqual(len(context['differentlist'][2]), 1, "The third column's length is not equal to 1")
        self.assertEqual(context['differentlist'][2][0], 'list', "'test' was not properly sorted into the third column")
    
    def test_stacked_keyword(self):
        
        mylist = ['some', 'test', 'list', 'dude']
        expr = '{% columnize mylist into 3 stacked %}'
        rendered, context = self.render(expr, {'mylist': mylist})
        
        self.assertEqual(len(context['mylist']), 3, "The length of 'mylist' in the resulting context is not 3")
        
        self.assertEqual(context['mylist'][0], ['some', 'test'], "First column was not sorted properly")
        self.assertEqual(context['mylist'][1], ['list'], "Second column was not sorted properly")
        self.assertEqual(context['mylist'][2], ['dude'], "Third column was not sorted properly")
        
        # Longer list
        
        mylist = ['some', 'list', 'to', 'test', 'with', 'and', 'such', 'dude', 'awesome']
        expr = '{% columnize mylist into 4 stacked as testlist %}'
        rendered, context = self.render(expr, {'mylist': mylist})
        
        self.assertEqual(context['mylist'], mylist, "The value of 'mylist' changed in the resulting context")
        self.assertEqual(len(context['testlist']), 4, "The length of 'testlist' is incorrect")
        
        self.assertEqual(len(context['testlist'][0]), 3, "The first column's length is incorrect")
        self.assertEqual(context['testlist'][0], ['some', 'list', 'to'], "The first column was not sorted properly")
        
        self.assertEqual(len(context['testlist'][1]), 2, "The second column's length is incorrect")
        self.assertEqual(context['testlist'][1], ['test', 'with'], "The second column was not sorted properly")
        
        self.assertEqual(len(context['testlist'][2]), 2, "The third column's length is incorrect")
        self.assertEqual(context['testlist'][2], ['and', 'such'], "The third column was not sorted properly")
        
        self.assertEqual(len(context['testlist'][3]), 2, "The fourth column's length is incorrect")
        self.assertEqual(context['testlist'][3], ['dude', 'awesome'], "The fourth column was not sorted properly")

class TruncateStringTagTestCase(BaseTestCase):
    
    """
    Tests for 'truncatestring' template tag
    """
    
    default_template_string = '{% load machete %}'
    
    def test_basic(self):
        
        # Basic truncation
        
        mystr = 'Hello'
        expr = "{% truncatestring mystr 4 %}"
        rendered = self.render_template(
            expr,
            {'mystr': mystr}
        )
        
        self.assertEqual(rendered, 'Hell...')
        
        # No truncation
        
        mystr = 'Hello'
        expr = "{% truncatestring mystr 5 %}"
        rendered = self.render_template(
            expr,
            {'mystr': mystr}
        )
        
        self.assertEqual(rendered, 'Hello')
        
        # Append string
        
        mystr = 'Hello there'
        expr = "{% truncatestring mystr 7 '!!!' %}"
        rendered = self.render_template(
            expr,
            {'mystr': mystr}
        )
        
        self.assertEqual(rendered, 'Hello t!!!')
        
        # Another append string
        
        mystr = 'Hello there'
        expr = "{% truncatestring mystr 6 '' %}"
        rendered = self.render_template(
            expr,
            {'mystr': mystr}
        )
        
        self.assertEqual(rendered, 'Hello')
        
        # No double-appending
        
        mystr = 'Hello there... how are you?'
        expr = "{% truncatestring mystr 14 %}"
        rendered = self.render_template(
            expr,
            {'mystr': mystr}
        )
        
        self.assertEqual(rendered, 'Hello there...')