import pygame
import math
import heapq

POINT_SELECT_RADIUS = 8
DRAW_GRAPH = False

def vector(a, b):
    return (b[0]-a[0], b[1]-a[1])

def ccw(A, B, C):
    a, b = vector(A, B), vector(A, C)
    return a[0]*b[1] - a[1]*b[0]

def segments_intersect(l1, l2):
    '''
    not cross : 0
    cross : 1
    overlap : 2
    '''
    A, B = l1
    C, D = l2
    if A > B: A, B = B, A
    if C > D: C, D = D, C
    abc = ccw(A, B, C)
    abd = ccw(A, B, D)
    cda = ccw(C, D, A)
    cdb = ccw(C, D, B)
    x = abc*abd
    y = cda*cdb
    if abc == abd == 0:
        if B < C or D < A: return 0
        elif B == C or D == A: return 1
        else: return 2
    elif x <= 0 and y <= 0: return 1
    else: return 0

def segment_intersects_polygon(line, polygon):
    '''
    not cross : 0
    touch : 1
    intersect : 2
    '''
    result = 0
    for i in range(len(polygon)):
        if line[0] == polygon[i] or line[1] == polygon[i] or line[0] == polygon[i-1] or line[1] == polygon[i-1]: result = max(result, 1)
        elif segments_intersect(line, (polygon[i-1], polygon[i])): result = 2
    return result

def is_in_polygon(polygon, p):
    count = 0
    v = (p, (int(1e9), p[1]+1))
    for index in range(len(polygon)):
        line = (polygon[index-1], polygon[index])
        if segments_intersect(line, v): count += 1
    return count % 2 == 1

def dist(a, b):
    v = vector(a, b)
    return math.hypot(*v)

def routing(start, end, buildings, depth=0):
    if depth > 100:
        print(start, end, buildings)
        return [start, end]
    polygons = [[start], [end]]
    for polygon in buildings:
        if segment_intersects_polygon((start, end), polygon):
            polygons.append(polygon)

    table = []
    graph = []
    for polygon in polygons:
        offset = len(table)
        edges = []
        for i in range(len(polygon)):
            edges.append([offset + (i - 1) % len(polygon), offset + (i + 1) % len(polygon)])
            for j, other_point in enumerate(table):
                for other_polygon in polygons:
                    if segment_intersects_polygon((polygon[i], other_point), other_polygon) == 2: break
                else:
                    graph[j].append(offset + i)
                    edges[i].append(j)
        table.extend(polygon)
        graph.extend(edges)

    dist_table = [-1] * len(table)
    connection = [None] * len(table)
    dist_table[0] = 0
    queue = [(0, 0, 0)]
    while queue:
        _, d, x = heapq.heappop(queue)
        if x == 1: break
        if dist_table[x] != d: continue

        for y in graph[x]:
            d_ = dist(table[x], table[y]) + dist_table[x]
            if dist_table[y] != -1 and d_ >= dist_table[y]: continue
            dist_table[y] = d_
            connection[y] = x
            heapq.heappush(queue, (d_ + dist(table[1], table[y]), d_, y))

    if DRAW_GRAPH:
        for i in range(len(table)):
            for j in graph[i]:
                pygame.draw.line(screen, (120, 120, 120), table[i], table[j], 1)

    x = 1
    route = [x]
    while x != 0:
        x = connection[x]
        route.append(x)
    route.reverse()

    if len(route) == 2:
        return [table[x] for x in route]
    else:
        new_route = []
        for i in range(len(route) - 1):
            new_route.extend(routing(table[route[i]], table[route[i+1]], buildings, depth+1))
            new_route.pop()
        new_route.append(table[route[-1]])
        return new_route


def main():
    global DRAW_GRAPH

    buildings = []
    start_point = (0, 0)
    end_point = (600, 600)

    # mode 1 : edit point position
    # mode 2 : add point
    # mode 3 : delete point
    mode = None
    selected = None
    while True:
        clock.tick(60)
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    start_point = pos
                elif event.key == pygame.K_2:
                    end_point = pos
                elif event.key == pygame.K_SPACE:
                    DRAW_GRAPH = not DRAW_GRAPH
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    min_dist = 100
                    selected = None
                    for i, polygon in enumerate(buildings):
                        for j, point in enumerate(polygon):
                            d = dist(point, pos)
                            if d < POINT_SELECT_RADIUS and d < min_dist:
                                min_dist = d
                                selected = (i, j)
                    if selected == None:
                        for i, polygon in enumerate(buildings):
                            if is_in_polygon(polygon, pos):
                                selected = (i,)
                        mode = 2
                    else:
                        mode = 1
                elif event.button == pygame.BUTTON_RIGHT:
                    selected = None
                    for i, polygon in enumerate(buildings):
                        if is_in_polygon(polygon, pos):
                            selected = (i,)
                    if selected == None:
                        mode = None
                    else:
                        mode = 3
            elif event.type == pygame.MOUSEBUTTONUP:
                if mode == 1:
                    pass
                elif mode == 2:
                    if selected == None:
                        size = 10
                        x, y = pos
                        polygon = [(x + size, y + size), (x + size, y - size), (x - size, y - size), (x - size, y + size)]
                        buildings.append(polygon)
                    else:
                        polygon = buildings[selected[0]]
                        x = (polygon[0][0] + polygon[-1][0]) // 2
                        y = (polygon[0][1] + polygon[-1][1]) // 2
                        polygon.append((x, y))
                elif mode == 3:
                    polygon = buildings[selected[0]]
                    if len(polygon) > 3: polygon.pop()
                    else: buildings.pop(selected[0])
                mode = None
                selected = None
            elif event.type == pygame.MOUSEMOTION:
                if mode == 1:
                    buildings[selected[0]][selected[1]] = pos
                elif mode == 2:
                    if selected is not None:
                        if not is_in_polygon(buildings[selected[0]], pos):
                            mode = None
                            selected = None
                elif mode == 3:
                    if not is_in_polygon(buildings[selected[0]], pos):
                        mode = None
                        selected = None

        screen.fill((255, 255, 255))

        pygame.draw.circle(screen, (255, 0, 0), start_point, 5)
        pygame.draw.circle(screen, (0, 255, 0), end_point, 5)
        for polygon in buildings:
            pygame.draw.polygon(screen, (0, 0, 0), polygon, 2)
            for point in polygon:
                pygame.draw.circle(screen, (0, 0, 0), point, 3)

        route = routing(start_point, end_point, buildings)
        for i in range(len(route) - 1):
            pygame.draw.line(screen, (0, 0, 255), route[i], route[i+1], 1)
        pygame.display.flip()

if __name__  == "__main__":
    pygame.init()
    size = (600, 600)
    screen = pygame.display.set_mode(size)
    clock = pygame.time.Clock()

    main()