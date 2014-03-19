import os
import sys
import json
import datetime
import smtplib
from email.MIMEText import MIMEText

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
            os.path.dirname(__file__),
            '../../../../../',
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

            alert_messages = {}
            # get the last test_run date
            test_run_data = ptm.get_last_test_run_date(
                profile['machine'],
                profile['product']['product'],
                profile['product']['branch'],
                profile['product']['version'],
                profile['tests'],
                profile['pages'],
            )

            for datum in test_run_data:
                # check if we need to alert
                if datum['date_run']:
                    last_run_date = datetime.datetime.fromtimestamp(datum['date_run']) or None
                    diff = datetime.datetime.now() - last_run_date
                    age = (diff.microseconds +
                        (diff.seconds + diff.days * 24 * 3600) * 1e6) / 1e6
                    if age / 60 < profile['alert_minutes']:
                        continue
                    else:
                        datum['age'] = self.human_duration(age)

                        if datum['test'] not in alert_messages:
                            alert_messages[datum['test']] = []

                        alert_messages[datum['test']].append(datum)

            if alert_messages:

                border = "------------------------------------------------------------\n"
                sender = 'auto-tools@mozilla.org'
                subject = "Ingestion alert for {0} on {1} {2} {3}".format(
                    profile['machine'], profile['product']['product'],
                    profile['product']['branch'], profile['product']['version'])

                alert = "Device Type: {0}, Product: {1}, {2}, {3}\n".format(
                    profile['machine'], profile['product']['product'],
                    profile['product']['branch'], profile['product']['version'])

                alert += border

                for test in alert_messages:
                    alert += "Test: {0}\n".format(test)
                    for m in alert_messages[test]:
                        alert += "   App: {0}, no data in {1}\n".format(
                            m['app'], m['age']
                            )
                    alert += "\n"

                alert += border

                for recipient in profile['alert_recipients']:
                    if settings.DEBUG:
                        message = "From: %s\nTo: %s\nSubject: %s\n\n%s" \
                            % (sender, recipient, subject, alert)
                        print message
                        print "SMTP_HOST: {0}".format(settings.SMTP_HOST)
                    else:

                        efrom = 'auto-tools@mozilla.com'

                        msg = MIMEText(alert)
                        msg['Subject'] = subject
                        msg['From'] = efrom
                        msg['To'] = recipient
                        msg.preamble = 'Datazilla ingestion alert'

                        s = smtplib.SMTP(settings.SMTP_HOST)
                        s.sendmail(efrom, recipient, msg.as_string())

        for key in self.models:
            self.models[key].disconnect()

    def get_ptm(self, product):
        product = product.lower()
        if not product in self.models:
            self.models[product] = PerformanceTestModel(product)
        return self.models[product]

    def check_mandatory(self, alerts_dict, key):
        if not key in alerts_dict:
            print "ingestion_alerts.json is missing '" + key + "'"
            pprint(alerts_dict)
            sys.exit(1)
        if isinstance(alerts_dict[key], list) and not len(alerts_dict[key]):
            print "ingestion_alerts.json '" + key + "' is empty"
            pprint(alerts_dict)
            sys.exit(1)

    def canonicalise(self, ptm, alerts_dict, key, table, column):
        if isinstance(alerts_dict[key], list):
            for value in alerts_dict[key]:
                canon = ptm.get_canonical_value(table, column, value)
                if not canon:
                    print "ingestion_alerts.json '" + key + "'.'" + value + "' is invalid"
                    pprint(alerts_dict)
                    sys.exit(1)
                value = canon
        else:
            canon = ptm.get_canonical_value(table, column, alerts_dict[key])
            if not canon:
                print "ingestion_alerts.json '" + key + "'.'" + alerts_dict[key] + "' is invalid"
                pprint(alerts_dict)
                sys.exit(1)
            alerts_dict[key] = canon

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

class Profiles(object):
    def __init__(self, filename):
        try:
            with open(filename) as f:
                data = json.load(f)
        except ValueError as e:
            raise ProfileError("Malformed JSON: {0}".format(e))

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
