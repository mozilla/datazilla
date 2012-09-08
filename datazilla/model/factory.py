"""
Define factories for the Datazilla Models.

The main purpose of this is to provide universal hooks for tests to override
in instantiating models.
"""

from base import PerformanceTestModel, PushLogModel
from stats import PerformanceTestStatsModel, PushLogStatsModel


def get_ptsm(project):
    """Shortcut to return the PerformanceTestStatsModel."""
    return PerformanceTestStatsModel(project)


def get_ptm(project):
    """Shortcut to return the PerformanceTestModel."""
    return PerformanceTestModel(project)


def get_plm():
    """Shortcut to return the PushLogModel."""
    return PushLogModel()


def get_plsm():
    """Shortcut to return the PushLogStatsModel."""
    return PushLogStatsModel()


