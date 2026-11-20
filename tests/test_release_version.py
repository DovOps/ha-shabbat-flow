"""Prevent stale immutable frontend URLs in release archives."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('build_ha', Path(__file__).resolve().parents[1] / 'scripts/build_ha.py')
build_ha = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_ha)

class ReleaseVersionTests(unittest.TestCase):
    def test_mismatched_frontend_version_cannot_be_packaged(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            (target / 'manifest.json').write_text(json.dumps({'version': '0.16.3'}))
            (target / 'const.py').write_text('VERSION = "0.16.1"\nSTATIC = "/shabbat_flow_static/0.16.1"\n')
            with patch.object(build_ha, 'TARGET', target):
                with self.assertRaisesRegex(SystemExit, 'Manifest/frontend version mismatch'):
                    build_ha.build()
