# -*- coding: utf-8 -*-
# �� �̹����� ������ �м�
import cv2
import numpy as np

def analyze_image_properties(image_path):
    """�̹����� �Ӽ��� �м��ϴ� �Լ�"""
    image = cv2.imread(image_path)
    if image is None:
        print(f"�̹����� �ҷ��� �� �����ϴ�: {image_path}")
        return
    
    h, w, c = image.shape
    
    # �̹��� �⺻ ����
    print(f"\n=== {image_path.split('\\')[-1]} ===")
    print(f"�ػ�: {w} x {h}")
    print(f"ä�� ��: {c}")
    print(f"���� ũ��: {w * h * c} bytes")
    
    # ��� �м�
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    std_brightness = np.std(gray)
    print(f"��� ���: {mean_brightness:.2f}")
    print(f"��� ǥ������: {std_brightness:.2f}")
    
    # ��� �м�
    contrast = std_brightness / mean_brightness if mean_brightness > 0 else 0
    print(f"���: {contrast:.3f}")
    
    # ������ �м�
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    noise_level = np.mean(np.abs(gray.astype(float) - blurred.astype(float)))
    print(f"������ ����: {noise_level:.2f}")
    
    return {
        'resolution': (w, h),
        'brightness': mean_brightness,
        'contrast': contrast,
        'noise': noise_level
    }

# �� �̹��� ��
image1 = r"C:\Users\user\Desktop\Github\cosrec\KakaoTalk_20250706_161302093.jpg"  # ���� ����
image2 = r"C:\Users\user\Desktop\Github\cosrec\KakaoTalk_20250715_141326156.jpg"  # ���� ����

props1 = analyze_image_properties(image1)
props2 = analyze_image_properties(image2)

print("\n=== �� ��� ===")
if props1 and props2:
    print(f"�ػ� ����: {props1['resolution']} vs {props2['resolution']}")
    print(f"��� ����: {props1['brightness']:.2f} vs {props2['brightness']:.2f}")
    print(f"��� ����: {props1['contrast']:.3f} vs {props2['contrast']:.3f}")
    print(f"������ ����: {props1['noise']:.2f} vs {props2['noise']:.2f}")
