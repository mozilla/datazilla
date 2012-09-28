"""
Define factories for the Datazilla Models.

The main purpose of this is to provide universal hooks for tests to override
in instantiating models.
"""

from base import PerformanceTestModel, PushLogModel
from refdata import PerformanceTestRefDataModel, PushLogRefDataModel
from metrics import MetricsTestModel


def get_ptrdm(project):
    """Shortcut to return the PerformanceTestStatsModel."""
    return PerformanceTestRefDataModel(project)


def get_ptm(project):
    """Shortcut to return the PerformanceTestModel."""
    return PerformanceTestModel(project)


def get_plm(project=None):
    """Shortcut to return the PushLogModel."""
    return PushLogModel(project)


def get_plrdm():
    """Shortcut to return the PushLogStatsModel."""
    return PushLogRefDataModel()


def get_mtm(project):
    """Shortcut to return the MetricsTestModel."""
    return MetricsTestModel(project)


