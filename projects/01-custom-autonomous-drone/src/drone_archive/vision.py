"""Detect bright connected regions in a synthetic grayscale image."""
from collections import deque

class VisionError(ValueError):
    pass

def detect_regions(pixels, threshold, minimum_area):
    if not isinstance(pixels, list) or not pixels or not isinstance(pixels[0], list) or not pixels[0]:
        raise VisionError('Image must contain rows of grayscale pixels')
    height, width = len(pixels), len(pixels[0])
    if width * height > 1000000:
        raise VisionError('Image exceeds the supported size')
    if any(not isinstance(row, list) or len(row) != width for row in pixels):
        raise VisionError('Image rows must have equal lengths')
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 255 for row in pixels for v in row):
        raise VisionError('Pixels must be integers between 0 and 255')
    if isinstance(threshold, bool) or not isinstance(threshold, int) or not 0 <= threshold <= 255:
        raise VisionError('Threshold must be an integer between 0 and 255')
    if isinstance(minimum_area, bool) or not isinstance(minimum_area, int) or minimum_area < 1:
        raise VisionError('Minimum area must be a positive integer')
    visited = set()
    regions = []
    for y in range(height):
        for x in range(width):
            if pixels[y][x] < threshold or (x,y) in visited:
                continue
            queue = deque([(x,y)])
            visited.add((x,y))
            area = sum_x = sum_y = 0
            left = right = x
            top = bottom = y
            while queue:
                cx, cy = queue.popleft()
                area += 1; sum_x += cx; sum_y += cy
                left, right = min(left, cx), max(right, cx)
                top, bottom = min(top, cy), max(bottom, cy)
                for dx, dy in ((0,-1),(-1,0),(1,0),(0,1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < width and 0 <= ny < height and (nx,ny) not in visited and pixels[ny][nx] >= threshold:
                        visited.add((nx,ny)); queue.append((nx,ny))
            if area >= minimum_area:
                regions.append({'area_pixels': area, 'centroid_x': sum_x / area, 'centroid_y': sum_y / area,
                                'bounds': {'left': left, 'top': top, 'right': right, 'bottom': bottom}})
    return regions
