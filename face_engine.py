import numpy as np
import cv2
from PIL import Image
import os
import math

# Try importing DeepFace
try:
    from deepface import DeepFace
except ImportError:
    DeepFace = None

class FaceEngine:
    def __init__(self):
        self.known_encodings = []
        self.known_ids = []
        # Use a lightweight model for recognition and detection
        self.model_name = "VGG-Face" 

    def load_known_faces(self, events_data):
        self.known_encodings = []
        self.known_ids = []
        for evt_id, event in events_data.items():
            for person in event.get('data', []):
                if 'encoding' in person:
                    self.known_encodings.append(np.array(person['encoding']))
                    self.known_ids.append({'event_id': evt_id, 'name': person.get('name', 'Unknown')})

    def process_image(self, image_pil, detector_backend='ssd'):
        if DeepFace is None:
            return []

        # Convert PIL to BGR (DeepFace usually expects BGR/OpenCV format)
        img_np = np.array(image_pil)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        # List of backends to try. 
        # Priority: Requested Backend -> RetinaFace -> SSD -> OpenCV -> MTCNN
        backends_to_try = [detector_backend]
        fallbacks = ['retinaface', 'ssd', 'opencv', 'mtcnn', 'yolov8']
        for fb in fallbacks:
            if fb not in backends_to_try:
                backends_to_try.append(fb)

        embeddings_obj = None
        last_error = None

        for backend in backends_to_try:
            try:
                # 1. Detection & Embedding (Represent)
                # Enforce detection=True to catch "No face" errors explicitly
                embeddings_obj = DeepFace.represent(
                    img_path=img_bgr, 
                    model_name=self.model_name, 
                    detector_backend=backend,
                    enforce_detection=True
                )
                if embeddings_obj:
                    # If we got here, it worked!
                    # print(f"Face detected using {backend}")
                    break
            except ValueError as e:
                # "Face could not be detected" - try next backend
                last_error = e
                continue
            except Exception as e:
                # Other errors (e.g. missing dependencies)
                print(f"DeepFace Error ({backend}): {e}")
                last_error = e
                continue
        
        if embeddings_obj is None:
            # All backends failed
            return []

        results = []
        for face_obj in embeddings_obj:
            if 'embedding' not in face_obj: continue
            
            embedding = face_obj['embedding']
            area = face_obj.get('facial_area', {})
            x, y, w, h = area.get('x',0), area.get('y',0), area.get('w',0), area.get('h',0)
            
            # Check for invalid face area (DeepFace sometimes returns full image if enforce_detection=False and no face)
            # If w and h are almost the size of image, likely no face found with 'opencv' or 'ssd' if enforce_detection=False
            H, W, _ = img_np.shape
            if w > W*0.9 and h > H*0.9:
                # Likely false positive full-image return
                continue

            # Create standard bbox format (top, right, bottom, left)
            top, right, bottom, left = y, x+w, y+h, x
            
            face_data = {
                "bbox": (top, right, bottom, left),
                "encoding": embedding,
                "gender": "Unknown",
                "confidence": 0.0,
                "is_duplicate": False,
                "duplicate_info": None
            }
            
            # 2. Gender Detection
            face_crop = img_np[y:y+h, x:x+w]
            
            if face_crop.size > 0:
                try:
                    # Use 'skip' detector since we already cropped the face
                    analysis = DeepFace.analyze(
                        img_path=face_crop,
                        actions=['gender'],
                        detector_backend='skip',
                        enforce_detection=False,
                        silent=True
                    )
                    
                    if isinstance(analysis, list): analysis = analysis[0]
                    g_res = analysis['dominant_gender']
                    if g_res == "Man": g_res = "Male"
                    if g_res == "Woman": g_res = "Female"
                    
                    face_data["gender"] = g_res
                    face_data["confidence"] = analysis['gender'][analysis['dominant_gender']]
                except:
                    face_data["gender"] = "Unknown"

            # 3. De-duplication (Cosine Similarity)
            if self.known_encodings:
                current_vec = np.array(embedding)
                
                for idx, known_vec in enumerate(self.known_encodings):
                    dot = np.dot(known_vec, current_vec)
                    norm_a = np.linalg.norm(known_vec)
                    norm_b = np.linalg.norm(current_vec)
                    if norm_a == 0 or norm_b == 0: continue
                    
                    cosine_similarity = dot / (norm_a * norm_b)
                    
                    if cosine_similarity > 0.60:
                        face_data["is_duplicate"] = True
                        face_data["duplicate_info"] = self.known_ids[idx]
                        break
            
            results.append(face_data)
            
        return results

def draw_results(image_pil, results):
    img_cv = np.array(image_pil)
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
    
    for res in results:
        if "error" in res: continue
        
        top, right, bottom, left = res['bbox']
        color = (0, 255, 0)
        label = res['gender']
        
        if res['is_duplicate']:
            color = (0, 0, 255)
            label += " (DUPLICATE)"
            
        cv2.rectangle(img_cv, (left, top), (right, bottom), color, 2)
        cv2.putText(img_cv, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
    return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
