import copy
import json
import pytest

from api.movies import handle, UnsupportedMethod


def test_unsupported_method():
    event = {
        "requestContext": {
            "http": {
                "method": "AA"
            }
        },
        "queryStringParameters": {
            "mal_id": "123"
        }
    }

    with pytest.raises(UnsupportedMethod):
        handle(event, None)


class TestPost:
    event = {
        "requestContext": {
            "http": {
                "method": "POST"
            }
        },
        "body": '{"api_id": "123", "api_name": "tmdb"}'
    }

    def test_success(self, mocked_movies_db):
        mocked_movies_db.table.query.side_effect = mocked_movies_db.NotFoundError

        res = handle(self.event, None)

        exp = {
            "body": json.dumps({"id": "e6d4fa11-1ad7-5137-a962-9554c8766356"}),
            "statusCode": 200
        }
        assert res == exp

    def test_already_exist(self, mocked_movies_db):
        mocked_movies_db.table.query.return_value = {
            "Items": [
                {
                    "tmdb_id": "123"
                }
            ]
        }

        res = handle(self.event, None)

        exp = {
            "body": json.dumps({"id": "e6d4fa11-1ad7-5137-a962-9554c8766356"}),
            "statusCode": 200
        }
        assert res == exp

    def test_no_body(self, mocked_movies_db):
        mocked_movies_db.table.query.return_value = {
            "Items": [
                {
                    "tmdb_id": "123"
                }
            ]
        }
        event = copy.deepcopy(self.event)
        del event["body"]

        res = handle(event, None)

        exp = {
            "statusCode": 400,
            "body": "Invalid post body"
        }
        assert res == exp

    def test_invalid_body(self, mocked_movies_db):
        mocked_movies_db.table.query.return_value = {
            "Items": [
                {
                    "mal_id": 123
                }
            ]
        }
        event = copy.deepcopy(self.event)
        event["body"] = '{"aa": "bb"}'

        res = handle(event, None)

        exp = {
            'body': '{"message": "Invalid post schema", '
                    '"error": "Additional properties are not allowed (\'aa\' was unexpected)"}',
            'statusCode': 400
        }
        assert res == exp


class TestGet:
    event = {
        "requestContext": {
            "http": {
                "method": "GET"
            }
        },
        "queryStringParameters": {
            "api_id": "123",
            "api_name": "tmdb",
        }
    }

    def test_success(self, mocked_movies_db):
        exp_res = {
            "id": "123"
        }
        mocked_movies_db.table.query.return_value = {
            "Items": [
                exp_res
            ]
        }

        res = handle(self.event, None)

        exp = {
            "statusCode": 200,
            "body": json.dumps(exp_res)
        }
        assert res == exp

    def test_not_found(self, mocked_movies_db):
        mocked_movies_db.table.query.side_effect = mocked_movies_db.NotFoundError

        res = handle(self.event, None)

        exp = {
            "statusCode": 404,
        }
        assert res == exp

    def test_empty_query_params(self):
        event = copy.deepcopy(self.event)
        event["queryStringParameters"] = {}

        res = handle(event, None)

        exp = {
            "statusCode": 400,
            "body": json.dumps({"error": "Please specify query parameters"})
        }
        assert res == exp

    def test_invalid_query_params(self):
        event = copy.deepcopy(self.event)
        event["queryStringParameters"] = {
            "abc": "123"
        }

        res = handle(event, None)

        exp = {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing api_id query parameter"})
        }
        assert res == exp

    def test_missing_api_name(self):
        event = copy.deepcopy(self.event)
        del event["queryStringParameters"]["api_name"]

        res = handle(event, None)

        exp = {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing api_name query parameter"})
        }
        assert res == exp

    def test_invalid_api_name(self):
        event = copy.deepcopy(self.event)
        event["queryStringParameters"]["api_name"] = "INVALID"

        res = handle(event, None)

        exp = {
            "statusCode": 400,
            "body": json.dumps({"error": "Unsupported query param"})
        }
        assert res == exp
