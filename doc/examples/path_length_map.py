"""
==================================
Calculate Path Length Map
(e.g. For Anisotropic Radiation Therapy Contours)
==================================

We show how to calculate a Path Length Map given a set of streamlines and a
region of interest (ROI). The Path Length Map is a volume in which each voxel's
value is the shortest distance along a streamline to a given
region of interest (ROI). This map can be used to anisotropically modify
radiation therapy treatment contours based on a tractography model of the local
white matter anatomy, as described in [Jordan_2018_plm]_, by
executing this tutorial with the gross tumor volume (GTV) as the ROI.

"""

from dipy.data import read_stanford_labels
from dipy.reconst.shm import CsaOdfModel
from dipy.data import default_sphere
from dipy.direction import peaks_from_model
from dipy.tracking.local import ThresholdTissueClassifier
from dipy.tracking import utils
from dipy.tracking.local import LocalTracking
from dipy.tracking.streamline import Streamlines
from dipy.viz import actor, window
from dipy.viz.colormap import line_colors
from dipy.tracking.utils import get_flexi_tvis_affine, path_length
import nibabel as nib
import numpy as np

"""
First, we need to generate some streamlines and visualize. For a more complete
description of these steps, please refer to the CSA Probabilistic Tracking and
the Visualization of ROI Surface Rendered with Streamlines Tutorials.

"""

hardi_img, gtab, labels_img = read_stanford_labels()
data = hardi_img.get_data()
labels = labels_img.get_data()
affine = hardi_img.affine

white_matter = (labels == 1) | (labels == 2)

csa_model = CsaOdfModel(gtab, sh_order=6)
csa_peaks = peaks_from_model(csa_model, data, default_sphere,
                             relative_peak_threshold=.8,
                             min_separation_angle=45,
                             mask=white_matter)

classifier = ThresholdTissueClassifier(csa_peaks.gfa, .25)

"""
We will use an anatomically-based corpus callosum ROI as our seed mask to
demonstrate the method. In practice, this corpus callosum mask (labels == 2)
should be replaced with the desired ROI mask (e.g. gross tumor volume (GTV),
lesion mask, or electrode mask).

"""

# Make a corpus callosum seed mask for tracking
seed_mask = labels == 2
seeds = utils.seeds_from_mask(seed_mask, density=[1, 1, 1], affine=affine)

# Make a streamline bundle model of the corpus callosum ROI connectivity
streamlines = LocalTracking(csa_peaks, classifier, seeds, affine,
                            step_size=2)
streamlines = Streamlines(streamlines)

# Visualize the streamlines and the Path Length Map base ROI
# (in this case also the seed ROI)

streamlines_actor = actor.line(streamlines, line_colors(streamlines))
surface_opacity = 0.5
surface_color = [0, 1, 1]
seedroi_actor = actor.contour_from_roi(seed_mask, affine,
                                       surface_color, surface_opacity)

ren = window.ren()
ren.add(streamlines_actor)
ren.add(seedroi_actor)

"""
If you set interactive to True (below), the rendering will pop up in an
interactive window.
"""

interactive = False
if interactive:
    window.show(ren)

ren.zoom(1.5)
ren.reset_clipping_range()

window.record(ren, out_path='plm_roi_sls.png', size=(1200, 900),
              reset_camera=False)

"""
.. figure:: plm_roi_sls.png
   :align: center

   **A top view of corpus callosum streamlines with the blue transparent ROI in
   the center**.
"""

"""
Now we calculate the Path Length Map using the corpus callosum streamline
bundle and corpus callosum ROI.

NOTE: the mask used to seed the tracking does not have to be the Path
Length Map base ROI, as we do here, but it often makes sense for them to be the
same ROI if we want a map of the whole brain's distance back to our ROI.
(e.g. we could test a hypothesis about the motor system by making a streamline
bundle model of the cortico-spinal track (CST) and input a lesion mask as our
Path Length Map base ROI to restrict the analysis to the CST)
"""


# set the path to the data
basedir = '/path/to/mydata'  # INSERT PATH TO DATA#

# set the path to the ROI (roi) and the streamlines (trk)
roi_pathfrag = 'GTV_diffusion_space.nii.gz'
trk_pathfrag = 'GTV_streamlines.trk'

roipath = os.path.join(basedir, roi_pathfrag)
trkpath = os.path.join(basedir, trk_pathfrag)
savepath = os.path.join(basedir, 'WMPL_map.nii.gz')

# load the streamlines from the trk file
trk, hdr = nib.trackvis.read(trkpath)
sls = [item[0] for item in trk]

# load the ROI from the nifti file
roiim = nib.load(roipath)
roidata = roiim.get_data()
roiaff = roiim.get_affine()

# create mapping between the streamlines and ROI
grid2trk_aff = get_flexi_tvis_affine(hdr, affine)

# calculate the WMPL
wmpl = path_length(sls, roidata, grid2trk_aff)

# save the WMPL as a nifti
path_length_img = nib.Nifti1Image(wmpl.astype(np.float32), affine)
nib.save(path_length_img, 'example_cc_path_length_map.nii.gz')


"""
.. figure:: Path_Length_Map.png
   :align: center

   **Path Length Map showing the shortest distance, along a streamline,
   from the corpus callosum ROI**.

References
----------

.. [Jordan_2018_plm] Jordan K. et al., "An Open-Source Tool for Anisotropic
Radiation Therapy Planning in Neuro-oncology Using DW-MRI Tractography",
PREPRINT (biorxiv), 2018.

.. include:: ../links_names.inc

"""
