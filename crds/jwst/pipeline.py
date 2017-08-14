"""This module provides functions that interface with the JWST calibration code to determine
things like "reference types used by a pipeline."

>>> header_to_reftypes(test_header("0.7.0", "FGS_DARK"))
['ipc', 'linearity', 'mask', 'refpix', 'rscd', 'saturation', 'superbias']

>>> header_to_reftypes(test_header("0.7.0", "NRS_BRIGHTOBJ"))
['area', 'camera', 'collimator', 'dark', 'disperser', 'distortion', 'drizpars', 'extract1d', 'filteroffset', 'fore', 'fpa', 'fringe', 'gain', 'ifufore', 'ifupost', 'ifuslicer', 'ipc', 'linearity', 'mask', 'msa', 'ote', 'pathloss', 'photom', 'readnoise', 'refpix', 'regions', 'rscd', 'saturation', 'specwcs', 'straymask', 'superbias', 'v2v3', 'wavelengthrange']

>>> header_to_reftypes(test_header("0.7.0", "MIR_IMAGE"))
['area', 'camera', 'collimator', 'dark', 'disperser', 'distortion', 'filteroffset', 'flat', 'fore', 'fpa', 'gain', 'ifufore', 'ifupost', 'ifuslicer', 'ipc', 'linearity', 'mask', 'msa', 'ote', 'photom', 'readnoise', 'refpix', 'regions', 'rscd', 'saturation', 'specwcs', 'superbias', 'v2v3', 'wavelengthrange']

>>> header_to_reftypes(test_header("0.7.0", "MIR_LRS-FIXEDSLIT"))
['area', 'camera', 'collimator', 'dark', 'disperser', 'distortion', 'drizpars', 'extract1d', 'filteroffset', 'flat', 'fore', 'fpa', 'fringe', 'gain', 'ifufore', 'ifupost', 'ifuslicer', 'ipc', 'linearity', 'mask', 'msa', 'ote', 'pathloss', 'photom', 'readnoise', 'refpix', 'regions', 'rscd', 'saturation', 'specwcs', 'straymask', 'superbias', 'v2v3', 'wavelengthrange']

>>> header_to_pipelines(test_header("0.7.0", "FGS_DARK"))
['calwebb_dark.cfg', 'skip_2b.cfg']

>>> header_to_pipelines(test_header("0.7.0", "NRS_BRIGHTOBJ"))
['calwebb_sloper.cfg', 'calwebb_spec2.cfg']

>>> header_to_pipelines(test_header("0.7.0", "MIR_IMAGE"))
['calwebb_sloper.cfg', 'calwebb_image2.cfg']
    
>>> header_to_pipelines(test_header("0.7.0", "MIR_LRS-FIXEDSLIT"))
['calwebb_sloper.cfg', 'calwebb_spec2.cfg']

>>> _get_missing_calver("0.7.0")
'0.7.0'

>>> s = _get_missing_calver(None)
>>> isinstance(s, str)
True

>>> s = _get_missing_calver()
>>> isinstance(s, str)
True

>>> _get_missing_context()
'jwst-operational'

>>> _get_missing_context('jwst_0341.pmap')
'jwst_0341.pmap'

"""

# --------------------------------------------------------------------------------------

import os.path

# import yaml     DEFERRED

# --------------------------------------------------------------------------------------

# from jwst import version     DEFERRED

# --------------------------------------------------------------------------------------
import crds
from crds.core import log, utils
from crds.core.log import srepr
from crds.client import api

# --------------------------------------------------------------------------------------

def test_header(calver, exp_type):
    header = {
        "META.INSTRUMENT.NAME" : "SYSTEM",
        "REFTYPE" : "CRDSCFG",
        "META.CALIBRATION_SOFTWARE_VERSION" : calver,
        "META.EXPOSURE.TYPE" : exp_type,
        }
    return header

# --------------------------------------------------------------------------------------

HERE = os.path.dirname(__file__) or "."

SYSTEM_CRDSCFG_B7_PATH = os.path.join(HERE, "jwst_system_crdscfg_b7.yaml")
SYSTEM_CRDSCFG_B7_1_PATH = os.path.join(HERE, "jwst_system_crdscfg_b7.1.yaml")

# --------------------------------------------------------------------------------------

def _get_missing_calver(cal_ver=None):
    """If `cal_ver` is None, return the calibration software version for 
    the installed version of calibration code.  Otherwise return `cal_ver`
    unchanged.
    """
    if cal_ver is None:
        from jwst import version
        cal_ver = version.__version__
    return cal_ver

def _get_missing_context(context=None):
    """Default the context to `jwst-operational` if `context` is None, otherwise
    return context unchanged.
    """
    return "jwst-operational" if context is None else context
    
# --------------------------------------------------------------------------------------

def header_to_reftypes(header, context=None):
    """Given a dataset `header`,  extract the EXP_TYPE or META.EXPOSURE.TYPE keyword
    from and use it to look up the reftypes required to process it.

    Return a list of reftype names.
    """
    with log.warn_on_exception("Failed determining exp_type, cal_ver from header", log.PP(header)):
        exp_type, cal_ver = _header_to_exptype_calver(header)
        return get_reftypes(exp_type, cal_ver, context)
    return []

