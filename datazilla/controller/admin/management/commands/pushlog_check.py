import json

from datazilla.model import PerformanceTestModel, PushLogModel
from base import ProjectCommand

class Command(ProjectCommand):
    """
    Compare perftest test_run.revision field with pushlog revision field
    for a project.  Anything in one and not in the other should be reported.

    Jeads is seeing data in pushlog that's not in perftest.
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

        test_runs = ptm.get_all_test_run_revisions()
        tr_set = set([x["revision"] for x in test_runs])

        pl_nodes = plm.get_all_changeset_nodes_by_id()

        # build a dict with pushlog_id as the keys, and changeset list as
        # values
        pl_dict = {}
        for pl in pl_nodes:
            node_list = pl_dict.setdefault(pl["pushlog_id"], [])
            node_list.append(pl["node"][:12])

        no_match = [x for x in pl_dict.keys() if (
            len(tr_set.intersection(set(pl_dict[x]))) == 0)
            ]

        ptm.disconnect()
        plm.disconnect()

        self.stdout.write("datazilla testrun count: {0}\n".format(len(tr_set)))
        self.stdout.write("pushlog count: {0}\n".format(len(pl_dict)))
        self.stdout.write("pushlog changeset count: {0}\n".format(pl_nodes.rowcount))
        self.stdout.write("No match count: {0}\n".format(len(no_match)))
#        self.stdout.write("No match: {0}".format(", ".join(str(x) for x in no_match)))
