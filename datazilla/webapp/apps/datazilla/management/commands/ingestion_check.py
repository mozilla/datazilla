import os
import sys
import json
import datetime
from dateutil.relativedelta import relativedelta
from optparse import make_option
from django.core.management.base import BaseCommand
from django.conf import settings
from datazilla.model import PerformanceTestModel

from pprint import pprint

class Command(BaseCommand):
    models = {}

    help = (
            "Check ingestion rates"
            )

    def handle(self, *args, **options):

        settings_file = os.path.join(
            os.path.dirname(sys.argv[0]),
            'datazilla',
            'settings',
            'ingestion_alerts.json',
            )
        profiles = json.load(open(settings_file))

        for profile in profiles:
            # rudimentary sanity check of the json structure
            self.check_mandatory(profile, 'name')
            self.check_mandatory(profile, 'machine')
            self.check_mandatory(profile, 'product')
            self.check_mandatory(profile['product'], 'product')
            self.check_mandatory(profile['product'], 'branch')
            self.check_mandatory(profile['product'], 'version')
            self.check_mandatory(profile, 'tests')
            self.check_mandatory(profile, 'pages')
            self.check_mandatory(profile, 'alert_minutes')
            self.check_mandatory(profile, 'alert_recipients')

            ptm = self.get_ptm(profile['product']['product'])

            # verify values against database and canonicalise
            self.canonicalise(ptm, profile, 'machine', \
                'machine', 'type')
            self.canonicalise(ptm, profile['product'], 'product', \
                'product', 'product')
            self.canonicalise(ptm, profile['product'], 'branch', \
                'product', 'branch')
            self.canonicalise(ptm, profile['product'], 'version', \
                'product', 'version')
            self.canonicalise(ptm, profile, 'tests', 'test', 'name')
            self.canonicalise(ptm, profile, 'pages', 'pages', 'url')

            # get the last test_run date
            last_run_date = ptm.get_last_test_run_date(
                profile['machine'],
                profile['product']['product'],
                profile['product']['branch'],
                profile['product']['version'],
                profile['tests'],
                profile['pages'],
            )

            # check if we need to alert
            if last_run_date:
                age = (datetime.datetime.now() - last_run_date).total_seconds()
                if age / 60 < profile['alert_minutes']:
                    return

            sender = 'nobody@mozilla.org'
            subject = 'Ingestion alert for "%s"' % profile['name']
            if last_run_date:
                alert = subject + ":\nNo test data for %s.\n" \
                    % self.human_duration(age)
            else:
                alert = subject + ":\nNo matching test data found.\n"

            for recipient in profile['alert_recipients']:
                # XXX if recipient is an email address
                if True:
                    message = "From: %s\nTo: %s\nSubject: %s\n\n%s" \
                        % (sender, recipient, subject, alert)
                    if settings.DEBUG:
                        print "---\n%s---\n" % message
                    else:
                        p = os.popen('/usr/lib/sendmail -t -i -f %s' \
                            % sender, 'w')
                        p.write(message)
                        p.close()
                # XXX else if recipient is sentry

        for key in self.models:
            self.models[key].disconnect()

    def get_ptm(self, product):
        product = product.lower()
        if not product in self.models:
            self.models[product] = PerformanceTestModel(product)
        return self.models[product]

    def check_mandatory(self, dict, key):
        if not key in dict:
            print "ingestion_alerts.json is missing '" + key + "'"
            pprint(dict)
            sys.exit(1)
        if isinstance(dict[key], list) and not len(dict[key]):
            print "ingestion_alerts.json '" + key + "' is empty"
            pprint(dict)
            sys.exit(1)

    def canonicalise(self, ptm, dict, key, table, column):
        if isinstance(dict[key], list):
            for value in dict[key]:
                canon = ptm.get_canonical_value(table, column, value)
                if not canon:
                    print "ingestion_alerts.json '" + key + "'.'" + value + "' is invalid"
                    pprint(dict)
                    sys.exit(1)
                value = canon
        else:
            canon = ptm.get_canonical_value(table, column, dict[key])
            if not canon:
                print "ingestion_alerts.json '" + key + "'.'" + dict[key] + "' is invalid"
                pprint(dict)
                sys.exit(1)
            dict[key] = canon

    def human_duration(self, seconds):
        delta = relativedelta(seconds = seconds)
        result = []
        for attr in ['years', 'months', 'days', 'hours', 'minutes']:
            value = getattr(delta, attr)
            if value:
                if value == 1:
                    attr = attr[:-1]
                result.append('%d %s' % (value, attr))
        return ', '.join(result)
