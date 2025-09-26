import datetime
import json
from unittest.mock import patch
import requests_mock
from parameterized import parameterized
from pylti1p3.grade import Grade
from pylti1p3.lineitem import LineItem
from .request import FakeRequest
from .tool_config import get_test_tool_conf
from .base import TestServicesBase


class TestGrades(TestServicesBase):
    # pylint: disable=import-outside-toplevel

    @parameterized.expand(
        [["line_items_exist", True], ["line_items_dont_exist", False]]
    )
    def test_get_grades(
        self, name, line_items_exist
    ):  # pylint: disable=unused-argument
        from pylti1p3.contrib.django import DjangoMessageLaunch

        tool_conf = get_test_tool_conf()

        with patch.object(
            DjangoMessageLaunch, "_get_jwt_body", autospec=True
        ) as get_jwt_body:
            message_launch = DjangoMessageLaunch(FakeRequest(), tool_conf)
            line_items_url = "http://canvas.docker/api/lti/courses/1/line_items"
            get_jwt_body.side_effect = lambda x: self._get_jwt_body()
            with patch("socket.gethostbyname", return_value="127.0.0.1"):
                with requests_mock.Mocker() as m:
                    m.post(
                        self._get_auth_token_url(),
                        text=json.dumps(self._get_auth_token_response()),
                    )

                    line_items_response = []
                    if line_items_exist:
                        line_items_response = [
                            {
                                "scoreMaximum": 100.0,
                                "tag": "score",
                                "id": "http://canvas.docker/api/lti/courses/1/line_items/1",
                                "label": "Score",
                            },
                            {
                                "scoreMaximum": 999.0,
                                "tag": "time",
                                "id": "http://canvas.docker/api/lti/courses/1/line_items/2",
                                "label": "Time Taken",
                            },
                        ]
                    else:
                        m.post(
                            line_items_url,
                            text=json.dumps(
                                {
                                    "scoreMaximum": 100.0,
                                    "tag": "score",
                                    "id": "http://canvas.docker/api/lti/courses/1/line_items/1",
                                    "label": "Score",
                                }
                            ),
                        )

                    m.get(line_items_url, text=json.dumps(line_items_response))
                    m.get(
                        "http://canvas.docker/api/lti/courses/1/line_items/1/results",
                        text=json.dumps(
                            [
                                {
                                    "resultScore": 13.0,
                                    "resultMaximum": 100.0,
                                    "userId": "20eb59f5-26e8-46bc-87b0-57ed54820aeb",
                                    "id": "http://canvas.docker/api/lti/courses/1/line_items/1/results/1",
                                    "scoreOf": "http://canvas.docker/api/lti/courses/1/line_items/1",
                                }
                            ]
                        ),
                    )

                    ags = message_launch.validate_registration().get_ags()

                    score_line_item = LineItem()
                    score_line_item.set_tag("score").set_score_maximum(100).set_label(
                        "Score"
                    )

                    line_item = ags.find_or_create_lineitem(score_line_item)
                    self.assertIsNotNone(line_item)

                    scores = list(ags.get_grades(line_item))
                    self.assertEqual(len(scores), 1)
                    self.assertDictEqual(
                        scores[0],
                        {
                            "resultScore": 13.0,
                            "resultMaximum": 100.0,
                            "userId": "20eb59f5-26e8-46bc-87b0-57ed54820aeb",
                            "id": "http://canvas.docker/api/lti/courses/1/line_items/1/results/1",
                            "scoreOf": "http://canvas.docker/api/lti/courses/1/line_items/1",
                        },
                    )

    def test_send_scores(self):
        from pylti1p3.contrib.django import DjangoMessageLaunch

        tool_conf = get_test_tool_conf()

        with patch.object(
            DjangoMessageLaunch, "_get_jwt_body", autospec=True
        ) as get_jwt_body:
            message_launch = DjangoMessageLaunch(FakeRequest(), tool_conf)
            get_jwt_body.side_effect = lambda x: self._get_jwt_body()
            with patch("socket.gethostbyname", return_value="127.0.0.1"):
                with requests_mock.Mocker() as m:
                    m.post(
                        self._get_auth_token_url(),
                        text=json.dumps(self._get_auth_token_response()),
                    )
                    m.get(
                        "http://canvas.docker/api/lti/courses/1/line_items",
                        text=json.dumps(
                            [
                                {
                                    "scoreMaximum": 100.0,
                                    "tag": "score",
                                    "id": "http://canvas.docker/api/lti/courses/1/line_items/1",
                                    "label": "Score",
                                }
                            ]
                        ),
                    )
                    expected_result = {
                        "resultUrl": "http://canvas.docker/api/lti/courses/1/line_items/1/results/4"
                    }
                    m.post(
                        "http://canvas.docker/api/lti/courses/1/line_items/1/scores",
                        text=json.dumps(expected_result),
                    )

                    ags = message_launch.validate_registration().get_ags()
                    sub = message_launch.get_launch_data().get("sub")

                    timestamp = datetime.datetime.utcnow().strftime(
                        "%Y-%m-%dT%H:%M:%S+0000"
                    )
                    sc = Grade()
                    sc.set_score_given(5).set_score_maximum(100).set_timestamp(
                        timestamp
                    ).set_activity_progress("Completed").set_grading_progress(
                        "FullyGraded"
                    ).set_user_id(
                        sub
                    )

                    sc_line_item = LineItem()
                    sc_line_item.set_tag("score").set_score_maximum(100).set_label(
                        "Score"
                    )

                    resp = ags.put_grade(sc, sc_line_item)
                    self.assertEqual(expected_result, resp["body"])
