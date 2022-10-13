"""
twixtools: provides reading and limited writing capability of Siemens MRI raw
           data files (.dat).

@author: Philipp Ehses (philipp.ehses@dzne.de)
"""

import os
import re
import numpy as np


import twixtools.twixprot as twixprot
import twixtools.helpers as helpers
import twixtools.mdb
import twixtools.hdr_def as hdr_def


def read_twix(infile, read_prot=True, keep_syncdata_and_acqend=True,
              include_scans=None, parse_data=True):
    """Function for reading siemens twix raw data files.

    Parameters
    ----------
    infile : filename or measurement id of .dat file
    read_prot : bool, optional
        By default, the protocol information is read and parsed
        (this is also highly recommended)
    keep_syncdata_and_acqend : bool, optional
        By default, syncdata and acqend blocks are included in the mdb list.
        This is helpful for twix writing, but unnecessary otherwise.
    include_scans: list of scan numbers or None, optional
        By default, all scans in a multi-raid file are parsed.

    Returns
    -------
    out: list of twix scan(s)
        The twix scans themselves consist of a dict with these elements:
            - hdr: dict of parsed ascconv and XProtocol header information
            - hdr_str: header bytearray (used by write_twix)
            - mdb: list of measurement data blocks -- here is the MRI data
              use `help(twixtools.mdb.Mdb)` for more information
    """
    if isinstance(infile, str):
        # assume that complete path is given
        if infile[-4:].lower() != '.dat':
            infile += '.dat'   # adds filetype ending to file
    else:
        # filename not a string, so assume that it is the MeasID
        measID = infile
        infile = [f for f in os.listdir('.') if re.search(
            r'^meas_MID0*' + str(measID) + r'.*\.dat$', f)]
        if len(infile) == 0:
            print('error: .dat file with measID', measID, 'not found')
            raise ValueError
        elif len(infile) > 1:
            print('multiple files with measID', measID,
                  'found, choosing first occurence')
        infile = infile[0]

    infile = os.path.realpath(infile)

    fid = open(infile, 'rb')
    fid.seek(0, os.SEEK_END)
    fileSize = np.uint64(fid.tell())
    version_is_ve, NScans = helpers.idea_version_check(fid)

    out = list()
    # lazy software version check (VB or VD?)
    if version_is_ve:
        print('Software version: VD/VE (!?)')
        fid.seek(0, os.SEEK_SET)  # move pos to 9th byte in file
        raidfile_hdr = np.fromfile(fid, dtype=hdr_def.MultiRaidFileHeader,
                                   count=1)[0]
        # WARNING:
        # it is probably no longer necessary to append the raidfile_hdr for
        # lossless twix writing (as long as there are no changes to the twix
        # format!), so we don't need the following line
        # out.append(raidfile_hdr)
        NScans = raidfile_hdr["hdr"]["count_"]
        measOffset = list()
        measLength = list()
        for k in range(NScans):
            measOffset.append(raidfile_hdr['entry'][k]['off_'])
            measLength.append(raidfile_hdr['entry'][k]['len_'])
    else:
        # in VB versions, the first 4 bytes indicate the beginning of the
        # raw data part of the file
        print('Software  : VB (!?)')
        # VB does not support multiple scans in one file:
        measOffset = [np.uint64(0)]
        measLength = [fileSize]

    print('')
    for s in range(NScans):
        if include_scans is not None and s not in include_scans:
            # skip scan if it is not requested
            continue

        scanStart = measOffset[s]
        scanEnd = scanStart + measLength[s]
        pos = measOffset[s]
        fid.seek(pos, os.SEEK_SET)
        meas_init = np.fromfile(fid, dtype=hdr_def.SingleMeasInit, count=1)[0]
        hdr_len = meas_init["hdr_len"]
        out.append(dict())
        out[-1]['mdb'] = list()
        if read_prot:
            fid.seek(pos, os.SEEK_SET)
            hdr = twixprot.parse_twix_hdr(fid)
            out[-1]['hdr'] = hdr
            fid.seek(pos, os.SEEK_SET)
            out[-1]['hdr_str'] = np.fromfile(fid, dtype="<S1", count=hdr_len)

        if version_is_ve:
            out[-1]['raidfile_hdr'] = raidfile_hdr['entry'][s]

        # if data is not requested (headers only)
        if not parse_data:
            continue

        pos = measOffset[s] + np.uint64(hdr_len)
        scanStart = pos
        print('Scan ', s)
        helpers.update_progress(pos - scanStart, scanEnd - scanStart, True)
        while pos + 128 < scanEnd:  # fail-safe not to miss ACQEND
            helpers.update_progress(
                pos - scanStart, scanEnd - scanStart, False)
            fid.seek(pos, os.SEEK_SET)
            mdb = twixtools.mdb.Mdb(fid, version_is_ve)

            # jump to mdh of next scan
            pos += mdb.dma_len

            if not keep_syncdata_and_acqend:
                if mdb.is_flag_set('SYNCDATA'):
                    continue
                elif mdb.is_flag_set('ACQEND'):
                    break

            out[-1]['mdb'].append(mdb)

            if mdb.is_flag_set('ACQEND'):
                break

        print()

    fid.close()

    return out


