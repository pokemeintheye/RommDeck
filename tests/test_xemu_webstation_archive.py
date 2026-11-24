import io
import json
import unittest
import zipfile
from tools.xemu_webstation_archive import (
    UnsafeArchive, rommdeck_to_webstation, webstation_to_rommdeck,
)


def makezip(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return out.getvalue()


def inspect(data):
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return {n: zf.read(n) for n in zf.namelist()}


class XboxArchiveTests(unittest.TestCase):
    def setUp(self):
        self.contents = {'54430003/TitleMeta.xbx': b'meta', '54430003/ABC/save0': b'progress'}
        self.raw = makezip(self.contents)

    def test_upload_broker_root_and_manifest(self):
        output = inspect(rommdeck_to_webstation(self.raw, '54430003'))
        self.assertEqual(output['UDATA/54430003/ABC/save0'], b'progress')
        manifest = json.loads(output['.broker-manifest.json'])
        self.assertEqual(manifest['version'], 1)
        self.assertEqual(manifest['session']['emulator'], 'xemu')
        self.assertEqual(len(manifest['files']), 2)

    def test_round_trip(self):
        webstation = rommdeck_to_webstation(self.raw, '54430003')
        self.assertEqual(inspect(webstation_to_rommdeck(webstation, '54430003')), self.contents)

    def test_refuses_wrong_game(self):
        with self.assertRaises(UnsafeArchive):
            rommdeck_to_webstation(self.raw, '4d530021')

    def test_refuses_tdata_loss(self):
        with self.assertRaises(UnsafeArchive):
            webstation_to_rommdeck(makezip({'TDATA/54430003/cache': b'important'}), '54430003')

    def test_refuses_traversal(self):
        with self.assertRaises(UnsafeArchive):
            rommdeck_to_webstation(makezip({'54430003/../../escape': b'x'}), '54430003')


if __name__ == '__main__':
    unittest.main()
