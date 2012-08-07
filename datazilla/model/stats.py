import json

from base import PerformanceTestModel, PushLogModel


class PushlogStatsModel(PushLogModel):
    """Model for PushLog statistics and error information."""

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
            placeholders=[startdate, enddate, ", ".join(branch_names)],
            return_type='iter',
            )

        return data_set


    def get_pushlog_count_since_date(self, startdate, enddate, branches):

        proc = 'hgmozilla.selects.get_pushlog_count_by_date'

        count = self.hg_ds.dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[startdate, enddate, ", ".join(branches)],
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


    def get_pushlogs_not_in_set_by_branch(self, tr_set, startdate, enddate, branch_names):
        pl_dict = self.get_pushlog_dict(startdate, enddate, branch_names)

        branch_wo_match = {}
        branch_w_match = {}
        for pl, data in pl_dict.iteritems():
            if not len(tr_set.intersection(set(data["revisions"]))):
                bucket = branch_wo_match
            else:
                bucket = branch_w_match

            br_list = bucket.setdefault(data["branch_name"], {})
            br_list[pl] = data["revisions"]

        return branch_wo_match, branch_w_match



class PerformanceTestStatsModel(PerformanceTestModel):
    """Model for PerformanceTest statistics and error information."""

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


    def get_runs_by_branch(self, startdate, enddate):
        """Return a list of test runs by branch in date range"""
        placeholders = [startdate, enddate]

        data_iter = self.sources["perftest"].dhub.execute(
            proc="perftest.selects.get_test_runs",
            debug_show=self.DEBUG,
            placeholders = placeholders,
            return_type='tuple',
            )

        return data_iter


    def get_all_object_errors(self):
        """ Get all the error records in the objectstore """

        data_iter = self.sources["objectstore"].dhub.execute(
            proc="objectstore.selects.get_all_errors",
            debug_show=self.DEBUG,
            chunk_size=30,
            chunk_source="objectstore.id",
            return_type='tuple',
            )

        return data_iter


    def get_object_error_metadata(self):
        """ Get all the error records metadata in the objectstore """

        data_iter = self.sources["objectstore"].dhub.execute(
            proc="objectstore.selects.get_all_error_metadata",
            debug_show=self.DEBUG,
            return_type='tuple',
            )

        return data_iter


    def get_object_error_counts(self):
        """ Get all the error records in the objectstore """

        data_iter = self.sources["objectstore"].dhub.execute(
            proc="objectstore.selects.get_count_errors",
            debug_show=self.DEBUG,
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


