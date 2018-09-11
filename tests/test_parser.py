from django.test import TestCase
from customquery import Parser, exceptions
from .models import TestModel
from django.db.models import Q

class BaseTest(TestCase):
    def setUp(self):
        self.parser = Parser(TestModel)

    def parse(self, query):
        return self.parser.parse(query)

class SingleParserTest(BaseTest):

    def test_number(self):
        self.assertEquals(self.parse("numfield=1"), Q(numfield=1))

    def test_whitespaces_are_ignored(self):
        self.assertEquals(self.parse("numfield = 1"), Q(numfield=1))
        self.assertEquals(self.parse("numfield  = 1"), Q(numfield=1))

    def test_basic_operators(self):
        self.assertEquals(self.parse("numfield > 1"), Q(numfield__gt=1))
        self.assertEquals(self.parse("numfield >= 1"), Q(numfield__gte=1))
        self.assertEquals(self.parse("numfield < 1"), Q(numfield__lt=1))
        self.assertEquals(self.parse("numfield <= 1"), Q(numfield__lte=1))

    def test_basic_operators(self):
        self.assertEquals(self.parse("numfield > 1"), Q(numfield__gt=1))
        self.assertEquals(self.parse("numfield >= 1"), Q(numfield__gte=1))
        self.assertEquals(self.parse("numfield < 1"), Q(numfield__lt=1))
        self.assertEquals(self.parse("numfield <= 1"), Q(numfield__lte=1))

    def test_not(self):
        self.assertEquals(self.parse("numfield <> 1"), ~Q(numfield=1))
        self.assertEquals(self.parse("numfield != 1"), ~Q(numfield=1))

    def test_single_string(self):
        self.assertEquals(self.parse('charfield=foo'), Q(charfield="foo"))
        self.assertEquals(self.parse('charfield="foo"'), Q(charfield="foo"))
        self.assertEquals(self.parse("charfield='foo'"), Q(charfield="foo"))
        
    def test_string_phrase(self):
        self.assertEquals(self.parse('charfield="foo bar"'), Q(charfield="foo bar"))
        self.assertEquals(self.parse("charfield='foo bar'"), Q(charfield="foo bar"))

    def test_related_field(self):
        self.assertEquals(self.parse('related__name="foo bar"'), Q(related__name="foo bar"))

    def test_related_field_can_be_acessed_with_doc(self):
        self.assertEquals(self.parse('related.name="foo bar"'), Q(related__name="foo bar"))

class SimpleOperatorTest(BaseTest):

    def test_or(self):
        self.assertEquals(self.parse('numfield=1 or charfield="foo"'),
                          Q(numfield=1) | Q(charfield="foo"))
        self.assertEquals(self.parse('numfield=1 OR charfield="foo"'),
                          Q(numfield=1) | Q(charfield="foo"))
        self.assertEquals(self.parse('numfield = 1 or charfield="foo"'),
                          Q(numfield=1) | Q(charfield="foo"))
        self.assertEquals(self.parse("numfield=1 OR charfield = 'foo'"),
                          Q(numfield=1) | Q(charfield="foo"))
    def test_and(self):
        self.assertEquals(self.parse('numfield=1 and charfield="foo"'),
                          Q(numfield=1) & Q(charfield="foo"))
        self.assertEquals(self.parse('numfield=1 AND charfield="foo"'),
                          Q(numfield=1) & Q(charfield="foo"))

class ParenthesisTest(BaseTest):

    def test_one_parenthesis(self):
        self.assertEquals(self.parse('numfield=1 or (numfield > 5 and numfield < 10)'),
                          Q(numfield=1) | (Q(numfield__gt=5) & Q(numfield__lt=10)))
        
    def test_complex_parenthesis(self):
        query = ('numfield=1 or ' +
                 '(numfield > 5 and (numfield <= 10 or charfield = "foobar"))')
        expected = Q(numfield=1) | (Q(numfield__gt=5) & (Q(numfield__lte=10) | Q(charfield="foobar")))

        self.assertEquals(self.parse(query), expected)

class BetweenTest(BaseTest):

    def test_between_number(self):
        self.assertEquals(self.parse('numfield between 1 and 5'), Q(numfield__gte=1) & Q(numfield__lte=5))
        
    def test_between_char(self):
        self.assertEquals(self.parse('charfield between "foo" and "foo bar"'),
                          Q(charfield__gte="foo") & Q(charfield__lte="foo bar"))

class ValidationTest(BaseTest):

    def test_field_must_exist_in_model(self):
        # Use field that is not present on TestModel
        try:
            self.parse("unknown > 10")
        except exceptions.FieldDoesNotExist as e:
            self.assertEquals(e.field, 'unknown')
        else:
            self.fail("Unknown field shouldn't be accepted")

    def test_parenthesis_must_match(self):
        try:
            self.parse("(numfield > 10")
        except exceptions.ParenthesisDontMatch:
            pass
        else:
            self.fail("Parenthesis matching is not properly validated")

    def test_check_unknown_operator(self):
        try:
            parsed = self.parse("numfield ? 10")
            import ipdb; ipdb.set_trace()
        except exceptions.UnknownOperator as e:
            self.assertEquals(e.operator, "?")
        else:
            self.fail("Operator should be checked")
