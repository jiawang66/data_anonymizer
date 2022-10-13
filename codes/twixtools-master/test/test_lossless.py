import os
import tempfile
import unittest
from twixtools import twixzip


def md5(fname):
    import hashlib
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.digest()


infile = 'example_data/gre.dat'


class test_lossless(unittest.TestCase):

    def test(self):

        md5_orig = md5(infile)

        with tempfile.NamedTemporaryFile(suffix='.dat') as out_dat:
            with tempfile.NamedTemporaryFile(suffix='.h5') as out_h5:
                twixzip.compress_twix(infile=infile, outfile=out_h5.name)
                twixzip.reconstruct_twix(infile=out_h5.name,
                                         outfile=out_dat.name)
            md5_new = md5(out_dat.name)

        self.assertEqual(md5_orig, md5_new,
                         'lossless compression: md5 hashes do not match')


class test_remove_os(unittest.TestCase):

    def test(self):
        sz_orig = os.path.getsize(infile)

        with tempfile.NamedTemporaryFile(suffix='.dat') as out_dat:
            with tempfile.NamedTemporaryFile(suffix='.h5') as out_h5:
                twixzip.compress_twix(infile=infile, outfile=out_h5.name,
                                      remove_os=True)
                twixzip.reconstruct_twix(infile=out_h5.name,
                                         outfile=out_dat.name)
            sz_new = os.path.getsize(out_dat.name)

        self.assertEqual(sz_orig, sz_new,
                         'remove_os: file size not equal to original')


if __name__ == '__main__':
    unittest.main()
