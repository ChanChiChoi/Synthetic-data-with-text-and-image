# -*- coding: utf-8 -*-

import os
import cv2
import glob
import math
import random
import numpy as np
import os.path as osp
from xml.dom.minidom import Document
import multiprocessing as mp
import logging
from PIL import Image,ImageDraw,ImageFont 

#resultImgsDir: the directory of resulting images
resultImgsDir = '/home/synth_recepit_text/result_imgs'

#resultXmlDir:the directory of resulting xml
resultXmlDir = '/home/synth_recepit_text/result_xmls' 

#bgiDIr: the directory of background images
bgiDir = '/home/synth_recepit_text/bgi'

FORMAT = '%(asctime)-15s [%(processName)s] %(message)s'
gTtf= '/home/synth_recepit_text/ttf'
logging.basicConfig(format = FORMAT)

#gBlockSize: the size of text lines, which one process will process
gBlockSize = 30
#ttfSize: the set of sizes of font, which will be used to create the text
ttfSize = [25,30,35,40,45,50,55,60,65,70,75,80]

def _paste(bgi,draw,ttf,size,curRow,curCol,curText,cols):

    ttfont = ImageFont.truetype(ttf,size) 
    curText = curText.split('\t')
    curText = curText[random.randint(0,len(curText)-1 )]
    maxNumText = math.floor((cols-curCol)/size)
    string = curText[:maxNumText].strip()
    numText = len(string)
    numAscii = sum([1 for i in string if 0<ord(i)<255])
    
    if numText >= 2:
        #random the RGB values
        bgr = [random.randint(100,254) for i in range(3)]
        #x,y point
        #draw = ImageDraw.Draw(bgi)
        #logging.warn('{}_{}_{}_{}\t{}'.format(cols,curCol,size,string,numText))
        draw.text((curCol,curRow),string, tuple(bgr), font=ttfont) 
    else:
        string = ''
        
    #=====
    '''width height '''
    width,height = ttfont.getsize(string)
#    bgi = np.array(bgi,dtype = np.uint8)
#    cv2.rectangle(bgi,(curCol,curRow),(curCol+width,curRow+height),(0,0,0),1)
#    
#    bgi = Image.fromarray(bgi)
    return bgi,string,width,height

def _xml(doc,anno,string,xminT,yminT,xmaxT,ymaxT):

    if not string: return
    body = doc.createElement('object')
    anno.appendChild(body)

    name = doc.createElement('name')
    nameText = doc.createTextNode('text')
    name.appendChild(nameText)
    body.appendChild(name)

    content = doc.createElement('textContent')
    contentText = doc.createTextNode(string)
    content.appendChild(contentText)
    body.appendChild(content)

    bndbox = doc.createElement('bndbox')

    xmin = doc.createElement('xmin')
    ymin = doc.createElement('ymin')
    xmax = doc.createElement('xmax')
    ymax = doc.createElement('ymax')

    xminText = doc.createTextNode(str(xminT))
    yminText = doc.createTextNode(str(yminT))
    xmaxText = doc.createTextNode(str(xmaxT))
    ymaxText = doc.createTextNode(str(ymaxT))

    xmin.appendChild(xminText)
    ymin.appendChild(yminText)
    xmax.appendChild(xmaxText)
    ymax.appendChild(ymaxText)

    bndbox.appendChild(xmin)
    bndbox.appendChild(ymin)
    bndbox.appendChild(xmax)
    bndbox.appendChild(ymax)
    body.appendChild(bndbox)


def paste(imgname,bgi,text,ttf,ttfRandom):

    bgi = cv2.imread(bgi)
    rows,cols,depth = bgi.shape
    
    bgi = Image.fromarray(bgi)
    draw = ImageDraw.Draw(bgi)

    curRow = 0
    curRowInter = random.randint(2,7)
    curRow += curRowInter
    curTtfSize = random.randint(0,len(ttfRandom)-1)

    #create the xml head
    doc = Document()
    anno = doc.createElement('Annotations')
    doc.appendChild(anno)
    imgNameNode = doc.createElement('imgName')
    imgNameNode.appendChild(doc.createTextNode(imgname))
    anno.appendChild(imgNameNode)

    height,width,depth = rows,cols,depth
    sizeNode = doc.createElement('size')
    widthNode = doc.createElement('width')
    widthNode.appendChild(doc.createTextNode(str(width)))
    sizeNode.appendChild(widthNode)
    heightNode = doc.createElement('height')
    heightNode.appendChild(doc.createTextNode(str(height)))
    sizeNode.appendChild(heightNode)
    depthNode = doc.createElement('depth')
    depthNode.appendChild(doc.createTextNode(str(depth)))
    sizeNode.appendChild(depthNode)
    anno.appendChild(sizeNode)

    #calc the row and write the text on the row
    while curRow + ttfRandom[curTtfSize] <=rows:
        #cur col point
        curCol = random.randint(0,cols-1)
        
        #cur row point
        '''paste the text on bgi '''
        if curCol < cols*0.9 and curRow+ttfRandom[curTtfSize] <= rows:
           #if curcols is bigger than 0.9*cols, then do not paste the line
           curText = text[random.randint(0,len(text)-1)]
           
           bgi,string,width,height = _paste(bgi,draw,ttf,ttfRandom[curTtfSize],curRow,curCol,curText,cols)
           _xml(doc,anno,string,xminT = curCol,yminT = curRow,xmaxT = curCol+width,ymaxT = curRow+height)
           curRow += curRowInter 
           curRow += ttfRandom[curTtfSize]
           
        #cur intervel
        curRowInter = random.randint(2,7)
        #cur ttf size
        curTtfSize = random.randint(0,len(ttfRandom)-1)
        
    return np.array(bgi), doc

def handle(text):
    
    ind, text = text
    #pid
    pid = os.getpid()
    #background image
    bgis = glob.glob( osp.join(bgiDir,'*.jpg') )
    #select one background image
    curBgi = random.randint(0,len(bgis)-1)
    bgi = bgis[curBgi]

    #ttf
    ttfs = glob.glob(osp.join(gTtf,'*.ttf'))
    curTtf = random.randint(0,len(ttfs)-1)    
    ttf = ttfs[curTtf]
   
    #ttf size random
    ttfRandom = [1]+[ random.randint(0,1) for i in range(len(ttfSize)-1)] 
    ttfRandom = [ran*size for ran,size in zip(ttfRandom, ttfSize)] 
    ttfRandom = [i for i in ttfRandom if i != 0] 
    
    imgname = '{}_{}_{}.jpg'.format(ind,pid,curTtf) 
    bgi,doc =  paste(imgname,bgi,text,ttf,ttfRandom)
    cv2.imwrite(osp.join('result_imgs',imgname),bgi)
    xmlFileName = osp.join('result_xmls','{}.xml'.format(imgname[:-4]))
    with open(xmlFileName, "w") as fxml:
        fxml.write(str(doc.toprettyxml(indent = "    ", newl = "\n", encoding = "utf-8"),encoding = 'utf-8'))
    logging.warn('{}'.format(ind))
    return

if __name__ == '__main__':

    #the directory of text,which will be paste on the background images
    textDir = '/home/zzc/data/synth_recepit_text/text'
    
    total = open(osp.join(textDir,'text.txt')).readlines()

    numP = 20
    totalSP = []
    inter = math.ceil(len(total)/gBlockSize)
    for i in range(inter):
        totalSP.append(total[i::inter]) 
    
    p = mp.Pool(20)
    p.map(handle, enumerate(totalSP))
