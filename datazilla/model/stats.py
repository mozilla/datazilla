import json

from base import PerformanceTestModel, PushLogModel


class PushLogStatsModel(PushLogModel):
    """Model for PushLog statistics and error information."""

    def get_db_size(self):
        """Return size of DB on disk in MB."""
        placeholders = ["%{0}%".format(self.project)]
        return self.hg_ds.dhub.execute(
            proc='generic.selects.get_db_size',
            debug_show=self.DEBUG,
            placeholders=placeholders,
            return_type='tuple',
            )


    def get_pushlogs_since_date(self, startdate, enddate, branch_names):

        proc = 'hgmozilla.selects.get_pushlogs_since_date'

        data_iter = self.hg_ds.dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[startdate, enddate, ", ".join(branch_names)],
            return_type='tuple',
            )

        return data_iter


    def get_changeset_nodes_since_date(self, startdate, enddate, branch_names):

        proc = 'hgmozilla.selects.get_changeset_nodes_since_date'

        data_set = self.hg_ds.dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            replace_quote=[branch_names],
            placeholders=[startdate, enddate],
            return_type='iter',
            )

        return data_set


    def get_pushlog_count_since_date(self, startdate, enddate, branches):

        proc = 'hgmozilla.selects.get_pushlog_count_by_date'

        count = self.hg_ds.dhub.execute(
            proc=proc,
            replace_quote=[branches],
            debug_show=self.DEBUG,
            placeholders=[startdate, enddate],
            return_type='tuple',
            )

        return count


    def get_pushlog_dict(self, startdate, enddate, branch_names):
        # get the pushlogs in the specified date range
        pl_nodes = self.get_changeset_nodes_since_date(startdate, enddate, branch_names)

        # build a dict with pushlog_id as the keys, and changeset list as
        # values.
        # testrun revision will match the first 12 characters of a node.
        pl_dict = {}
        for pl in pl_nodes:
            node_branch = pl_dict.setdefault(pl["push_id"], {})
            revision_list = node_branch.setdefault("revisions", [])
            revision_list.append(unicode(pl["node"][:12]))
            node_branch.setdefault("branch_name", pl["branch_name"])

        return pl_dict


class PerformanceTestStatsModel(PerformanceTestModel):
    """Model for PerformanceTest statistics and error information."""

    def get_db_size(self, source="perftest"):
        """Return size of DB on disk in MB."""
        placeholders = ["%{0}%".format(self.project)]
        return self.sources[source].dhub.execute(
            proc='generic.selects.get_db_size',
            debug_show=self.DEBUG,
            placeholders=placeholders,
            return_type='tuple',
            )


    def get_distinct_test_run_revisions(self):
        """Return ids and revisions of all test runs"""

        proc = 'perftest.selects.get_distinct_test_run_revisions'

        data_iter = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='set',
            key_column="revision",
            )

        return data_iter


    def get_run_lists_by_branch(self, startdate, enddate):
        """Return a list of test runs by branch in date range"""
        placeholders = [startdate, enddate]

        data_iter = self.sources["perftest"].dhub.execute(
            proc="perftest.selects.get_test_runs",
            debug_show=self.DEBUG,
            placeholders = placeholders,
            return_type='tuple',
            )

        return data_iter


    def get_run_counts_by_branch(self, startdate, enddate):
        """Return a count of test runs by branch in date range"""
        placeholders = [startdate, enddate]

        data_iter = self.sources["perftest"].dhub.execute(
            proc="perftest.selects.get_test_run_counts",
            debug_show=self.DEBUG,
            placeholders = placeholders,
            return_type='tuple',
            )

        return data_iter


    def get_all_object_errors(self, startdate, enddate):
        """ Get all the error records in the objectstore """

        data_iter = self.sources["objectstore"].dhub.execute(
            proc="objectstore.selects.get_all_errors",
            debug_show=self.DEBUG,
            chunk_size=30,
            chunk_source="objectstore.id",
            placeholders=[startdate, enddate],
            return_type='tuple',
            )

        return data_iter


    def get_object_error_metadata(self, startdate, enddate):
        """ Get all the error records metadata in the objectstore """

        data_iter = self.sources["objectstore"].dhub.execute(
            proc="objectstore.selects.get_error_metadata",
            debug_show=self.DEBUG,
            placeholders=[startdate, enddate],
            return_type='tuple',
            )

        return data_iter


    def get_object_error_counts(self, startdate, enddate):
        """ Get all the error records in the objectstore """

        data_iter = self.sources["objectstore"].dhub.execute(
            proc="objectstore.selects.get_error_counts",
            debug_show=self.DEBUG,
            replace=[str(startdate), str(enddate)],
            return_type='tuple',
            )

        return data_iter


    def get_object_json_blob(self, id):
        blob = self.sources["objectstore"].dhub.execute(
            proc="objectstore.selects.get_json_blob",
            debug_show=self.DEBUG,
            placeholders = [id],
            return_type='tuple',
            )

        return blob


    def get_object_error_data(self):
        """Process all the errors in the objectstore and summarize."""
        import re
        data_iter = self.get_all_object_errors()

        results = []
        versions = {}
        for d in data_iter:
            # one chunk
            for data in d:
                # one item of one chunk
                blob = data["json_blob"]
                try:
                    res_data = json.loads(blob)
                    # since this parsed ok, let's get some values
                    data_error = {
                        "status": "json parsed",
                        "test_build": {
                            "name": res_data["test_build"]["name"],
                            "branch": res_data["test_build"]["branch"],
                            "version": res_data["test_build"]["version"],
                            }
                    }
                    results.append(data_error)
                    tb = res_data["test_build"]
                    versions[tb["version"]] = versions.get(tb["version"], 0) + 1

                except ValueError:
                    # we need to use regex to do SOME parsing of this
                    # data to extract some field values
                    data_error = {"status": "bad json"}

                    # attempt to find the test_machine
                    re_tb = re.compile("(?<=\"test_build\":)(.*?})")
                    tb_res = re_tb.search(blob)

                    try:
                        # maybe this much JSON is ok.
                        tb = json.loads(tb_res.group())
                        data_error["test_build"] = {
                            "name": tb["name"],
                            "branch": tb["branch"],
                            "version": tb["version"],
                            }
                        versions[tb["version"]] = versions.get(tb["version"], 0) + 1

                    except ValueError:
                        # nope, let's just store this now
                        data_error["test_build"] = tb_res.group()
                        versions["unparsable"] = versions.get("unparsable", 0) + 1


                    results.append(data_error)

        return results


