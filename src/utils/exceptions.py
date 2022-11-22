"""Provides custom Exceptions."""


class NoAvailableData(Exception):
    def __str__(self):
        return "No mean values were passed for comparison"
