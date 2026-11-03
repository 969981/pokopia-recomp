# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only first-run verification; no game files or compiler required."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class VerifyOnlyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.script = self.root / 'pkp_build.py'
        shutil.copyfile(Path(__file__).with_name('pkp_build.py'), self.script)
        self.exefs = self.root / 'exefs'
        self.exefs.mkdir()
        self.bid = bytes(range(20))
        main = bytearray(0x100)
        main[:4] = b'NSO0'
        main[0x40:0x54] = self.bid
        self.files = {'main': bytes(main), 'sdk': b'sdk', 'main.npdm': b'META'}
        for name, data in self.files.items():
            (self.exefs / name).write_bytes(data)
        manifest = {'version': 'test build', 'main_build_id': self.bid.hex(),
                    'sha256': {n: hashlib.sha256(d).hexdigest() for n, d in self.files.items()}}
        (self.root / 'dump_hashes.json').write_text(json.dumps(manifest), encoding='utf-8')

    def run_verify(self, *extra):
        before = {str(p.relative_to(self.root)): p.read_bytes()
                  for p in self.root.rglob('*') if p.is_file()}
        result = subprocess.run([sys.executable, '-I', str(self.script), '--verify-only',
                                 '--exefs', str(self.exefs), *extra], capture_output=True, text=True)
        after = {str(p.relative_to(self.root)): p.read_bytes()
                 for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after, 'verification must not modify files')
        self.assertFalse((self.root / 'build').exists())
        return result

    def test_supported_dump_without_compiler_or_game_directory(self):
        r = self.run_verify()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('@verify main match ', r.stdout)
        self.assertIn('@verify sdk match ', r.stdout)

    def test_wrong_build_still_reports_every_module(self):
        data = bytearray(self.files['main'])
        data[0x40] ^= 0xff
        (self.exefs / 'main').write_bytes(data)
        r = self.run_verify()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('different version', r.stdout)
        self.assertIn('@verify main mismatch ', r.stdout)
        self.assertIn('@verify sdk match ', r.stdout)

    def test_hash_mismatch_with_correct_build_id(self):
        (self.exefs / 'sdk').write_bytes(b'changed')
        r = self.run_verify()
        self.assertEqual(r.returncode, 1)
        self.assertIn('@verify sdk mismatch ', r.stdout)

    def test_missing_module_still_checks_present_modules(self):
        (self.exefs / 'sdk').unlink()
        r = self.run_verify()
        self.assertEqual(r.returncode, 1)
        self.assertIn('@verify sdk missing', r.stdout)
        self.assertIn('@verify main match ', r.stdout)

    def test_truncated_main_has_specific_error(self):
        (self.exefs / 'main').write_bytes(b'NSO0')
        r = self.run_verify()
        self.assertEqual(r.returncode, 1)
        self.assertIn('truncated', r.stdout)

    def test_invalid_nso_signature(self):
        (self.exefs / 'main').write_bytes(b'bad!' + self.files['main'][4:])
        r = self.run_verify()
        self.assertEqual(r.returncode, 1)
        self.assertIn('not a decrypted NSO', r.stdout)

    def test_game_directory_is_not_touched(self):
        game = self.root / 'game'
        (game / 'build').mkdir(parents=True)
        (game / 'build' / 'cancel').write_text('pause', encoding='utf-8')
        r = self.run_verify('--game', str(game))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == '__main__':
    unittest.main()
