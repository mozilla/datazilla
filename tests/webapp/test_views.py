import json

from mock import patch


class TestSetTestData(object):
    """Tests for set_test_data view."""
    def test_happy(self, client, dm):
        """Can set test data in objectstore via API endpoint."""
        response = client.oauth_post(dm, {"test": "foo"})

        row_data = dm.sources["objectstore"].dhub.execute(
            proc="objectstore_test.selects.all")[0]

        assert json.loads(row_data["json_blob"]) == {"test": "foo"}
        assert response.json == {
            u"size": 15, u"status": u"well-formed JSON stored"}


    def test_no_oauth(self, client):
        """Trying to set test data without OAuth creds results in an error."""
        response = client.post("/testproj/api/load_test", {}, status=403)

        assert response.json["status"] == u"No OAuth credentials provided."


    def _patch(self, dotted_path, *args, **kwargs):
        """Prepend given path with the containing module path and patch it."""
        full_path = "datazilla.webapp.apps.datazilla.views." + dotted_path
        return patch(full_path, *args, **kwargs)


    def test_oauth_error(self, client, dm):
        """Incorrect oauth signature results in an error."""
        def _raise_oauth_error(*args, **kwargs):
            from oauth2 import Error
            raise Error("Some error.")

        with self._patch("oauth.Server.verify_request") as mock_verify:
            mock_verify.side_effect = _raise_oauth_error

            response = client.oauth_post(dm, {}, status=403)

        assert response.json["status"] == u"Oauth verification error."


    def test_talos_oauth_exception(self, client):
        """Talos can post without OAuth (for now). (TODO remove this.)"""
        with self._patch("PerformanceTestModel"):
            response = client.post("/talos/api/load_test", {"data": "{}"})

        assert response.json["status"] == u"well-formed JSON stored"


    def test_talos_legacy_url(self, client):
        """Talos can post to legacy /views/... url (for now). (TODO remove)"""
        with self._patch("PerformanceTestModel") as mock_PerformanceTestModel:
            response = client.post("/views/api/load_test", {"data": "{}"})

        assert response.json["status"] == u"well-formed JSON stored"
        mock_PerformanceTestModel.assert_called_with("talos")


    def test_no_data(self, client, dm):
        response = client.oauth_post(dm, None, status=400)

        assert response.json["status"] == u"No POST data found"


    def test_malformed_json(self, client, dm):
        response = client.oauth_post(dm, "{[[[", status=400)

        row_data = dm.sources["objectstore"].dhub.execute(
            proc="objectstore_test.selects.all")[0]

        assert row_data["error_flag"] == "Y"
        assert response.json["status"] == u"Malformed JSON"
        assert "message" in response.json


    def test_unknown_error(self, client, dm):
        def _raise(*args, **kwargs):
            raise Exception("boom!")

        with self._patch("PerformanceTestModel.store_test_data") as mock_store:
            mock_store.side_effect = _raise
            response = client.oauth_post(dm, {}, status=500)

        assert response.json["status"] == "Unknown error"
        assert response.json["message"] == "boom!"


    def test_bad_project(self, client, dm):
        dm.project = "doesnotexist"
        response = client.oauth_post(dm, {}, status=404)

        assert response.json["status"] == "Unknown project 'doesnotexist'"
