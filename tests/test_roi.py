from __future__ import annotations

import numpy as np
from unittest.mock import MagicMock
from rppg_stress.roi import FaceRoiExtractor, RoiResult, draw_roi_overlay

def test_face_distance_calculation():
    # Inisialisasi extractor dengan backend haar
    extractor = FaceRoiExtractor(backend="haar")
    
    # Mock detect_face untuk mengembalikan bounding box tertentu
    # x1=100, y1=100, x2=200, y2=200 (lebar = 100 px)
    extractor.detect_face = MagicMock(return_value=(100, 100, 200, 200))
    
    # Buat frame dummy ukuran 640x480
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Panggil extract
    result = extractor.extract(frame)
    
    # Bounding box width = 200 - 100 = 100 pixels
    # frame_width = 640
    # focal_length = 640 * 0.8 = 512
    # expected_distance = (512 * 14.0) / 100 = 71.68 cm
    assert result.face_distance is not None
    assert abs(result.face_distance - 71.68) < 1e-2

def test_draw_roi_overlay_handles_distance():
    # Test bahwa draw_roi_overlay tidak crash saat face_distance diset
    result = RoiResult(
        rgb=np.array([120.0, 120.0, 120.0]),
        bbox=(100, 100, 200, 200),
        boxes={"forehead": (120, 110, 180, 130)},
        face_area_ratio=0.1,
        detected=True,
        face_distance=71.68
    )
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    out_frame = draw_roi_overlay(frame, result)
    assert out_frame.shape == frame.shape

def test_draw_roi_overlay_handles_landmarks():
    # Test bahwa draw_roi_overlay tidak crash saat landmarks diset (gambar mesh)
    dummy_landmarks = [(150, 150) for _ in range(468)]
    result = RoiResult(
        rgb=np.array([120.0, 120.0, 120.0]),
        bbox=(100, 100, 200, 200),
        boxes={"forehead": (120, 110, 180, 130)},
        face_area_ratio=0.1,
        detected=True,
        face_distance=71.68,
        landmarks=dummy_landmarks
    )
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    out_frame = draw_roi_overlay(frame, result)
    assert out_frame.shape == frame.shape


def test_draw_roi_overlay_handles_raw_landmarks():
    # Test bahwa draw_roi_overlay tidak crash saat raw_landmarks diset (menggunakan drawing_utils resmi)
    class MockNormalizedLandmark:
        def __init__(self, x, y, z=0.0):
            self.x = x
            self.y = y
            self.z = z

    dummy_raw_landmarks = [MockNormalizedLandmark(0.5, 0.5) for _ in range(468)]
    dummy_landmarks = [(150, 150) for _ in range(468)]
    result = RoiResult(
        rgb=np.array([120.0, 120.0, 120.0]),
        bbox=(100, 100, 200, 200),
        boxes={"forehead": (120, 110, 180, 130)},
        face_area_ratio=0.1,
        detected=True,
        face_distance=71.68,
        landmarks=dummy_landmarks,
        raw_landmarks=dummy_raw_landmarks
    )
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    out_frame = draw_roi_overlay(frame, result)
    assert out_frame.shape == frame.shape


def test_mediapipe_extract_no_face():
    extractor = FaceRoiExtractor(backend="mediapipe")
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = extractor.extract(frame)
    assert not result.detected
    assert result.bbox is None


def test_mediapipe_extract_with_face():
    extractor = FaceRoiExtractor(backend="mediapipe")
    
    # Mock result dari FaceLandmarker
    mock_result = MagicMock()
    # 468 landmarks
    landmarks = []
    for i in range(468):
        lm = MagicMock()
        # default coordinates
        lm.x = 0.5
        lm.y = 0.5
        landmarks.append(lm)
        
    mock_result.face_landmarks = [landmarks]
    extractor._mp_mesh.detect = MagicMock(return_value=mock_result)
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = extractor.extract(frame)
    assert result.detected
    assert result.bbox is not None
    assert result.landmarks is not None
    assert len(result.landmarks) == 468


def test_draw_roi_overlay_cheek_symmetry():
    from unittest.mock import patch
    import cv2
    from rppg_stress.roi import FACEMESH_SYMMETRY, LEFT_CHEEK_BOUNDARY, RIGHT_CHEEK_BOUNDARY
    
    # Create landmarks where landmarks[i] = (i * 10, i * 10)
    dummy_landmarks = [(i * 10, i * 10) for i in range(468)]
    
    # We want right_inside to contain some specific indices, e.g., 350 and 351.
    def mock_point_polygon_test(poly, pt, measureDist):
        # Determine which region is being tested by checking the first vertex of the polygon
        first_vertex_x = poly[0][0]
        # Since landmarks[i] = (i * 10, i * 10), index = x // 10
        first_idx = int(round(first_vertex_x / 10.0))
        
        # If first_idx is RIGHT_CHEEK_BOUNDARY[0] (366)
        if first_idx == 366:
            pt_idx = int(round(pt[0] / 10.0))
            if pt_idx in [350, 351]:
                return 1.0
        return -1.0

    result = RoiResult(
        rgb=np.array([120.0, 120.0, 120.0]),
        bbox=(100, 100, 200, 200),
        boxes={"right_cheek": (100, 100, 150, 150), "left_cheek": (150, 100, 200, 150)},
        face_area_ratio=0.1,
        detected=True,
        face_distance=71.68,
        landmarks=dummy_landmarks
    )
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    drawn_lines = []
    def mock_line(img, pt1, pt2, color, thickness=1, lineType=cv2.LINE_AA):
        idx1 = int(round(pt1[0] / 10.0))
        idx2 = int(round(pt2[0] / 10.0))
        drawn_lines.append((idx1, idx2))
        return img

    # We also mock FACEMESH_TESSELATION to contain some specific edges for testing
    mock_tessellation = {(350, 351), (350, 360)}
    
    with patch("cv2.pointPolygonTest", side_effect=mock_point_polygon_test), \
         patch("cv2.line", side_effect=mock_line), \
         patch("rppg_stress.roi.FACEMESH_TESSELATION", mock_tessellation):
        
        draw_roi_overlay(frame, result)
        
    mirror_350 = FACEMESH_SYMMETRY[350]
    mirror_351 = FACEMESH_SYMMETRY[351]
    
    assert (350, 351) in drawn_lines or (351, 350) in drawn_lines
    assert (mirror_350, mirror_351) in drawn_lines or (mirror_351, mirror_350) in drawn_lines



