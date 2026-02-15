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
        # Use Facenet512 - faster and more accurate than VGG-Face
        self.model_name = "Facenet512"
        # Cache for model warmup
        self._model_loaded = False

    def load_known_faces(self, events_data):
        self.known_encodings = []
        self.known_ids = []
        for evt_id, event in events_data.items():
            for person in event.get('data', []):
                if 'encoding' in person:
                    self.known_encodings.append(np.array(person['encoding']))
                    self.known_ids.append({'event_id': evt_id, 'name': person.get('name', 'Unknown')})

    def _preprocess_image(self, img_np, max_size=800):
        """Resize large images for faster processing while maintaining quality."""
        h, w = img_np.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            img_np = cv2.resize(img_np, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return img_np

    def process_image(self, image_pil, detector_backend='opencv', skip_gender=False):
        if DeepFace is None:
            return []

        # Convert PIL to BGR (DeepFace usually expects BGR/OpenCV format)
        img_np = np.array(image_pil)
        
        # Preprocess: resize large images for speed
        img_np = self._preprocess_image(img_np, max_size=720)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        # Optimized backend order: opencv (fastest) -> ssd (balanced) -> retinaface (accurate)
        # Limit fallbacks to 3 for speed
        backends_to_try = [detector_backend]
        fallbacks = ['opencv', 'ssd', 'retinaface']
        for fb in fallbacks:
            if fb not in backends_to_try and len(backends_to_try) < 3:
                backends_to_try.append(fb)

        embeddings_obj = None
        last_error = None

        for backend in backends_to_try:
            try:
                # Detection & Embedding with optimized settings
                embeddings_obj = DeepFace.represent(
                    img_path=img_bgr, 
                    model_name=self.model_name, 
                    detector_backend=backend,
                    enforce_detection=True,
                    align=True  # Alignment improves accuracy
                )
                if embeddings_obj:
                    self._model_loaded = True
                    break
            except ValueError as e:
                last_error = e
                continue
            except Exception as e:
                print(f"DeepFace Error ({backend}): {e}")
                last_error = e
                continue
        
        if embeddings_obj is None:
            return []

        results = []
        for face_obj in embeddings_obj:
            if 'embedding' not in face_obj: continue
            
            embedding = face_obj['embedding']
            area = face_obj.get('facial_area', {})
            x, y, w, h = area.get('x',0), area.get('y',0), area.get('w',0), area.get('h',0)
            
            # Check for invalid face area
            H, W, _ = img_np.shape
            if w > W*0.9 and h > H*0.9:
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
            
            # Gender Detection - optional for speed optimization
            if not skip_gender:
                face_crop = img_np[y:y+h, x:x+w]
                
                if face_crop.size > 0:
                    try:
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

            # Duplicate Detection using Cosine Similarity (more robust for Facenet512)
            if self.known_encodings:
                current_vec = np.array(embedding)
                current_norm = np.linalg.norm(current_vec)
                
                if current_norm > 0:
                    best_similarity = 0
                    best_match_idx = -1
                    
                    for idx, known_vec in enumerate(self.known_encodings):
                        known_norm = np.linalg.norm(known_vec)
                        if known_norm == 0: continue
                        
                        cosine_similarity = np.dot(known_vec, current_vec) / (known_norm * current_norm)
                        
                        if cosine_similarity > best_similarity:
                            best_similarity = cosine_similarity
                            best_match_idx = idx
                    
                    # Threshold: 0.65 for Facenet512 (optimized for accuracy)
                    if best_similarity > 0.65 and best_match_idx >= 0:
                        face_data["is_duplicate"] = True
                        face_data["duplicate_info"] = self.known_ids[best_match_idx]
                        face_data["match_confidence"] = best_similarity
            
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
