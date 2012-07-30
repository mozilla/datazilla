import json

from datazilla.model import PerformanceTestModel
from base import ProjectCommand

class Command(ProjectCommand):

    help = (
        "Generate a report of all the JSON data that had an error "
        "and could, therefore, not be processed."
        )


    def handle_project(self, project, **options):
        """Count errors of the project grouped by name, branch and version."""

        self.stdout.write("Processing project {0}\n".format(project))

        ptm = PerformanceTestModel(project)
        err_data = ptm.get_object_error_data()
        ptm.disconnect()

        counts = {}
        for item in err_data:
            tb = item["test_build"]
            counts[self.result_key(tb)] = counts.get(self.result_key(tb), 0) + 1

        self.stdout.write("{0}\n".format(json.dumps(counts, indent=4)))


    def result_key(self, tb):
        """Build a key based on the fields of tb."""
        try:
            key = "{0} - {1} - {2}".format(
                tb["name"],
                tb["branch"],
                tb["version"],
                )

        except KeyError:
            key = "unknown"

        return key
