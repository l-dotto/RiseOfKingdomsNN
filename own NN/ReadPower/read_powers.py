import cv2
from glob import glob
import numpy as np
import pickle
from sklearn.preprocessing import normalize
from sklearn.neural_network import MLPClassifier
import sys
from collections import Counter
from os import listdir

#list for wrongly classified 
img_list = []

#takes an image and returns array with all digits pixels in it
def val(im):
    #copy becuase will be edited
    img = im.copy()

    #make an output, convert to grayscale and apply thresh-hold
    out = np.zeros(im.shape,np.uint8)
    gray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray,255,1,1,11,2)

    #find conours
    contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)

    #create empty return list
    samples =  np.empty((0,100))

    #for every contour if area large enoug to be digit add the box to list
    li = []
    for cnt in contours:
        if cv2.contourArea(cnt)>20:
            [x,y,w,h] = cv2.boundingRect(cnt)
            li.append([x,y,w,h])
    #sort list so it read from right to left
    li = sorted(li,key=lambda x: x[0], reverse=True)

    #loop over all digits
    for i in li:
        #unpack data
        x,y,w,h = i[0], i[1], i[2], i[3]

        #check if large enough to be digit but small enough to ignore rest
        if  h>20 and h<40 and w>15 and w<40:

            #draw rectangle with thresh-hold and shape correct form
            cv2.rectangle(im,(x,y),(x+w,y+h),(0,255,0),2)
            roi = thresh[y:y+h,x:x+w]
            roismall = cv2.resize(roi,(10,10))
            sample = roismall.reshape((1,100))
            samples = np.append(samples,sample,0)
            classification = int(classify(samples))

            #if user wants images shown
            if show_img:
                cv2.namedWindow('View Power',cv2.WINDOW_NORMAL)
                cv2.resizeWindow('View Power', 1600,600)
                cv2.imshow('View Power', im)
                #show for 100 ms and check if exit called (esc key)
                key = cv2.waitKey(0)
                if key == 27:
                    sys.exit()
                #print what the NN would classify the digits as
                print(classification)
    
    #if full number lower than 10m, add to wrongly classified list
    if classification < 10000000:
        img_list.append(img)

    #return all digits found
    return samples

#get list of found digits and runs it through NN
def classify(data):
    clas = []

    #run every found digit through NN
    for i in data:
        a = int(clf.predict([i])[0])
        if a == 11:
            a = 44
        clas.append(a)

    #reverse list and add all together in 1 integer to find final power
    clas.reverse()
    clas = map(str, clas)
    clas = ''.join(clas)
    return clas

#check if need to retrain NN, otherwise load old one
train = input("Train again? y/n ")
filename = 'finalized_model.sav'
if train == 'y':
    #load data and labels
    X = np.loadtxt('generalsamples.data',np.float32)
    Y = np.loadtxt('generalresponses.data',np.float32)
    print(Counter(Y))
    #normalize and set ratio for training/testing
    X_norm = normalize(X, axis=1, norm='l2')
    tr_ind = int(len(Y)*0.8)

    #create traiing and testing data
    X_train = X_norm[:tr_ind]
    X_test = X_norm[tr_ind:]

    Y_train = Y[:tr_ind]
    Y_test = Y[tr_ind:]

    #make NN and train
    clf = MLPClassifier(activation='relu', solver='adam', hidden_layer_sizes=(32), random_state=1, max_iter=5000)
    clf.fit(X_train, Y_train)

    #save the NN
    pickle.dump(clf, open(filename, 'wb'))
else:
    clf = pickle.load(open(filename, 'rb'))

#check if user wants to see image classification animation
show_img = input("Want to show all images being classified? y/n ")
if show_img == 'y':
    show_img = True
else:
    show_img = False

#ask user which kingdom to check
dirs = listdir('TestPictures/')
kingdom = input(f"What kindom would you like to check? {[i for i in dirs]}")
while kingdom not in dirs:
    kingdom = input(f"Please enter correct kingdom? {[i for i in dirs]}")

#get all images in kingdoms subdir
img_mask = f'TestPictures/{kingdom}/*.jpg'
img_names = glob(img_mask)
power = []

#loop over all images
for fn in img_names:
    #read image and zoom in on power
    img = cv2.imread(fn)
    img = img[450:1400, 1900:2150]

    #find all 6 powers in picture and append classified digits to list
    img1 = img[40:120, 20:220]
    data = val(img1)
    power.append(int(classify(data)))

    img2 = img[195:275, 20:220]
    data = val(img2)
    power.append(int(classify(data)))

    img3 = img[360:440, 20:220]
    data = val(img3)
    power.append(int(classify(data)))

    img4 = img[525:605, 20:220]
    data = val(img4)
    power.append(int(classify(data)))

    img5 = img[685:765, 20:220]
    data = val(img5)
    power.append(int(classify(data)))

    img6 = img[850:930, 20:220]
    data = val(img6)
    power.append(int(classify(data)))

#handle wrongly classified cases 
print(f"Could not read {len(img_list)} numbers. They will be shown to you, type them please!")
print("You can use enter to submit number and backspace to delete and escape to quit")

#loop over all wrongly classified images and let user enter power manually
img_list_dict = {48:0, 49:1, 50:2, 51:3, 52:4, 53:5, 54:6, 55:7, 56:8, 57:9}
for im in img_list: 
    add = ""
    while True:
        cv2.imshow('View Power', im)
        key = cv2.waitKey(0)
        back = False
        if key == 27:
            sys.exit()
        elif key == 8:
            back = True
        elif key == 13:
            print('\n')
            break
        elif key in img_list_dict.keys():
            number = img_list_dict[key]

        if not back:
            add = add + str(number)
        else:
            add = add[:-1]
        print(add)
    power.append(int(add))

#sort whole power list from large to small
sorted_list = sorted(power, reverse=True)

#remove the wrongly classified numbers
for i in  range(len(img_list)):
    sorted_list.remove(min(sorted_list))

print("Length: ", len(sorted_list))
print("Maximum: ", max(sorted_list))
print("Average: ", np.mean(sorted_list))
print("Minimum: ", min(sorted_list))
#print some statistics
total = sum(sorted_list)
top10 = np.sum(sorted_list[0:10])
top25 = np.sum(sorted_list[0:25])
top50 = np.sum(sorted_list[0:50])
top100 = np.sum(sorted_list[0:100])
print(f"Top 10 power is {top10} with average of {top10/10}")
print(f"Top 25 power is {top25} with average of {top25/25}")
print(f"Top 50 power is {top50} with average of {top50/50}")
print(f"Top 100 power is {top100} with average of {top100/100}")
print("Total power", total)