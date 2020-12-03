import argparse
import os
import multiprocessing
import sys
import numpy as np
from scipy.ndimage import filters,interpolation,morphology,measurements
from scipy import stats
import ocrolib
import cv2
import os

parser = argparse.ArgumentParser("""
 Image binarization using non-linear processing.

 This is a compute-intensive binarization method that works on degraded
 and historical book pages.
 """)
args = parser.parse_args()
args.nocheck = False
args.show = False
args.rawcopy = False
args.gray = False
args.threshold = 0.5
args.zoom = 0.5
args.escale = 1.0
args.bignore = 0.1
args.perc = 80
args.range = 20
args.maxskew = 2
args.lo = 5
args.hi = 90
args.skewsteps = 8
args.debug = 0
args.parallel = 0


def print_info(*objs):
    print("INFO: ", *objs, file=sys.stdout)


def print_error(*objs):
    print("ERROR: ", *objs, file=sys.stderr)


def check_page(image):
    if len(image.shape)==3: return "input image is color image %s"%(image.shape,)
    if np.mean(image)<np.median(image): return "image may be inverted"
    h,w = image.shape
    if h<600: return "image not tall enough for a page image %s"%(image.shape,)
    if h>10000: return "image too tall for a page image %s"%(image.shape,)
    if w<600: return "image too narrow for a page image %s"%(image.shape,)
    if w>10000: return "line too wide for a page image %s"%(image.shape,)
    return None

def estimate_skew_angle(image,angles):
    estimates = []
    for a in angles:
        v = np.mean(interpolation.rotate(image,a,order=0,mode='constant'),axis=1)
        v = np.var(v)
        estimates.append((v,a))
    # if args.debug>0:
    #     plt.plot([y for x,y in estimates],[x for x,y in estimates])
    #     plt.ginput(1,args.debug)
    _,a = max(estimates)
    return a


def H(s): return s[0].stop-s[0].start
def W(s): return s[1].stop-s[1].start
def A(s): return W(s)*H(s)



def normalize_raw_image(raw, fname):
    ''' perform image normalization '''
    image = raw-np.amin(raw)
    if np.amax(image)==np.amin(image):
        print_info("# image is empty: %s" % (fname))
        return None
    image /= np.amax(image)
    return image


def estimate_local_whitelevel(image, zoom=0.5, perc=80, range=20, debug=0):
    '''flatten it by estimating the local whitelevel
    zoom for page background estimation, smaller=faster, default: %(default)s
    percentage for filters, default: %(default)s
    range for filters, default: %(default)s
    '''
    m = interpolation.zoom(image,zoom)
    m = filters.percentile_filter(m,perc,size=(range,2))
    m = filters.percentile_filter(m,perc,size=(2,range))
    m = interpolation.zoom(m,1.0/zoom)
    # if debug>0:
        # plt.clf()
        # plt.imshow(m,vmin=0,vmax=1)
        # plt.ginput(1,debug)
    w,h = np.minimum(np.array(image.shape),np.array(m.shape))
    flat = np.clip(image[:w,:h]-m[:w,:h]+1,0,1)
    # if debug>0:
        # plt.clf()
        # plt.imshow(flat,vmin=0,vmax=1)
        # plt.ginput(1,debug)
    return flat


def estimate_skew(flat, bignore=0.1, maxskew=2, skewsteps=8):
    ''' estimate skew angle and rotate'''
    d0,d1 = flat.shape
    o0,o1 = int(bignore*d0),int(bignore*d1) # border ignore
    flat = np.amax(flat)-flat
    flat -= np.amin(flat)
    est = flat[o0:d0-o0,o1:d1-o1]
    ma = maxskew
    ms = int(2*maxskew*skewsteps)
    # print(linspace(-ma,ma,ms+1))
    angle = estimate_skew_angle(est,np.linspace(-ma,ma,ms+1))
    flat = interpolation.rotate(flat,angle,mode='constant',reshape=0)
    flat = np.amax(flat)-flat
    return flat, angle



