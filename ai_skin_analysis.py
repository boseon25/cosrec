# -*- coding: utf-8 -*-
"""
Google AI Studio ���� �Ǻ� �м� �ý���
���� ��ǻ�� ���� �м� + Google Gemini ��Ƽ��� AI �м�
"""

import cv2
import mediapipe as mp
import numpy as np
import google.generativeai as genai
from PIL import Image
import os
import tempfile
import base64
from datetime import datetime

class SkinAnalysisSystem:
    def __init__(self, api_key=None):
        """
        �Ǻ� �м� �ý��� �ʱ�ȭ
        
        Args:
            api_key (str): Google AI Studio API Ű
        """
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            print("?? API Ű�� �������� �ʾҽ��ϴ�. ��ǻ�� ���� �м��� �����մϴ�.")
    
    def extract_face_with_skin_mask(self, image_path):
        """���� �� ���� �� �Ǻ� ����ũ ���� �Լ�"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                print(f"? �̹����� �ҷ��� �� �����ϴ�: {image_path}")
                return None, None
            
            # �̹��� ǰ�� ����
            def enhance_image(img):
                denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
                lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                l = clahe.apply(l)
                enhanced = cv2.merge([l, a, b])
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
                return enhanced
            
            # MediaPipe �ʱ�ȭ
            mp_face_detection = mp.solutions.face_detection
            mp_face_mesh = mp.solutions.face_mesh
            
            # �� ����
            with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.3) as face_detection:
                results = face_detection.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                
                if not results.detections:
                    print("? �̹��� ǰ�� ���� �� ��õ�...")
                    enhanced_image = enhance_image(image)
                    results = face_detection.process(cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2RGB))
                    
                    if not results.detections:
                        print("? �ŷڵ��� ���缭 ��õ�...")
                        with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.1) as face_detection_low:
                            results = face_detection_low.process(cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2RGB))
                            if results.detections:
                                print("? �� ���� ����!")
                                image = enhanced_image
                            else:
                                print("? ���� ������ �� �����ϴ�.")
                                return None, None
                    else:
                        print("? �� ���� ����!")
                        image = enhanced_image
                
                # ���� ū �� ����
                largest_detection = max(results.detections, 
                                      key=lambda d: d.location_data.relative_bounding_box.width * d.location_data.relative_bounding_box.height)
                
                bboxC = largest_detection.location_data.relative_bounding_box
                h, w, _ = image.shape
                
                # �ٿ�� �ڽ� ���
                margin = 0.1
                x1 = max(0, int((bboxC.xmin - margin * bboxC.width) * w))
                y1 = max(0, int((bboxC.ymin - margin * bboxC.height) * h))
                x2 = min(w, int((bboxC.xmin + bboxC.width + margin * bboxC.width) * w))
                y2 = min(h, int((bboxC.ymin + bboxC.height + margin * bboxC.height) * h))
                
                face_img = image[y1:y2, x1:x2]
                
                # �Ǻ� ����ũ ����
                with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, 
                                         refine_landmarks=True, min_detection_confidence=0.3) as face_mesh:
                    face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                    mesh_results = face_mesh.process(face_rgb)
                    
                    if mesh_results.multi_face_landmarks:
                        landmarks = mesh_results.multi_face_landmarks[0]
                        mask = self._create_skin_mask(face_img, landmarks)
                        return face_img, mask
                    else:
                        print("?? �Ǻ� ����ũ ���� ����")
                        return face_img, None
                        
        except Exception as e:
            print(f"? ���� �߻�: {e}")
            return None, None
    
    def _create_skin_mask(self, face_img, landmarks):
        """�Ǻ� ����ũ ����"""
        face_h, face_w = face_img.shape[:2]
        mask = np.zeros((face_h, face_w), dtype=np.uint8)
        
        # �� ������
        FACE_OVAL = [
            10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
            397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
            172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109
        ]
        
        # ������ ������
        exclude_regions = {
            "left_eye": [159, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],
            "right_eye": [385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382],
            "left_eyebrow": [70, 63, 105, 66, 107, 55, 65, 52, 53, 46],
            "right_eyebrow": [296, 334, 293, 300, 276, 283, 282, 295, 285, 336],
            "lips": [61, 146, 91, 181, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
        }
        
        # �� �⺻ ����ũ ����
        face_points = []
        for idx in FACE_OVAL:
            if idx < len(landmarks.landmark):
                x = int(landmarks.landmark[idx].x * face_w)
                y = int(landmarks.landmark[idx].y * face_h)
                face_points.append([x, y])
        
        if len(face_points) > 0:
            face_points = np.array(face_points)
            cv2.fillPoly(mask, [face_points], 255)
            
            # ���� ���� ����ŷ
            for region_name, indices in exclude_regions.items():
                exclude_points = []
                for idx in indices:
                    if idx < len(landmarks.landmark):
                        x = int(landmarks.landmark[idx].x * face_w)
                        y = int(landmarks.landmark[idx].y * face_h)
                        exclude_points.append([x, y])
                
                if len(exclude_points) > 2:
                    exclude_points = np.array(exclude_points)
                    hull = cv2.convexHull(exclude_points)
                    
                    if region_name == "lips":
                        # �Լ��� �� �����ϰ� ó��
                        kernel_small = np.ones((3,3), np.uint8)
                        temp_mask = np.zeros((face_h, face_w), dtype=np.uint8)
                        cv2.fillPoly(temp_mask, [hull], 255)
                        temp_mask = cv2.erode(temp_mask, kernel_small, iterations=1)
                        mask = cv2.bitwise_and(mask, cv2.bitwise_not(temp_mask))
                    else:
                        cv2.fillPoly(mask, [hull], 0)
            
            # ����ũ ��ó��
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.GaussianBlur(mask, (3,3), 0)
            _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
            
        return mask
    
    def computer_vision_analysis(self, face_img, skin_mask):
        """��ǻ�� ���� ��� �Ǻ� �м�"""
        if face_img is None:
            return None
        
        # �ָ� Ž��
        def detect_wrinkles(img, mask):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray_eq = cv2.equalizeHist(gray)
            blurred = cv2.GaussianBlur(gray_eq, (3, 3), 0)
            edges = cv2.Canny(blurred, 30, 100)
            
            if mask is not None:
                edges = cv2.bitwise_and(edges, mask)
                mask_area = (mask > 0).sum()
                wrinkle_ratio = (edges > 0).sum() / mask_area if mask_area > 0 else 0
            else:
                wrinkle_ratio = (edges > 0).sum() / edges.size
            
            return wrinkle_ratio, edges
        
        # ��� Ž��
        def detect_pores(img, mask):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            high_pass = cv2.subtract(gray, cv2.GaussianBlur(gray, (9, 9), 0))
            _, binarized = cv2.threshold(high_pass, 15, 255, cv2.THRESH_BINARY)
            
            if mask is not None:
                binarized = cv2.bitwise_and(binarized, mask)
                mask_area = (mask > 0).sum()
                pore_ratio = (binarized > 0).sum() / mask_area if mask_area > 0 else 0
            else:
                pore_ratio = (binarized > 0).sum() / binarized.size
            
            return pore_ratio, binarized
        
        wrinkle_score, wrinkle_img = detect_wrinkles(face_img, skin_mask)
        pore_score, pore_img = detect_pores(face_img, skin_mask)
        
        return {
            'wrinkle_score': wrinkle_score,
            'pore_score': pore_score,
            'wrinkle_img': wrinkle_img,
            'pore_img': pore_img
        }
    
    def gemini_analysis(self, face_img, user_description="", cv_results=None):
        """Google Gemini�� Ȱ���� ��Ƽ��� AI �Ǻ� �м�"""
        if self.model is None:
            return "? API Ű�� �������� �ʾҽ��ϴ�."
        
        try:
            # �̹����� PIL ���·� ��ȯ
            face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(face_rgb)
            
            # ��ǻ�� ���� ��� ������ ������Ʈ ����
            cv_info = ""
            if cv_results:
                cv_info = f"""
                
                **��ǻ�� ���� �м� ���:**
                - �ָ� ����: {cv_results['wrinkle_score']:.3f}
                - ��� ����: {cv_results['pore_score']:.3f}
                """
            
            prompt = f"""
            �ȳ��ϼ���! ÷�ε� �� �̹����� �Ǻΰ� ������ �������� ���������� �м����ּ���.
            
            **����� ����:**
            {user_description}
            {cv_info}
            
            **�м� ��û ����:**
            
            1. ? **�Ǻ� ���� ���� ��** (10�� ����)
               - �������� �Ǻ� �ǰ���
               - �Ǻ� ���� ���ϼ�
               - �Ǻ� ������ ź�¼�
               - ���� ������ �ٰ�
            
            2. ? **�ָ� �м�**
               - �ָ��� ���� (ǥ�� �ָ�, ���� �ָ�, ���ָ�)
               - �ָ��� ���̿� ����
               - �ֿ� �߻� ���� (�̸�, ����, �԰� ��)
               - �ɰ��� �� (1-5�ܰ�)
            
            3. ?? **��� �м�**
               - ����� ũ��� ���ü�
               - ��� Ȯ�� ���� (��, ��, �̸�)
               - �����/ȭ��Ʈ��� ����
               - ��� ���� �� (1-5�ܰ�)
            
            4. ? **�Ǻ� �� & ���� �м�**
               - �Ǻ� ���� ���ϼ�
               - ���� ħ���̳� ���� ����
               - ȫ���� ���� ¡��
               - �Ǻ� ������ ����
            
            5. ? **����/���� ����**
               - ���� �Ǻ� Ÿ�� (�Ǽ�/����/���ռ�/�ΰ���)
               - ���� ���� ¡��
               - T���� U�� ���� ����
               - �Ǻ� �庮 ����
            
            6. ? **������ ����**
               - �켱 ���� �ʿ� ����
               - �ϻ� ��Ų�ɾ� ��ƾ ����
               - �����ؾ� �� �Ǻ� ����
               - �Ǻΰ� ġ�� ���� ����
            
            7. ? **�ܰ躰 ���� ��ȹ**
               - 1-2�� �ܱ� ���� �ɾ�
               - 1-3���� �߱� ���� ���
               - 6����+ ��� ���� ��ȹ
            
            **�м� �� �������:**
            - ����� ������ ������ ����Ͽ� �м�
            - ���̿� ������ ���� �Ϲ��� �Ǻ� Ư�� �ݿ�
            - �������� ������ ���� ���
            - �ǿ����̰� ��ü���� ���� ����
            - �ѱ��� �Ǻ� Ư�� ���
            
            ������ �� ��ü���̰� �ǿ����� �м��� ������ �ѱ���� �������ּ���.
            """
            
            response = self.model.generate_content([prompt, pil_image])
            return response.text
            
        except Exception as e:
            return f"? AI �м� �� ���� �߻�: {e}"
    
    def comprehensive_analysis(self, image_path, user_description=""):
        """�������� �Ǻ� �м� (��ǻ�� ���� + AI)"""
        print("? �� ���� �� �Ǻ� ���� ���� ��...")
        face_img, skin_mask = self.extract_face_with_skin_mask(image_path)
        
        if face_img is None:
            return None
        
        print("? ��ǻ�� ���� �м� ��...")
        cv_results = self.computer_vision_analysis(face_img, skin_mask)
        
        print("? AI ������ �м� ��...")
        ai_analysis = self.gemini_analysis(face_img, user_description, cv_results)
        
        # ��� ����
        report = self._generate_comprehensive_report(cv_results, ai_analysis, user_description)
        
        return {
            'face_img': face_img,
            'skin_mask': skin_mask,
            'cv_results': cv_results,
            'ai_analysis': ai_analysis,
            'comprehensive_report': report
        }
    
    def _generate_comprehensive_report(self, cv_results, ai_analysis, user_description):
        """���� ����Ʈ ����"""
        
        def interpret_cv_score(score, score_type):
            if score_type == "wrinkle":
                if score < 0.01:
                    return "�ſ� ����"
                elif score < 0.02:
                    return "����"
                elif score < 0.04:
                    return "����"
                else:
                    return "����"
            else:  # pore
                if score < 0.005:
                    return "�ſ� ����"
                elif score < 0.01:
                    return "����"
                elif score < 0.02:
                    return "����"
                else:
                    return "����"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
        ???????????????????????????????????????????????????????????
        ? **AI �Ǻ� �м� ���� ����Ʈ**
        ???????????????????????????????????????????????????????????
        
        ? **�м� �Ͻ�:** {timestamp}
        ? **����� ����:** {user_description}
        
        ����������������������������������������������������������������������������������������������������������������������������������������������
        ? **������ �м� ��� (Computer Vision)**
        ����������������������������������������������������������������������������������������������������������������������������������������������
        
        ? **�ָ� �м�**
        ? �ָ� ����: {cv_results['wrinkle_score']:.3f}
        ? ���� ��: {interpret_cv_score(cv_results['wrinkle_score'], 'wrinkle')}
        
        ?? **��� �м�**
        ? ��� ����: {cv_results['pore_score']:.3f}
        ? ���� ��: {interpret_cv_score(cv_results['pore_score'], 'pore')}
        
        ����������������������������������������������������������������������������������������������������������������������������������������������
        ? **AI ������ �м� ��� (Google Gemini)**
        ����������������������������������������������������������������������������������������������������������������������������������������������
        
        {ai_analysis}
        
        ����������������������������������������������������������������������������������������������������������������������������������������������
        ? **���� ���**
        ����������������������������������������������������������������������������������������������������������������������������������������������
        
        �� �м��� ��ǻ�� ������ ������ �м��� AI�� ������ �м��� ������ ����Դϴ�.
        
        ? **�м� �����:**
        ? ��ǻ�� ����: ������ ��ġ ��� ���� �м�
        ? AI ������: �ƶ��� �ؼ��� ������ ��
        ? ���� ���: ��ȣ ������ ���� ����
        
        ?? **���ǻ���:**
        ? �� �м��� ������̸� ������ ������ ��ü���� �ʽ��ϴ�
        ? �ɰ��� �Ǻ� ���� �� ������ ����� �����մϴ�
        ? �������� ȯ�� ������ ����Ͽ� �ؼ��Ͻñ� �ٶ��ϴ�
        
        ???????????????????????????????????????????????????????????
        """
        
        return report
    
    def save_analysis_results(self, results, output_dir="analysis_results"):
        """�м� ��� ����"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # �̹��� ��� ����
        cv2.imwrite(f"{output_dir}/face_{timestamp}.jpg", results['face_img'])
        cv2.imwrite(f"{output_dir}/wrinkle_{timestamp}.jpg", results['cv_results']['wrinkle_img'])
        cv2.imwrite(f"{output_dir}/pore_{timestamp}.jpg", results['cv_results']['pore_img'])
        
        if results['skin_mask'] is not None:
            cv2.imwrite(f"{output_dir}/skin_mask_{timestamp}.jpg", results['skin_mask'])
        
        # ����Ʈ ����
        with open(f"{output_dir}/report_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write(results['comprehensive_report'])
        
        print(f"? �м� ����� '{output_dir}' ������ ����Ǿ����ϴ�.")
        
        return f"{output_dir}/report_{timestamp}.txt"


def interactive_skin_analysis():
    """��ȭ�� �Ǻ� �м� �������̽�"""
    print("? AI �Ǻ� �м� �ý��� v2.0")
    print("=" * 60)
    
    # API Ű �Է�
    api_key = input("? Google AI Studio API Ű�� �Է��ϼ��� (���û���): ").strip()
    if not api_key:
        print("?? API Ű ���� ��ǻ�� ���� �м��� �����մϴ�.")
    
    # �ý��� �ʱ�ȭ
    system = SkinAnalysisSystem(api_key if api_key else None)
    
    # �̹��� ��� �Է�
    image_path = input("? �м��� �̹��� ���� ��θ� �Է��ϼ���: ").strip()
    
    if not os.path.exists(image_path):
        print("? ������ ã�� �� �����ϴ�.")
        return
    
    # ����� ���� �Է�
    print("\n? �߰� ������ �Է����ּ��� (���û���):")
    age = input("����: ").strip()
    gender = input("����: ").strip()
    skin_type = input("�Ǻ� Ÿ�� (�Ǽ�/����/���ռ�/�ΰ���): ").strip()
    concerns = input("�ֿ� �Ǻ� ���: ").strip()
    routine = input("���� ��Ų�ɾ� ��ƾ: ").strip()
    
    user_description = f"""
    ����: {age}
    ����: {gender}
    �Ǻ� Ÿ��: {skin_type}
    �ֿ� ���: {concerns}
    ���� ��ƾ: {routine}
    """.strip()
    
    # �м� ����
    print("\n? �м��� �����մϴ�...")
    print("=" * 60)
    
    results = system.comprehensive_analysis(image_path, user_description)
    
    if results is None:
        print("? �м��� �����߽��ϴ�.")
        return
    
    # ��� ���
    print(results['comprehensive_report'])
    
    # �̹��� ��� ǥ��
    print("\n? �м� ��� �̹����� ǥ���մϴ�...")
    cv2.imshow("���� ��", results['face_img'])
    cv2.imshow("�ָ� �м�", results['cv_results']['wrinkle_img'])
    cv2.imshow("��� �м�", results['cv_results']['pore_img'])
    
    if results['skin_mask'] is not None:
        cv2.imshow("�Ǻ� ����ũ", results['skin_mask'])
        masked_face = cv2.bitwise_and(results['face_img'], results['face_img'], mask=results['skin_mask'])
        cv2.imshow("�Ǻ� ������", masked_face)
    
    # ��� ���� ���� Ȯ��
    print("\n? �м� ����� �����Ͻðڽ��ϱ�? (y/n): ", end="")
    if input().lower() == 'y':
        report_path = system.save_analysis_results(results)
        print(f"? �� ����Ʈ: {report_path}")
    
    print("\n�ƹ� Ű�� ������ â�� �����ϴ�...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    interactive_skin_analysis()
