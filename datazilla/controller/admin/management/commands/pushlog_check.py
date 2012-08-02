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

        range_key = "days_7"
        since_date = utils.get_time_ranges()[range_key]["stop"]
        pl_count = plm.get_pushlog_count_since_date(since_date)

        # get the unique revisions for testruns for this project
        tr_set = ptm.get_distinct_test_run_revisions(since_date)
        ptm.disconnect()
        self.stdout.write("{0} datazilla testrun count: {1}\n".format(
            range_key,
            len(tr_set),
        ))
        self.stdout.write("{0} pushlog count: {1}\n".format(
            range_key,
            pl_count[0]["pl_count"],
            ))

        self.query_technique(plm, tr_set, since_date)
        return




        # create a list of counts by branch for output
        branch_wo_match, branch_w_match = plm.get_pushlogs_not_in_set_by_branch(tr_set, since_date)

        total_wo_match = 0
        for br in branch_wo_match.itervalues():
            total_wo_match += len(br)

        plm.disconnect()

        self.stdout.write("{0} no match count: {1}\n".format(
            range_key,
            total_wo_match,
            ))

        for brdict in [branch_wo_match, branch_w_match]:
            # print counts by branch
            self.stdout.write("\nBreakdown by branch:\n")
            for br in brdict.iterkeys():
                self.stdout.write("{0} - {1}\n".format(
                    br,
                    len(brdict[br]),
                    ))

        self.stdout.write("date: {0}".format(since_date))


    def query_technique(self, plm, tr_set, since_date):

        pushlogs = plm.get_pushlogs_since_date(since_date)

        count = 0
        branch_counts = {}
        for pl in pushlogs:
            br_count = branch_counts.get(pl["branch_name"], 0)

            changesets = plm.get_changesets(pl["push_id"])
            revisions = [x["node"][:12] for x in changesets]

            if not tr_set.intersection(revisions):
                count += 1
                br_count += 1
                branch_counts[pl["branch_name"]] = br_count



        self.stdout.write("No match by query: {0}\n".format(count))
        self.stdout.write("\nBreakdown by branch:\n")
        for br, ct in branch_counts.iteritems():
            self.stdout.write("{0} - {1}\n".format(
                br,
                ct,
                ))

        plm.disconnect()

