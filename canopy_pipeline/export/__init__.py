"""Export stage — assemble the JSON, produce rasters/GeoJSON, hand off paths.

Note: this stage PRODUCES files and returns their paths. The actual upload to
production cloud storage is Cem's job (spec §8.2) — see raster_export.py.
"""
