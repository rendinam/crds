{
    'extra_keys': (),
    'file_ext': '.fits',
    'filetype': 'dark',
    'ld_tpn': 'wfc3_drk_ld.tpn',
    'parkey': ('DETECTOR', 'CCDAMP', 'BINAXIS1', 'BINAXIS2', 'CCDGAIN', 'SAMP_SEQ', 'SUBTYPE'),
    'parkey_relevance': {'binaxis1': '(DETECTOR == "UVIS")', 'binaxis2': '(DETECTOR == "UVIS")', 'subtype': '(DETECTOR == "IR")', 'ccdgain': '(DETECTOR == "IR")', 'samp_seq': '(DETECTOR == "IR")'},
    'reffile_format': 'IMAGE',
    'reffile_required': 'none',
    'reffile_switch': 'darkcorr',
    'rmap_relevance': '(DARKCORR != "OMIT")',
    'suffix': 'drk',
    'text_descr': 'Dark Frame',
    'tpn': 'wfc3_drk.tpn',
    'unique_rowkeys': None,
}