def get_reftypes(exp_type, cal_ver=None, context=None):
    """Given `exp_type` and `cal_ver` and `context`,  locate the appropriate SYSTEM CRDSCFG
    reference file and determine the reference types required to process every pipeline Step
    nominally associated with that exp_type.
    """
    context = _get_missing_context(context)
    cal_ver = _get_missing_calver(cal_ver)
    with log.warn_on_exception("Failed determining required reftypes from",
                               "EXP_TYPE", srepr(exp_type), "CAL_VER", srepr(cal_ver)):
        config_manager = _get_config_manager(context, cal_ver)
        return config_manager.exptype_to_reftypes(exp_type)
    return []

# This is potentially an external interface to system data processing (SDP) / the archive pipeline.
def header_to_pipelines(header, context=None):
    """Given a dataset `header`,  extract the EXP_TYPE or META.EXPOSURE.TYPE keyword
    from and use it to look up the pipelines required to process it.

    Return a list of reftype names.
    """
    with log.augment_exception("Failed determining exp_type, cal_ver from header", log.PP(header)):
        exp_type, cal_ver = _header_to_exptype_calver(header)
    return get_pipelines(exp_type, cal_ver, context)

def get_pipelines(exp_type, cal_ver=None, context=None):
    """Given `exp_type` and `cal_ver` and `context`,  locate the appropriate SYSTEM CRDSCFG
    reference file and determine the sequence of pipeline .cfgs required to process that
    exp_type.
    """
    context = _get_missing_context(context)
    cal_ver = _get_missing_calver(cal_ver)
    with log.augment_exception("Failed determining required pipeline .cfgs for",
                               "EXP_TYPE", srepr(exp_type), "CAL_VER", srepr(cal_ver)):
        config_manager = _get_config_manager(context, cal_ver)
        return config_manager.exptype_to_pipelines(exp_type)

def _header_to_exptype_calver(header):
    """Given dataset `header`,  return the EXP_TYPE and CAL_VER values."""
    cal_ver = header.get("META.CALIBRATION_SOFTWARE_VERSION", header.get("CAL_VER"))
    exp_type = header.get("META.EXPOSURE.TYPE",  header.get("EXP_TYPE", "UNDEFINED"))
    return exp_type, cal_ver

@utils.cached  # for caching,  pars must be immutable, ideally simple
def _get_config_manager(context, cal_ver):
    """Given `context` and calibration s/w version `cal_ver`,  identify the appropriate
    SYSTEM CRDSCFG reference file and create a CrdsCfgManager from it.
    """
    refpath = _get_config_refpath(context, cal_ver)
    return _load_refpath(context, refpath)

def _load_refpath(context, refpath):
    """Given `context` and SYSTEM CRDSCFG reference at `refpath`,  construct a CrdsCfgManager."""
    import yaml
    with open(refpath) as opened:
        crdscfg =  yaml.load(opened)
    return CrdsCfgManager(context, refpath, crdscfg)

def _get_config_refpath(context, cal_ver):
    """Given CRDS `context` and calibration s/w version `cal_ver`,  identify the applicable
    SYSTEM CRDSCFG reference file, cache it, and return the file path.
    """
    # default enables running if system calver is never delivered as reference file.
    # and for B7 and earlier.
    if cal_ver < '0.7.7':
        refpath = SYSTEM_CRDSCFG_B7_PATH
    else:
        refpath = SYSTEM_CRDSCFG_B7_1_PATH
        
    with log.verbose_warning_on_exception(
            "Failed locating SYSTEM CRDSCFG reference",
            "under context", repr(context),
            "and cal_ver", repr(cal_ver) + "."):
        header = {
            "META.INSTRUMENT.NAME" : "SYSTEM", 
            "META.CALIBRATION_SOFTWARE_VERSION": cal_ver 
        }
        pmap = crds.get_symbolic_mapping(context)
        imap = pmap.get_imap("system")
        rmapping = imap.get_rmap("crdscfg")
        ref = rmapping.get_best_ref(header)
        refpath = rmapping.locate_file(ref)
        api.dump_references(context, [ref])
    log.verbose("Using", srepr(os.path.basename(refpath)),
                "to determine applicable default reftypes for", srepr(cal_ver))
    return refpath

class CrdsCfgManager(object):
    """The CrdsCfgManager handles using SYSTEM CRDSCFG information to compute things."""
    def __init__(self, context, refpath, crdscfg):
        self._context = context
        self._refpath = refpath
        self._crdscfg = utils.Struct(crdscfg)
        
    def exptype_to_reftypes(self, exp_type):
        """For a given EXP_TYPE string, return a list of reftypes needed to process that
        EXP_TYPE through the data levels appropriate for that EXP_TYPE.

        Return [reftypes, ... ]
        """
        reftypes = self._crdscfg.exptypes_to_reftypes[exp_type]
        log.verbose("Applicable reftypes for", srepr(exp_type), 
                    "determined by", srepr(os.path.basename(self._refpath)),
                    "are", srepr(reftypes))
        return reftypes

    def exptype_to_pipelines(self, exp_type):
        """For a given EXP_TYPE string, return a list of pipeline .cfg's needed to 
        process that EXP_TYPE through the appropriate data levels.

        Return [.cfg's, ... ]
        """
        pipelines = self._crdscfg.exptypes_to_pipelines[exp_type]
        log.verbose("Applicable pipelines for", srepr(exp_type), 
                    "determined by", srepr(os.path.basename(self._refpath)),
                    "are", srepr(pipelines))
        return pipelines

def test():
    import doctest, crds.jwst.pipeline
    return doctest.testmod(crds.jwst.pipeline)

# --------------------------------------------------------------------------------------

if __name__ == "__main__":
    print(test())
