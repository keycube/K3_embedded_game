import keypad
import neopixel
import time

class LightEffect:
    # Type: 1 = Sequence
    def __init__(self, type: int = 0, color = (0, 0, 0), sequence: list[list[int]] = []) -> None:
        self.type = type
        self.color = color
        self.sequence = sequence

class LightManager:
    # Return the list of element in a matrix
    def matFlat(self, matrix):
        flattened = []
        for row in matrix:
            flattened.extend(row)
        return flattened

    # Return distance of a point from the center of a matrix
    def matDist(self, matrix):
        centre = (len(matrix) // 2) - (len(matrix)+1)%2*0.5

        distances = []
        for i in range(len(matrix)):
            for j in range(len(matrix)):
                distance = max(abs(i - centre), abs(j - centre))
                distances.append(int(distance))

        matriceUp = [[] for _ in range(distances[0]+1)]
        for y in range(len(matrix)):
            for x in range(len(matrix)):
                matriceUp[distances[len(matrix)*y + x]].append(matrix[y][x])

        return matriceUp

    # Rotate a matrix by 90 degrees, n: 0 = 0°, 1 = 90°, 2 = 180°, 3 = 270°/-90°
    def matRot(self, matrix, n):
        rotMatrix = [[0] * len(matrix) for _ in range(len(matrix[0]))]

        if (n <= 0):
            return matrix

        for _ in range(n):
            for y in range(len(matrix)):
                for x in range(len(matrix[0])):
                    rotMatrix[x][len(matrix) - 1 - y] = matrix[y][x]

        if (n == 1):
            return rotMatrix

        return self.matRot(rotMatrix, n - 1)

    # Create a cube pattern centered on the top face of the cube with all connected faces
    def createCubeTopView(self) -> list[list[int]]:
        cubeTopView = [[-1] * (self.size * 3) for _ in range(self.size * 3)]

        for y in range(self.size):
            for x in range(self.size):
                cubeTopView[y + self.size * 0][x + self.size * 1] = self.matRot(self.NF, 0)[y][x]
                cubeTopView[y + self.size * 1][x + self.size * 1] = self.matRot(self.TF, 0)[y][x]
                cubeTopView[y + self.size * 1][x + self.size * 0] = self.matRot(self.WF, 0)[y][x]
                cubeTopView[y + self.size * 1][x + self.size * 2] = self.matRot(self.EF, 0)[y][x]
                cubeTopView[y + self.size * 2][x + self.size * 1] = self.matRot(self.SF, 0)[y][x]

        return cubeTopView

    # Create a cube pattern centered on the north face of the cube with all connected faces
    def createCubeNorthView(self) -> list[list[int]]:
        cubeNorthView = [[-1] * (self.size * 5) for _ in range(self.size * 3)]

        for y in range(self.size):
            for x in range(self.size):
                cubeNorthView[y + self.size * 0][x + self.size * 2] = self.matRot(self.SF, 2)[y][x]
                cubeNorthView[y + self.size * 1][x + self.size * 2] = self.matRot(self.TF, 2)[y][x]
                cubeNorthView[y + self.size * 2][x + self.size * 0] = self.matRot(self.SF, 0)[y][x]
                cubeNorthView[y + self.size * 2][x + self.size * 1] = self.matRot(self.EF, 1)[y][x]
                cubeNorthView[y + self.size * 2][x + self.size * 2] = self.matRot(self.NF, 2)[y][x]
                cubeNorthView[y + self.size * 2][x + self.size * 3] = self.matRot(self.WF, 3)[y][x]
                cubeNorthView[y + self.size * 2][x + self.size * 4] = self.matRot(self.SF, 0)[y][x]

        return cubeNorthView

    # Create a cube pattern centered on the south face of the cube with all connected faces
    def createCubeSouthView(self) -> list[list[int]]:
        cubeSouthView = [[-1] * (self.size * 5) for _ in range(self.size * 3)]

        for y in range(self.size):
            for x in range(self.size):
                cubeSouthView[y + self.size * 0][x + self.size * 2] = self.matRot(self.NF, 0)[y][x]
                cubeSouthView[y + self.size * 1][x + self.size * 2] = self.matRot(self.TF, 0)[y][x]
                cubeSouthView[y + self.size * 2][x + self.size * 0] = self.matRot(self.NF, 2)[y][x]
                cubeSouthView[y + self.size * 2][x + self.size * 1] = self.matRot(self.WF, 3)[y][x]
                cubeSouthView[y + self.size * 2][x + self.size * 2] = self.matRot(self.SF, 0)[y][x]
                cubeSouthView[y + self.size * 2][x + self.size * 3] = self.matRot(self.EF, 1)[y][x]
                cubeSouthView[y + self.size * 2][x + self.size * 4] = self.matRot(self.NF, 2)[y][x]

        return cubeSouthView

    # Create a cube pattern centered on the east east of the cube with all connected faces
    def createCubeEastView(self) -> list[list[int]]:
        cubeEastView = [[-1] * (self.size * 5) for _ in range(self.size * 4)]

        for y in range(self.size):
            for x in range(self.size):
                cubeEastView[y + self.size * 0][x + self.size * 2] = self.matRot(self.WF, 1)[y][x]
                cubeEastView[y + self.size * 1][x + self.size * 2] = self.matRot(self.TF, 1)[y][x]
                cubeEastView[y + self.size * 2][x + self.size * 0] = self.matRot(self.WF, 3)[y][x]
                cubeEastView[y + self.size * 2][x + self.size * 1] = self.matRot(self.SF, 0)[y][x]
                cubeEastView[y + self.size * 2][x + self.size * 2] = self.matRot(self.EF, 1)[y][x]
                cubeEastView[y + self.size * 2][x + self.size * 3] = self.matRot(self.NF, 2)[y][x]
                cubeEastView[y + self.size * 2][x + self.size * 4] = self.matRot(self.WF, 3)[y][x]

        return cubeEastView

    # Create a cube pattern centered on the west face of the cube with all connected faces
    def createCubeWestView(self) -> list[list[int]]:
        cubeWestView = [[-1] * (self.size * 5) for _ in range(self.size * 3)]

        for y in range(self.size):
            for x in range(self.size):
                cubeWestView[y + self.size * 0][x + self.size * 2] = self.matRot(self.EF, 3)[y][x]
                cubeWestView[y + self.size * 1][x + self.size * 2] = self.matRot(self.TF, 3)[y][x]
                cubeWestView[y + self.size * 2][x + self.size * 0] = self.matRot(self.EF, 1)[y][x]
                cubeWestView[y + self.size * 2][x + self.size * 1] = self.matRot(self.NF, 2)[y][x]
                cubeWestView[y + self.size * 2][x + self.size * 2] = self.matRot(self.WF, 3)[y][x]
                cubeWestView[y + self.size * 2][x + self.size * 3] = self.matRot(self.SF, 0)[y][x]
                cubeWestView[y + self.size * 2][x + self.size * 4] = self.matRot(self.EF, 1)[y][x]

        return cubeWestView

    # Create a raimbow pattern with all steps and gestion of top face step by distance
    def createRaimbow(self) -> list[list[int]]:
        raimbowPattern = []
        raimbowTop = self.matDist(self.TF)
        for i in range(len(raimbowTop)):
            raimbowPattern.append(raimbowTop[i])

        for y in range(self.size):
            step = []
            for x in range(self.size):
                step.append(self.SF[y][x])
                step.append(self.matRot(self.EF, 1)[y][x])
                step.append(self.matRot(self.NF, 2)[y][x])
                step.append(self.matRot(self.WF, 3)[y][x])

            raimbowPattern.append(step)

        return raimbowPattern

    # Update the raimbow color
    def raimbowColorUpdate(self) -> None:
        self.RAIMBOWCOLOR = (self.RAIMBOWCOLOR + self.RAIMBOWDIRECTION) % 255
        self.CUSTOMRAIMBOWSTEP = (self.CUSTOMRAIMBOWSTEP + self.RAIMBOWDIRECTION) % 255

    # Update the brightness
    def brightnessUpdate(self) -> None:
        self.BRIGHTNESS = self.BRIGHTNESS + self.BRIGHTNESS_INCREASE

        if self.BRIGHTNESS >= 0.1 or self.BRIGHTNESS <= 0.01:
            self.BRIGHTNESS_INCREASE = -self.BRIGHTNESS_INCREASE

    def interpolate_color(self, start_color, end_color, n_steps):

        start_r, start_g, start_b = start_color
        end_r, end_g, end_b = end_color

        step_r = (end_r - start_r) / n_steps
        step_g = (end_g - start_g) / n_steps
        step_b = (end_b - start_b) / n_steps

        interpolated_colors = [
            (
                round(start_r + step_r * i),
                round(start_g + step_g * i),
                round(start_b + step_b * i)
            )
            for i in range(n_steps + 1)
        ]

        return interpolated_colors

    # Detect the face of a key
    def detectFace(self, key: int) -> int:
        if key in self.matFlat(self.TF):
            return [self._CTV, (self.matFlat(self._CTV).index(key) // len(self._CTV[0]), self.matFlat(self._CTV).index(key) % len(self._CTV[0]))]
        elif key in self.matFlat(self.NF):
            return [self._CNV, (self.matFlat(self._CNV).index(key) // len(self._CNV[0]), self.matFlat(self._CNV).index(key) % len(self._CNV[0]))]
        elif key in self.matFlat(self.SF):
            return [self._CSV, (self.matFlat(self._CSV).index(key) // len(self._CSV[0]), self.matFlat(self._CSV).index(key) % len(self._CSV[0]))]
        elif key in self.matFlat(self.EF):
            return [self._CEV, (self.matFlat(self._CEV).index(key) // len(self._CEV[0]), self.matFlat(self._CEV).index(key) % len(self._CEV[0]))]
        elif key in self.matFlat(self.WF):
            return [self._CWV, (self.matFlat(self._CWV).index(key) // len(self._CWV[0]), self.matFlat(self._CWV).index(key) % len(self._CWV[0]))]
        else:
            return -1

    # Create a ripple effect from a key coordinate
    def rippleEffect(self, tab, actual, previous = [], counter = 0):
        interpolateColor = self.interpolate_color((255, 0, 0), (0, 0, 255), 3)
        if (interpolateColor[len(interpolateColor) - 1] != (0,0,0)):
            interpolateColor.append((0,0,0))

        if (len(self.matFlat(previous)) >= self.size * self.size * 5):
            for k in range(1, len(interpolateColor)):
                for i in range(0, min(len(interpolateColor), len(previous))):
                    for j in range(0, len(previous[i])):
                        y = previous[i][j][0]
                        x = previous[i][j][1]
                        self.p[tab[y][x]] = interpolateColor[min(len(interpolateColor) - 1, i + k)]

                self.p.show()
                time.sleep(0.05)

            return 0

        newPrevious = []

        for i in range(0, len(actual)):
            y = actual[i][0]
            x = actual[i][1]
            if (y >= 0) and (y < len(tab)) and (x >= 0) and (x < len(tab[0])) and (tab[y][x] != -1):
                newPrevious.append(actual[i])

        previous.insert(0, newPrevious)

        for i in range(0, min(len(interpolateColor), len(previous))):
            for j in range(0, len(previous[i])):
                y = previous[i][j][0]
                x = previous[i][j][1]
                self.p[tab[y][x]] = interpolateColor[i]

        previousFlat = self.matFlat(previous)

        self.p.show()
        actual = []

        for i in range(0, len(newPrevious)):
            y = newPrevious[i][0]
            x = newPrevious[i][1]
            if (y + 1, x) not in previousFlat and (y + 1, x) not in actual:
                actual.append((y + 1, x))
            if (y - 1, x) not in previousFlat and (y - 1, x) not in actual:
                actual.append((y - 1, x))
            if (y, x + 1) not in previousFlat and (y, x + 1) not in actual:
                actual.append((y, x + 1))
            if (y, x - 1) not in previousFlat and (y, x - 1) not in actual:
                actual.append((y, x - 1))

        time.sleep(0.05)
        return self.rippleEffect(tab, actual, previous, counter+1)

    def rippleInit(self, tab, actual):
        self.rippleEffect(tab, [actual], [], 0)

    def __init__(self, size: int, pixels: neopixel.NeoPixel, keys: keypad.KeyMatrix, TF: list[list[int]], NF: list[list[int]], SF: list[list[int]], EF: list[list[int]], WF: list[list[int]]):
        self.RAIMBOWCOLOR: int = 0
        self.RAIMBOWDIRECTION: int = 1
        self.CUSTOMRAIMBOWSTEP: int = 0
        self.BRIGHTNESS: int = 0.1
        self.BRIGHTNESS_INCREASE: int = -0.0005

        self.colorEffect: int = 1
        self.color: int = 0
        self.colorSwitch: int = TF[0][0]

        self.size: int = size
        self.p: neopixel.NeoPixel = pixels
        self.k: keypad.KeyMatrix = keys

        self.TF: list[list[int]] = TF
        self.NF: list[list[int]] = NF
        self.SF: list[list[int]] = SF
        self.EF: list[list[int]] = EF
        self.WF: list[list[int]] = WF

        self._CTV: list[list[int]] = self.createCubeTopView() # Cube Top View
        self._CNV: list[list[int]] = self.createCubeNorthView() # Cube North View
        self._CSV: list[list[int]] = self.createCubeSouthView() # Cube South View
        self._CEV: list[list[int]] = self.createCubeEastView() # Cube East View
        self._CWV: list[list[int]] = self.createCubeWestView() # Cube West View

        self.RP: list[list[int]] = self.createRaimbow() # Raimbow Pattern
