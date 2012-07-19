import json

import pytest



@pytest.mark.integration
def test_set_test_data(client, dm):
    """Can set test data in objectstore via API endpoint."""
    client.oauth_post(dm, "/testproj/api/load_test", {"data": "foo"})

    row_data = dm.sources["objectstore"].dhub.execute(
        proc="objectstore_test.selects.all")[0]

    assert json.loads(row_data["json_blob"]) == {"data": "foo"}
