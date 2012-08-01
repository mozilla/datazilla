from datazilla.model import PerformanceTestModel, PushLogModel, utils
from base import ProjectCommand

class Command(ProjectCommand):
    """
    Compare perftest test_run.revision field with pushlog revision field
    for a project.  Anything in one and not in the other for the most recent
    7 day period will be reported.

    """
    help = (
        "Check each pushlog entry for a project and report any changeset"
        "that doesn't have test data for it."
        )


    def handle_project(self, project, **options):
        """Count errors of the project grouped by name, branch and version."""

        self.stdout.write("Processing project {0}\n".format(project))

        ptm = PerformanceTestModel(project)
        plm = PushLogModel()

        # get the unique revisions for testruns for this project
        tr_set = ptm.get_all_test_run_revisions()

        range_key = "days_7"
        since_date = utils.get_time_ranges()[range_key]["stop"]
        pl_count = plm.get_pushlog_count_by_date(since_date)

#        import json
#        c = 0
#        for k, v in pl_dict.iteritems():
#
#            self.stdout.write("{0}: {1}\n".format(k, json.dumps(v, indent=4)))
#            c += 1
#            if c == 5: break

        # create a list of counts by branch for output
        branch_wo_match = plm.get_pushlogs_not_in_set_by_branch(tr_set, since_date)

        total_wo_match = 0
        for br in branch_wo_match.itervalues():
            total_wo_match += len(br)

        ptm.disconnect()
        plm.disconnect()

        self.stdout.write("total datazilla testrun count: {0}\n".format(
            len(tr_set),
            ))
        self.stdout.write("{0} pushlog count: {1}\n".format(
            range_key,
            pl_count[0]["pl_count"],
            ))
        self.stdout.write("{0} no match count: {1}\n".format(
            range_key,
            total_wo_match,
            ))

        # print counts by branch
        self.stdout.write("Breakdown by branch:\n")
        for br in branch_wo_match.iterkeys():
            self.stdout.write("{0} - {1}\n".format(
                br,
                len(branch_wo_match[br]),
                ))

        self.stdout.write("date: {0}".format(since_date))