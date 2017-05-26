# -*- coding:utf-8 -*-  
import numpy as np
from scipy.misc import imread,imresize,imsave
import scipy.stats as stats
import matplotlib.pyplot as plt
import h5py
from math import sqrt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import threading
import multiprocessing
normpdf = stats.norm.pdf        # probability density function for norm
norm = np.linalg.norm           
pinv = np.linalg.pinv
dot = np.dot
t = np.transpose

samples = {'A':0.8, 'B':0.4, 'C':0.6,'D':0.8,'E':0.8,'F':0.8}

# tranfer when calculating error
def im2double(im):
    info = np.iinfo(im.dtype)
    return im.astype(np.double) / info.max

# read image
def readImg(filename):
    img=im2double(imread(filename))
    if len(img.shape) == 2:
        img=img[:,:,np.newaxis]
    return img

def imwrite(im, filename):
    img = np.copy(im)
    img = img.squeeze()
    if img.dtype==np.double:
        #img = np.array(img*255, dtype=np.uint8)
        img = img * np.iinfo(np.uint8).max
        img = img.astype(np.uint8)
    imsave(filename, img)

# get the noise mask of corrImg
def getNoiseMask(corrImg):
    return np.array(corrImg!=0,dtype='double')

# restore image by calculating RGB means of surrounding pixels.
def restoreByMeans(img,radius):
    resImg=np.copy(img)
    noiseMask=getNoiseMask(img)
    rows,cols,channel = img.shape
    completedNum=0
    for row in range(rows):
        for col in range(cols):
            for chan in range(channel):
                if noiseMask[row,col,chan] != 0.:
                    continue
                tmpArr=[]
                # surrounding pixels with radius %radius%
                for i in range(row-radius,row+radius):
                    if i<0 or i>=rows:
                        continue
                    for j in range(col-radius,col+radius):
                        if j<0 or j>=cols or noiseMask[i,j,chan] == 0.:
                            continue
                        if i==row and j==col:
                            continue
                        tmpArr.append(img[i,j,chan]) 
                if len(tmpArr) == 0:
                    tmpArr=[0]
                # get the means of surrounding pixel's RGB
                resImg[row,col,chan]=np.mean(tmpArr,axis=0)
            completedNum+=1
            if completedNum%100==0:
                print "completed:"+str(float(completedNum)/rows/cols*100)+"%"
    return resImg

# restore image by quadratic linear regression
def restoreByLinearRegression(img,filename):
    radius=int(8*samples[filename])
    resImg=np.copy(img)
    noiseMask=getNoiseMask(img)
    rows,cols,channel = img.shape
    completedNum=0
    oldRate=0
    for row in range(rows):
        for col in range(cols):
            # considering the boundary, and transfer the square horizontally and vertically
            if row-radius<0:
                rowl=0
                rowr=rowl+2*radius
            elif row+radius>=rows:
                rowr=rows-1
                rowl=rowr-2*radius
            else:
                rowl=row-radius
                rowr=row+radius

            if col-radius<0:
                coll=0
                colr=coll+2*radius
            elif col+radius>=cols:
                colr=cols-1
                coll=colr-2*radius
            else:
                coll=col-radius
                colr=col+radius
            
            for chan in range(channel):
                if noiseMask[row,col,chan] != 0.:
                    continue
                x_train=[]
                y_train=[]
                for i in range(rowl,rowr):
                    for j in range(coll,colr):
                        if noiseMask[i,j,chan] == 0. or (i==row and j==col):
                            continue
                        x_train.append([i,j])
                        y_train.append([img[i,j,chan]])
                if len(x_train)==0:
                    continue
                # quadratic linear regression
                quadratic=PolynomialFeatures(degree=3)
                x_train_quadratic=quadratic.fit_transform(x_train)
                regressor_quadratic=LinearRegression()
                regressor_quadratic.fit(x_train_quadratic,y_train)
                # predict    
                test=quadratic.transform([[row,col]])
                resImg[row,col,chan]=regressor_quadratic.predict(test)
            completedNum+=1
            rate=int(float(completedNum)/rows/cols*100)
            if rate-oldRate > 0:
                print filename+".png restored:"+str(rate)+"%"
                oldRate=rate
    return resImg

# evaluate error rate
def computeError(resImg,corrImg,filename):
    noiseRatio=samples[filename]
    try:
        im1=readImg(filename+'_ori.png').flatten()
        im2=corrImg.flatten()
        im3=resImg.flatten()
        print((
            '{}({}):\n'
            'Distance between original and corrupted: {}\n'
            'Distance between original and reconstructed (regression): {}'
        ).format(filename, noiseRatio, norm(im1-im2, 2), norm(im1-im3, 2)))
    except Exception as error:
        print error

# do restoring
def run(filename):
    img=readImg(filename+'.png')
    # resImg=restoreByMeans(img,4)
    # imwrite(resImg,filename+'_recoverMean.png')
    # computeError(resImg,img,filename)
    resImg=restoreByLinearRegression(img,filename)
    imwrite(resImg,filename+'_recoverLinear.png')
    computeError(resImg,img,filename)

def main():
    queue=['A','B','C']     # task img queue
    for img in queue:
        t=multiprocessing.Process(target=run,args=img)
        t.start()
        print 'Begin to restore '+img+'.png'

if __name__=='__main__':
    main()
    


