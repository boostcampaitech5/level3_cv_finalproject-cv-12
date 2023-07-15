import cv2
import matplotlib.pyplot as plt
import copy
import numpy as np

from src import model
from src import util
from src.body import Body
from src.hand import Hand

TEST_IMAGE = '/opt/ml/dataset/ganddddi/sw2_0.jpg'
OUTPUT = '/opt/ml/pytorch-openpose/output/sw2_0.png'


# Body, Hand model load
body_estimation = Body('/opt/ml/checkpoints/body_pose_model.pth')
hand_estimation = Hand('model/hand_pose_model.pth')

# image read
test_image = TEST_IMAGE
oriImg = cv2.imread(test_image)  # B,G,R order

# body_estimation foreward
candidate, subset = body_estimation(oriImg)

print(len(candidate)) # 14*4
print(candidate)
print(len(subset[0])) # [[20개]]
exit()
canvas = copy.deepcopy(oriImg)
canvas = util.draw_bodypose(canvas, candidate, subset)

# hand를 detect 후 hands_list에 넣는다.
# detect된 hand 들은 hands_list에 들어 있을 듯하다. ex) [hand1, hand2]
hands_list = util.handDetect(candidate, subset, oriImg)

all_hand_peaks = []
for x, y, w, is_left in hands_list:
    # cv2.rectangle(canvas, (x, y), (x+w, y+w), (0, 255, 0), 2, lineType=cv2.LINE_AA)
    # cv2.putText(canvas, 'left' if is_left else 'right', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # if is_left:
        # plt.imshow(oriImg[y:y+w, x:x+w, :][:, :, [2, 1, 0]])
        # plt.show()
    peaks = hand_estimation(oriImg[y:y+w, x:x+w, :])
    peaks[:, 0] = np.where(peaks[:, 0]==0, peaks[:, 0], peaks[:, 0]+x)
    peaks[:, 1] = np.where(peaks[:, 1]==0, peaks[:, 1], peaks[:, 1]+y)
    # else:
    #     peaks = hand_estimation(cv2.flip(oriImg[y:y+w, x:x+w, :], 1))
    #     peaks[:, 0] = np.where(peaks[:, 0]==0, peaks[:, 0], w-peaks[:, 0]-1+x)
    #     peaks[:, 1] = np.where(peaks[:, 1]==0, peaks[:, 1], peaks[:, 1]+y)
    #     print(peaks)
    all_hand_peaks.append(peaks)

canvas = util.draw_handpose(canvas, all_hand_peaks)

plt.imshow(canvas[:, :, [2, 1, 0]])
plt.axis('off')

plt.savefig(OUTPUT)

# plt.show()?
