import json

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

        branches = ["Mozilla-Inbound"]
        days_ago = 30
        numdays = 30
        range_key = "{0} days of data, starting {1} days ago: ".format(
            numdays,
            days_ago,
            )
        date_range = utils.get_day_range(days_ago, numdays)
        pl_count = plm.get_pushlog_count_since_date(
            date_range["start"],
            date_range["stop"],
            branches,
            )

        # get the unique revisions for testruns for this project
        tr_set = ptm.get_distinct_test_run_revisions()
        ptm.disconnect()
        self.stdout.write("{0} datazilla testrun distinct revision count: {1}\n".format(
            "TOTAL",
            len(tr_set),
        ))
        self.stdout.write("{0} pushlog count: {1}\n".format(
            range_key,
            pl_count[0]["pl_count"],
            ))

        self.query_technique(plm, tr_set, date_range, branches)

        self.stdout.write("\nBY DICT\n=======\n")



        # create a list of counts by branch for output
        branch_wo_match, branch_w_match = plm.get_pushlogs_not_in_set_by_branch(
            tr_set,
            date_range["start"],
            date_range["stop"],
            branches,
            )

        total_wo_match = 0
        for br in branch_wo_match.itervalues():
            total_wo_match += len(br)

        plm.disconnect()

        self.stdout.write("{0} no match count: {1}\n".format(
            range_key,
            total_wo_match,
            ))

        def print_branches(text, brdict):
            # print counts by branch
            self.stdout.write("\n{0}:\n".format(text))
            for br in brdict.iterkeys():
                self.stdout.write("{0} - {1}\n".format(
                    br,
                    len(brdict[br]),
                    ))

        print_branches("Non-Matching by branch", branch_wo_match)
        print_branches("Matching by branch", branch_w_match)

        import time

        self.stdout.write("Dates: {0}\nStart: {1}\nEnd: {2}\n".format(
            json.dumps(date_range),
            time.ctime(date_range["start"]),
            time.ctime(date_range["stop"]),
            ))

#        self.stdout.write(json.dumps(branch_wo_match, indent=4))
        plm.disconnect()
        return



    def query_technique(self, plm, tr_set, date_range, branches):
        """
        Use a query to get the list of pushlogs, then separate
        queries per pushlog to get the changesets that apply to it.

        Slower, but possibly more accurate?
        """

        self.stdout.write("\nBY QUERY\n========\n")
        pushlogs = plm.get_pushlogs_since_date(
            date_range["start"],
            date_range["stop"],
            branches,
            )

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


