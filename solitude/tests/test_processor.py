from nose.tools import eq_

from solitude.processor import JSONProcessor, sanitise


sanitise_dicts = [
    [None, None],
    [{'foo': 'bar'}, {'foo': 'bar'}],
    [{'foo': {'pin': 'bar'}}, {'foo': {'pin': '*' * 8}}]
]

process_data = [
    [{'sentry.interfaces.Http': {'data': '{"pin": "1234"}'}},
     {'sentry.interfaces.Http': {'data': '{"pin": "********"}'}}],
    # All the following remain unchanged.
    [{'sentry.interfaces.Http': {}},
     {'sentry.interfaces.Http': {}}],
    [{'sentry.interfaces.Http': 'None'},
     {'sentry.interfaces.Http': 'None'}],
    [{'sentry.interfaces.Http': {'data': 'blargh!'}},
     {'sentry.interfaces.Http': {'data': 'blargh!'}}],
    [{}, {}],
]


def test_processor():
    for value, expected in process_data:
        eq_(JSONProcessor('').process(value), expected)


def test_sanitise():
    for value, expected in sanitise_dicts:
        eq_(sanitise(value, ['pin']), expected)
