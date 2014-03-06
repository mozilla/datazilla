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

        profiles = Profiles(settings_file)
        for profile in profiles:
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
                diff = datetime.datetime.now() - last_run_date
                age = (diff.microseconds +
                    (diff.seconds + diff.days * 24 * 3600) * 1e6) / 1e6
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

class ProfileError(ValueError):
    pass

class Profiles:
    def __init__(self, filename):
        try:
            with open(filename) as f:
                data = json.load(f)
        except ValueError as e:
            raise ProfilesError("Malformed JSON: {0}".format(e))

        self.list = []
        for item in data:
            self.list.append(Profile(item, str(len(self.list))))

    def __iter__(self):
        return iter(self.list)

class Profile(dict):
    def __init__(self, data, context=None):
        self.context = context or []
        super(Profile, self).__init__(data)

    def __getitem__(self, name):
        full_context = list(self.context) + [name]

        # throw an exception which provides better context
        try:
            value = super(Profile, self).__getitem__(name)
        except KeyError:
            raise ProfileError("Missing value for: {0}".format(
                "".join(["['{0}']".format(c) for c in full_context])))

        # recurse into dicts
        if isinstance(value, dict):
            value = self.__class__(value, full_context)

        # lists must not be empty
        if isinstance(value, list) and not len(value):
            raise ProfileError("Value is an empty list: {0}".format(
                "".join(["['{0}']".format(c) for c in full_context])))

        return value
