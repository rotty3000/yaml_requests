from unittest import TestCase

from yaml_requests.utils.template import Environment
from yaml_requests._request import Request, RequestState

class RequestStateTest(TestCase):
    def test_init_with_unknown_state_raises(self):
        with self.assertRaises(ValueError):
            RequestState('UNKNOWN')

REQUEST_WITH_VARIABLE = dict(
    name='Get {{ url }}',
    get=dict(url='{{ url }}')
)

REQUEST_WITOUT_METHOD = dict(
    name='HTTP method missing'
)

class MockResponse:
    def __init__(self, ok):
        self.ok = ok

    def __call__(self, *args, **kwargs):
        return self


class RequestTest(TestCase):
    def test_init_sets_error_when_template_processing_fails(self):
        env = Environment()

        req = Request(REQUEST_WITH_VARIABLE, env)
        self.assertEqual(req.state, RequestState.ERROR)

        env.register('url','http://localhost:5000')
        req = Request(REQUEST_WITH_VARIABLE, env)
        self.assertIsNone(req.state)

    def test_init_sets_error_when_no_http_method(self):
        env = Environment()

        req = Request(REQUEST_WITOUT_METHOD, env)
        self.assertEqual(req.state, RequestState.ERROR)

    def test_send_invalid_does_not_raise(self):
        env = Environment()

        req = Request(REQUEST_WITOUT_METHOD, env)
        self.assertEqual(req.state, RequestState.ERROR)

        req.send(lambda: None)
        self.assertIsNone(req.response)

    def test_send_sets_status(self):
        env = Environment()
        env.register('url','http://localhost:5000')

        for raise_for_status, response_ok, expected in [
            (None, False, RequestState.FAILURE),
            (None, True, RequestState.SUCCESS),
            (True, False, RequestState.FAILURE),
            (True, True, RequestState.SUCCESS),
            (False, False, RequestState.NOT_RAISED),
            (False, True, RequestState.SUCCESS),
        ]:
            if raise_for_status is not None:
                request_dict = {
                    **REQUEST_WITH_VARIABLE,
                    'raise_for_status': raise_for_status}
            else:
                request_dict = REQUEST_WITH_VARIABLE

            req = Request(request_dict, env)
            req.send(MockResponse(response_ok))
            self.assertEqual(
                req.state,
                expected,
                msg=f'{raise_for_status}, {response_ok} => {str(req.state)}')