def estimate_thresholds(flat, bignore=0.1, escale=1.0, lo=5, hi=90, debug=0):
    '''# estimate low and high thresholds
    ignore this much of the border for threshold estimation, default: %(default)s
    scale for estimating a mask over the text region, default: %(default)s
    lo percentile for black estimation, default: %(default)s
    hi percentile for white estimation, default: %(default)s
    '''
    d0,d1 = flat.shape
    o0,o1 = int(bignore*d0),int(bignore*d1)
    est = flat[o0:d0-o0,o1:d1-o1]
    if escale>0:
        # by default, we use only regions that contain
        # significant variance; this makes the percentile
        # based low and high estimates more reliable
        e = escale
        v = est-filters.gaussian_filter(est,e*20.0)
        v = filters.gaussian_filter(v**2,e*20.0)**0.5
        v = (v>0.3*np.amax(v))
        v = morphology.binary_dilation(v,structure=np.ones((int(e*50),1)))
        v = morphology.binary_dilation(v,structure=np.ones((1,int(e*50))))
        # if debug>0:
        #     plt.imshow(v)
        #     plt.ginput(1,debug)
        est = est[v]
    lo = stats.scoreatpercentile(est.ravel(),lo)
    hi = stats.scoreatpercentile(est.ravel(),hi)
    return lo, hi


def process1(job):
    fname,i = job
    print_info("# %s" % (fname))
    if args.parallel<2: print_info("=== %s %-3d" % (fname, i))
    raw = ocrolib.common.read_image_gray(fname)
    # dshow(raw,"input")
    # perform image normalization
    image = normalize_raw_image(raw, fname)

    if not args.nocheck:
        check = check_page(np.amax(image)-image)
        if check is not None:
            print_error(fname+"SKIPPED"+check+"(use -n to disable this check)")
            # return

    # check whether the image is already effectively binarized
    if args.gray:
        extreme = 0
    else:
        extreme = (np.sum(image<0.05)+np.sum(image>0.95))*1.0/np.prod(image.shape)
    if extreme>0.95:
        comment = "no-normalization"
        flat = image
    else:
        comment = ""
        # if not, we need to flatten it by estimating the local whitelevel
        if args.parallel<2: print_info("flattening")
        flat = estimate_local_whitelevel(image, args.zoom, args.perc, args.range, args.debug)

    # estimate skew angle and rotate
    if args.maxskew>0:
        if args.parallel<2: print_info("estimating skew angle")
        flat, angle = estimate_skew(flat, args.bignore, args.maxskew, args.skewsteps)
    else:
        angle = 0

    # estimate low and high thresholds
    if args.parallel<2: print_info("estimating thresholds")
    lo, hi = estimate_thresholds(flat, args.bignore, args.escale, args.lo, args.hi, args.debug)
    # rescale the image to get the gray scale image
    if args.parallel<2: print_info("rescaling")
    flat -= lo
    flat /= (hi-lo)
    flat = np.clip(flat,0,1)
    # if args.debug>0:
    #     plt.imshow(flat,vmin=0,vmax=1)
    #     plt.ginput(1,args.debug)
    bin = 1*(flat>args.threshold)

    # output the normalized grayscale and the thresholded images
    print_info("%s lo-hi (%.2f %.2f) angle %4.1f %s" % (fname, lo, hi, angle, comment))
    if args.parallel<2: print_info("writing")

    if args.output:
        if args.rawcopy: ocrolib.write_image_gray(args.output+"/%04d.raw.png"%i,raw)
        ocrolib.write_image_binary(args.output+"/"+os.path.basename(job[0])[:-4]+".png", bin)
        # ocrolib.write_image_gray(args.output+"/%04d.nrm.png"%i,flat)
    else:
        base,_ = ocrolib.allsplitext(fname)
        ocrolib.write_image_binary(args.output+"/"+os.path.basename(job[0])[:-4]+".png", bin)
        # ocrolib.write_image_gray(base+".nrm.png",flat)


def pre_processing(input_path, output_path):
    args.files = input_path
    args.output = output_path

    if args.debug>0 or args.show>0: args.parallel = 0

    if args.output:
        if not os.path.exists(args.output):
            os.mkdir(args.output)

    if args.parallel<2:
        # for i,f in enumerate(args.files):
            process1((args.files,0+1))
    else:
        pool = multiprocessing.Pool(processes=args.parallel)
        jobs = []
        for i,f in enumerate(args.files): jobs += [(f,i+1)]
        result = pool.map(process1,jobs)

if __name__ == '__main__':
    pre_processing(r'/Backup_Python_Files/template_match/main.png', 'output')



