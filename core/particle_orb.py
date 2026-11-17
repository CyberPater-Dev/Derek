"""
Drop-in Core Widget de Puntos Cuánticos para Mark-LV.
Reemplaza el círculo plano de reactor por el orbe de partículas 3D idéntico al que le encantó al usuario.
"""
import math
import random
import numpy as np
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush

NUM_PTS = 500
RADIUS = 95.0

class ParticleOrbRenderer:
    def __init__(self):
        self.points = []
        self.angle_y = 0.0
        self.angle_x = 0.0
        self.pulse = 0.0

        # Esfera de Fibonacci con partículas
        for i in range(NUM_PTS):
            phi = math.acos(1.0 - 2.0 * (i + 0.5) / NUM_PTS)
            theta = math.pi * (1.0 + math.sqrt(5.0)) * i
            bx = RADIUS * math.sin(phi) * math.cos(theta)
            by = RADIUS * math.cos(phi)
            bz = RADIUS * math.sin(phi) * math.sin(theta)
            size = random.uniform(1.2, 2.4)
            self.points.append({
                "bx": bx, "by": by, "bz": bz,
                "size": size
            })

    def render(self, p: QPainter, cx: float, cy: float, level: float = 0.0, speaking: bool = False, listening: bool = False):
        speed = 0.025 if speaking else (0.035 if listening else 0.012)
        wave_amp = (level * 28.0) if speaking else (14.0 if listening else 3.0)
        
        self.angle_y += speed
        self.angle_x += speed * 0.45
        self.pulse += 0.08

        # Color: blanco/cian cuántico puro idéntico a la imagen del usuario
        if listening:
            base_r, base_g, base_b = 248, 113, 113 # Pulso de escucha
        elif speaking:
            base_r, base_g, base_b = 56, 189, 248  # Azul cian al hablar
        else:
            base_r, base_g, base_b = 235, 242, 250 # Partículas blancas brillantes idénticas a la foto

        cos_y, sin_y = math.cos(self.angle_y), math.sin(self.angle_y)
        cos_x, sin_x = math.cos(self.angle_x), math.sin(self.angle_x)

        p.save()
        p.setPen(Qt.PenStyle.NoPen)

        for pt in self.points:
            # Ondulación por voz
            r_off = wave_amp * math.sin(self.pulse + pt["by"] * 0.08)
            scale_r = (RADIUS + r_off) / RADIUS

            x1 = pt["bx"] * scale_r
            y1 = pt["by"] * scale_r
            z1 = pt["bz"] * scale_r

            x2 = x1 * cos_y + z1 * sin_y
            z2 = -x1 * sin_y + z1 * cos_y

            y3 = y1 * cos_x - z2 * sin_x
            z3 = y1 * sin_x + z2 * cos_x

            # Proyección en perspectiva
            fov = 280.0
            scale = fov / (fov + z3)
            proj_x = cx + x2 * scale
            proj_y = cy + y3 * scale

            alpha = int(max(40, min(255, ((z3 + RADIUS) / (2.0 * RADIUS)) * 215 + 40)))
            p.setBrush(QBrush(QColor(base_r, base_g, base_b, alpha)))

            d_size = pt["size"] * scale
            p.drawEllipse(QPointF(proj_x, proj_y), d_size, d_size)

        p.restore()