def write_twix(scanlist, outfile, version_is_ve=True):
    """Function for writing siemens twix raw data files.

    Parameters
    ----------
    scanlist: list of twix scan(s)
    outfile: output filename for twix file (.dat)
    version_is_ve: bool that determines what whether to write a VA/VB
        or VD/VE compatible twix file.
        IMPORTANT: This tool does not allow for conversion between versions.
        This bool should be set to the original twix file version!
        IMPORTANT: `write_twix` currently only supports VE twix files!
    """

    def write_sync_bytes(fid):
        syncbytes = (512-(fid.tell()) % 512) % 512
        fid.write(b'\x00' * syncbytes)

    if isinstance(scanlist, dict):
        scanlist = [scanlist]

    with open(outfile, 'xb') as fid:
        if version_is_ve:
            # allocate space for multi-header
            fid.write(b'\x00' * 10240)

        scan_pos = list()
        scan_len = list()
        for scan in scanlist:

            if not isinstance(scan, dict):
                continue

            # keep track of byte pos
            scan_pos.append(fid.tell())

            # write header
            scan['hdr_str'].tofile(fid)

            # make sure that scan counters are consecutive integers
            fix_scancounters(scan['mdb'])

            # write mdbs
            for mdb in scan['mdb']:
                # write mdh
                mdb.mdh.tofile(fid)
                data = np.atleast_2d(mdb.data)
                if version_is_ve:
                    if mdb.is_flag_set('SYNCDATA')\
                            or mdb.is_flag_set('ACQEND'):
                        data.tofile(fid)
                    else:
                        for c in range(data.shape[0]):
                            # write channel header
                            mdb.channel_hdr[c].tofile(fid)
                            # write data
                            data[c].tofile(fid)
                else:  # WIP: VB version
                    mdb.mdh.tofile(fid)
                    # write data
                    data[c].tofile(fid)

            # update scan_len
            scan_len.append(fid.tell() - scan_pos[-1])

            # add sync bytes between scans
            write_sync_bytes(fid)

        # now write preallocated MultiRaidFileHeader
        if version_is_ve:
            multi_header = construct_multiheader(scanlist)
            # write scan_pos & scan_len for each scan (in case they changed)
            for key, (pos_, len_) in enumerate(zip(scan_pos, scan_len)):
                multi_header['entry'][key]['len_'] = len_
                multi_header['entry'][key]['off_'] = pos_
            # write MultiRaidFileHeader
            fid.seek(0)
            multi_header.tofile(fid)


def construct_multiheader(scanlist):
    multi_header = np.zeros(1, dtype=hdr_def.MultiRaidFileHeader)[0]
    n_scans = len(scanlist)
    for key, scan in enumerate(scanlist):
        if 'raidfile_hdr' in scan:
            # we have a template
            multi_header['entry'][key] = scan['raidfile_hdr'].copy()
        else:  # not really necessary anymore, but may be helpful in future
            # start from scratch
            pat = b'x' * 20
            prot = b'noname'
            meas_id = np.uint32(0)
            file_id = np.uint32(0)
            if 'file_id' in scan:
                file_id = scan['file_id']
            if 'hdr' in scan and 'Config' in scan['hdr']:
                config = scan['hdr']['Config']
                if 'tPatientName' in config:
                    pat = config['tPatientName'].encode()
                    if all([item == 'x' for item in pat.decode()]):
                        # fix number of 'x' for anonymized names (lucky? guess)
                        pat = b'x' * min(64, len(pat)+9)
                if 'SequenceDescription' in config:
                    prot = config['SequenceDescription'].encode()
                if 'SequenceDescription' in config:
                    meas_id = np.uint32(config['MeasUID'])

            multi_header['entry']['measId_'][key] = meas_id
            multi_header['entry']['fileId_'][key] = file_id
            multi_header['entry']['patName_'][key] = pat
            multi_header['entry']['protName_'][key] = prot

    # write NScans
    multi_header['hdr']['count_'] = n_scans

    return multi_header


def fix_scancounters(mdb_list, start_cnt=1):
    ''' makes sure that all ulScanCounter in mdb_list are consecutive integers
    This is necessary if mdbs are added/removed to/from a mdb_list.
    '''
    cnt = start_cnt
    for mdb in mdb_list:
        if mdb.is_flag_set('SYNCDATA'):  # ignore SYNCDATA
            continue
        mdb.mdh['ulScanCounter'] = cnt
        for cha in mdb.channel_hdr:
            cha['ulScanCounter'] = cnt
        cnt += 1


def del_from_mdb_list(mdb_list, function):
    ''' helper function to safely remove multiple items from mdb_list at once
    Parameters
    ----------
    mdb_list: input list of mdbs
    function: function used to filter mdbs

    Example
    --------
    Remove all mdbs from mdb_list which have the flag 'noname60' set to True.
    >>> del_from_mdb_list(mdb_list, lambda mdb: mdb.is_flag_set('noname60'))
    '''

    ind2remove = [key for key, mdb in enumerate(mdb_list) if function(mdb)]

    for key in sorted(ind2remove, reverse=True):
        del mdb_list[key]

    return
