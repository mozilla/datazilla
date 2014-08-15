import json

from operator import itemgetter
from optparse import make_option
from datazilla.model import PerformanceTestModel
from base import ProjectBatchCommand

check_for_idx = """
SHOW INDEX FROM machine WHERE KEY_NAME = 'unique_machine'
"""

drop_machine_idx = """
ALTER TABLE b2g_perftest_1.machine
DROP INDEX unique_machine
"""

add_machine_idx = """
ALTER TABLE b2g_perftest_1.machine
ADD CONSTRAINT unique_machine UNIQUE (`name`, `operating_system_id`, `type`)
"""

get_objects = """
SELECT test_run_id, json_blob
FROM objectstore
WHERE id >= {0}
"""

get_unique_machines = """
SELECT m.id, m.name AS m_name, m.type AS m_type,
       o.id AS os_id, o.name AS os_name, o.version AS os_version
FROM machine AS m
JOIN operating_system AS o ON m.operating_system_id = o.id
GROUP BY m.name, m.type, o.name, o.version
"""

get_operating_systems = """
SELECT id, name, version
FROM operating_system
"""

insert_new_machine = """
INSERT INTO machine (name, operating_system_id, type, date_added)
VALUES (?, ?, ?, ?)
"""

get_new_machine_id = """
SELECT id
FROM machine
WHERE name = ? AND operating_system_id = ? AND type = ?
"""

update_test_run_machine_id = """
UPDATE test_run
SET machine_id = ?
WHERE id IN (REP0)
"""

class Command(ProjectBatchCommand):

    LOCK_FILE = "fix_b2g_machines"

    help = "Fix b2g machine to test_run associations"

    option_list = ProjectBatchCommand.option_list + (

        make_option(
            '--min_id',
            action='store',
            dest='min_id',
            default=1,
            help='minimum object id to start the reassociation from'),
        )

    def handle_project(self, project, **options):

        min_id = options.get("min_id", 354404)

        ptm = PerformanceTestModel(project)

        exists = ptm.sources["perftest"].dhub.execute(sql=check_for_idx)
        if len(exists) > 0:
            try:
                ptm.sources["perftest"].dhub.execute(sql=drop_machine_idx)
            except:
                pass
            finally:
                ptm.sources["perftest"].dhub.execute(sql=add_machine_idx)

        unique_os_set = self.get_unique_operating_systems(ptm)
        data_objects = ptm.sources["objectstore"].dhub.execute(
            sql=get_objects.format(str(min_id))
            )

        machine_groups = {}
        for obj in data_objects:

            tr_id = obj['test_run_id']
            json_obj = json.loads(obj['json_blob'])
            m_name = json_obj['test_machine']['name']
            m_type = json_obj['test_machine']['type']
            os_name = json_obj['test_machine']['os']
            os_version = json_obj['test_machine']['osversion']
            date = json_obj['testrun']['date']

            os_id = unique_os_set[
                self.get_os_key(os_name, os_version)
                ]

            key = self.get_key(m_name, m_type, os_name, os_version)

            if key not in machine_groups:
                machine_groups[key] = {
                    "machine_name":"", "machine_type":"",
                    "os_id":"", "os_name":"", "os_version":"", "date":"",
                    "tr_ids":[]
                    }

            machine_groups[key]["machine_name"] = m_name
            machine_groups[key]["machine_type"] = m_type
            machine_groups[key]["os_id"] = os_id
            machine_groups[key]["os_name"] = os_name
            machine_groups[key]["os_version"] = os_version
            machine_groups[key]["date"] = date
            machine_groups[key]["tr_ids"].append(tr_id)

        unique_machine_set = self.get_unique_machines(ptm)

        for key in machine_groups:

            mg_obj = machine_groups[key]

            if key not in unique_machine_set:

                # No entry, could have been overwritten from re-using the
                # same machine name with different device type names.

                print "NEW MACHINE"

                # Insert new machine in the machine table
                ptm.sources["perftest"].dhub.execute(
                    sql=insert_new_machine,
                    placeholders=[
                        mg_obj['machine_name'],
                        mg_obj['os_id'],
                        mg_obj['machine_type'],
                        mg_obj['date']
                        ]
                    )

                machine_id = ptm.sources["perftest"].dhub.execute(
                    sql=get_new_machine_id,
                    placeholders=[
                        mg_obj['machine_name'],
                        mg_obj['os_id'],
                        mg_obj['machine_type']
                        ]
                    )[0]['id']

                # Update the associated test_run.id's with the appropriate
                # machine id

                ptm.sources["perftest"].dhub.execute(
                    sql=update_test_run_machine_id,
                    replace=[ mg_obj['tr_ids'] ],
                    placeholders=[ machine_id ]
                    )

                print "machine_id:{0}".format(str(machine_id))
                print json.dumps(mg_obj)

            else:
                # We have an entry but we still need to confirm the
                # test_run.id to machine.id associations are correct

                # Update the machine.id associations in the test_run.id
                # table
                print "MACHINE EXISTS"
                machine_id = unique_machine_set[key]['m_id']

                ptm.sources["perftest"].dhub.execute(
                    sql=update_test_run_machine_id,
                    replace=[ mg_obj['tr_ids'] ],
                    placeholders=[ machine_id ]
                    )

                print "machine_id:{0}".format( str(machine_id) )
                print json.dumps(mg_obj)

    def get_key(self, m_name, m_type, os_name, os_version):

        return "{0} {1} {2} {3}".format(m_name, m_type, os_name, os_version)

    def get_os_key(self, os_name, os_version):

        return "{0} {1}".format(os_name, os_version)

    def get_unique_machines(self, ptm):

        unique_machines = ptm.sources["perftest"].dhub.execute(sql=get_unique_machines)

        unique_machine_set = {}
        for um in unique_machines:
            unique_machine_set[
                self.get_key(
                    um['m_name'], um['m_type'], um['os_name'], um['os_version']
                    )
                ] = { 'm_id':um['id'], 'os_id':um['os_id'] }

        return unique_machine_set

    def get_unique_operating_systems(self, ptm):

        operating_systems = ptm.sources["perftest"].dhub.execute(sql=get_operating_systems)

        unique_operating_systems = {}
        for uo in operating_systems:
            unique_operating_systems[
                self.get_os_key(uo['name'], uo['version'])
                ] = uo['id']

        return unique_operating_systems

