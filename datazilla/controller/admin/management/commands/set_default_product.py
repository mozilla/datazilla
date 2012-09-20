from optparse import make_option

from datazilla.controller.admin.default_product import set_default_products

from base import ProjectBatchCommand


class Command(ProjectBatchCommand):

    help = "Set default products for projects."

    def handle_project(self, project, **options):

        set_default_products(project)

    def println(self, val):
        self.stdout.write("{0}\n".format(str(val)))

