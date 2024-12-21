import random
import math
from PIL import Image

# Configuration
MAP_WIDTH = 30
MAP_HEIGHT = 30
POPULATION_SIZE = 50
MUTATION_RATE = 0.03
GENERATIONS = 200

PLAINS = 0
MOUNTAIN = 1
RIVER = 2
ROCK = 3

TILE_IMAGES = {
    PLAINS: Image.open("grass.png"),
    MOUNTAIN: Image.open("mountain.png"),
    RIVER: Image.open("river.png"),
    ROCK: Image.open("rock.png")
}

TILE_SIZE = TILE_IMAGES[PLAINS].size  # e.g. (64, 64)


def generate_random_map():
    """
    Generate a random 30x30 map (2D list) of tile types (0-3).
    Partially constrain edges to be mountains from the start.
    """
    m = []
    for y in range(MAP_HEIGHT):
        row = []
        for x in range(MAP_WIDTH):
            # Force edges to be MOUNTAIN
            if x == 0 or x == MAP_WIDTH - 1 or y == 0 or y == MAP_HEIGHT - 1:
                row.append(MOUNTAIN)
            else:
                # Random tile among {PLAINS, MOUNTAIN, RIVER, ROCK}
                row.append(random.randint(0, 3))
        m.append(row)
    return m


def is_in_central_circle(x, y, center=15, radius=8):
    dist_sq = (x - center) ** 2 + (y - center) ** 2
    return dist_sq <= radius ** 2


def enforce_constraints(tile_map):
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if is_in_central_circle(x, y):
                tile_map[y][x] = PLAINS

    for x in range(MAP_WIDTH):
        tile_map[0][x] = MOUNTAIN
        tile_map[MAP_HEIGHT - 1][x] = MOUNTAIN
    for y in range(MAP_HEIGHT):
        tile_map[y][0] = MOUNTAIN
        tile_map[y][MAP_WIDTH - 1] = MOUNTAIN


def get_river_row(x):
    """
    Return the y-position for the river at column x.
    This function defines a slight curvature (sine wave, for instance).
    """
    return int(15 + 3 * math.sin(2 * math.pi * x / MAP_WIDTH))


def place_river(tile_map):
    for x in range(MAP_WIDTH):
        y_river = get_river_row(x)

        for offset in [-1, 0, 1]:
            yy = y_river + offset
            if 0 < yy < MAP_HEIGHT - 1:
                tile_map[yy][x] = RIVER


def place_rocks(tile_map, num_clusters=8):
    """
    Randomly place several small clusters (3-5 tiles) of ROCK
    on the PLAINS. We do this after the river & circle constraints.
    """
    for _ in range(num_clusters):
        while True:
            cx = random.randint(5, MAP_WIDTH - 5)
            cy = random.randint(5, MAP_HEIGHT - 5)
            if tile_map[cy][cx] != MOUNTAIN:
                break
        cluster_size = random.randint(3, 5)
        for _ in range(cluster_size):
            nx = cx + random.randint(-1, 1)
            ny = cy + random.randint(-1, 1)
            if 0 < nx < MAP_WIDTH - 1 and 0 < ny < MAP_HEIGHT - 1:
                if tile_map[ny][nx] == PLAINS:
                    tile_map[ny][nx] = ROCK


def calculate_fitness(tile_map):
    score = 0

    # 1. Central circle should be plains
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if is_in_central_circle(x, y):
                if tile_map[y][x] == PLAINS:
                    score += 1
                else:
                    score -= 1  # penalty if not plains

    # 2. Edges should be mountains
    for x in range(MAP_WIDTH):
        for y in range(MAP_HEIGHT):
            if tile_map[y][x] == MOUNTAIN:
                if is_in_central_circle(x, y, 15, 13):
                    score -= 10
                else:
                    score += 5

    # 3. check if river is near get_river_row(x)
    for x in range(MAP_WIDTH):
        y_river = get_river_row(x)
        found_river_in_band = False
        for offset in [-1, 0, 1]:
            yy = y_river + offset
            if 0 <= yy < MAP_HEIGHT and tile_map[yy][x] == RIVER:
                found_river_in_band = True
                break
        if found_river_in_band:
            score += 50
        else:
            score -= 500

    # 4. Rough measure for rock clusters on plains
    rock_count = 0
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if tile_map[y][x] == ROCK:
                rock_count += 1

    if 20 <= rock_count <= 40:
        score += 50
    else:
        score -= abs(rock_count - 22)  # penalty if too many/few

    return score


def crossover(map1, map2):
    child = []
    mid = MAP_HEIGHT // 2
    for y in range(MAP_HEIGHT):
        if y < mid:
            child.append(map1[y][:])  # copy row from map1
        else:
            child.append(map2[y][:])  # copy row from map2
    return child


def mutate(tile_map):
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if random.random() < MUTATION_RATE:
                tile_map[y][x] = random.randint(0, 3)

    enforce_constraints(tile_map)

    place_river(tile_map)

    for yy in range(MAP_HEIGHT):
        for xx in range(MAP_WIDTH):
            if tile_map[yy][xx] == ROCK:
                tile_map[yy][xx] = PLAINS

    place_rocks(tile_map)

    return tile_map


def main():
   for i in range(10):
       # 1. Initialize population
       population = []
       for _ in range(POPULATION_SIZE):
           individual = generate_random_map()

           enforce_constraints(individual)
           place_river(individual)
           place_rocks(individual)
           population.append(individual)

       for generation in range(GENERATIONS):
           fitness_scores = [calculate_fitness(ind) for ind in population]

           best_score = max(fitness_scores)
           avg_score = sum(fitness_scores) / len(fitness_scores)

           if generation % 10 == 0:
               print(f"Generation {generation + 1} - Best: {best_score}, Avg: {int(avg_score)}")

           # Select parents (elite selection + random selection, for example)
           sorted_pop = [x for _, x in sorted(zip(fitness_scores, population), key=lambda x: x[0], reverse=True)]

           # Take top 5 as elites
           new_population = sorted_pop[:5]

           while len(new_population) < POPULATION_SIZE:
               parent1 = random.choice(sorted_pop[:15])
               parent2 = random.choice(sorted_pop[:15])
               child = crossover(parent1, parent2)
               child = mutate(child)
               new_population.append(child)

           population = new_population

       final_fitness_scores = [calculate_fitness(ind) for ind in population]
       best_index = max(range(len(population)), key=lambda i: final_fitness_scores[i])
       best_map = population[best_index]

       render_map_image(best_map, f"generated_map{i}.png")
       print("Best map saved to generated_map.png")


def render_map_image(tile_map, output_path):
    out_width = MAP_WIDTH * TILE_SIZE[0]
    out_height = MAP_HEIGHT * TILE_SIZE[1]
    out_img = Image.new('RGB', (out_width, out_height))

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tile_type = tile_map[y][x]
            tile_img = TILE_IMAGES[tile_type]

            out_img.paste(tile_img, (x * TILE_SIZE[0], y * TILE_SIZE[1]))

    out_img.save(output_path)


if __name__ == "__main__":
    main()
