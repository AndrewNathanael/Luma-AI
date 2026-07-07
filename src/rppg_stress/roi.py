"""Face detection and skin ROI extraction for rPPG."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import cv2
import numpy as np


Box = Tuple[int, int, int, int]  # x1, y1, x2, y2

# 1. Definisi koneksi kontur latar belakang wajah (faint mesh)
FACEMESH_LIPS = frozenset([(61, 146), (146, 91), (91, 181), (181, 84), (84, 17),
                           (17, 314), (314, 405), (405, 321), (321, 375),
                           (375, 291), (61, 185), (185, 40), (40, 39), (39, 37),
                           (37, 0), (0, 267),
                           (267, 269), (269, 270), (270, 409), (409, 291),
                           (78, 95), (95, 88), (88, 178), (178, 87), (87, 14),
                           (14, 317), (317, 402), (402, 318), (318, 324),
                           (324, 308), (78, 191), (191, 80), (80, 81), (81, 82),
                           (82, 13), (13, 312), (312, 311), (311, 310),
                           (310, 415), (415, 308)])

FACEMESH_LEFT_EYE = frozenset([(263, 249), (249, 390), (390, 373), (373, 374),
                               (374, 380), (380, 381), (381, 382), (382, 362),
                               (263, 466), (466, 388), (388, 387), (387, 386),
                               (386, 385), (385, 384), (384, 398), (398, 362)])

FACEMESH_LEFT_EYEBROW = frozenset([(276, 283), (283, 282), (282, 295),
                                   (295, 285), (300, 293), (293, 334),
                                   (334, 296), (296, 336)])

FACEMESH_RIGHT_EYE = frozenset([(33, 7), (7, 163), (163, 144), (144, 145),
                                (145, 153), (153, 154), (154, 155), (155, 133),
                                (33, 246), (246, 161), (161, 160), (160, 159),
                                (159, 158), (158, 157), (157, 173), (173, 133)])

FACEMESH_RIGHT_EYEBROW = frozenset([(46, 53), (53, 52), (52, 65), (65, 55),
                                    (70, 63), (63, 105), (105, 66), (66, 107)])

FACEMESH_FACE_OVAL = frozenset([(10, 338), (338, 297), (297, 332), (332, 284),
                                (284, 251), (251, 389), (389, 356), (356, 454),
                                (454, 323), (323, 361), (361, 288), (288, 397),
                                (397, 365), (365, 379), (379, 378), (378, 400),
                                (400, 377), (377, 152), (152, 148), (148, 176),
                                (176, 149), (149, 150), (150, 136), (136, 172),
                                (172, 58), (58, 132), (132, 93), (93, 234),
                                (234, 127), (127, 162), (162, 21), (21, 54),
                                (54, 103), (103, 67), (67, 109), (109, 10)])

FACEMESH_BACKGROUND_CONTOURS = FACEMESH_LIPS.union(
    FACEMESH_LEFT_EYE, FACEMESH_LEFT_EYEBROW,
    FACEMESH_RIGHT_EYE, FACEMESH_RIGHT_EYEBROW,
    FACEMESH_FACE_OVAL
)

# 2. MediaPipe FaceMesh Tessellation (sumber resmi: face_mesh_connections.py)
# Digunakan untuk menggambar mesh triangulasi padat di area sensor aktif.
FACEMESH_TESSELATION = frozenset([
    (127, 34),  (34, 139),  (139, 127), (11, 0),    (0, 37),    (37, 11),
    (232, 231), (231, 120), (120, 232), (72, 37),   (37, 39),   (39, 72),
    (128, 121), (121, 47),  (47, 128),  (232, 121), (121, 128), (128, 232),
    (104, 69),  (69, 67),   (67, 104),  (175, 171), (171, 148), (148, 175),
    (118, 50),  (50, 101),  (101, 118), (73, 39),   (39, 40),   (40, 73),
    (9, 151),   (151, 108), (108, 9),   (48, 115),  (115, 131), (131, 48),
    (194, 204), (204, 211), (211, 194), (74, 40),   (40, 185),  (185, 74),
    (80, 42),   (42, 183),  (183, 80),  (40, 92),   (92, 186),  (186, 40),
    (230, 229), (229, 118), (118, 230), (202, 212), (212, 214), (214, 202),
    (83, 18),   (18, 17),   (17, 83),   (76, 61),   (61, 146),  (146, 76),
    (160, 29),  (29, 30),   (30, 160),  (56, 157),  (157, 173), (173, 56),
    (106, 204), (204, 194), (194, 106), (135, 214), (214, 192), (192, 135),
    (203, 165), (165, 98),  (98, 203),  (21, 71),   (71, 68),   (68, 21),
    (51, 45),   (45, 4),    (4, 51),    (144, 24),  (24, 23),   (23, 144),
    (77, 146),  (146, 91),  (91, 77),   (205, 50),  (50, 187),  (187, 205),
    (201, 200), (200, 18),  (18, 201),  (91, 106),  (106, 182), (182, 91),
    (90, 91),   (91, 181),  (181, 90),  (85, 84),   (84, 17),   (17, 85),
    (206, 203), (203, 36),  (36, 206),  (148, 171), (171, 140), (140, 148),
    (92, 40),   (40, 39),   (39, 92),   (193, 189), (189, 244), (244, 193),
    (159, 158), (158, 28),  (28, 159),  (247, 246), (246, 161), (161, 247),
    (236, 3),   (3, 196),   (196, 236), (54, 68),   (68, 104),  (104, 54),
    (193, 168), (168, 8),   (8, 193),   (117, 228), (228, 31),  (31, 117),
    (189, 193), (193, 55),  (55, 189),  (98, 97),   (97, 99),   (99, 98),
    (126, 47),  (47, 100),  (100, 126), (166, 79),  (79, 218),  (218, 166),
    (155, 154), (154, 26),  (26, 155),  (209, 49),  (49, 131),  (131, 209),
    (135, 136), (136, 150), (150, 135), (47, 126),  (126, 217), (217, 47),
    (223, 52),  (52, 53),   (53, 223),  (45, 51),   (51, 134),  (134, 45),
    (211, 170), (170, 140), (140, 211), (67, 69),   (69, 108),  (108, 67),
    (43, 106),  (106, 91),  (91, 43),   (230, 119), (119, 120), (120, 230),
    (226, 130), (130, 247), (247, 226), (63, 53),   (53, 52),   (52, 63),
    (238, 20),  (20, 242),  (242, 238), (46, 70),   (70, 156),  (156, 46),
    (78, 62),   (62, 96),   (96, 78),   (46, 53),   (53, 63),   (63, 46),
    (143, 34),  (34, 227),  (227, 143), (123, 117), (117, 111), (111, 123),
    (44, 125),  (125, 19),  (19, 44),   (236, 134), (134, 51),  (51, 236),
    (216, 206), (206, 205), (205, 216), (154, 153), (153, 22),  (22, 154),
    (39, 37),   (37, 167),  (167, 39),  (200, 201), (201, 208), (208, 200),
    (36, 142),  (142, 100), (100, 36),  (57, 212),  (212, 202), (202, 57),
    (20, 60),   (60, 99),   (99, 20),   (28, 158),  (158, 157), (157, 28),
    (35, 226),  (226, 113), (113, 35),  (160, 159), (159, 27),  (27, 160),
    (204, 202), (202, 210), (210, 204), (113, 225), (225, 46),  (46, 113),
    (43, 202),  (202, 204), (204, 43),  (62, 76),   (76, 77),   (77, 62),
    (137, 123), (123, 116), (116, 137), (41, 38),   (38, 72),   (72, 41),
    (203, 129), (129, 142), (142, 203), (64, 98),   (98, 240),  (240, 64),
    (49, 102),  (102, 64),  (64, 49),   (41, 73),   (73, 74),   (74, 41),
    (212, 216), (216, 207), (207, 212), (42, 74),   (74, 184),  (184, 42),
    (169, 170), (170, 211), (211, 169), (170, 149), (149, 176), (176, 170),
    (105, 66),  (66, 69),   (69, 105),  (122, 6),   (6, 168),   (168, 122),
    (123, 147), (147, 187), (187, 123), (96, 77),   (77, 90),   (90, 96),
    (65, 55),   (55, 107),  (107, 65),  (89, 90),   (90, 180),  (180, 89),
    (101, 100), (100, 120), (120, 101), (63, 105),  (105, 104), (104, 63),
    (93, 137),  (137, 227), (227, 93),  (15, 86),   (86, 85),   (85, 15),
    (129, 102), (102, 49),  (49, 129),  (14, 87),   (87, 86),   (86, 14),
    (55, 8),    (8, 9),     (9, 55),    (100, 47),  (47, 121),  (121, 100),
    (145, 23),  (23, 22),   (22, 145),  (88, 89),   (89, 179),  (179, 88),
    (6, 122),   (122, 196), (196, 6),   (88, 95),   (95, 96),   (96, 88),
    (138, 172), (172, 136), (136, 138), (215, 58),  (58, 172),  (172, 215),
    (115, 48),  (48, 219),  (219, 115), (42, 80),   (80, 81),   (81, 42),
    (195, 3),   (3, 51),    (51, 195),  (43, 146),  (146, 61),  (61, 43),
    (171, 175), (175, 199), (199, 171), (81, 82),   (82, 38),   (38, 81),
    (53, 46),   (46, 225),  (225, 53),  (144, 163), (163, 110), (110, 144),
    (52, 65),   (65, 66),   (66, 52),   (229, 228), (228, 117), (117, 229),
    (34, 127),  (127, 234), (234, 34),  (107, 108), (108, 69),  (69, 107),
    (109, 108), (108, 151), (151, 109), (48, 64),   (64, 235),  (235, 48),
    (62, 78),   (78, 191),  (191, 62),  (129, 209), (209, 126), (126, 129),
    (111, 35),  (35, 143),  (143, 111), (117, 123), (123, 50),  (50, 117),
    (222, 65),  (65, 52),   (52, 222),  (19, 125),  (125, 141), (141, 19),
    (221, 55),  (55, 65),   (65, 221),  (3, 195),   (195, 197), (197, 3),
    (25, 7),    (7, 33),    (33, 25),   (220, 237), (237, 44),  (44, 220),
    (70, 71),   (71, 139),  (139, 70),  (122, 193), (193, 245), (245, 122),
    (247, 130), (130, 33),  (33, 247),  (71, 21),   (21, 162),  (162, 71),
    (170, 169), (169, 150), (150, 170), (188, 174), (174, 196), (196, 188),
    (216, 186), (186, 92),  (92, 216),  (2, 97),    (97, 167),  (167, 2),
    (141, 125), (125, 241), (241, 141), (164, 167), (167, 37),  (37, 164),
    (72, 38),   (38, 12),   (12, 72),   (38, 82),   (82, 13),   (13, 38),
    (63, 68),   (68, 71),   (71, 63),   (226, 35),  (35, 111),  (111, 226),
    (101, 50),  (50, 205),  (205, 101), (206, 92),  (92, 165),  (165, 206),
    (209, 198), (198, 217), (217, 209), (165, 167), (167, 97),  (97, 165),
    (220, 115), (115, 218), (218, 220), (133, 112), (112, 243), (243, 133),
    (239, 238), (238, 241), (241, 239), (214, 135), (135, 169), (169, 214),
    (190, 173), (173, 133), (133, 190), (171, 208), (208, 32),  (32, 171),
    (125, 44),  (44, 237),  (237, 125), (86, 87),   (87, 178),  (178, 86),
    (85, 86),   (86, 179),  (179, 85),  (84, 85),   (85, 180),  (180, 84),
    (83, 84),   (84, 181),  (181, 83),  (201, 83),  (83, 182),  (182, 201),
    (137, 93),  (93, 132),  (132, 137), (76, 62),   (62, 183),  (183, 76),
    (61, 76),   (76, 184),  (184, 61),  (57, 61),   (61, 185),  (185, 57),
    (212, 57),  (57, 186),  (186, 212), (214, 207), (207, 187), (187, 214),
    (34, 143),
])

# 3. Boundary poligon untuk setiap area sensor aktif
# Digunakan untuk: (a) filter tessellation, (b) polygon fill shading, (c) ROI bounding box

# Dahi — mengikuti lengkung natural garis rambut dan alis
FOREHEAD_BOUNDARY = [54, 103, 67, 109, 10, 338, 297, 332, 284, 336, 9, 108]

# Pipi Kiri — mengikuti kontur tulang pipi, hidung, dan rahang
LEFT_CHEEK_BOUNDARY = [137, 123, 50, 36, 203, 206, 207, 213, 147]

# Pipi Kanan — mirror simetris dari pipi kiri
RIGHT_CHEEK_BOUNDARY = [366, 352, 280, 266, 423, 426, 436, 416, 376]

# Map simetri 468 titik FaceMesh untuk pencerminan spasial kiri-kanan yang presisi
FACEMESH_SYMMETRY = [
    37, 1, 2, 248, 4, 5, 6, 390, 8, 9, 10, 72, 38, 82, 87, 86, 85, 84, 83, 19,
    462, 251, 451, 23, 24, 339, 452, 257, 258, 259, 30, 448, 262, 249, 264, 265, 266, 0, 12, 302,
    272, 312, 42, 335, 274, 275, 445, 277, 439, 279, 280, 281, 282, 53, 284, 285, 286, 291, 288, 305,
    328, 308, 325, 283, 455, 295, 296, 297, 298, 299, 276, 301, 11, 268, 311, 75, 375, 321, 324, 309,
    402, 81, 13, 18, 17, 16, 15, 14, 88, 403, 404, 405, 322, 323, 141, 95, 319, 97, 327, 326,
    329, 330, 294, 332, 333, 334, 406, 336, 337, 338, 254, 346, 112, 467, 343, 344, 345, 117, 347, 348,
    349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 255, 360, 361, 463, 363, 394, 379, 366, 364, 368,
    369, 94, 371, 372, 374, 253, 146, 376, 148, 400, 378, 151, 152, 252, 256, 341, 383, 384, 385, 386,
    387, 388, 389, 373, 164, 391, 392, 393, 168, 395, 170, 396, 397, 398, 399, 175, 377, 401, 317, 316,
    315, 314, 313, 318, 184, 415, 409, 411, 412, 189, 413, 191, 434, 417, 194, 195, 419, 197, 420, 199,
    200, 421, 424, 423, 418, 425, 426, 436, 428, 429, 431, 211, 287, 416, 214, 435, 410, 437, 438, 219,
    440, 441, 442, 443, 444, 260, 446, 447, 228, 449, 450, 231, 232, 453, 454, 235, 456, 457, 458, 459,
    460, 461, 370, 243, 464, 465, 466, 247, 3, 33, 250, 21, 153, 145, 110, 130, 154, 27, 28, 29,
    225, 261, 32, 263, 34, 35, 36, 267, 73, 269, 270, 271, 40, 273, 44, 45, 70, 47, 49, 279,
    50, 51, 52, 63, 54, 55, 56, 212, 58, 289, 290, 57, 292, 293, 102, 65, 66, 67, 68, 69,
    300, 71, 39, 303, 304, 59, 306, 307, 61, 79, 310, 74, 41, 182, 181, 180, 179, 178, 183, 96,
    320, 77, 92, 93, 78, 62, 99, 98, 60, 100, 101, 331, 103, 104, 105, 43, 107, 108, 109, 25,
    340, 155, 342, 114, 115, 116, 111, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 359,
    131, 132, 362, 134, 138, 365, 137, 367, 139, 140, 242, 142, 143, 163, 144, 76, 147, 176, 150, 136,
    380, 381, 382, 156, 157, 158, 159, 160, 161, 162, 7, 165, 166, 167, 135, 169, 171, 172, 173, 174,
    149, 177, 80, 89, 90, 91, 106, 407, 408, 186, 216, 187, 188, 190, 414, 185, 213, 193, 204, 196,
    198, 201, 422, 203, 202, 205, 206, 427, 208, 209, 430, 210, 432, 433, 192, 215, 207, 217, 218, 48,
    220, 221, 222, 223, 224, 46, 226, 227, 31, 229, 230, 22, 26, 233, 234, 64, 236, 237, 238, 239,
    240, 241, 20, 133, 244, 245, 246, 113,
]

@dataclass
class RoiResult:
    rgb: np.ndarray
    bbox: Optional[Box]
    boxes: Dict[str, Box]
    face_area_ratio: float
    detected: bool
    face_distance: Optional[float] = None
    landmarks: Optional[List[Tuple[int, int]]] = None
    raw_landmarks: Optional[List[Any]] = None




class FaceRoiExtractor:
    """Extract average RGB values from forehead and cheek ROIs.

    The implementation uses a face bounding box and relative subregions. This is
    simple, fast, and suitable as a baseline. For higher robustness, replace the
    ROI box logic with landmark-based skin masks.
    """

    def __init__(
        self,
        backend: str = "mediapipe",
        regions: Iterable[str] = ("forehead", "left_cheek", "right_cheek"),
        min_detection_confidence: float = 0.5,
    ) -> None:
        self.backend = backend.lower().strip()
        self.regions = tuple(regions)
        self.min_detection_confidence = min_detection_confidence
        self._mp_mesh = None
        self._haar = None

        if self.backend == "mediapipe":
            try:
                import os
                import urllib.request
                import mediapipe as mp
                from mediapipe.tasks import python
                from mediapipe.tasks.python import vision

                model_path = "models/face_landmarker.task"
                if not os.path.exists(model_path):
                    os.makedirs(os.path.dirname(model_path), exist_ok=True)
                    url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
                    urllib.request.urlretrieve(url, model_path)

                base_options = python.BaseOptions(model_asset_path=model_path)
                options = vision.FaceLandmarkerOptions(
                    base_options=base_options,
                    output_face_blendshapes=False,
                    output_facial_transformation_matrixes=False,
                    num_faces=1,
                    min_face_detection_confidence=min_detection_confidence,
                    min_face_presence_confidence=min_detection_confidence,
                )
                self._mp_mesh = vision.FaceLandmarker.create_from_options(options)
                self._mp = mp
            except Exception as exc:  # pragma: no cover - depends on environment
                raise RuntimeError(
                    "MediaPipe backend requested but face landmarker could not be initialized. "
                    "Ensure internet connection to download the model, or use backend='haar'."
                ) from exc
        elif self.backend == "haar":
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._haar = cv2.CascadeClassifier(cascade_path)
            if self._haar.empty():
                raise RuntimeError("Could not load OpenCV Haar cascade")
        else:
            raise ValueError("backend must be 'mediapipe' or 'haar'")

    def close(self) -> None:
        if self._mp_mesh is not None:
            self._mp_mesh.close()

    def detect_face(self, frame_bgr: np.ndarray) -> Optional[Box]:
        if self.backend == "mediapipe":
            return self._detect_face_mediapipe(frame_bgr)
        return self._detect_face_haar(frame_bgr)

    def _detect_face_mediapipe(self, frame_bgr: np.ndarray) -> Optional[Box]:
        height, width = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=frame_rgb)
        result = self._mp_mesh.detect(mp_image)
        if not result.face_landmarks:
            return None
        
        # Hitung bounding box wajah dari koordinat landmark min/max
        xs = [int(round(lm.x * width)) for lm in result.face_landmarks[0]]
        ys = [int(round(lm.y * height)) for lm in result.face_landmarks[0]]
        x1, y1 = max(0, min(xs)), max(0, min(ys))
        x2, y2 = min(width, max(xs)), min(height, max(ys))
        return _clip_box((x1, y1, x2, y2), width, height)

    def _detect_face_haar(self, frame_bgr: np.ndarray) -> Optional[Box]:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self._haar.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces) == 0:
            return None
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        return _clip_box((int(x), int(y), int(x + w), int(y + h)), frame_bgr.shape[1], frame_bgr.shape[0])

    def get_roi_boxes(self, bbox: Box, frame_shape: Tuple[int, int, int]) -> Dict[str, Box]:
        height, width = frame_shape[:2]
        x1, y1, x2, y2 = bbox
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)

        candidates: Dict[str, Box] = {
            "forehead": (
                x1 + int(0.30 * w),
                y1 + int(0.07 * h),
                x1 + int(0.70 * w),
                y1 + int(0.25 * h),
            ),
            "left_cheek": (
                x1 + int(0.18 * w),
                y1 + int(0.45 * h),
                x1 + int(0.42 * w),
                y1 + int(0.70 * h),
            ),
            "right_cheek": (
                x1 + int(0.58 * w),
                y1 + int(0.45 * h),
                x1 + int(0.82 * w),
                y1 + int(0.70 * h),
            ),
        }
        out: Dict[str, Box] = {}
        for name in self.regions:
            if name in candidates:
                out[name] = _clip_box(candidates[name], width, height)
        return out

    def extract(self, frame_bgr: np.ndarray) -> RoiResult:
        raw_landmarks = None
        if self.backend == "mediapipe":
            height, width = frame_bgr.shape[:2]
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=frame_rgb)
            result = self._mp_mesh.detect(mp_image)
            if not result.face_landmarks:
                return RoiResult(
                    rgb=np.array([np.nan, np.nan, np.nan], dtype=float),
                    bbox=None,
                    boxes={},
                    face_area_ratio=0.0,
                    detected=False,
                    face_distance=None,
                    landmarks=None,
                    raw_landmarks=None,
                )

            face_landmarks = result.face_landmarks[0]
            raw_landmarks = face_landmarks
            coords = []
            for lm in face_landmarks:
                cx = int(round(lm.x * width))
                cy = int(round(lm.y * height))
                coords.append((cx, cy))

            # Hitung bounding box wajah dari koordinat landmark min/max
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            x1, y1 = max(0, min(xs)), max(0, min(ys))
            x2, y2 = min(width, max(xs)), min(height, max(ys))
            bbox = (x1, y1, x2, y2)

            # Sinkronisasi ROI dinamis berdasarkan koordinat FaceMesh
            # Hitung bounding box dari titik-titik boundary poligon yang mengikuti bentuk wajah
            def _bbox_from_landmarks(idxs):
                pts = [coords[i] for i in idxs]
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                return (min(xs), min(ys), max(xs), max(ys))

            forehead_box = _bbox_from_landmarks(FOREHEAD_BOUNDARY)
            left_cheek_box = _bbox_from_landmarks(LEFT_CHEEK_BOUNDARY)
            right_cheek_box = _bbox_from_landmarks(RIGHT_CHEEK_BOUNDARY)

            boxes = {
                "forehead": _clip_box(forehead_box, width, height),
                "left_cheek": _clip_box(left_cheek_box, width, height),
                "right_cheek": _clip_box(right_cheek_box, width, height)
            }
            boxes = {name: box for name, box in boxes.items() if name in self.regions}
            landmarks = coords
        else:
            bbox = self.detect_face(frame_bgr)
            if bbox is None:
                return RoiResult(
                    rgb=np.array([np.nan, np.nan, np.nan], dtype=float),
                    bbox=None,
                    boxes={},
                    face_area_ratio=0.0,
                    detected=False,
                    face_distance=None,
                    landmarks=None,
                    raw_landmarks=None,
                )
            boxes = self.get_roi_boxes(bbox, frame_bgr.shape)
            landmarks = None

        rgb_values: List[np.ndarray] = []
        for name, box in boxes.items():
            x1, y1, x2, y2 = box
            if x2 <= x1 or y2 <= y1:
                continue
            roi_bgr = frame_bgr[y1:y2, x1:x2]
            if roi_bgr.size == 0:
                continue
            roi_rgb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2RGB)
            
            if landmarks is not None:
                boundary_map = {
                    "forehead": FOREHEAD_BOUNDARY,
                    "left_cheek": LEFT_CHEEK_BOUNDARY,
                    "right_cheek": RIGHT_CHEEK_BOUNDARY,
                }
                boundary = boundary_map.get(name)
                if boundary:
                    poly_pts = np.array([landmarks[idx] for idx in boundary], dtype=np.int32)
                    shifted_poly = poly_pts - np.array([x1, y1])
                    mask = np.zeros(roi_bgr.shape[:2], dtype=np.uint8)
                    cv2.fillPoly(mask, [shifted_poly], 255)
                    
                    # Skin filter using YCrCb
                    roi_ycrcb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2YCrCb)
                    skin_mask = cv2.inRange(roi_ycrcb, (0, 133, 77), (255, 173, 127))
                    combined_mask = cv2.bitwise_and(mask, skin_mask)
                    
                    skin_pixels_rgb = roi_rgb[combined_mask == 255]
                    if len(skin_pixels_rgb) < 10:
                        skin_pixels_rgb = roi_rgb[mask == 255]
                    if len(skin_pixels_rgb) == 0:
                        skin_pixels_rgb = roi_rgb.reshape(-1, 3)
                        
                    rgb_values.append(np.mean(skin_pixels_rgb, axis=0))
                else:
                    rgb_values.append(np.mean(roi_rgb.reshape(-1, 3), axis=0))
            else:
                rgb_values.append(np.mean(roi_rgb.reshape(-1, 3), axis=0))

        if not rgb_values:
            avg_rgb = np.array([np.nan, np.nan, np.nan], dtype=float)
        else:
            avg_rgb = np.mean(np.vstack(rgb_values), axis=0)

        frame_area = float(frame_bgr.shape[0] * frame_bgr.shape[1])
        face_area = float(max(0, bbox[2] - bbox[0]) * max(0, bbox[3] - bbox[1]))

        # Estimasi jarak wajah menggunakan pinhole camera model
        frame_width = frame_bgr.shape[1]
        focal_length = frame_width * 0.8
        face_width_pixels = float(bbox[2] - bbox[0])
        if face_width_pixels > 0:
            face_distance = (focal_length * 14.0) / face_width_pixels
        else:
            face_distance = None

        return RoiResult(
            rgb=avg_rgb.astype(float),
            bbox=bbox,
            boxes=boxes,
            face_area_ratio=face_area / max(frame_area, 1.0),
            detected=True,
            face_distance=face_distance,
            landmarks=landmarks,
            raw_landmarks=raw_landmarks,
        )



def _clip_box(box: Box, width: int, height: int) -> Box:
    x1, y1, x2, y2 = box
    x1 = max(0, min(width - 1, x1))
    x2 = max(0, min(width, x2))
    y1 = max(0, min(height - 1, y1))
    y2 = max(0, min(height, y2))
    if x2 <= x1:
        x2 = min(width, x1 + 1)
    if y2 <= y1:
        y2 = min(height, y1 + 1)
    return int(x1), int(y1), int(x2), int(y2)


def draw_roi_overlay(frame_bgr: np.ndarray, result: RoiResult) -> np.ndarray:
    """Draw face bbox and ROI boxes on a frame."""
    out = frame_bgr.copy()
    
    # 1. Gambar kotak wajah utama (putih)
    if result.bbox is not None:
        x1, y1, x2, y2 = result.bbox
        cv2.rectangle(out, (x1, y1), (x2, y2), (255, 255, 255), 1)
        
        # Tampilkan estimasi jarak di atas bounding box wajah
        if getattr(result, "face_distance", None) is not None:
            dist_text = f"Dist: {result.face_distance:.1f} cm"
            # Gambar teks dengan background hitam transparan agar mudah dibaca
            (text_w, text_h), baseline = cv2.getTextSize(dist_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            text_y = max(text_h + 5, y1 - 8)
            cv2.rectangle(out, (x1, text_y - text_h - 2), (x1 + text_w + 4, text_y + baseline), (0, 0, 0), -1)
            cv2.putText(out, dist_text, (x1 + 2, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
            
    # 2. Gambar FaceMesh jika landmarks tersedia (High-Tech Futuristic HUD Mode)
    if getattr(result, "landmarks", None) is not None and result.landmarks:
        
        # Buat set indeks mata, alis, dan iris untuk dieleminasi dari visualisasi
        LEFT_EYE_IDXS = {362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398}
        RIGHT_EYE_IDXS = {33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246}
        LEFT_EYEBROW_IDXS = {336, 296, 334, 293, 300, 276, 283, 282, 295, 285}
        RIGHT_EYEBROW_IDXS = {70, 63, 105, 66, 107, 55, 65, 52, 53, 46}
        EXCLUDED_IDXS = LEFT_EYE_IDXS.union(RIGHT_EYE_IDXS).union(LEFT_EYEBROW_IDXS).union(RIGHT_EYEBROW_IDXS).union(set(range(468, 478)))

        # A. Gambar menggunakan referensi code resmi MediaPipe Python Tasks Face Landmarker
        drawn_official = False
        if getattr(result, "raw_landmarks", None) is not None:
            try:
                from mediapipe.tasks.python.vision import drawing_utils, drawing_styles
                from mediapipe.tasks.python.vision.face_landmarker import FaceLandmarksConnections
                
                # Filter koneksi kontur tebal agar tidak menggambar di area mata dan alis
                filtered_contours = [
                    conn for conn in FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS
                    if conn.start not in EXCLUDED_IDXS and conn.end not in EXCLUDED_IDXS
                ]

                # 1. Tesselation (Jaring wajah penuh - tipis, menutupi seluruh wajah termasuk mata & alis)
                drawing_utils.draw_landmarks(
                    image=out,
                    landmark_list=result.raw_landmarks,
                    connections=FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=drawing_styles.get_default_face_mesh_tesselation_style()
                )
                # 2. Contours (Garis tebal - hanya bibir & oval wajah, tanpa mata & alis)
                drawing_utils.draw_landmarks(
                    image=out,
                    landmark_list=result.raw_landmarks,
                    connections=filtered_contours,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=drawing_styles.get_default_face_mesh_contours_style()
                )
                # (Iris sengaja dilewati / tidak digambar)
                drawn_official = True
            except Exception:
                pass
                
        if not drawn_official:
            # Fallback jika raw_landmarks tidak tersedia (misal saat running Haar backend atau di unit test)
            for edge in FACEMESH_TESSELATION:
                pt1 = result.landmarks[edge[0]]
                pt2 = result.landmarks[edge[1]]
                cv2.line(out, pt1, pt2, (50, 50, 50), 1, cv2.LINE_AA)
                
            for connection in FACEMESH_BACKGROUND_CONTOURS:
                if connection[0] not in EXCLUDED_IDXS and connection[1] not in EXCLUDED_IDXS:
                    start_idx = connection[0]
                    end_idx = connection[1]
                    pt1 = result.landmarks[start_idx]
                    pt2 = result.landmarks[end_idx]
                    cv2.line(out, pt1, pt2, (80, 80, 80), 1, cv2.LINE_AA)
            
        # C. Gambar tessellation mesh padat di area sensor aktif (dahi, pipi)
        overlay = out.copy()
        
        all_region_boundaries = [
            ("forehead", FOREHEAD_BOUNDARY),
            ("right_cheek", RIGHT_CHEEK_BOUNDARY),
            ("left_cheek", LEFT_CHEEK_BOUNDARY),
        ]
        
        all_active_pts = []  # untuk menggambar node di akhir
        inside_regions = {}  # simpan set inside per region
        
        for name, boundary_idxs in all_region_boundaries:
            # Buat poligon boundary dari landmark koordinat
            poly_pts = np.array(
                [result.landmarks[idx] for idx in boundary_idxs], dtype=np.int32
            )
            poly_f32 = poly_pts.astype(np.float32)
            
            # Shading transparan cyan mengikuti bentuk poligon wajah
            cv2.fillPoly(overlay, [poly_pts], (255, 255, 0))
            
            # Cari semua landmark yang berada DI DALAM poligon region ini
            if name == "left_cheek":
                # Gunakan simetri dari pipi kanan agar graf pipi kiri sama persis (topologically mirrored) dengan pipi kanan
                right_inside = inside_regions.get("right_cheek", set())
                inside = {FACEMESH_SYMMETRY[idx] for idx in right_inside}
            else:
                inside = set()
                for i in range(468):
                    pt = result.landmarks[i]
                    if cv2.pointPolygonTest(poly_f32, (float(pt[0]), float(pt[1])), False) >= 0:
                        inside.add(i)
                inside_regions[name] = inside
            
            # Filter tessellation: gambar hanya edge yang kedua titiknya di dalam region
            if name == "left_cheek":
                right_edges = inside_regions.get("right_edges", [])
                for edge in right_edges:
                    pt1 = result.landmarks[FACEMESH_SYMMETRY[edge[0]]]
                    pt2 = result.landmarks[FACEMESH_SYMMETRY[edge[1]]]
                    cv2.line(out, pt1, pt2, (200, 200, 200), 1, cv2.LINE_AA)
            else:
                drawn_edges = []
                for edge in FACEMESH_TESSELATION:
                    if edge[0] in inside and edge[1] in inside:
                        pt1 = result.landmarks[edge[0]]
                        pt2 = result.landmarks[edge[1]]
                        cv2.line(out, pt1, pt2, (200, 200, 200), 1, cv2.LINE_AA)
                        if name == "right_cheek":
                            drawn_edges.append(edge)
                if name == "right_cheek":
                    inside_regions["right_edges"] = drawn_edges
            
            # Gambar boundary tebal (outline region)
            cv2.polylines(out, [poly_pts], True, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Kumpulkan semua titik node dalam region untuk glow
            for idx in inside:
                pt = result.landmarks[idx]
                all_active_pts.append(pt)
                cv2.circle(overlay, pt, 4, (255, 255, 0), -1, cv2.LINE_AA)
        
        # Blend overlay ke out (opacity 12%)
        cv2.addWeighted(overlay, 0.12, out, 0.88, 0, out)
        
        # C. Gambar node tajam di atas pendaran cahaya
        for pt in all_active_pts:
            # Dot cyan padat bagian dalam
            cv2.circle(out, pt, 1, (255, 255, 0), -1, cv2.LINE_AA)
            # Ring putih tipis bagian luar
            cv2.circle(out, pt, 3, (255, 255, 255), 1, cv2.LINE_AA)
            
        # D. Gambar label teks untuk setiap area sensor aktif
        label_map = {
            "forehead": "Dahi",
            "left_cheek": "Pipi Kiri",
            "right_cheek": "Pipi Kanan",
        }
        for name, box in result.boxes.items():
            label = label_map.get(name)
            if label is None:
                continue
            x1, y1, x2, y2 = box
            (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.40, 1)
            tx = (x1 + x2) // 2 - tw // 2
            ty = y1 - 6
            # Background hitam agar teks mudah dibaca
            cv2.rectangle(out, (tx - 2, ty - th - 2), (tx + tw + 2, ty + baseline + 2), (0, 0, 0), -1)
            cv2.putText(out, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 0), 1, cv2.LINE_AA)
    else:
        # Fallback jika hanya menggunakan Haar (gambar titik pelacak biasa)
        for name, box in result.boxes.items():
            x1, y1, x2, y2 = box
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            cv2.circle(out, (cx, cy), 8, (0, 255, 255), 1, cv2.LINE_AA)
            cv2.circle(out, (cx, cy), 4, (0, 255, 255), -1, cv2.LINE_AA)
            
    return out

