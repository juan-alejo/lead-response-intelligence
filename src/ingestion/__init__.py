"""Prospect ingestion: pull businesses from Google Places (or CSV), deduplicate."""

from .base import ProspectSource
from .csv_source import CSVSource
from .dedup import Deduplicator
from .google_places import GooglePlacesSource

__all__ = ["ProspectSource", "GooglePlacesSource", "CSVSource", "Deduplicator"]
